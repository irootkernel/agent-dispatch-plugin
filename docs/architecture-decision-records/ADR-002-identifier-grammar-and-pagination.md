# ADR-002: Identifier Grammar, State Tokens, and Pagination Bounds

Status: Accepted

## Context

The PRD requires documented length and grammar constraints for every
identifier, rejection before process creation, literal preservation after
validation, list limits from 1 through 100 with default 25, and non-negative
offsets with an implementation-documented upper bound. The PRD does not fix
the concrete grammar or the offset bound; TASK-001 freezes them.

## Decision

- All identifier parameters (`route_id`, `dispatch_id`, `receipt_id`,
  `aggregate_id`, `quarantine_id`, and the `route`, `dispatch`, `sink`
  filters) match `^[A-Za-z0-9][A-Za-z0-9._:@-]{0,127}$` with a 128-character
  maximum. The colon is included because upstream addresses qualified
  identities with it; slash, whitespace, shell metacharacters, option
  prefixes, and control bytes are excluded.
- Unenumerated upstream state filters (`state` on dispatches list and
  notifications list) match the lowercase token grammar
  `^[a-z][a-z0-9-]{0,63}$`. Enumerated upstream sets stay closed: receipt
  `kind` is `acceptance|execution_projection|work` and quarantine `state` is
  `held|released|discarded|superseded`, both documented by the Agent Dispatch
  v0.1.6 command help.
- Pagination: `limit` is an integer from 1 through 100, default 25; `offset`
  is an integer from 0 through 1,000,000. The offset bound is the documented
  plugin-side upper bound required by the PRD.
- Diagnostic bounds: at most 16 diagnostics per result, each at most 512
  characters; plugin error messages are at most 512 characters.

The grammar is deliberately a conservative fail-closed allowlist. It may
reject an exotic upstream identifier that the real product would accept; that
rejection is the designed posture, and widening requires an ADR amendment
backed by qualification evidence.

## Consequences

- Injection, traversal, option-prefix, and whitespace payloads fail schema
  validation before any process is created.
- Identifiers are preserved byte-for-byte after validation; handlers never
  normalize them.
- A real upstream identifier outside the grammar surfaces as
  `invalid_argument` during qualification, which is a contract decision to
  review, not a runner defect.

## Alternatives

- Passthrough with per-command denylist checks: rejected as weaker than a
  positive allowlist and harder to test.
- Deriving the grammar from live CLI observation at runtime: rejected because
  the contract must be frozen, offline-testable, and reviewable.

## Verification

`contracts/validate.py` asserts pattern, length, and bound consistency across
every tool schema, and boundary fixtures (1/100/0/1,000,000 pass; 0/101/-1/
1,000,001 fail) exercise the frozen values.
