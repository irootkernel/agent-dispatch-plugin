# EPIC-002 Secure Runner

Status: Adopted
Roadmap: EPIC-002 in docs/roadmap/README.md
Tasks: TASK-004, TASK-005, TASK-006
Depends on: EPIC-001

## Outcome

Make runner.py the sole fail-closed boundary between Hermes tools and the
trusted Agent Dispatch executable.

## Delivery

- Resolve immutable plugin configuration and verify platform, executable path,
  executable digest, trusted config path, and supported version.
- Construct only registered fixed argv templates with shell false, a neutral
  cwd, minimal environment, and closed extra descriptors.
- Drain both streams concurrently, enforce the PRD byte and time limits,
  terminate the entire process group, and never retry.
- Validate the envelope and command identity, map exit behavior into the closed
  error set, and redact bounded diagnostics.

## Decisions to record

- Neutral cwd and minimal environment allowlist.
- Safe non-symlink path verification and time-of-check handling.
- Concurrent capture mechanism and process-group termination implementation.
- Diagnostic field bounds and redaction pipeline.

## Acceptance

Tests prove fixed argv, no shell, no model-controlled execution settings, binary
and config trust failures, version rejection, deadline and overflow behavior,
TERM-to-force-kill behavior, no retry, malformed output rejection, contract
mismatch rejection, partial-output disposal, and seeded-secret redaction.

## Non-goals

Direct SQLite access, domain-state interpretation, automatic remediation, tool
roster changes, and release qualification.

## Guidance inherited from EPIC-001

- Verify with the real Agent Dispatch binary that the PRD-documented
  `quarantine list --route/--limit` filters and the absence of a
  notifications `--offset` filter match actual flag support; a mismatch is
  an upstream compatibility finding, not a contract change.
- Reuse contracts/v0.1.0 fixtures for envelope, wrapper, and error
  validation cases before writing new ones.
- Derive command descriptors from contracts/v0.1.0/catalog.json through the
  registry and never hand-edit derived views (ADR-001).
