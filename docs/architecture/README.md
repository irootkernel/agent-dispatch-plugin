# Architecture

The v0.1.0 architecture is a thin, management-only adapter:

Hermes model -> typed plugin schema -> validated tool handler -> shared runner
-> Agent Dispatch CLI -> validated agent-dispatch.cli/v1 envelope -> bounded
plugin result.

The plugin owns input validation, fixed command selection, process isolation,
envelope validation, and diagnostic redaction. Agent Dispatch remains the
authority for domain state and semantics. runner.py is the sole process
boundary, and handlers cannot open the Agent Dispatch database.

Durable implementation choices must be recorded in
docs/architecture-decision-records/README.md. Normative behavior remains in
docs/specs/PRD.md.

## Skeleton components (TASK-002)

The repository root is the Hermes plugin directory: `plugin.yaml` plus the
flat package modules. Hermes imports it as `hermes_plugins.agent_dispatch_plugin`
and calls `register(ctx)`.

- `registry.py` is the declarative registry: it parses
  `contracts/v0.1.0/catalog.json` into frozen tool and action specs and owns
  the expected inventory. Every downstream view derives from it (ADR-001).
- `schemas.py` serves the frozen input schemas and descriptions to Hermes;
  it composes nothing of its own.
- `tools/__init__.py` builds the skeleton handlers: every tool fails closed
  with the frozen `binary_unavailable` error and the availability check hides
  the toolset until the EPIC-002 runner exists.
- `runner.py` is the reserved sole process-execution boundary; nothing calls
  it in the skeleton.
- `plugin.yaml` is generated and verified by `scripts/manifest_parity.py`,
  which also proves catalog, manifest, registration, and expected-inventory
  parity for exactly ten tools by driving the real registration path.
- `pyproject.toml` is the uv project authority; the runtime is
  dependency-free and the dev group pins the validation toolchain
  (jsonschema 4.26.0, referencing 0.37.0, PyYAML).
