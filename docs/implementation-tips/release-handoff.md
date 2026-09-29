# Release Handoff Runbook: Exact-Commit Candidate

Target: declaring and verifying an immutable release candidate. The original
v0.1.0 handoff remains historical; the current EPIC-007 development handoff
is below.
Environment: each claimed native host with Hermes (v0.20.5 or newer) on
`PATH` and its catalog-pinned legacy and v0.2.0 Agent Dispatch artifacts;
see the [qualification matrices](README.md#verify-and-hand-off).

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
   byte-compilation, both contract oracles, manifest/registry
   parity), the deterministic unit suite, the integration suite
   including the fresh-session thirteen-tool inventory, and the Plugin
   Doctor e2e stage.
3. `make test-qualify` — the disposable action-level compatibility
   matrix (every advertised public action through the real Hermes
   runtime against the host-selected legacy artifacts and pinned v0.2.0
   candidate) and the disposable installation lifecycle (disabled default,
   explicit plugin and toolset enablement, disablement,
   rollback/restoration, residue-free removal). The v0.2.0 stage also
   requires a native user service manager for absent, loaded, and drifted
   sync-service inspection.

Together these are exactly the EPIC-004 release gates plus the EPIC-005
distribution gates; the qualification runbook records the artifact
identities and adjudicated boundaries they carry.

## EPIC-007 development handoff

The committed Plugin implementation basis after TASK-026 is
`938247793115407ae187fc1f64b50e1180d34762`. It pairs with Agent
Dispatch source candidate `6b1c78b19f4cdb69dfd070ea016430f03075b73d`,
the provider bundle at `48f13a4eef68e219a51d188decb8749a5fba9282`,
and contract digest
`sha256:30cf47b1bd854a0271aa9df3e7b37f0cc14cdd86d3f06a65a2cb787c6741131b`.
The per-platform executable digests are in the
[v0.2.0 catalog](../../contracts/v0.2.0/catalog.json). This implementation
basis is not a selected release candidate: TASK-027 documentation and the
remaining EPIC-007 acceptance gate can change the final revision.

TASK-026 ran `make test` (605 unit, 28 integration, one E2E) and
`make test-qualify` (nine Darwin arm64 and seven native Linux arm64 cases)
on the corrected candidate. The qualification includes real Hermes
action dispatch, original ten-tool regressions, and native user service
inspection of absent, loaded, and drifted definitions. The deterministic
security negatives are included in the aggregate. The
[TASK-026 close record](../todo/TODO-SYNC-INSPECTION.md#task-026-close)
states their scope.

Native Linux amd64 v0.2.0 Hermes and systemd user-manager qualification is
still required before EPIC-007 closure or a Linux amd64 v0.2.0 support claim.
The [deferred feedback owner and re-entry gate](../deferred-feedback/README.md#linux-amd64-v020-sync-inspection-qualification)
name the exact work. A final whole-epic audit, cold review, and exact
release-candidate gate remain separate. Neither ARM qualification nor this
handoff authorizes release, installation, activation, or publication.

| EPIC-007 acceptance area | Current authority and result |
|---|---|
| Contract, three fixed reads, pins, and inventory | [PRD amendment](../specs/PRD.md#approved-v020-two-node-inspection-amendment-epic-007--task-023), [catalog](../../contracts/v0.2.0/catalog.json), and [manifest parity](../../TESTING.md); thirteen registered, with zero/ten/thirteen available by trust and capability state |
| Real Hermes actions and failure paths | [TASK-026 close record](../todo/TODO-SYNC-INSPECTION.md#task-026-close) and the [Darwin](qualification-darwin-arm64.md) / [Linux arm64](qualification-linux-arm64.md) qualification runbooks; native Linux amd64 v0.2.0 remains open |
| Status and service interpretation | [Result contracts](../specs/contracts.md), [public guidance](../../README.md#inspect-a-two-node-sync-group), and [operations diagnosis](../ops/troubleshooting.md#sync-status-and-service-evidence-disagree) distinguish disabled/incomplete groups, local projections, service definitions, and listener evidence |
| Inspection-only and legacy behavior | [PRD](../specs/PRD.md), frozen v0.1.0 catalog, and TASK-026 original ten-action regressions; no sync mutation is registered |
| Final Epic and release decision | Native Linux amd64 v0.2.0 evidence and whole-epic cold validation are still required; release QA and publication have their own authorization |

## Release checklist

- [ ] The candidate revision is named by its full commit object ID and
      every member task of the delivery epic is Completed in the
      roadmap with its named evidence.
- [ ] The clean-clone gate set above passes at the exact revision.
- [ ] The whole-epic validation review of the candidate is committed
      with complete coverage, a passing CI decision, and every finding
      dispositioned.
- [ ] The compatibility matrix is current for the host-selected legacy
      artifacts and exact v0.2.0 candidate on each claimed platform.
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
doctor variants against each claimed host's catalog-pinned legacy artifacts:
v0.1.6 and v0.1.7 on Darwin arm64, and the selected highest compatible
release, v0.1.8, on Linux. A passing historical transcript does not establish
this requirement for a new candidate.

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

The v0.1.0 to v0.1.1 next-cycle handoff was completed and v0.1.1 was
published. Its `plugin.version`, derived manifest, Python project, and
lockfile changed together while the v0.1.0 API baseline stayed frozen.
For the current development version and contract, consult the
[roadmap](../roadmap/README.md) and [contract index](../specs/contracts.md).
Choosing a later release target, tagging, and publication belong to the
separate release lifecycle.

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
