# Qualification Runbook: Darwin arm64 Compatibility Matrix

Target: the `agent-dispatch-plugin` v0.1.0 public surface.
Environment: disposable profile on Darwin arm64 (this runbook's evidence
path never touches the operator's live Agent Dispatch configuration,
state database, or LaunchAgents).

## Exact artifact identities

| Component | Identity |
|---|---|
| Hermes | >=0.20.5 on `PATH` (qualified reference: v0.20.5, build 2026.8.19); the stage resolves the install's venv interpreter for the deterministic dispatch driver |
| Agent Dispatch | tag `v0.1.6`, commit `fc67cf540383e51cdcf4a1aff6c9f2a1b7d252a5` |
| Agent Dispatch binary | release build `dist/agent-dispatch-v0.1.6-darwin-arm64`, SHA-256 `ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479` |
| Envelope | `agent-dispatch.cli/v1` (verified per action by the matrix) |
| Host | darwin/arm64 |

Support matrix rationale: the mandatory range is `>=0.1.6,<0.2.0`. The
tag inventory recorded during TASK-012 below 0.2.0 was `v0.1.5` and
`v0.1.6`; `v0.1.5` is below the floor, so **v0.1.6 was both the minimum
and the highest available compatible release in that inventory** and the matrix is a single
entry. Out-of-range rejection (including versions below the floor) is
proven deterministically by the unit suite's fake-binary version-gate
tests; a future tag inside the range widens the matrix by adding its
artifact digest as a second qualification identity.

## Reproduction

```bash
# 1. Provide the pinned artifact: any byte-identical copy of the
#    v0.1.6 darwin/arm64 release build (verified by SHA-256 before use).
export AGENT_DISPATCH_QUALIFY_BINARY=/path/to/agent-dispatch-v0.1.6-darwin-arm64

# 2. Ensure hermes on PATH is v0.20.5 or newer, then run the matrix.
make test-qualify
```

The stage builds one disposable profile per run: a temporary `HERMES_HOME`
carrying the plugin (enabled, with the five frozen settings pointing into
the sandbox), a temporary Agent Dispatch configuration and state directory
seeded through Agent Dispatch's own commands (`init`, `config validate`,
two-key `route enable`, `dispatch --input watchman --no-submit`, `work
begin`/`work complete`, and a protected-path fixture for quarantine), and
a controlled fake downstream Hermes target answering only the probe
surfaces. Every advertised action is then dispatched through the real
Hermes runtime (v0.20.5 or newer) (`model_tools.handle_function_call` — the same
dispatcher the agent loop and the Hermes tools MCP server use), with no
model and no network. Seeding commands run with `HOME` inside the sandbox
so home-resolved state (including the hermes capability cache) stays
disposable; through the plugin boundary `HOME` is absent by the frozen
environment contract, so the capability cache falls back to the
per-user temp directory under the sandbox's unique target identity.

## Recorded boundaries (historical adjudication)

See the [release acceptance gap](release-handoff.md#compatibility-acceptance-gap)
before using these recorded dispositions to assess a new candidate.

1. **doctor and the watchman dependency.** Upstream `doctor` probes the
   watchman daemon whenever the configuration loads and reports
   `watchman_unavailable` as an error-severity finding when the binary is
   not reachable, exiting 3 with an `ok:true` findings envelope on
   stdout. Under the plugin's frozen PATH allowlist
   (`/usr/bin:/bin:/usr/sbin:/sbin`) a Homebrew-installed watchman is
   unreachable, so both `agent_dispatch_doctor` variants close as the
   frozen `contract_mismatch` error on this host class. The PRD's fixture
   clause supplements their success evidence (the unit suite proves the
   success mapping with the deterministic fake); the matrix asserts the
   closed negative deterministically. A future canonical amendment could
   make the PATH allowlist operator-extensible.
2. **Upstream receipt-id quirk (v0.1.6).** `work complete`'s envelope
   reports a receipt id that `receipts list`/`receipts show` never serve;
   the durable receipt is the begin-time row. The qualification resolves
   receipt ids from the list surface; the plugin is unaffected because it
   never fabricates identifiers.
3. **Handler calling convention (remediated in TASK-012).** The Hermes
   v0.20.5 dispatcher invokes tool handlers with the request object as
   one positional argument and accepts only string results. The plugin's
   handlers originally accepted keyword arguments and returned the
   wrapper dict — invisible to registration-time checks and to the
   direct-call test suite, and a hard dispatch failure through the real
   runtime. The qualification caught it; the handlers now take
   `(args, **_context)` and return the wrapper's JSON encoding.

## Success verification

`make test-qualify` exits 0 with every success case asserting the frozen
wrapper schema, `ok`, exit code 0, the action's expected command
identity, and the seeded synthetic state surfacing through the qualified
actions (`schedule inspect` proving the absent-schedule successful
inspection with `present=false`).

## Ownership and failure recovery

The plugin maintainer owns qualification and the release owner consumes its
candidate-specific evidence. Check platform, Hermes version, and the pinned
artifact identity before running the isolated test environment. A prerequisite
failure must be resolved without substituting a live profile or bypassing the
hash gate. If a case fails, retain its bounded diagnostic and candidate identity,
resolve it through the owning contract or implementation, and rerun qualification.
The disposable test resources require no live-environment rollback. Escalate
external CLI incompatibilities to the Agent Dispatch maintainer; do not silently
adapt the plugin's frozen contracts.
