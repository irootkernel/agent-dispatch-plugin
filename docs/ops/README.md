# Operations

Plugin maintainers own these runbooks for operators of Hermes profiles.
The published GitHub tag `v0.1.0` remains Darwin arm64. The living
candidate also has Linux source-directory lifecycle runbooks. The plugin
has no independent daemon or hosted service: Hermes
owns the profile and tool lifecycle, and Agent Dispatch owns its configuration,
store, sensing, and execution. Start with the public
[installation instructions](../../README.md) for normal first use.

## Runbooks

| Purpose | Owner document |
|---|---|
| Install, enable, disable, remove, and clean profile bookkeeping (Darwin) | [Installation lifecycle (Darwin arm64)](install-lifecycle-darwin-arm64.md) |
| Install, enable, disable, remove, and clean profile bookkeeping (Linux) | [Installation lifecycle (Linux)](install-lifecycle-linux.md) |
| Replace an installed revision and recover through rollback (Darwin) | [Upgrade and rollback (Darwin arm64)](upgrade-rollback-darwin-arm64.md) |
| Replace an installed revision and recover through rollback (Linux) | [Upgrade and rollback (Linux)](upgrade-rollback-linux.md) |
| Capture bounded, redacted support evidence | [Security evidence capture](security-evidence-capture.md) |
| Diagnose missing tools, trust failures, and known runtime boundaries | [Troubleshooting](troubleshooting.md) |

Check the runbook's prerequisites and target profile before following it.
Qualification procedures use disposable profiles and synthetic state; their
recorded transcripts are historical evidence, not a statement about a current
operator profile. For unresolved failures, use the troubleshooting escalation
path and provide evidence under the security capture guide to plugin maintainers.

## Development and release procedures

Code-changing and release-engineering guidance is owned by
[implementation tips](../implementation-tips/README.md):

- [Qualification matrix (Darwin arm64)](../implementation-tips/qualification-darwin-arm64.md).
- [Qualification matrix (Linux arm64)](../implementation-tips/qualification-linux-arm64.md).
- [Qualification matrix (Linux amd64)](../implementation-tips/qualification-linux-amd64.md).
- [Maintainer guide](../implementation-tips/maintainer-guide.md).
- [Clean-clone verification](../implementation-tips/clean-clone-verification.md), including Plugin Doctor and fresh-session inventory.
- [Release handoff](../implementation-tips/release-handoff.md).
- [Dispatch E20 / E20-T1 handoff](../implementation-tips/dispatch-e20-handoff.md).

Installation, plugin enablement, and toolset enablement are separate states.
A documented procedure does not authorize changes to a live profile or a
release publication.
