# Upgrade and Rollback Runbook: Pinned Revisions in a Disposable Profile

Target: moving an installed `agent-dispatch-plugin` between documented
pinned revisions inside one Hermes profile.
Environment: Hermes (v0.20.5 or newer) on `PATH`, the pinned Agent Dispatch v0.1.6
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
survives the swap unchanged. The recorded revisions share the same five-setting contract. Check the
target revision and executable identity before assuming those settings remain
valid for another upgrade or rollback.

## Procedure

Owner: the plugin maintainer; the profile operator performs the change with
access to that profile and its installed plugin directory. Stop active sessions
using the plugin before replacing it. Keep the previous source directory and
plugin-specific settings available for recovery.

1. Confirm the current installed commit and select an exact target commit.
   Review its compatibility requirements and preserve unrelated profile entries.
2. Run `hermes tools disable agent_dispatch`, then
   `hermes plugins disable agent-dispatch-plugin` against the selected profile.
3. Prepare the target source from `git archive <exact-revision>` in a fresh
   directory. Retain the old plugin directory separately and replace only
   `<HERMES_HOME>/plugins/agent-dispatch-plugin` with the prepared source.
   Do not overlay files from two revisions or delete Agent Dispatch state.
4. Verify the installed directory with `hermes plugins doctor <plugin-directory> --ci`.
   Confirm the trusted binary and config settings still meet the target contract.
5. Re-enable the plugin with `--no-allow-tool-override`, then enable the
   `agent_dispatch` toolset. Start a fresh interactive session and verify one
   status inspection as well as the ten-tool inventory.

If verification fails, keep the plugin and toolset disabled, restore the retained
source and plugin-specific settings, and repeat verification before activation.
A plugin rollback does not reverse an Agent Dispatch store migration; that
recovery belongs to Agent Dispatch. Escalate unresolved failures to plugin
maintainers with the previous/target commit identities and a bounded diagnostic.

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
