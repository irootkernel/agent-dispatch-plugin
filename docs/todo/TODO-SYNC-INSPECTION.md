# EPIC-007 Two-Node Sync Inspection and Diagnostics

Status: In Progress (the roadmap owns lifecycle)
Roadmap: EPIC-007 / TASK-023 through TASK-027 in docs/roadmap/README.md
Depends on: EPIC-006 Completed; Agent Dispatch E20-E22 Completed
Next eligible task: TASK-024 after TASK-023 commit
After completion: no automatic next epic; EPIC-008 remains Deferred
Planned Plugin target: v0.2.0, with a new versioned public contract

## Provenance and admission boundary

The repository-sibling source documents `../agent-dispatch-plugin.md` and
`../agent-dispatch.md` described an N-member program with a Dispatch E26
handoff, six sync read tools, and a management request tool. They remain
proposal provenance, not the implemented provider contract. Dispatch
ADR-0023 / D-030 narrowed the v0.2.0 target to exactly two active nodes;
its E20-E22 roadmap is Completed.
This dossier was prepared against Dispatch HEAD
`48f13a4eef68e219a51d188decb8749a5fba9282`. The E22 qualification
record names committed code candidate `6b1c78b19f4cdb69dfd070ea016430f03075b73d`.
Recheck both identities and the provider bundle before TASK-023 changes an
executable contract. Completion of the core epic is not a Plugin release or
qualification claim.

The current Plugin contract still admits Agent Dispatch
`>=0.1.6,<0.2.0` and exactly ten tools. Dispatch v0.2.0 remains unavailable
to it until a canonical Plugin amendment and action-level qualification.
The checked-in core `dist/` contains v0.1.8 release artifacts, not v0.2.0
qualification artifacts. A development executable that implements sync but
reports v0.1.8 cannot stand in for a correctly identified v0.2.0 candidate.

## Outcome and public surface

Expose only the implemented local read commands through the existing
`agent_dispatch` toolset and sole trusted runner. The proposed addition is
three tools, for a qualified total of thirteen. Their inputs are closed empty
objects; a new optional trusted Plugin setting `sync_group_id` selects the
one configured group for the two group-scoped commands. It must match the
provider's group grammar. The model cannot select a group, config, executable,
remote, ref, endpoint, file, or flag.

| Tool | Fixed provider command | Evidence returned |
|---|---|---|
| `agent_dispatch_sync_capabilities` | `sync capabilities --output json` | Provider contract version/digest and supported capabilities |
| `agent_dispatch_sync_status` | `sync status --group GROUP --output json` | Local group/control posture, expected two nodes, latest publication/delivery/import/verification, recovery and health evidence |
| `agent_dispatch_sync_service_inspect` | `sync service inspect --group GROUP --output json` | Managed definition, digest match, load/config posture; not listener reachability |

The trusted runner supplies its pinned `--config` path for `sync status` and
`sync service inspect`. `sync capabilities` accepts only `--output json`;
its fixed argv must omit `--config` even though the runner still validates
the trusted configuration path before the call. The Plugin retains the
existing `agent-dispatch-plugin.result/v1` wrapper and closed error behavior;
the core's `agent-dispatch.cli/v1` envelope and each sync result must be
validated before presentation. No command above starts
fresh verification, fetches Git, applies files, or edits service state.

The v0.2.0 provider bundle at
`docs/contracts/sync-provider-v1/` in Agent Dispatch includes commands,
semantic result fragments, errors, schemas, examples, and `SHA256SUMS`.
Its currently observed semantic `contract_digest` is
`sha256:30cf47b1bd854a0271aa9df3e7b37f0cc14cdd86d3f06a65a2cb787c6741131b`.
The Plugin contract must pin the verified bundle and define its own exact
CLI result validation for the three commands; the provider's
`results.json` fragments are not complete CLI response schemas. A digest,
command, result, or error mismatch blocks admission rather than widening
parsing. Later provider changes require a new reviewed amendment.

## Compatibility and availability rules

- Preserve the qualified original ten-tool behavior for
  `>=0.1.6,<0.2.0`. On v0.2.0, the operator-configured SHA-256 must match
  both the binary and the reviewed platform-specific SHA allowlist in the
  v0.2.0 catalog before any of the thirteen tools can run. Qualify the
  original ten actions again on each admitted candidate. A matching version
  or provider digest alone does not admit another build or later v0.2.x.
- Only expose the three sync tools when trusted binary/config/host checks
  pass, `sync_group_id` is set, and a bounded fixed `sync capabilities`
  probe reports `v1`, the pinned digest, and `contract_read`, `status_read`,
  and `service_inspect`. A missing, malformed, or incompatible probe hides
  all three while preserving independently qualified ordinary inspection.
  Each sync handler repeats the bounded capability/digest check immediately
  before its command, since Hermes may cache availability and may dispatch
  a registered handler directly. A failed check closes without running the
  requested read command.
- With an old compatible core, a missing group setting, or an absent sync
  capability, the model-facing available definitions contain ten tools.
  With the qualified v0.2.0 core, matching capability evidence, and the
  group setting, they contain thirteen. The catalog, derived manifest, and
  registered tool names contain thirteen regardless of availability.
  A disabled configured group may still be inspected and must display its
  disabled state rather than a fabricated healthy sync state. An unqualified
  or unsupported core exposes zero model-facing tools under the trust gate.
- Keep capability detection and handlers on the same fixed runner/trust
  boundary. Never execute an unregistered provider subcommand, query peer
  HTTP, read SQLite, or parse the core config as a second authority.

## Task order and completion evidence

### TASK-023: Admit the provider and contract

Review Dispatch ADR-0023, E22/G18 evidence, CLI specification, checksummed
provider bundle, and exact v0.2.0 source and build identities. Through the
Plugin's change-control process, amend the PRD and introduce a full
`contracts/v0.2.0/` catalog, schemas, fixtures, compatibility rules, and
version metadata while preserving the frozen v0.1.0 contract. Define the
three read mappings, including the `sync capabilities` config-flag exception;
the trusted group setting; the fixed thirteen-name catalog/manifest roster
versus 0/10/13 available definitions; result/error shapes; and the exact
supported version/artifact matrix. Pin reviewed v0.2.0 SHA-256 values per
supported platform in the catalog in addition to the operator SHA check.
Record the source, build, and checksum identity for each candidate; the
platform support claim remains provisional until TASK-026 qualifies it.
Amend the PRD and create an ADR that supersedes ADR-006 while retaining its
unchanged envelope, error, and diagnostic decisions before changing
redaction: only explicitly named, schema-validated public identity fields
(provider `contract_digest` and status target/config/membership revisions)
may retain their exact values. Apply existing redaction to all other
strings, keys, warnings, errors, diagnostics, unknown fields, and malformed
results. Define the allowed paths and formats in the new contract; the old
v0.1.0 behavior remains frozen. If the required maintainer approval, bundle,
or properly stamped candidate is absent, mark the task Blocked with the
missing prerequisite; do not accept a speculative command.

Evidence: reviewed amendment and provider checksums/digest; contract oracle
and negative fixtures for unsupported versions, digest/capability drift,
SHA allowlist mismatch, invalid group configuration, command mismatch,
malformed responses, and secret-shaped content outside the identity allowlist.

TASK-023 close record (2026-09-29): Master approved the canonical PRD and
contract amendment. The v0.2.0 catalog pins Dispatch source candidate
`6b1c78b19f4cdb69dfd070ea016430f03075b73d`, provider bundle commit
`48f13a4eef68e219a51d188decb8749a5fba9282`, semantic digest
`sha256:30cf47b1bd854a0271aa9df3e7b37f0cc14cdd86d3f06a65a2cb787c6741131b`,
and the three platform release-artifact checksums. The original v0.1.0
contract remains unchanged. `make test` passed with 542 unit, 28 integration,
and one E2E test. Two staged Mulgae assessments completed with passing CI,
complete coverage, committed publication, and successful findings queries;
the first four findings were corrected in the second reviewed candidate.
The second assessment's two Low documentation findings were resolved by an
isolated three-file delta and `make test-prepare` passed on that delta.
This is contract admission evidence only; TASK-024 activates registration and
runtime and TASK-026 owns native platform qualification.

### TASK-024: Add three fixed inspection tools

Implement catalog-derived registration, closed empty input schemas,
immutable argv descriptors, and per-tool availability checks through the
existing runner. Bind the two `--group` flags to trusted `sync_group_id` and
the config path to trusted Plugin configuration. Omit `--config` only for
`sync capabilities`; retain trusted path validation for every action.
Require each sync handler to make a fresh bounded capability/digest check
through that same runner before executing its command, independent of
Hermes availability caching or direct handler dispatch. Keep the old ten
tools available on qualified pre-v0.2.0 cores without a sync setting.
Regenerate `plugin.yaml` only from the amended catalog with the repository's
manifest parity script.

Evidence: fixed thirteen-name catalog/manifest/registration parity and
0/10/13 available-definition cases; exact argv tests for all three commands;
pre-spawn denial of untrusted inputs, group/command mismatch, missing group,
capability drift after a cached visible state, direct dispatch, and
capability-probe failure tests.

### TASK-025: Preserve evidence and safe presentation

Validate the three result shapes and present core states without inferring
stronger outcomes. In `sync status`, keep publication, peer delivery, local
import, historical verification, and fresh pair verification distinct.
Preserve reported expected-node identities, target/config/membership
revisions, freshness, dirty/pending/uncertain state, and bounded reasons when
the provider supplies them. An offline node remains expected. `latest_*`
fields are latest local projections, not a complete history or a fresh
network check. In service inspection, a loaded matching definition is not
proof that the listener is accepting peer traffic. Validate `side_effects`
as empty for every successful read. Preserve exact values only at the
contract's validated public identity paths; redact secrets, local sensitive
paths, untrusted diagnostic text, and all other strings under the admitted
public contract. Do not exempt a whole result object or a string merely
because it resembles a hash.

Evidence: disabled, incomplete, blocked, stale/target-changed, offline,
absent/pruned latest record, service-drift, exact public identity, and
seeded-secret fixtures, including token-like data in nearby fields.
Malformed or stronger-than-supported provider results fail closed.

### TASK-026: Qualify through Hermes

Run `make test` and the required `make test-qualify` matrix on native
Darwin arm64, Linux amd64, and Linux arm64 using properly version-stamped,
checksummed v0.2.0 candidates from the reviewed source. Confirm each
candidate matches the platform SHA allowlist before claiming support. Drive
every new public read action and the retained ten-tool action matrix through
fresh Hermes sessions over isolated synthetic state. Include disabled and
enabled group evidence, partial/offline pair evidence, capability mismatch,
malformed output, time/output limits, and redaction failures. Qualify `sync service
inspect` against a disposable native user service manager and isolated
managed definition on each platform, including absent, loaded, and drifted
states. The current minimal runner environment does not pass HOME/XDG
variables; prove the real command works under that boundary. If it needs
more variables, amend the trusted environment contract and requalify rather
than treating an isolated process fixture as native service evidence.
Core E22/G18 evidence is the provider baseline, not substitute Plugin/Hermes
evidence. Missing platform capacity leaves the corresponding support claim
unqualified. Update the qualification harness and TESTING.md to name the new
candidate pins and 10/13 inventory cases before claiming the gate passed.

Evidence: per-platform candidate SHA and Hermes identities, public action
transcripts, native service-manager observations, deterministic security
results, and registered versus available inventory counts.

### TASK-027: Close documentation and handoff

Update public and maintainer guidance for capability detection, two-node
status meaning, disabled groups, service-definition inspection versus
listener health, and exact upgrade/rollback behavior. Record the reviewed
Plugin/core candidate pair, contract digest, all gates, and a bounded cold
review. Close the epic only when every task and required acceptance check is
complete. The handoff identifies no automatic successor; EPIC-008 remains
Deferred. Release, installation, activation, tag, and publication remain
separate lifecycle actions.

Evidence: accurate examples, links, acceptance traceability, review
disposition, and exact candidate identities without machine-local secrets.

## Epic acceptance

- The amended PRD, executable contract, derived manifest, registration,
  fixed commands, platform SHA allowlist, and registered versus available
  inventory agree on the three added read tools.
- Every advertised action has a successful real Hermes/Dispatch path on each
  supported host and deterministic negative coverage for trust, parsing,
  bounds, and redaction. Missing required platform evidence blocks closure.
- Disabled, incomplete, blocked, stale, and service-only evidence cannot be
  presented as fresh two-node convergence or listener readiness.
- The existing ten tools retain their qualified behavior; no new mutation,
  direct database/network access, arbitrary CLI pass-through, or automatic
  retry is reachable from Plugin tools.
- The close record names the exact candidate and reviewed evidence. No
  deferred task is silently promoted or represented as completed.

## Exclusions and deferred re-entry

The implemented v0.2.0 provider has no `sync peers`, `sync publications`,
`sync imports`, `sync verifications`, or `sync requests` list/show commands.
It also lacks the proposal's durable management request ID and follow-up
lookup surface. Do not create tools for those commands or infer complete
history from `sync status`. `sync verify`, `sync reconcile`, `sync publish`,
pause/resume, membership/checkpoint apply, and service mutations are outside
EPIC-007 even when the provider implements them.

EPIC-008 and TASK-028 through TASK-032 retain their IDs in Deferred state.
Re-entry requires an implemented versioned core request/query contract and
provider qualification, an approved Plugin PRD/contract authority amendment,
and a separate management authorization design. Replan those tasks against
the actual provider at that time; the original five-action request proposal
and old Dispatch E27 handoff are not executable acceptance criteria.
