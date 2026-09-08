# Agent Dispatch Plugin v0.1.0 Product Requirements

Status: Approved design baseline
Scope: Single product scope
License: MIT
Canonical language: English

## Product outcome

Deliver a secure, inspection-only Hermes plugin exposing exactly ten typed
tools over fixed Agent Dispatch CLI operations. The plugin gives a Hermes user
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
| agent_dispatch_schedule_inspect | schedule inspect --route ID --platform launchd --output json | Required route_id | Presence, loaded state, definition match, digests, and health |
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
- Darwin arm64

Qualification must record exact artifact identities and use a disposable,
isolated profile containing synthetic Agent Dispatch state and controlled fake
targets. The support matrix must include Agent Dispatch v0.1.6 and the selected
highest available compatible release below v0.2.0.

Every advertised public action must complete a successful end-to-end path
through Hermes v0.20.5 or newer invoking the real pinned Agent Dispatch executable on
Darwin arm64. Contract fixtures supplement this evidence for malformed
envelopes, unknown versions, truncation, resource limits, redaction, unavailable
dependencies, and unsafe or nondeterministic failure branches. Fixtures never
replace a successful real run of an advertised action.

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
- Linux, Windows, Hermes versions below v0.20.5, or Agent Dispatch 0.2.x.
- Automatic installation, activation, publication, tagging, or release.

Worker receipt mutations and administrative mutations are post-v0.1.0
candidates. Other non-goals have no initial roadmap identity.

## Change control

Adding, removing, or renaming a tool; changing an action-to-command mapping;
expanding authority; weakening a release gate; or changing the public result,
error, compatibility, or resource contract requires explicit maintainer
approval and a canonical amendment. Implementation decisions that preserve
these contracts belong in ADRs and adopted dossiers.
