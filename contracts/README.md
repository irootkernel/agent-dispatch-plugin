# Frozen Public Contracts

`v0.1.0/` is the testable source of truth for the plugin's public contracts,
frozen by TASK-001 from `docs/specs/PRD.md`. The Python package created by
TASK-002 derives its manifest, registry, and expected tool inventory from this
source; nothing downstream may widen it without an approved canonical
amendment.

## Layout

- `v0.1.0/catalog.json` — the single declarative source: tool roster, fixed
  action-to-command mappings, identifier and state grammars, closed enums,
  pagination bounds, command vocabulary allowlist and denylist, wrapper,
  envelope, and error contracts, resource limits, compatibility matrix, and
  redaction rules.
- `v0.1.0/schemas/` — JSON Schema (draft 2020-12) for the closed wrapper, the
  `agent-dispatch.cli/v1` envelope, the plugin error object, and the ten tool
  input schemas.
- `v0.1.0/fixtures/` — deterministic valid and invalid fixtures for every
  schema, indexed by `catalog.json`.

## Validation

Run the deterministic offline gate (no process, database, or network by the
gate itself):

```bash
uv run --with jsonschema==4.26.0 --with referencing==0.37.0 contracts/validate.py
```

The validator asserts that the catalog equals the PRD invariants, every schema
is metaschema-valid with closed boundaries, schema-level enums and grammars
equal the catalog's closed enums and grammars, the wrapper operation enum
equals the tool roster, every fixture behaves as labeled, every action
resolves to a concrete argv with the declared command identity, and no denied
subcommand or forbidden input property is reachable. The pinned dependency
versions are part of the frozen surface until TASK-003 establishes the locked
project toolchain.

## Change control

These contracts are frozen for v0.1.0. Adding, removing, or renaming a tool,
changing an action-to-command mapping, or changing the public result, error,
compatibility, or resource contract requires explicit maintainer approval and
a canonical amendment to the PRD, then a new versioned contract directory.
The PRD oracle constants inside `validate.py` are part of the frozen surface
and must be updated together with the catalog and schemas in any amendment.
