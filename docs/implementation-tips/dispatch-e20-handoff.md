# Dispatch E20 / E20-T1 Handoff

Owner after this record: Agent Dispatch, epic **E20**, first task **E20-T1**.
Plugin program position **G01** (EPIC-006) is complete. Stop plugin
feature work until Dispatch **E26** is accepted. Do not start EPIC-007
(G09) or EPIC-008 (G10) from this repository.

This handoff is not a release authorization and does not publish a tag.

## Product that is handed off

The plugin remains a **ten-tool inspection product**. Public tools are
unchanged: status, doctor (two variants), routes, schedule inspect,
config (two variants), dispatches, receipts, events, quarantine,
notifications. No sync inspection, no management request tool, no
mutations.

Schedule inspect still takes only `route_id`. The trusted host selects
`--platform launchd` on macOS and `--platform systemd` on Linux.

## Exact qualified combinations

| Platform | Plugin source recorded | Agent Dispatch | SHA-256 | Hermes |
|---|---|---|---|---|
| darwin/arm64 | TASK-021 Darwin slice (v0.1.6 and v0.1.7 matrix) | v0.1.6 and v0.1.7 darwin-arm64 | `ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479`, `c949e5c56929332cc102c228bfd9415fee0dbdd0b21c296ac136b9d114efbccf` | >=0.20.5 (recorded v0.21.0) |
| linux/arm64 | `e7f3375` on `vnic-doksuri` | v0.1.7 linux-arm64 | `5493b1a13d28fa28eee850617be7c745d47898b87a7c3c4ea114f5c1cf2481c0` | >=0.20.5 (recorded v0.21.2) |
| linux/amd64 | `fa6f1cd` on `cursor` | v0.1.8 linux-amd64 | `ac844117af9cb10d5e7a18b5294336283e03e44bd8ab3c59aa500d0ad4b6ce7d` | >=0.20.5 (recorded v0.21.3) |

Compatibility range stays `>=0.1.6,<0.2.0` with envelope
`agent-dispatch.cli/v1`. GitHub v0.1.6 and v0.1.7 published Darwin arm64
only; unpublished Linux artifacts for those tags are not claimed.
Translated amd64 is not linux/amd64.

The published GitHub tag `v0.1.0` remains the Darwin-only operator
release. Living catalog version is `0.1.1` unreleased. Packaging these
identities is the table above, not a new GitHub Release.

## What Dispatch E20 should consume

- Plugin inspection of existing routes, schedules, and doctor findings
  now works on the three advertised platforms at the pins above.
- Source-directory install, enable, disable, remove, upgrade, and
  rollback: Darwin runbooks plus
  [install-lifecycle-linux.md](../ops/install-lifecycle-linux.md) and
  [upgrade-rollback-linux.md](../ops/upgrade-rollback-linux.md).
- Roadmap next position: **Dispatch E20 / E20-T1**.
- Plugin sync work waits for Dispatch E26 (checksummed provider bundle
  and exact artifacts) before EPIC-007 may start.

## What this handoff does not authorize

Production activation, a v0.1.1 tag, Hermes core changes, companion
repository edits, EPIC-007/008 implementation, or treating mocked
`sys.platform` as Linux support.
