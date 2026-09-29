# Specifications

Specifications define externally observable behavior and acceptance. They do
not track implementation progress.

- docs/specs/PRD.md is the canonical product requirements document. The
  current development catalog identifies Plugin v0.2.0 and thirteen registered
  tools while preserving the ten-tool v0.1.0 baseline. Native v0.2.0 sync-read
  qualification records cover Darwin arm64 and Linux arm64. The Linux amd64
  record under docs/implementation-tips/ covers the historical v0.1.8 ten-tool
  matrix; native v0.2.0 qualification is deferred to EPIC-009/TASK-033.
- docs/specs/contracts.md binds the PRD to the frozen v0.1.0 and approved
  v0.2.0 contracts and their deterministic offline gates.

The Completed EPIC-007 two-node inspection scope is defined by the
[PRD amendment](PRD.md#approved-v020-two-node-inspection-amendment-epic-007--task-023)
and [v0.2.0 contract](contracts.md). TASK-023 owns the approved amendment;
TASK-024 activated the new runtime surface. The [roadmap](../roadmap/README.md)
owns delivery lifecycle.

Changes to scope, public tools, fixed command mappings, authority, compatibility
claims, error contracts, or release gates require explicit maintainer approval.
