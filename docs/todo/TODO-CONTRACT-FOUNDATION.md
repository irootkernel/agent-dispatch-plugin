# EPIC-001 Contract Foundation

Status: Adopted
Roadmap: EPIC-001 in docs/roadmap/README.md
Tasks: TASK-001, TASK-002, TASK-003

## Outcome

Create one testable source of truth for the public contracts and a minimal
Hermes plugin skeleton without implementing business-domain behavior.

## Delivery

- TASK-001 materializes the exact tool roster, action mappings, schemas,
  compatibility matrix, errors, resource limits, redaction rules, and fixture
  catalog from the PRD.
- TASK-002 creates the Python project authority, standalone manifest v2/API v1
  package skeleton, and one declarative registry that drives tool registration
  and parity checks.
- TASK-003 invokes $aquarium:test-setup as a later, separate workflow and
  establishes aquarium-test-contract/v1 plus the baseline test handlers. This
  project-design workflow does not perform test setup.

## Decisions to record

- Registry shape and generated-versus-handwritten artifact ownership.
- Identifier grammars, pagination upper bounds, closed enums, and the precise
  command-specific result schemas.
- Test layers and evidence locations established by TASK-003.

## Acceptance

- Exactly ten tools appear once in manifest, registry, and expected inventory.
- No mutation command or undeclared Hermes surface exists.
- All contracts have deterministic validation fixtures.
- Plugin Doctor can inspect the skeleton without network, database, migration,
  or Agent Dispatch state activity during registration.

## Non-goals

Runner implementation, tool-domain handlers, compatibility claims, install,
activation, commit, tag, publication, and release.
