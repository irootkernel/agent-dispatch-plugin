# Upgrade and Rollback Runbook: Pinned Revisions on Linux

Target: moving an installed `agent-dispatch-plugin` between documented
pinned revisions inside one Hermes profile on Linux.
Environment: Hermes (>=0.20.5) on `PATH`, the host-selected pinned Agent
Dispatch artifact (linux/arm64 v0.1.7 or linux/amd64 v0.1.8), native
Linux. The procedure is identical for an operator profile and a
disposable one.

The Darwin model in
[upgrade-rollback-darwin-arm64.md](upgrade-rollback-darwin-arm64.md)
applies: an installation is the plugin directory at one exact revision;
profile enablement and the five frozen settings survive the swap.

## Procedure

1. Confirm the current installed commit and select an exact target commit.
2. `hermes tools disable agent_dispatch`, then
   `hermes plugins disable agent-dispatch-plugin`.
3. `git archive <exact-revision>` into a fresh directory. Replace only
   `<HERMES_HOME>/plugins/agent-dispatch-plugin`. Do not overlay two
   revisions or delete Agent Dispatch state.
4. `hermes plugins doctor <plugin-directory> --ci`. Confirm the trusted
   binary and settings still meet the target contract.
5. Re-enable the plugin with `--no-allow-tool-override`, then enable the
   `agent_dispatch` toolset. Verify ten tools and one status inspection
   in a fresh session.

## Linux-specific rollback boundary

The recorded Darwin-only pre-release `0c4e70e384bc9891bc15820c4e0b6a42ba700d5a`
rejects Linux at the platform gate. On linux/arm64 and linux/amd64 the
qualification lifecycle asserts that rollback to that revision keeps the
toolset unavailable (`binary_unavailable`) until the Linux-admitting
candidate is restored. Darwin still expects a successful smoke through
the same rollback source. Do not treat that closed toolset as a broken
install.

## Recorded evidence

`make test-qualify` on each advertised Linux host already swaps to
`0c4e70e` and back to the candidate. See
[qualification-linux-arm64.md](../implementation-tips/qualification-linux-arm64.md)
and
[qualification-linux-amd64.md](../implementation-tips/qualification-linux-amd64.md).

A plugin rollback does not reverse an Agent Dispatch store migration.
