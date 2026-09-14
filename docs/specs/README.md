# Specifications

Specifications define externally observable behavior and acceptance. They do
not track implementation progress.

- docs/specs/PRD.md is the canonical product requirements document. The
  living v0.1.1 catalog admits Darwin arm64, Linux amd64, and Linux arm64;
  Darwin arm64 remains the qualified host.
- docs/specs/contracts.md binds the PRD to the frozen v0.1.0 contract
  artifacts in contracts/v0.1.0/ and their deterministic offline gate.

Changes to scope, public tools, fixed command mappings, authority, compatibility
claims, error contracts, or release gates require explicit maintainer approval.
