# ADR-009: Validated Public Sync Identities

Status: Accepted (EPIC-007 / TASK-023; Master approval 2026-09-29)
Supersedes: [ADR-006](ADR-006-closed-errors-diagnostics-redaction.md) for
the three v0.2.0 sync results' explicitly listed identity fields only.

## Context

ADR-006 redacts long hex strings everywhere. Two-node inspection needs the
provider contract digest and selected status revisions or Git targets intact
to compare evidence without treating unrelated hash-shaped text as public.
The core v0.2.0 result fragments are not complete CLI result schemas.

## Decision

The v0.2.0 contract pins the provider bundle and exact platform artifacts.
Before presenting a sync success, the runner verifies the closed CLI
envelope, exact command, successful exit, command-specific result schema,
and empty `side_effects`. It then preserves exact values only at
`sync_provider.public_identity_paths` in the catalog and only when those
fields satisfy their format constraints. The approved paths are
`sync capabilities.result.contract_digest`, `sync status.result.config_revision`,
and each present `latest_publication`, `latest_delivery`, `latest_import`, or
`latest_verification` `target_commit`. The provider currently emits no
status membership revision, so none is exempt.

All other strings and object keys continue through ADR-006 redaction,
including warnings, errors, diagnostics, unknown fields, and adjacent
secret-shaped strings. A malformed result cannot gain an exemption. A
redaction failure still returns the closed `redaction_failure` error. The
wrapper, envelope, error mapping, diagnostics bounds, process limits, and
five redaction categories in ADR-006 are unchanged. The old v0.1.0 result
path retains its original behavior.

## Consequences

Operators can compare the narrow public revision evidence byte for byte.
Adding another identity path, changing its format, or admitting a new
provider build requires a reviewed contract amendment. A record's target
commit is historical local evidence, never proof of fresh pair agreement.

## Alternatives

- Exempt all hex strings: rejected because secret-like neighboring content
  could leave the plugin unchanged.
- Redact every digest: rejected because that removes the exact identity
  evidence required to detect provider and target drift.

## Verification

The v0.2.0 result fixtures cover the exact identity formats, disabled and
enabled status shapes, malformed and non-empty-side-effect results. Runtime
tests must prove exact allowed identities survive while seeded token-like
values in neighboring fields, warnings, errors, and diagnostics do not.
