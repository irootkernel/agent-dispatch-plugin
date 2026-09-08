# Maintainer Guide

Audience: maintainers of `agent-dispatch-plugin` v0.1.0. This guide owns
the durable maintenance procedure: what is frozen, how changes are
accepted, which gates every change runs, and which development or operational document
answers each question. It intentionally references the canonical owners
instead of restating them.

## Frozen surface and change control

The product scope, tool roster, command vocabulary, wrapper and error
contracts, resource limits, and compatibility matrix are frozen in
`contracts/v0.1.0/` and bound by `docs/specs/PRD.md` and
`docs/specs/contracts.md`. Changes require explicit maintainer approval
and a canonical amendment; the deterministic oracle
(`uv run contracts/validate.py`) and the parity gate
(`uv run scripts/manifest_parity.py`) fail closed on any drift between
the catalog, schemas, `plugin.yaml`, and the registered inventory.
`plugin.yaml` is derived — never edit it directly; regenerate with
`uv run scripts/manifest_parity.py --write` after a catalog change.

## Distinct states

Repository source, exact commit, release tag, plugin enablement, and
toolset enablement are separate states with separate owners and
commands. None implies another:

| State | Owner | Command that changes it |
|---|---|---|
| Repository source | the Git remote the operator clones | `git clone <source>` |
| Exact commit | the working tree / installed plugin directory | `git checkout <revision>` (see the upgrade/rollback runbook) |
| Release tag | the release process | tagging is separately authorized and recorded in the release handoff |
| Plugin enablement | profile config `plugins.enabled` | `hermes plugins enable/disable agent-dispatch-plugin` |
| Toolset enablement | profile config `platform_toolsets.cli` | `hermes tools enable/disable agent_dispatch` |

The installed plugin is a source-only directory at one exact revision
(the installer manifest boundary is recorded in the installation
lifecycle runbook); the five frozen settings under
`plugins.entries.agent-dispatch-plugin.settings` are the operator's
trust anchor and are validated by the plugin's own trust gate on every
session start.

## Every-change gates

Before any change is committed, `make test` must pass: the prepare
gates (format, lint, type check, byte-compilation, the frozen-contract
oracle, and manifest/registry parity), the deterministic unit and
integration suites, and the Plugin Doctor e2e stage. Changes that touch
the pinned runtime surface additionally run `make test-qualify`
(disposable compatibility matrix and installation lifecycle; requires
Hermes v0.20.5 or newer and the pinned Agent Dispatch artifact — see [TESTING.md](../../TESTING.md)).
A clean clone of the exact candidate revision must pass the same gates
(the clean-clone runbook records the procedure and the recorded
directory-name defect with its remediation).

## Documentation map

- [Compatibility and artifact identity](qualification-darwin-arm64.md).
- [Clean-clone CI, Plugin Doctor, and fresh-session inventory](clean-clone-verification.md).
- [Installation, enablement, disablement, and removal](../ops/install-lifecycle-darwin-arm64.md).
- [Upgrade and rollback](../ops/upgrade-rollback-darwin-arm64.md).
- [Redaction-safe evidence capture](../ops/security-evidence-capture.md).
- [Symptom-driven diagnosis](../ops/troubleshooting.md).
- [Release candidate preparation](release-handoff.md).

Maintainers add a new operational document only through a roadmap work
unit that names its owner; [the operations index](../ops/README.md) remains
its entrypoint. Development and release guidance belongs to
[implementation tips](README.md).

## Review checklist for documentation changes

A documentation change in this repository is complete when: every
statement names its canonical owner or is itself canonical; no secret,
credential, live path, or machine-specific trust assumption appears
(placeholders only); each reproduction procedure names its exact
prerequisites and artifact identities; lifecycle vocabulary matches the
roadmap; and every relative link resolves inside the repository.
