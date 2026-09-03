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
