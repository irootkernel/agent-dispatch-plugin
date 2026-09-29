# Qualification Runbook: Linux amd64 Compatibility Matrix

The recorded matrix below covers the historical v0.1.8 ten-tool surface.
Native Linux amd64 v0.2.0 Hermes and systemd user-manager qualification is
still pending under EPIC-009/TASK-033. The maintainer re-entry gate is in
[deferred feedback](../deferred-feedback/README.md#linux-amd64-v020-sync-inspection-qualification);
do not use this historical result as evidence for the three sync reads.

Target: the `agent-dispatch-plugin` public surface on native
`linux/amd64`.
Environment: disposable profile on Linux amd64 (this runbook's evidence
path never touches the operator's live Agent Dispatch configuration or
state database; the current stage uses a unique disposable systemd user unit).

This is maintainer qualification evidence for one advertised platform. It
does not authorize a release, does not replace Darwin arm64 as the current
release host, and does not treat a translated amd64 container as this host.

Deferred EPIC-009/TASK-033 v0.2.0 Linux amd64 qualification requires the
candidate with SHA-256 `59216c7ec8aee4abb9e00377a81686156b08a3235275afcde5b6ec28363bb8d6`,
at `AGENT_DISPATCH_QUALIFY_BINARY_V020`, plus a native systemd user manager.
The earlier TASK-021 result below remains historical; it does not qualify
the v0.2.0 Plugin candidate. Master closed TASK-026 for Darwin arm64 and
Linux arm64 on 2026-09-29; this native Linux amd64 matrix remains a
separate platform support gate owned by the Plugin maintainer.

## Exact artifact identities

| Component | Identity |
|---|---|
| Hermes | >=0.20.5 on `PATH`; the stage resolves the install's venv interpreter for the deterministic dispatch driver |
| Agent Dispatch | tag `v0.1.8` |
| Agent Dispatch binary | release build `agent-dispatch-v0.1.8-linux-amd64`, SHA-256 `ac844117af9cb10d5e7a18b5294336283e03e44bd8ab3c59aa500d0ad4b6ce7d` |
| Envelope | `agent-dispatch.cli/v1` (verified per action by the matrix) |
| Host | linux/amd64, native x86_64/amd64. Translated `VirtualApple` or qemu user-mode is not this platform |

The mandatory Agent Dispatch range remains `>=0.1.6,<0.2.0`. GitHub
releases v0.1.6 and v0.1.7 published Darwin arm64 only; the published
linux/amd64 artifact is v0.1.8. That identity is the TASK-018 Linux
selection. Do not substitute a Darwin binary, an arm64 binary, or an
arbitrary PATH binary for the pinned digest.

Native schedule inspection selects `--platform systemd` from the trusted
host. An absent unit is a successful inspection (`present=false`) with
systemd `service_path` / `timer_path` keys. This runbook does not
install, load, or repair a user timer.

## Reproduction

```bash
# 1. Provide the pinned linux-amd64 v0.1.8 release build (verified by SHA-256).
export AGENT_DISPATCH_QUALIFY_BINARY_V018=/path/to/agent-dispatch-v0.1.8-linux-amd64
export AGENT_DISPATCH_QUALIFY_BINARY_V020=/path/to/agent-dispatch-v0.2.0-linux-amd64

# 2. Ensure hermes on PATH is v0.20.5 or newer, then run the matrix.
make test-qualify
```

`AGENT_DISPATCH_QUALIFY_BINARY` and `AGENT_DISPATCH_QUALIFY_BINARY_V017`
are not required on linux/amd64. The stage collects the v0.1.8 legacy
matrix and lifecycle, plus the v0.2.0 matrix, lifecycle, and native
service cases. Native v0.2.0 results remain deferred until an x86_64
Linux host runs this stage.

The Darwin-only rollback source `0c4e70e` must keep the toolset
unavailable (`binary_unavailable`) until the candidate is restored.

## Success verification

`make test-qualify` exits 0 with every success case asserting the frozen
wrapper schema, `ok`, exit code 0 (or the documented doctor findings
exit 3), the action's expected command identity, the seeded synthetic
state, and schedule inspect `present=false` with systemd descriptor
paths.

Record Hermes `--version`, `uname -sm`, and the binary digest in the
TASK-021 evidence. Do not claim linux/arm64 or Darwin from this host.

## Recorded TASK-021 candidate (historical)

Recorded 2026-09-16 on native linux/amd64 host `cursor` (uid 1000)
against plugin source `fa6f1cd`:

| Component | Identity |
|---|---|
| Hermes | v0.21.3 (2026.9.14) · upstream `f13a87e6` |
| Agent Dispatch v0.1.8 linux-amd64 | SHA-256 `ac844117af9cb10d5e7a18b5294336283e03e44bd8ab3c59aa500d0ad4b6ce7d` |
| Host | Linux x86_64 |

`make test-qualify` passed (2 passed: v0.1.8 compatibility matrix and
installation lifecycle). This slice does not claim linux/arm64 or Darwin.

## What this slice does not close

- linux/arm64 (see [qualification-linux-arm64.md](qualification-linux-arm64.md))
- Darwin arm64 (see [qualification-darwin-arm64.md](qualification-darwin-arm64.md))
- Agent Dispatch v0.1.6 / v0.1.7 linux-amd64 (GitHub releases for those tags published Darwin arm64 only; not claimed)
- Linux operator install, upgrade, and rollback runbooks (TASK-022)
- a v0.1.1 release tag
