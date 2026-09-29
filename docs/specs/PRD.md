# Agent Dispatch Plugin Product Requirements

Status: Approved design baseline
Scope: Single product scope
License: MIT
Canonical language: English

## Product outcome

Deliver a secure, inspection-only Hermes plugin exposing ten typed tools in
the v0.1.0 baseline and three additional two-node reads in v0.2.0 over fixed
Agent Dispatch CLI operations. The plugin gives a Hermes user
validated and redacted operational evidence without granting database access,
arbitrary command execution, or mutation authority.

## Users

- Hermes users inspecting Agent Dispatch state and diagnostics.
- Plugin maintainers qualifying compatibility and release evidence.

## v0.1.0 public surface

All tools belong to the dynamic agent_dispatch toolset. Input objects are
closed with additionalProperties false.

| Tool | Fixed CLI mapping | Typed input | Typed result |
|---|---|---|---|
| agent_dispatch_status | status --output json | Empty object | Complete status envelope |
| agent_dispatch_doctor | doctor [--probe-targets] --output json | probe_targets optional boolean, default false | Findings and remediations |
| agent_dispatch_routes | route list, route show --route ID, or route preflight --route ID, then --output json | action list, show, or preflight; route_id required for show and preflight | Route projection or preflight checks |
| agent_dispatch_dispatches | dispatches list or dispatches show ID, documented filters, then --output json | action list or show; conditional dispatch_id; optional route, state, limit, offset | Redacted list or lineage |
| agent_dispatch_receipts | receipts list or receipts show ID, documented filters, then --output json | action list or show; conditional receipt_id; optional route, dispatch, kind, limit, offset | Redacted receipt evidence |
| agent_dispatch_event_show | events show AGGREGATE_ID --output json | Required aggregate_id | Aggregate and child evidence |
| agent_dispatch_quarantine | quarantine list or quarantine show ID, documented filters, then --output json | action list or show; conditional quarantine_id; optional route, state, limit | Held or resolved structural cases |
| agent_dispatch_notifications | notifications list, documented filters, then --output json | Optional route, state, sink, limit | Notification delivery evidence |
| agent_dispatch_schedule_inspect | schedule inspect --route ID --platform launchd or systemd --output json | Required route_id | Presence, loaded state, definition match, digests, and health. The trusted host selects launchd on macOS and systemd on Linux; the platform is not a model input. |
| agent_dispatch_config | config show or config validate [--probe-targets], then --output json | action show or validate; probe_targets valid only for validate | Redacted normalized config, revisions, or findings |

agent_dispatch_receipts is read-only inspection. It does not authorize worker
receipt submission, completion, or failure mutations.

List limits are integers from 1 through 100 and default to 25. Offsets are
non-negative and must have an implementation-documented upper bound. All
identifiers have documented length and grammar constraints, are preserved
literally after validation, and are rejected before process creation when
invalid. Inputs never accept flags, command, args, environment, cwd, binary,
config, or state_dir.

## Result and error contract

Every output uses the plugin-owned agent-dispatch-plugin.result/v1 wrapper with
ok, operation, exit_code, a validated agent-dispatch.cli/v1 envelope, and
bounded diagnostics.

The runner validates API version, command identity, parse completeness,
required fields, types, closed enums, output bounds, and exit consistency.
Command-specific result schemas are stable for v0.1.0. Validated Agent Dispatch
domain values remain unflattened and are not semantically reinterpreted.
Unconsumed additive domain fields may be ignored only where a contract
explicitly permits forward compatibility. Unknown protocol versions, missing
fields, changed types, unknown enum values, security-sensitive additions, and
unexpected fields at closed structural boundaries fail validation. Raw CLI
output is never returned as a successful result.

A validated success normally requires exit code 0. For
`agent_dispatch_doctor` with command identity `doctor`, exit code 3 also
means successful retrieval of diagnostic findings. Preserve `ok: true`,
`exit_code: 3`, and the redacted envelope; this does not assert a healthy
system. Other success/nonzero combinations remain `contract_mismatch`.
No raw stderr is added to this successful result.

The closed error codes are:

- binary_unavailable
- unsupported_agent_dispatch_version
- invalid_argument
- timeout
- output_too_large
- malformed_json
- contract_mismatch
- adapter_usage_error
- execution_failed
- redaction_failure

Errors contain code, a bounded human-readable message, and retryable false.
They never expose tracebacks, unrestricted stderr, environment dumps, raw
partial output, or file bodies.

## Process security contract

runner.py is the only process-execution boundary. It must:

- use the configured absolute, non-symlink Agent Dispatch executable after
  verifying its lowercase SHA-256;
- use only a trusted absolute, non-symlink configuration path;
- construct fixed argv in code and set shell false;
- use a neutral trusted working directory, a minimal environment allowlist,
  and closed unexpected file descriptors;
- only for `sync status` and `sync service inspect`, derive `HOME` from the
  current UID's OS account record and on Linux include an existing,
  UID-owned canonical `/run/user/<uid>` as `XDG_RUNTIME_DIR`; inherit neither
  value from Hermes or the parent environment, while the original actions
  retain the fixed `PATH`/`TMPDIR` environment;
- drain stdout and stderr concurrently with bounded buffers;
- terminate the entire process group on deadline or output overflow;
- perform no retry and no direct SQLite access;
- return bounded, redacted structured errors rather than raising into Hermes.

The default wall-clock timeout is 30 seconds and may be configured from 1
through 300 seconds. After the deadline, send TERM, wait a fixed two-second
grace period, then force-kill the process group. The timeout covers spawn
through normal completion; the grace period begins after the deadline.

Raw byte ceilings are 1,048,576 bytes for stdout, 65,536 bytes for stderr, and
1,048,576 bytes combined. Configuration may tighten but never raise the
combined hard ceiling. A deadline returns timeout. Any stream or combined
overflow returns output_too_large. Both terminate the process group, discard
captured raw output, and return only bounded redacted diagnostics.

## Compatibility and release gates

The mandatory, initially unverified targets are:

- Agent Dispatch >=0.1.6,<0.2.0
- envelope agent-dispatch.cli/v1
- Hermes >=0.20.5
- Darwin arm64, Linux amd64, and Linux arm64

Qualification must record exact artifact identities and use a disposable,
isolated profile containing synthetic Agent Dispatch state and controlled fake
targets. The support matrix must include Agent Dispatch v0.1.6 and the selected
highest available compatible release below v0.2.0.

Every advertised public action must complete a successful end-to-end path
through Hermes v0.20.5 or newer invoking the real pinned Agent Dispatch executable on
each advertised platform. Darwin arm64 remains the first qualified host.
Linux amd64 and Linux arm64 are admitted platforms whose missing real-host
evidence blocks those platform claims without rewriting the Darwin record.
Contract fixtures supplement this evidence for malformed
envelopes, unknown versions, truncation, resource limits, redaction, unavailable
dependencies, and unsafe or nondeterministic failure branches. Fixtures never
replace a successful real run of an advertised action. A real doctor findings
response with the approved exit code 3 satisfies diagnostic retrieval success;
fixtures cover the clean exit-0 variant and malformed responses.

Any failed compatibility assumption blocks v0.1.0. First distinguish a plugin
defect from upstream incompatibility. Release remains blocked pending a fix,
upstream resolution, or a separately approved canonical amendment. The
implementation may not silently narrow, widen, or adapt the baseline.

## Acceptance

Release acceptance requires:

1. manifest, registry, schemas, fixed command descriptors, and tool inventory
   agree on exactly the ten declared tools;
2. every tool has a stable schema contract and at least one success and one
   failure acceptance case;
3. every action branch and security-relevant input class has positive and
   negative coverage;
4. no mutation command, arbitrary flag, model-provided execution setting, raw
   output, SQLite path, automatic retry, or secret-bearing diagnostic is
   reachable;
5. process limits, termination, redaction, and closed error behavior have
   deterministic evidence;
6. every public action passes the mandatory real end-to-end compatibility gate;
7. clean-clone installation, disabled-by-default enablement, removal, and
   rollback evidence is complete for an exact immutable review target.

## Non-goals

- Worker receipt submission, completion, or failure mutations.
- Administrative mutations, including retry, drain, discard, release, install,
  enable, disable, or configuration rewrite operations.
- Direct Agent Dispatch database access or duplicated domain logic.
- Generic CLI pass-through, arbitrary command execution, plugin hooks, custom
  Hermes commands, LLM override, or Desktop plugin APIs.
- Windows, Hermes versions below v0.20.5, or Agent Dispatch 0.2.x under
  the frozen v0.1.0 baseline.
- Automatic installation, activation, publication, tagging, or release.

Worker receipt mutations and administrative mutations are post-v0.1.0
candidates. Other non-goals have no initial roadmap identity.

## Change control

Adding, removing, or renaming a tool; changing an action-to-command mapping;
expanding authority; weakening a release gate; or changing the public result,
error, compatibility, or resource contract requires explicit maintainer
approval and a canonical amendment. Implementation decisions that preserve
these contracts belong in ADRs and adopted dossiers.

## Approved pre-publication amendment and version ownership

The v0.1.0 release amendment admits doctor findings at exit 3 and updates
its schemas, fixtures, runtime, and qualification together in the existing
contract directory. It preserves every other execution and output boundary.
This is an explicit pre-publication rebaseline, not a retrospective waiver.

`contracts/v0.1.0/`, its schema URNs, and catalog `product_version` identify
the public contract baseline. Catalog `plugin.version` identifies the plugin
release and must match the derived manifest, Python project, and lockfile.
The published v0.1.0 tag is unchanged. The v0.1.2 development catalog
admits Darwin arm64, Linux amd64, and Linux arm64 and derives the schedule
`--platform` flag from the trusted host. Schema URNs remain under
`contracts/v0.1.0/` because the ten-tool input and result contracts are
otherwise unchanged.

The current v0.2.0 development catalog and schema URNs are under
`contracts/v0.2.0/`, as admitted by the amendment below.

## Approved v0.2.0 two-node inspection amendment (EPIC-007 / TASK-023)

Status: Approved by Master on 2026-09-29 for TASK-023 runtime work. The
frozen v0.1.0 contract remains valid for Agent Dispatch
`>=0.1.6,<0.2.0` and its ten tools.

The v0.2.0 contract adds exactly three read-only tools in the existing
`agent_dispatch` toolset: `agent_dispatch_sync_capabilities` maps to
`sync capabilities --output json`, `agent_dispatch_sync_status` maps to
`sync status --group GROUP --output json`, and
`agent_dispatch_sync_service_inspect` maps to
`sync service inspect --group GROUP --output json`. Each model input is a
closed empty object. Only the operator's optional `sync_group_id` setting
may supply GROUP; it follows `^[a-z][a-z0-9-]{0,62}$`. The runner supplies
the trusted config path to status and service inspect. Capabilities accepts
no `--config` flag, although the same trusted path check precedes its call.
No sync mutation, direct database or network access, arbitrary flags, or
model-supplied execution setting is admitted.

The catalog, derived manifest, and registry have thirteen fixed names.
Model-facing availability is zero when the common trust gate fails; ten
for a qualified legacy binary, or for the exact v0.2.0 binary without a
configured group or valid capability evidence; and thirteen only when the
configured group and a bounded capability probe attest `v1`, the pinned
digest, and `contract_read`, `status_read`, and `service_inspect`. A fresh
probe precedes each sync read, including direct handler dispatch. Probe
failure never triggers the requested command. A disabled configured group
is inspectable and stays disabled in the result.

The v0.2.0 binary is admitted only when its `version --json` reports
`0.2.0`, the operator SHA-256 matches its bytes, and those bytes match the
reviewed platform SHA allowlist in `contracts/v0.2.0/catalog.json`.
Later v0.2.x binaries are not automatically admitted. The pinned provider
bundle is `docs/contracts/sync-provider-v1/` at core commit
`48f13a4eef68e219a51d188decb8749a5fba9282`; the exact code candidate
is `6b1c78b19f4cdb69dfd070ea016430f03075b73d`. The semantic digest is
`sha256:30cf47b1bd854a0271aa9df3e7b37f0cc14cdd86d3f06a65a2cb787c6741131b`.
Native Hermes and service-manager qualification is complete for the v0.2.0
reads on Darwin arm64 and Linux arm64. EPIC-007 acceptance is limited to
those two hosts, subject to its whole-Epic audit and closeout. Linux amd64
v0.2.0 remains unqualified under deferred EPIC-009/TASK-033 in the
[roadmap](../roadmap/README.md); its catalog-pinned SHA permits exact-binary
identification, not a support claim. Native qualification remains required
before claiming the three sync reads on Linux amd64.

The three new results require command-specific closed validation, including
empty `side_effects`. Status keeps publication, delivery, import, and
verification as separate latest local projections; it never infers fresh
pair convergence from a historical verification. Its expected two nodes
remain visible even if one is offline. Service definition health does not
prove listener reachability. The v1 plugin wrapper, CLI envelope, error
codes, diagnostic bounds, and exit rules remain unchanged.

For these three validated sync results only, exact values at the catalog's
`public_identity_paths` may bypass token-like redaction after field-specific
format validation. These paths are the provider contract digest, status
config revision, and present latest target commits. The current status
provider does not emit a membership revision; if added later, that requires
a reviewed contract amendment. All other values and keys, including nearby
hash-shaped strings, warnings, errors, diagnostics, malformed results, and
unknown fields follow the existing redaction rules. No whole result object
or arbitrary hash is exempt.
