# Agent Dispatch Plugin

agent-dispatch-plugin is a standalone Hermes plugin that exposes a
small, typed, inspection-only view of Agent Dispatch. Version 0.1.0 is
built around ten fixed tool contracts, one hardened process boundary,
and explicit compatibility evidence: exactly ten tools under the
`agent_dispatch` toolset, a SHA-256-verified executable trust gate, a
bounded process-group runner, and closed redacted errors.

## Installation and enablement

The plugin installs as a source-only Hermes plugin directory at an exact
pinned revision and starts disabled. In a Hermes v0.20.5 profile:

```bash
# 1. Place the plugin at the pinned revision (source-only; the release
#    handoff names the exact revision per candidate).
git clone <repository-source> && git -C agent-dispatch-plugin checkout <revision>
cp -R agent-dispatch-plugin <HERMES_HOME>/plugins/agent-dispatch-plugin

# 2. Enable the plugin, then the toolset (separate states).
hermes plugins enable agent-dispatch-plugin --no-allow-tool-override
hermes tools enable agent_dispatch

# 3. Seed the five frozen settings (binary_path, binary_sha256,
#    config_path, timeout_seconds) — see the installation lifecycle
#    runbook; the plugin's trust gate validates them every session.
```

Removal is the exact reverse and leaves no registration or tool
inventory residue. The complete lifecycle — disabled-by-default
installation, explicit plugin and toolset enablement, disablement,
removal, upgrade, and rollback between pinned revisions — is qualified
in the operations runbooks and asserted by the qualification suite.

## Requirements

Agent Dispatch `>=0.1.6,<0.2.0` (darwin/arm64 release artifact verified
by SHA-256), Hermes exactly v0.20.5, Darwin arm64.

## Repository authority

- Product requirements: docs/specs/PRD.md
- Initial roadmap: docs/roadmap/README.md
- Maintainer documentation index: docs/README.md
- Operations runbooks (installation, lifecycle, upgrade/rollback,
  evidence capture, troubleshooting): docs/ops/README.md
- Hermes proposal: docs/agent-dispatch-plugin.md, retained as
  non-canonical working input

The project targets a public MIT-licensed repository at
github.com/irootkernel/agent-dispatch-plugin. Commit, push, tag,
publication, installation, and activation each require separate
authorization; none is granted by this repository's content.
