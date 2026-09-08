# Release Handoff Runbook: Exact-Commit Candidate

Target: declaring and verifying an immutable release candidate for
`agent-dispatch-plugin` v0.1.0.
Environment: Darwin arm64 with Hermes (v0.20.5 or newer) on `PATH` and both
pinned Agent Dispatch v0.1.6 and v0.1.7 release artifacts from the
[qualification matrix](qualification-darwin-arm64.md).

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

Every candidate must pass, from a full-history clean clone of the exact revision
([clean-clone verification](clean-clone-verification.md) records the procedure):

1. `uv sync` — the pinned environment resolves from `uv.lock`.
2. `make test` — the prepare gates (format, lint, type check,
   byte-compilation, the frozen-contract oracle, manifest/registry
   parity), the deterministic unit suite, the integration suite
   including the fresh-session ten-tool inventory, and the Plugin
   Doctor e2e stage.
3. `make test-qualify` — the disposable action-level compatibility
   matrix (every advertised public action through the real Hermes
   runtime against both pinned artifacts) and the disposable installation
   lifecycle (disabled default, explicit plugin and toolset enablement,
   disablement, rollback/restoration, residue-free removal).

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
      (minimum v0.1.6 and latest compatible v0.1.7).
- [ ] The doctor acceptance gap below has an explicit resolution.
- [ ] The operations runbooks form the complete index
      ([operations index](../ops/README.md)) with no required topic unmapped.

## Compatibility acceptance gap

The original doctor gap is resolved by the approved
[ADR-008](../architecture-decision-records/ADR-008-doctor-findings-exit-status.md)
contract amendment: retrieving doctor findings at exit 3 is a successful
inspection, not a claim of system health. The previous fake-only success
and real `contract_mismatch` expectation are no longer acceptable evidence.
Every new candidate must deliver the findings through real Hermes for both
doctor variants against v0.1.6 and v0.1.7. A passing historical transcript
does not establish this requirement.

## Changelog, publication, and the next cycle

Root [CHANGELOG.md](../../CHANGELOG.md) is the sole product release-history
source. Use concise `Added`, `Changed`, and `Fixed` outcomes, newest first;
keep test counts and detailed evidence outside it. A selected pending release
uses `## vX.Y.Z - Unreleased`; date it with the actual publication day before
freezing the final candidate. The hosted release copies those outcomes and
adds requirements, installation links, and its exact-artifact validation summary.

Generate the source tarball from `git archive` of the verified candidate,
with one top-level versioned directory. Publish it with `SHA256SUMS` and a
bounded validation summary. Verify the extracted plugin using Plugin Doctor
before publication and verify downloaded asset digests afterward. The plugin
never bundles the separately released Agent Dispatch executable.

Commit review adjudication before choosing the final candidate. Attach the
final clean-clone validation summary to the release rather than making a
self-referential evidence commit. Any later source change creates a new
candidate and requires applicable checks again.

After v0.1.0 publication is verified, the approved successor is v0.1.1.
In a separate commit, add its empty `Unreleased` section and update catalog
`plugin.version`, the derived manifest, Python project, and lockfile to 0.1.1.
Catalog `product_version`, the contract directory, and schema URNs remain the
v0.1.0 API baseline. Validate release-version parity, contracts, and `make test`
then push main. Do not tag or publish the development version. Preserve the
v0.1.0 tag and release assets exactly.

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
