# Qualification Runbook: Linux arm64 Compatibility Matrix

Target: the `agent-dispatch-plugin` v0.1.0 public surface on native
`linux/arm64`.
Environment: disposable profile on Linux arm64 (this runbook's evidence
path never touches the operator's live Agent Dispatch configuration,
state database, or systemd user units).

This is maintainer qualification evidence for one advertised platform. It
does not authorize a release, does not qualify `linux/amd64`, and does
not replace Darwin arm64 as the current release host.

## Exact artifact identities

| Component | Identity |
|---|---|
| Hermes | >=0.20.5 on `PATH` (this host recorded v0.21.2, build 2026.9.11, and v0.21.0, build 2026.8.31 / `29112bef`); the stage resolves the install's venv interpreter for the deterministic dispatch driver |
| Agent Dispatch | tag `v0.1.7` |
| Agent Dispatch binary | release build `agent-dispatch-v0.1.7-linux-arm64`, SHA-256 `5493b1a13d28fa28eee850617be7c745d47898b87a7c3c4ea114f5c1cf2481c0` |
| Envelope | `agent-dispatch.cli/v1` (verified per action by the matrix) |
| Host | linux/arm64, non-root, systemd as PID 1 |

The mandatory Agent Dispatch range remains `>=0.1.6,<0.2.0`. This linux/arm64
slice records the latest compatible published artifact available on the host
(v0.1.7). Agent Dispatch v0.1.6 linux-arm64 was not present and is not
claimed. The qualification fixture verifies the digest before the version
probe and never substitutes an arbitrary binary found on PATH for a missing
pinned identity.

Native schedule inspection selects `--platform systemd` from the trusted
host. The success path recorded here is the absent-schedule inspection
(`present=false`) with systemd `service_path` / `timer_path` keys. This
runbook does not install, load, or repair a user timer.

## Reproduction

```bash
# 1. Provide the pinned linux-arm64 v0.1.7 release build (verified by SHA-256).
export AGENT_DISPATCH_QUALIFY_BINARY_V017=/path/to/agent-dispatch-v0.1.7-linux-arm64

# 2. Ensure hermes on PATH is v0.20.5 or newer, then run the matrix.
make test-qualify
```

`AGENT_DISPATCH_QUALIFY_BINARY` (the Darwin v0.1.6 slot) is not required on
linux/arm64. The stage collects the v0.1.7 linux-arm64 matrix entry and the
installation lifecycle against that same artifact.

The stage builds one disposable profile per run: a temporary `HERMES_HOME`
carrying the plugin (enabled, with the five frozen settings pointing into
the sandbox), a temporary Agent Dispatch configuration and state directory
seeded through Agent Dispatch's own commands (`init`, `config validate`,
two-key `route enable`, `dispatch --input watchman --no-submit`, `work
begin`/`work complete`, and a protected-path fixture for quarantine), and
a controlled fake downstream Hermes target answering only the probe
surfaces. Every advertised action is then dispatched through the real
Hermes runtime (v0.20.5 or newer) (`model_tools.handle_function_call` — the
same dispatcher the agent loop and the Hermes tools MCP server use), with
no model and no network. Seeding commands run with `HOME` inside the
sandbox so home-resolved state stays disposable; through the plugin
boundary `HOME` is absent by the frozen environment contract.

## Recorded boundaries

1. **doctor and Watchman.** Under the plugin's frozen PATH allowlist
   (`/usr/bin:/bin:/usr/sbin:/sbin`) Watchman is unreachable. Both doctor
   variants must return the validated findings envelope at exit 3 with a
   `watchman_unavailable` finding ([ADR-008](../architecture-decision-records/ADR-008-doctor-findings-exit-status.md)).
2. **Native schedule mapping.** The model never supplies `--platform`.
   Linux inspects systemd. An absent unit is a successful inspection with
   `present=false`.
3. **Execute-only digest.** The hermetic runner suite must execute
   `test_execute_only_binary_is_unreadable_for_the_digest` as a non-root
   uid; root skips that branch and is not this host's evidence.
4. **Source rollback of the Darwin-only pre-release.** The lifecycle still
   swaps in commit `0c4e70e384bc9891bc15820c4e0b6a42ba700d5a`. That revision
   rejects linux/arm64 at the platform gate, so the toolset stays
   unavailable until the candidate is restored. Darwin continues to expect
   a successful smoke through that same rollback source.

## Success verification

`make test-qualify` exits 0 with every success case asserting the frozen
wrapper schema, `ok`, exit code 0 (or the documented doctor findings exit 3),
the action's expected command identity, the seeded synthetic state, and
schedule inspect `present=false` with systemd descriptor paths.

This host also recorded the hermetic aggregate (`make test-prepare`, unit,
integration) and Plugin Doctor (`hermes plugins doctor <plugin-directory>
--ci` reporting ten tools and zero hooks) before the qualification stage.

## What this slice does not close

- native `linux/amd64` (run [qualification-linux-amd64.md](qualification-linux-amd64.md) on a native x86_64 host)
- Agent Dispatch v0.1.6 linux-arm64 (GitHub releases v0.1.6 and v0.1.7 published Darwin arm64 only; not claimed)
- Linux operator install, upgrade, and rollback runbooks (TASK-022)
- a v0.1.1 release tag

A missing advertised environment blocks that platform claim; it does not
rewrite completed Darwin qualification.

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
