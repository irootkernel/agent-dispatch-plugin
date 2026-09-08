# ADR-003: Closed Result Boundaries and Command-Specific Envelope Identity

Status: Accepted

## Context

The PRD wraps every output in the plugin-owned
`agent-dispatch-plugin.result/v1` wrapper containing a validated
`agent-dispatch.cli/v1` envelope, requires the runner to validate command
identity and exit consistency, forbids flattening or reinterpreting domain
values, and permits ignoring unconsumed additive fields only where a contract
explicitly permits forward compatibility. TASK-001 freezes the precise
command-specific result schemas.

## Decision

Three closed boundaries and one open interior, expressed in
`contracts/v0.1.0/schemas/`:

- The wrapper (`wrapper.schema.json`) is closed: exactly `schema_version`,
  `ok`, `operation`, `exit_code`, `agent_dispatch`, `error`, `diagnostics`,
  with the five status members always required and the two evidence carriers
  governed by the carrier rule below; the operation is one of the ten tool
  names; diagnostics are bounded (16 items, 512 characters each).
- Carrier rule (clarified in TASK-001 review remediation): on `ok: true` the
  validated envelope (itself `ok: true`) is the sole carrier; on `ok: false`
  exactly one carrier is present — the validated envelope (itself `ok: false`)
  for a domain rejection, or the closed plugin error object when no envelope
  exists (timeout, output limits, unavailable binary, malformed output,
  execution or redaction failure). `exit_code` is 0 on validated success, also 3 for a validated `doctor`
  findings response (ADR-008), the
  Agent Dispatch exit status on domain rejection, and -1 when no process
  completed.
- The envelope (`envelope.schema.json`) is closed at its member set:
  `api_version` is the constant `agent-dispatch.cli/v1`, `command` is a
  non-empty bounded string, `ok` is boolean, and consistency rules require
  `result` exactly when `ok` is true and the closed `error` object
  (`code`, `category`, `message`, `retryable`) exactly when `ok` is false.
- The plugin error object (`error.schema.json`) is closed with the ten-code
  enum and `retryable` fixed to false.
- The envelope's `result` member is the single open interior: any object or
  array of unflattened domain values, where additive fields are explicitly
  permitted and may be ignored. No other boundary accepts additive fields.

Command-specific identity is per action, not per tool: each catalog action
carries an `expected_command` such as `route show` or `config validate`
(observed shape: the upstream envelope reports the full command path). The
runner must require `envelope.command` to equal the action's
`expected_command` exactly; a mismatch is `contract_mismatch`. Success
envelopes arrive on stdout as one JSON object; error reporting arrives via
the documented exit codes and stderr, which never re-enters results unredacted.

## Consequences

- Malformed envelopes, unknown protocol versions, member-set additions,
  success/error inconsistency, and command mismatches fail validation with
  closed codes instead of leaking raw output.
- The plugin stays a non-semantic adapter: it validates shape and identity,
  never domain meaning.
- If upstream introduces a new envelope member outside `result`, it fails
  closed pending a reviewed amendment; that is the intended posture.

## Alternatives

- Per-tool deep domain result schemas: rejected as a second semantic authority
  the PRD forbids.
- Fully open envelope (additionalProperties true): rejected as weakening the
  output-poisoning control the threat model requires.

## Verification

`fixtures/envelope.cases.json` and `fixtures/wrapper.cases.json` exercise
every consistency rule, the open-interior permission, and each invalid
boundary; `contracts/validate.py` enforces closed boundaries structurally.
