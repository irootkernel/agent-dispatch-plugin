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
- `tools/__init__.py` builds the handlers over the runner trust gate: the
  availability check exposes the toolset only when the configured
  executable, trusted configuration, and version verify (ADR-004), and
  every invocation fails closed with a frozen closed error until the
  bounded execution path lands later in EPIC-002.
- `runner.py` is the sole process boundary. Its trust gate resolves the
  immutable plugin configuration and verifies the platform, both trusted
  paths, the executable SHA-256, and the supported Agent Dispatch version
  (ADR-004); the bounded process-group execution and envelope validation
  arrive with the remaining EPIC-002 tasks.
- `plugin.yaml` is generated and verified by `scripts/manifest_parity.py`,
  which also proves catalog, manifest, registration, and expected-inventory
  parity for exactly ten tools by driving the real registration path.
- `pyproject.toml` is the uv project authority; the runtime is
  dependency-free and the dev group pins the validation toolchain
  (jsonschema 4.26.0, referencing 0.37.0, PyYAML).
