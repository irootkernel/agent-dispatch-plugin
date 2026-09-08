# Release Handoff Runbook: Exact-Commit Candidate

Target: declaring and verifying an immutable release candidate for
`agent-dispatch-plugin` v0.1.0.
Environment: Darwin arm64 with Hermes (v0.20.5 or newer) on `PATH` and the pinned
Agent Dispatch v0.1.6 darwin/arm64 release artifact (SHA-256
`ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479`).

## The immutable review target

The immutable review target for a release candidate is **the exact Git
commit that introduces this runbook plus every task commit it rests
on** — one revision carrying the complete qualified surface: the frozen
contracts, the runner boundary, the ten tools, the security and
compatibility evidence, the clean-clone proof, the installation
lifecycle qualification, and the operations documentation. A candidate
is declared by its full 40-character commit object ID; nothing else
(dates, branches, or working trees) identifies it.

## Candidate gate set

Every candidate must pass, from a clean clone of the exact revision
(the clean-clone runbook records the procedure):

1. `uv sync` — the pinned environment resolves from `uv.lock`.
2. `make test` — the prepare gates (format, lint, type check,
   byte-compilation, the frozen-contract oracle, manifest/registry
   parity), the deterministic unit suite, the integration suite
   including the fresh-session ten-tool inventory, and the Plugin
   Doctor e2e stage.
3. `make test-qualify` — the disposable action-level compatibility
   matrix (every advertised public action through the real Hermes
   runtime against the pinned artifact) and the disposable installation
   lifecycle (disabled default, explicit plugin and toolset enablement,
   disablement, residue-free removal).

Together these are exactly the EPIC-004 release gates plus the EPIC-005
distribution gates; the qualification runbook records the artifact
identities and adjudicated boundaries they carry.

## Release checklist

- [ ] The candidate revision is named by its full commit object ID and
      every member task of the delivery epic is Completed in the
      roadmap with its named evidence.
- [ ] The clean-clone gate set above passes at the exact revision.
- [ ] The whole-epic validation review of the candidate is committed
      with complete coverage, a passing CI decision, and every finding
      dispositioned.
- [ ] The compatibility matrix is current for the pinned artifacts
      (single-entry until a second in-range Agent Dispatch release
      exists).
- [ ] The operations runbooks form the complete index
      (`docs/ops/README.md`) with no required topic unmapped.

## Separate authorization boundary

Commit, push, tag, publication, installation, and activation are
**separate states, each requiring separate authorization**:

| Action | Boundary |
|---|---|
| Commit | the repository's normal commit boundary (task commits exist already) |
| Push | a separately authorized push to the public remote; this repository currently has none configured |
| Tag | a separately authorized annotated tag naming the exact candidate object ID |
| Publication | a separately authorized release publication (GitHub Release or equivalent) carrying the artifact identities |
| Installation | an operator-side action in a Hermes profile (the installation lifecycle runbook) |
| Activation | operator-side plugin enablement and toolset enablement (separate states, separate commands) |

Nothing in this repository's content, its documentation, or its
evidence grants any of these authorizations. Until each is explicitly
granted by the maintainer, the release candidate remains exactly that:
a verified, immutable revision awaiting release decisions.

## Success verification

A release candidate is verified when the checklist above is complete
and the final gate set has passed from a clean clone of the exact
revision, recorded against that commit object ID in the epic's
validation evidence.
