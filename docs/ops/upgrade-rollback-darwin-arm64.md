# Upgrade and Rollback Runbook: Pinned Revisions in a Disposable Profile

Target: moving an installed `agent-dispatch-plugin` between documented
pinned revisions inside one Hermes profile.
Environment: Hermes v0.20.5 on `PATH`, the pinned Agent Dispatch v0.1.6
darwin/arm64 release artifact (SHA-256
`ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479`),
Darwin arm64. The procedure is identical for an operator profile and a
disposable one; the reproduction below uses a disposable profile.

## Model

An installation is the plugin directory at one exact pinned revision.
Upgrade or rollback replaces that directory; the profile state — plugin
enablement (`plugins.enabled`), the five frozen settings
(`plugins.entries.agent-dispatch-plugin.settings`), and toolset
enablement (`platform_toolsets.cli`) — is profile configuration and
survives the swap unchanged. Because the five settings and the trust
gate contract are frozen across v0.1.x revisions, a swap never
invalidates them.

## Reproduction

```bash
# 1. Install the current candidate (see the Installation Lifecycle
#    Runbook), enable it, and seed the five settings.
git archive <current-revision> | tar -x -C <plugin-directory>
hermes plugins enable agent-dispatch-plugin --no-allow-tool-override
# seed plugins.entries.agent-dispatch-plugin.settings in the profile config

# 2. Roll back to a documented pinned revision: replace the directory.
rm -rf <plugin-directory> && mkdir <plugin-directory>
git archive <previous-pinned-revision> | tar -x -C <plugin-directory>

# 3. Verify in a fresh session (registration, availability, one smoke
#    inspection), then upgrade forward the same way.
```

## Transcript (recorded reproduction)

Rolling one disposable profile between the first two documented pinned
revisions — the EPIC-004 closeout revision
(`22bca58bccab6386c98275b913f7cc3bd0813361`) and the EPIC-005 candidate
(`156ca591132efd6adc9b1e83553b3a2654f3f3b9`, the commit that introduced
the release handoff and its self-declared immutable review target) —
with the profile state untouched between swaps:

| Step | Revision | Fresh-session observation |
|---|---|---|
| Install current candidate | `156ca591132efd6adc9b1e83553b3a2654f3f3b9` | 10 tools registered, toolset available, smoke inspection `ok: true` |
| Rollback | `22bca58bccab6386c98275b913f7cc3bd0813361` | 10 tools registered, toolset available, smoke inspection `ok: true` |
| Upgrade forward | `156ca591132efd6adc9b1e83553b3a2654f3f3b9` | 10 tools registered, toolset available, smoke inspection `ok: true` |

The revision history a rollback may target is exactly the committed
history of this repository; a release handoff (see the release handoff
runbook) names the exact revision it qualifies. Until a second release
tag exists, the single-entry support-matrix rationale of the
compatibility qualification applies to rollback targets as well: every
documented pinned revision below the next major boundary ships the same
frozen five-setting contract and manifest identity.

## Success verification

After every swap, a fresh session registers exactly the ten frozen
tools, the toolset reports available with the unchanged settings, and
one smoke inspection succeeds through the full boundary. A failed trust
gate after a swap means the settings no longer match the frozen contract
— restore the documented settings rather than loosening the gate.
