# Specifications

Specifications define externally observable behavior and acceptance. They do
not track implementation progress.

- docs/specs/PRD.md is the canonical product requirements document. The
  current development catalog identifies Plugin v0.1.2 and preserves the
  ten-tool v0.1.0 public contract. Darwin arm64, Linux amd64, and Linux arm64
  qualification records are under docs/implementation-tips/.
- docs/specs/contracts.md binds the PRD to the frozen v0.1.0 contract
  artifacts in contracts/v0.1.0/ and their deterministic offline gate.

The planned EPIC-007 two-node inspection scope is described in
[its adopted dossier](../todo/TODO-SYNC-INSPECTION.md). TASK-023 owns the
canonical PRD and versioned contract amendment; the dossier is not itself
an amendment to the current ten-tool surface.

Changes to scope, public tools, fixed command mappings, authority, compatibility
claims, error contracts, or release gates require explicit maintainer approval.
