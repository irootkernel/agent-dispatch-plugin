# Release Handoff Runbook: Exact-Commit Candidate

Target: declaring and verifying an immutable release candidate for
`agent-dispatch-plugin` v0.1.0.
Environment: Darwin arm64 with Hermes (v0.20.5 or newer) on `PATH` and the pinned
Agent Dispatch v0.1.6 darwin/arm64 release artifact (SHA-256
`ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479`).

## The immutable review target

The release owner selects the exact commit to qualify and records its full
40-character Git object ID with the candidate evidence. That revision must
include the contracts, implementation, tests, and documentation intended for
release. Branch names, dates, and working trees do not identify a candidate.
A later change requires a new candidate identity and its applicable gates.

The original TASK-017 handoff defined its target as the commit introducing
this runbook. That historical candidate was
`156ca591132efd6adc9b1e83553b3a2654f3f3b9`; the
[recorded upgrade/rollback transcript](../ops/upgrade-rollback-darwin-arm64.md)
retains that identity. It is not automatically the next release candidate.

Owner: the plugin release maintainer. Prerequisites: a selected committed
revision, the pinned qualification environment, and access appropriate to each
separately authorized release action. Read-only diagnosis begins with
`git status --short`, `git rev-parse HEAD`, and `git remote -v`; confirm the
candidate and intended destination before preparing any publication.

## Candidate gate set

Every candidate must pass, from a clean clone of the exact revision
([clean-clone verification](clean-clone-verification.md) records the procedure):

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
- [ ] The doctor acceptance gap below has an explicit resolution.
- [ ] The operations runbooks form the complete index
      ([operations index](../ops/README.md)) with no required topic unmapped.

## Compatibility acceptance gap

The [PRD](../specs/PRD.md) requires successful real execution of every advertised
action. The [historical qualification](qualification-darwin-arm64.md) instead
asserts `contract_mismatch` for both doctor variants at the documented Watchman
PATH boundary, supplemented by successful fake-executable tests. Its historical
non-blocking disposition does not amend the PRD.

Before declaring a new candidate ready, plugin maintainers and the release
owner must reconcile this difference through successful evidence, a fix, or an
explicit canonical amendment. Passing the existing qualification suite alone
does not resolve it. This documentation migration changes neither the gate nor
the historical disposition.

## Separate authorization boundary

Commit, push, tag, publication, installation, and activation are
**separate states, each requiring separate authorization**:

| Action | Boundary |
|---|---|
| Commit | the repository's normal commit boundary (task commits exist already) |
| Push | a separately authorized push to the verified remote destination (`git remote -v`) |
| Tag | a separately authorized annotated tag naming the exact candidate object ID |
| Publication | a separately authorized release publication (GitHub Release or equivalent) carrying the artifact identities |
| Installation | an operator-side action in a Hermes profile (the installation lifecycle runbook) |
| Activation | operator-side plugin enablement and toolset enablement (separate states, separate commands) |

Nothing in this repository's content, its documentation, or its
evidence grants any of these authorizations. Until each is explicitly
granted by the maintainer, the release candidate remains exactly that:
an immutable revision awaiting any outstanding verification and release decisions.

## Success verification

A release candidate is verified when the checklist above is complete
and the final gate set has passed from a clean clone of the exact
revision, recorded against that commit object ID in the epic's
validation evidence.

## Failure recovery

If a gate fails or candidate contents change, stop release preparation, record
the failure against that candidate, and return it to the owning maintainer.
Fixes require a new committed candidate and fresh evidence; do not reuse the
historical passing transcript. For an installed-profile regression, use the
[upgrade and rollback runbook](../ops/upgrade-rollback-darwin-arm64.md).
Publication correction requires a separate release-owner decision; this guide
does not authorize deleting or replacing a published tag.
