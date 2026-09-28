# Public Contracts

`v0.1.0/` is the frozen ten-tool baseline from TASK-001.
`v0.2.0/` is the approved EPIC-007 thirteen-tool contract for the exact
Agent Dispatch v0.2.0 provider candidate. The running plugin continues to
derive its manifest and registry from v0.1.0 until TASK-024 activates the new
catalog; TASK-026 owns native platform qualification. The PRD and
`docs/specs/contracts.md` bind both contract versions.

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
- `v0.2.0/` — the new catalog, all thirteen closed input schemas, the
  unchanged wrapper and envelope, three closed sync result schemas, and
  deterministic admission, command, result, and legacy fixtures.

## Validation

Run the deterministic offline gate (no process, database, or network by the
gate itself):

```bash
uv run --with jsonschema==4.26.0 --with referencing==0.37.0 contracts/validate.py
uv run --frozen contracts/validate_v020.py
```

The validator asserts that the catalog equals the PRD invariants, every schema
is metaschema-valid with closed boundaries, schema-level enums and grammars
equal the catalog's closed enums and grammars, the wrapper operation enum
equals the tool roster, every fixture behaves as labeled, every action
resolves to a concrete argv with the declared command identity, and no denied
subcommand or forbidden input property is reachable. The pinned dependency
versions are part of the frozen v0.1.0 surface. The v0.2.0 validator checks
the exact thirteen-name roster, three commands, trusted bindings, wrapper
operation enum, provider pins, identity paths and formats, and its fixtures.

## Change control

These contracts are frozen for v0.1.0. Adding, removing, or renaming a tool,
changing an action-to-command mapping, or changing the public result, error,
compatibility, or resource contract requires explicit maintainer approval and
a canonical amendment to the PRD, then a new versioned contract directory.
The PRD oracle constants inside `validate.py` remain the frozen v0.1.0
surface. The approved v0.2.0 amendment has its own catalog and oracle; later
changes to either version require another canonical approval.
