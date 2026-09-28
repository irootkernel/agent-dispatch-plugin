# Specifications

Specifications define externally observable behavior and acceptance. They do
not track implementation progress.

- docs/specs/PRD.md is the canonical product requirements document. The
  current development catalog identifies Plugin v0.1.2 and preserves the
  ten-tool v0.1.0 public contract. Darwin arm64, Linux amd64, and Linux arm64
  qualification records are under docs/implementation-tips/.
- docs/specs/contracts.md binds the PRD to the frozen v0.1.0 and approved
  v0.2.0 contracts and their deterministic offline gates.

The In Progress EPIC-007 two-node inspection scope is described in
[its adopted dossier](../todo/TODO-SYNC-INSPECTION.md). TASK-023 owns the
approved PRD and versioned contract amendment; TASK-024 activates the new
runtime surface. The dossier does not itself amend either contract.

Changes to scope, public tools, fixed command mappings, authority, compatibility
claims, error contracts, or release gates require explicit maintainer approval.
