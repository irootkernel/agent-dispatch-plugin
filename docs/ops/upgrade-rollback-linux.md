# Upgrade and Rollback Runbook: Pinned Revisions on Linux

Target: moving an installed `agent-dispatch-plugin` between documented
pinned revisions inside one Hermes profile on Linux.
Environment: Hermes (>=0.20.5) on `PATH`, the host-selected pinned Agent
Dispatch artifact (v0.1.8 for the legacy ten tools; v0.2.0 for the three
sync reads where native qualification is complete), native Linux. The
procedure is identical for an operator profile and a
disposable one.

The Darwin model in
[upgrade-rollback-darwin-arm64.md](upgrade-rollback-darwin-arm64.md)
applies: an installation is the plugin directory at one exact revision;
profile enablement and the configured plugin settings survive the swap.

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
   `agent_dispatch` toolset. In a fresh session, verify the target revision's
   registered roster (ten for v0.1.x; thirteen for v0.2.0), the expected
   available subset for the selected core, and one status inspection.

## Linux-specific rollback boundary

The recorded Darwin-only pre-release `0c4e70e384bc9891bc15820c4e0b6a42ba700d5a`
rejects Linux at the platform gate. On linux/arm64 and linux/amd64 the
qualification lifecycle asserts that rollback to that revision keeps the
toolset unavailable (`binary_unavailable` or
`unsupported_agent_dispatch_version`) until the Linux-admitting candidate
is restored. Darwin's legacy v0.1.6/v0.1.7 artifacts still pass that
rollback smoke; the v0.2.0 artifact remains unavailable under the old source.
Do not treat that closed toolset as a broken install.

## Recorded evidence

`make test-qualify` on each advertised Linux host already swaps to
`0c4e70e` and back to the candidate. See
[qualification-linux-arm64.md](../implementation-tips/qualification-linux-arm64.md)
and
[qualification-linux-amd64.md](../implementation-tips/qualification-linux-amd64.md).

A plugin rollback does not reverse an Agent Dispatch store migration.
For the v0.2.0 inspection tools, also recheck the configured binary's
platform SHA, trusted `sync_group_id`, and fresh capability contract
after either direction of the swap. A rollback to v0.1.x source registers
the historical ten tools; retaining `sync_group_id` in profile settings
does not grant the three sync reads. Native Linux amd64 v0.2.0
qualification remains open under the
[EPIC-007 re-entry gate](../deferred-feedback/README.md#linux-amd64-v020-sync-inspection-qualification).
