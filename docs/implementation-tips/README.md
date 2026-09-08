# Development Workflow

This role owns non-normative development, review, and release guidance.
The PRD, accepted ADRs, executable contracts, and roadmap keep their respective
authority. Start here when contributing to the plugin.

## Set up a checkout

Clone the repository and run `uv sync` from its root. The project requires
Python >=3.11 and pins development dependencies in `uv.lock`; it is source-only
and has no third-party runtime dependencies. Read the
[architecture](../architecture/README.md) before changing module boundaries.

Unit and integration tests use deterministic fakes. Plugin Doctor e2e needs
Hermes on PATH; qualification additionally needs Darwin arm64 and the pinned
Agent Dispatch artifact. See [TESTING.md](../../TESTING.md) for exact environment
requirements and failure behavior. Keep qualification profiles disposable.

## Choose the change entrypoint

| Change | Start with |
|---|---|
| Tool input, action mapping, or result contract | [Contract reference](../specs/contracts.md), then `contracts/v0.1.0/` and `registry.py` |
| Input validation | `tools/inputs.py` and its schema cross-check tests |
| Execution or availability | `runner.py` and trust, process, and security tests |
| Output validation or redaction | `envelopes.py` and frozen output fixtures |
| Hermes registration | Root `__init__.py`, `schemas.py`, and fresh-session integration tests |
| Documentation | [Ownership map](../README.md) and the maintainer review checklist |

Paths in the table are repository-relative. Keep process creation in
`runner.py`; use argv arrays, bounded stream draining, and existing closed
errors. Derive the manifest and tool inventory from the catalog. Contract
amendments need maintainer approval; do not edit generated `plugin.yaml`
directly. The [maintainer guide](maintainer-guide.md) explains regeneration and
change control.

## Verify and hand off

Use [TESTING.md](../../TESTING.md) to select local stages. Before a commit,
`make test` is the established aggregate gate; it includes a source formatter.
Review its changes. Documentation-only verification can use the non-writing
checks in the [documentation index](../README.md), but does not replace the
pre-commit or release gate.

A contribution should explain the observable change, its contract owner,
validation performed, and any unresolved limitation. Add tests for changed
behavior and failure boundaries. Preserve unrelated work and never treat an
old qualification transcript as proof for a new runtime revision.

- [Maintainer guide](maintainer-guide.md): frozen surface, review, and change control.
- [Clean-clone verification](clean-clone-verification.md): exact-revision test reproduction and historical evidence.
- [Qualification matrix](qualification-darwin-arm64.md): pinned artifacts and disposable compatibility verification.
- [Release handoff](release-handoff.md): candidate identity and release gates.
- [Operations](../ops/README.md): installation, recovery, and support.

## Tool input examples for integration work

Normal users ask Hermes to call tools in conversation. These JSON objects are for contributors inspecting handler inputs; they are not shell commands. The frozen schemas in `contracts/v0.1.0/schemas/tools/` remain authoritative.

`agent_dispatch_status`:

```json
{}
```

`agent_dispatch_routes` (replace the example route ID with an existing one):

```json
{"action": "show", "route_id": "inbox"}
```

`agent_dispatch_dispatches`:

```json
{"action": "list", "route": "inbox", "limit": 10}
```

Validate changed examples against their frozen input schemas. Executable selection and trusted configuration belong to profile settings; tool inputs cannot supply arbitrary commands, flags, or environment values.
