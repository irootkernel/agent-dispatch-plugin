# Installation Lifecycle Runbook: Disposable Hermes Profile (Linux)

Target: the `agent-dispatch-plugin` source-directory distribution
lifecycle in a disposable Hermes profile on Linux.
Environment: disposable `HERMES_HOME` on native `linux/arm64` or native
`linux/amd64` with Hermes (>=0.20.5) on `PATH` and the host-selected
pinned Agent Dispatch artifact. The procedure never touches the
operator's live Hermes profile, Agent Dispatch configuration, state
database, or systemd user units.

This is the Linux counterpart of
[install-lifecycle-darwin-arm64.md](install-lifecycle-darwin-arm64.md).
The state machine is the same. The pins and native scheduler differ.

## Exact identities

| Host | Agent Dispatch pin | SHA-256 | Env |
|---|---|---|---|
| linux/arm64 | v0.1.7 linux-arm64 | `5493b1a13d28fa28eee850617be7c745d47898b87a7c3c4ea114f5c1cf2481c0` | `AGENT_DISPATCH_QUALIFY_BINARY_V017` |
| linux/amd64 | v0.1.8 linux-amd64 | `ac844117af9cb10d5e7a18b5294336283e03e44bd8ab3c59aa500d0ad4b6ce7d` | `AGENT_DISPATCH_QUALIFY_BINARY_V018` |

Plugin installation remains a source-only directory at an exact pinned
revision. Hermes `plugins install` still rejects manifest 2; copy the
checkout into `<HERMES_HOME>/plugins/agent-dispatch-plugin`.

Translated amd64 (VirtualApple, qemu user-mode) is not this runbook.

## Reproduction

```bash
# linux/arm64
export AGENT_DISPATCH_QUALIFY_BINARY_V017=/path/to/agent-dispatch-v0.1.7-linux-arm64
make test-qualify

# linux/amd64
export AGENT_DISPATCH_QUALIFY_BINARY_V018=/path/to/agent-dispatch-v0.1.8-linux-amd64
make test-qualify
```

The stage builds one disposable profile per run: a fresh `HERMES_HOME`,
the repository checkout as the plugin directory, the pinned executable
copied into the sandbox and verified byte-exactly, and an Agent Dispatch
configuration seeded through the binary's own `init` command. Lifecycle
steps drive the real Hermes CLI and observe the runtime through a fresh
interpreter importing `model_tools`.

## Lifecycle states

The Darwin lifecycle table applies unchanged: installed disabled by
default, plugin enable without settings (`binary_unavailable`), five
settings seeded (smoke `ok: true`), toolset disable/enable as a separate
state, plugin disable, plugin remove, and profile bookkeeping cleaned.
See [install-lifecycle-darwin-arm64.md](install-lifecycle-darwin-arm64.md)
for the command-by-command transcript.

Recorded Linux transcripts:

- linux/arm64 v0.1.7 on `e7f3375` / `vnic-doksuri`:
  [qualification-linux-arm64.md](../implementation-tips/qualification-linux-arm64.md)
- linux/amd64 v0.1.8 on `fa6f1cd` / `cursor`:
  [qualification-linux-amd64.md](../implementation-tips/qualification-linux-amd64.md)

## Success verification

`make test-qualify` exits 0. Removal leaves no plugin registration or
tool inventory residue. Native schedule inspect is systemd with
`present=false` for an absent unit. This runbook does not install or
load a user timer.

## Ownership

Same as the Darwin lifecycle: maintainer owns qualification; the profile
operator owns live installation. Escalate through
[troubleshooting](troubleshooting.md#escalation).
