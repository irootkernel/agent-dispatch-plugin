# Operations

Plugin maintainers own these runbooks for operators of Hermes profiles on
Darwin arm64. The plugin has no independent daemon or hosted service: Hermes
owns the profile and tool lifecycle, and Agent Dispatch owns its configuration,
store, sensing, and execution. Start with the public
[installation instructions](../../README.md) for normal first use.

## Runbooks

| Purpose | Owner document |
|---|---|
| Install, enable, disable, remove, and clean profile bookkeeping | [Installation lifecycle](install-lifecycle-darwin-arm64.md) |
| Replace an installed revision and recover through rollback | [Upgrade and rollback](upgrade-rollback-darwin-arm64.md) |
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

- [Qualification matrix](../implementation-tips/qualification-darwin-arm64.md).
- [Maintainer guide](../implementation-tips/maintainer-guide.md).
- [Clean-clone verification](../implementation-tips/clean-clone-verification.md), including Plugin Doctor and fresh-session inventory.
- [Release handoff](../implementation-tips/release-handoff.md).

Installation, plugin enablement, and toolset enablement are separate states.
A documented procedure does not authorize changes to a live profile or a
release publication.
