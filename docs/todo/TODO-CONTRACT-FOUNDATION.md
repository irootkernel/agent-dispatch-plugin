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

All three groups are recorded as accepted ADR-001, ADR-002, and ADR-003; the
frozen artifacts live in contracts/v0.1.0/ with the offline gate
`uv run --with jsonschema contracts/validate.py` (docs/specs/contracts.md).

## Guidance for later tasks and epics

- TASK-002 derives plugin.yaml provides_tools, the Python registration table,
  and the expected inventory from contracts/v0.1.0/catalog.json; never
  hand-edit derived views (ADR-001).
- Observed against the installed Agent Dispatch v0.1.6 help: receipts kind is
  `acceptance|execution_projection|work`; quarantine state is
  `held|released|discarded|superseded`; the envelope `command` member carries
  the full command path (for example `config show`); error envelopes carry a
  closed `error` object (`code`, `category`, `message`, `retryable`) and are
  reported through exit codes and stderr, while success envelopes arrive on
  stdout.
- EPIC-002 must verify with the real binary that the PRD-documented
  `quarantine list --route/--limit` and the absence of a notifications
  `--offset` filter match actual flag support; a mismatch is an upstream
  compatibility finding, not a contract change.
- EPIC-002 runner tests should reuse contracts/v0.1.0 fixtures for envelope,
  wrapper, and error validation cases before writing new ones.
- TASK-003: the uv project authority and its pinned dev toolchain
  (jsonschema 4.26.0, referencing 0.37.0, PyYAML) exist since TASK-002; the
  test contract should run checks through `uv run` in that environment
  (`uv run contracts/validate.py`, `uv run scripts/manifest_parity.py`) and
  add the baseline suite as a project dev dependency.

## Acceptance

- Exactly ten tools appear once in manifest, registry, and expected inventory.
- No mutation command or undeclared Hermes surface exists.
- All contracts have deterministic validation fixtures.
- Plugin Doctor can inspect the skeleton without network, database, migration,
  or Agent Dispatch state activity during registration.

## Non-goals

Runner implementation, tool-domain handlers, compatibility claims, install,
activation, commit, tag, publication, and release.
