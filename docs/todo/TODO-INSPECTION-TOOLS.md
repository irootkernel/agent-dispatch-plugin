# EPIC-003 Inspection Tools

Status: Adopted
Roadmap: EPIC-003 in docs/roadmap/README.md
Tasks: TASK-007, TASK-008, TASK-009, TASK-010
Depends on: EPIC-001, EPIC-002

## Outcome

Expose exactly the ten PRD tools with stable schemas and fixed command mappings
while preserving Agent Dispatch as the domain authority.

## Delivery

- Implement status and doctor.
- Implement routes, schedule inspection, and config.
- Implement dispatches, read-only receipts, event show, quarantine, and
  notifications.
- Drive schemas, command descriptors, registration, and parity checks from the
  EPIC-001 registry.

## Execution notes

- TASK-007 added the derived input-validation layer (`tools/inputs.py`,
  ADR-007): handlers validate every request against the tool's frozen input
  schema and reject out-of-contract requests with `invalid_argument` before
  the runner boundary. TASK-008 and TASK-009 build their action-level
  positive and negative evidence on top of that layer; negative input cases
  prove no process is created by spying on `runner.run_inspection`.
- TASK-008 delivered the routes, schedule inspection, and config evidence as
  one parametrized action-branch matrix: each branch asserts its exact fixed
  argv and two-token envelope command identity through the full boundary,
  and the negative matrix covers route_id placement, the identifier grammar
  (including traversal separators), closed action enums, and
  probe_targets-is-validate-only.
- TASK-009 delivered the dispatch-family evidence the same way and added the
  read-only proof: every action template token stays inside the frozen
  command vocabulary (no denied mutation subcommand is reachable in a
  command slot; validated values occupy only value slots), receipts maps
  only to `receipts list` and `receipts show`, and grammar-validated values
  can never start an option prefix, so nothing can smuggle a flag into
  argv.
- TASK-010 closed the parity loop: `scripts/manifest_parity.py` now also
  proves the tool-schema-file set equals the roster and that every action's
  expected_command resolves inside the frozen command vocabulary with no
  denied subcommand in any argv template; a fresh-interpreter integration
  test registers the ten tools over the real Hermes-style loader and
  completes one trust-gated smoke inspection, and the e2e Plugin Doctor
  validates the same inventory over the public CLI.

## Acceptance

- Each tool and every action branch has valid-input success evidence.
- Conditional fields, identifier grammars, enums, pagination, and prohibited
  properties have negative coverage without process creation.
- Each tool has stable success and error results.
- Receipt inspection cannot reach worker receipt mutations.
- Manifest, registry, schema, command allowlist, and fresh-session inventory
  agree on exactly ten tools.
- No handler constructs arbitrary argv, accesses SQLite, retries, mutates
  Agent Dispatch, or interprets domain content.

## Non-goals

Worker or admin mutations, generic pass-through, new tools, hooks, custom CLI
commands, override capabilities, and compatibility sign-off.
