# Installation Lifecycle Runbook: Disposable Hermes Profile

Target: the `agent-dispatch-plugin` v0.1.0 distribution lifecycle in a
disposable Hermes profile.
Environment: disposable `HERMES_HOME` on Darwin arm64 with Hermes
(v0.20.5 or newer) on `PATH` and the pinned Agent Dispatch v0.1.6 darwin/arm64 release
artifact. The procedure never touches the operator's live Hermes profile,
Agent Dispatch configuration, state database, or LaunchAgents.

## Exact identities

| Component | Identity |
|---|---|
| Hermes | >=0.20.5 on `PATH` (qualified reference: v0.20.5, build 2026.8.19) |
| Agent Dispatch binary | v0.1.6 release build, SHA-256 `ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479` |
| Plugin installation | source-only plugin directory at an exact pinned revision of this repository |
| Host | darwin/arm64 |

## Recorded boundary: installer manifest support

The Hermes v0.20.5 `hermes plugins install` subcommand rejects
`manifest_version` 2 repositories ("requires manifest_version 2, but this
installer only supports up to 1") while the runtime directory loader,
`hermes plugins enable/disable/remove/list/show`, and the Plugin Doctor
all accept the frozen manifest 2 contract (`contracts/v0.1.0` pins
standalone format, manifest 2, API 1). Pinned installation therefore uses
the documented source-only plugin-directory mechanism — copy the checkout
at the exact pinned revision into `<HERMES_HOME>/plugins/agent-dispatch-plugin`
— which is the same mechanism the Plugin Doctor e2e stage and the
compatibility matrix qualify.

## Reproduction

```bash
# 1. Provide the pinned artifact (SHA-256 verified before use) and ensure
#    hermes on PATH is v0.20.5 or newer.
export AGENT_DISPATCH_QUALIFY_BINARY=/path/to/agent-dispatch-v0.1.6-darwin-arm64

# 2. Run the lifecycle qualification (with the compatibility matrix).
make test-qualify
```

The stage builds one disposable profile per run under a temporary
directory: a fresh `HERMES_HOME`, the repository checkout installed as
the plugin directory, the pinned executable copied into the sandbox and
verified byte-exactly, and an Agent Dispatch configuration seeded through
the binary's own `init` command with absolute sandbox paths. Every
lifecycle step drives the real Hermes CLI (`plugins show/enable/disable/
remove/list`, `tools enable/disable/list`, `config unset`) and observes
the real runtime through a fresh interpreter importing `model_tools` over
the profile.

## Lifecycle transcript (states asserted by the stage)

| State | Command | Recorded result |
|---|---|---|
| Installed, disabled by default | directory install | `plugins show` reports `Status: not enabled`; fresh session registers 0 tools |
| Plugin enabled, settings unseeded | `hermes plugins enable agent-dispatch-plugin --no-allow-tool-override` | exactly the ten frozen tools register; toolset availability stays `false`; one smoke dispatch closes as `binary_unavailable` |
| Plugin enabled, five settings seeded | profile config `plugins.entries…settings` | toolset availability `true`; the smoke inspection returns `ok: true` through the full boundary |
| Toolset disabled (plugin still enabled) | `hermes tools disable agent_dispatch` | `tools list` reports `✗ disabled`; the toolset leaves `platform_toolsets.cli` while the plugin stays enabled |
| Toolset re-enabled | `hermes tools enable agent_dispatch` | `tools list` reports `✓ enabled`; the toolset rejoins `platform_toolsets.cli` |
| Plugin disabled | `hermes plugins disable agent-dispatch-plugin` | fresh session registers 0 tools |
| Plugin removed | `hermes plugins remove agent-dispatch-plugin` | plugin directory deleted; `plugins list` shows no entry; fresh session registers 0 tools with no inventory entry |
| Profile bookkeeping cleaned | `hermes config unset plugins.entries.agent-dispatch-plugin`, then the plugin's entry removed from the `plugins.disabled` list | no `agent-dispatch-plugin` reference remains in the profile config; fresh session registers 0 tools |

The `plugins.disabled` list is a whole-list key: in this disposable profile it
holds only `agent-dispatch-plugin`, so the qualification removes the list
entirely. A shared operator profile must instead edit the list to drop only
this plugin's entry — unsetting the whole key there would erase other
plugins' disablement state.

Plugin enablement (`plugins.enabled`) and toolset enablement
(`platform_toolsets.cli`) are recorded by separate commands into separate
config states; neither step implies the other.

## Success verification

`make test-qualify` exits 0 with the lifecycle assertions above holding
deterministically: removal leaves no plugin registration or tool
inventory residue in a fresh session, and the cleaned profile contains no
reference to the plugin.

## Ownership and failure recovery

The plugin maintainer owns this qualification procedure; the profile operator
owns installation and activation. For normal installation and the three required
settings plus two defaults, use the [public guide](../../README.md#install).
Diagnosis starts with `hermes plugins show agent-dispatch-plugin` and
`hermes tools list` in the intended profile. These observe separate states.

If an operator installation fails verification, leave its toolset and plugin
disabled while diagnosing. Remove only this plugin through the lifecycle above
when abandoning the installation; preserve other plugin settings and all Agent
Dispatch data. A failed disposable test is evidence for the maintainer to inspect,
not a reason to repeat it against a live profile. Success requires the documented
fresh-session observations, not directory creation alone. Escalate unresolved
failures through [troubleshooting](troubleshooting.md#escalation).
