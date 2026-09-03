# ADR-006: Closed Errors, Bounded Diagnostics, and Defense-in-Depth Redaction

Status: Accepted

## Context

The PRD requires the runner to validate the envelope against the frozen
contracts — API version, command identity, parse completeness, required
fields, types, closed enums, output bounds, and exit consistency — to map
exit behavior onto the closed error set, to keep diagnostics bounded
(16 items of 512 characters), to return bounded redacted structured errors
rather than raising into Hermes, and to apply the five frozen
defense-in-depth redaction rules to diagnostics and wrapped results. The
runtime is dependency-free, so the frozen JSON Schema files remain the
authority and `envelopes.py` derives a pure-stdlib mirror of them. The
dossier names the diagnostic field bounds and the redaction pipeline as a
decision to record.

## Decision

- **Closed envelope validation mirrors the frozen schema.** One validator
  enforces the closed member set, the `agent-dispatch.cli/v1` constant, the
  bounded command string, the required-iff-ok carrier pair (`result`
  exactly when ok true, the closed `error` object exactly when ok false),
  the closed error member set with its bounds, the warnings bound
  (64 items of 1024) and the trace id bound (128). Unparseable output or an
  unknown protocol version closes as `malformed_json`; every structurally
  parseable violation — unknown members, missing or mistyped members,
  carrier inconsistency, bound breaches, a command that does not equal the
  action's `expected_command`, and a success envelope paired with a nonzero
  exit — closes as `contract_mismatch`.
- **The wrapper follows the closed carrier rule.** On validated success the
  redacted envelope (itself ok true) is the sole carrier with exit code 0;
  on a validated domain rejection the redacted envelope (itself ok false)
  is the sole carrier with the Agent Dispatch exit status; when no
  validated envelope exists, the closed plugin error object is the sole
  carrier and the exit code is the process status when one completed and
  -1 when it did not.
- **Diagnostics are bounded and never carry raw output.** Only the
  plugin-owned failure paths produce diagnostics: fixed bounded strings for
  timeout and overflow (where every captured byte is discarded) and a
  bounded, redacted tail of at most the final 16 stderr lines for
  `malformed_json` and `contract_mismatch`, where no envelope authority
  exists. Success and domain rejection carry no stderr diagnostics; the
  envelope's own warnings and error member already carry upstream
  information.
- **The five redaction rules run over every string.** Authorization values,
  secret references that reveal protected paths, token-like strings
  (32-plus hex and 40-plus base64 runs), sensitive webhook URLs (hosts
  under `hooks.` or any webhook path), and absolute paths outside the
  configured binary and config display policy are redacted — in envelope
  strings recursively, object keys included (the open `result` interior
  included, because rule 1 forbids authorization values in wrapped
  results), and in every diagnostic line. Protected-location paths redact
  wholly; other absolute paths keep only their final component so a
  diagnostic can still name what was involved. Allowed display paths are
  masked first and restored last so the other rules never rewrite them.
- **Redaction failure is its own closed error.** If the redaction pipeline
  itself raises, the result closes as `redaction_failure` with the
  inspection output discarded; a redaction outage can never leak the very
  content it exists to guard. A redacted envelope carries one bounded
  diagnostic noting that redactable content was removed.

## Consequences

- Unknown protocol versions, member additions, carrier inconsistencies,
  command spoofing, and exit inconsistencies all fail closed with distinct
  codes instead of leaking raw output.
- Legitimate long hashes in domain output are redacted like tokens; the
  plugin is a shape validator, not a secret classifier, so over-redaction
  is the accepted failure direction.
- Diagnostics from a hostile or chatty command are capped at 16 items of
  512 characters from the stderr tail, after redaction.
- The envelope's open `result` interior passes through structurally
  untouched except for string redaction; the plugin still never interprets
  domain meaning.

## Alternatives

- Runtime JSON Schema validation with jsonschema: rejected — the runtime is
  dependency-free by contract; the schema stays the authority and this
  module is its derived mirror, exercised by the frozen fixtures.
- Redacting only diagnostics, passing envelopes verbatim: rejected — rule 1
  explicitly covers wrapped results.
- Dropping envelopes that contain redactable content: rejected — a seeded
  secret inside one result string would erase an otherwise valid
  inspection; redaction preserves the domain shape.

## Verification

`tests/unit/test_validation.py` drives the validator with the frozen
envelope fixtures, proves every structural violation, command identity
mismatch, and exit inconsistency closes as contract_mismatch, proves
seeded bearer tokens, hex tokens, API keys, webhook URLs, and secret and
plain absolute paths never survive the output boundary while allowed
display paths do, proves the stderr-tail diagnostics stay within 16 by 512
after redaction, proves a broken pipeline closes as redaction_failure, and
validates every produced wrapper shape against the frozen wrapper schema.
