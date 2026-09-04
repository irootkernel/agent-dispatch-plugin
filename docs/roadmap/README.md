# Initial Roadmap

Lifecycle: Planned -> In Progress -> In Review -> Completed. Deferred and
Blocked are explicit terminal or waiting states. Completion requires the
evidence named by the Detailed SOT, not prose assertion.

## Epic register

| Epic | Outcome | Status | Detailed SOT |
|---|---|---|---|
| EPIC-001 | Establish canonical contracts and a testable plugin skeleton | Completed | Canonical Outcomes: contracts/v0.1.0/catalog.json, docs/specs/contracts.md, docs/architecture-decision-records/ADR-001-declarative-contract-registry.md, plugin.yaml, scripts/manifest_parity.py, TESTING.md, Makefile |
| EPIC-002 | Build the single secure process and validation boundary | Completed | Canonical Outcomes: runner.py, envelopes.py, docs/architecture-decision-records/ADR-004-runner-trust-gate.md, docs/architecture-decision-records/ADR-005-bounded-process-group-runner.md, docs/architecture-decision-records/ADR-006-closed-errors-diagnostics-redaction.md, TESTING.md |
| EPIC-003 | Deliver the exact ten inspection tools and parity evidence | Planned | docs/todo/TODO-INSPECTION-TOOLS.md |
| EPIC-004 | Prove security and compatibility release gates | Planned | docs/todo/TODO-SECURITY-COMPATIBILITY.md |
| EPIC-005 | Prove clean-clone distribution, rollback, and release readiness | Planned | docs/todo/TODO-DISTRIBUTION-RELEASE.md |

## Work units

| Task | Epic | Work unit | Status | Completion evidence |
|---|---|---|---|---|
| TASK-001 | EPIC-001 | Freeze compatibility, tool, result, error, security, and fixture contracts | Completed | Reviewed schemas and fixtures traceable to the PRD |
| TASK-002 | EPIC-001 | Create the Python package, manifest, and declarative registry skeleton | Completed | Python project authority, Plugin Doctor, and registry/manifest parity evidence |
| TASK-003 | EPIC-001 | Run $aquarium:test-setup to establish aquarium-test-contract/v1 and baseline checks | Completed | Approved test contract and reachable baseline gate |
| TASK-004 | EPIC-002 | Implement trusted configuration, platform, binary identity, and version checks | Completed | Positive and negative dependency checks |
| TASK-005 | EPIC-002 | Implement the bounded process-group runner | Completed | Timeout, stream limit, termination, and argv tests |
| TASK-006 | EPIC-002 | Implement closed errors, diagnostics, and defense-in-depth redaction | Completed | Seeded-secret and bounded-diagnostic tests |
| TASK-007 | EPIC-003 | Implement status and doctor tools | Completed | Schema, mapping, success, and failure evidence |
| TASK-008 | EPIC-003 | Implement routes, schedule inspection, and config tools | Completed | Action-level positive and negative evidence |
| TASK-009 | EPIC-003 | Implement dispatches, receipts, events, quarantine, and notifications | Completed | Action-level positive and negative evidence |
| TASK-010 | EPIC-003 | Prove manifest, registry, command, and fresh-session inventory parity | Planned | Exact ten-tool parity and smoke transcript |
| TASK-011 | EPIC-004 | Prove injection, traversal, secret, limit, malformed-output, and no-retry negatives | Planned | Deterministic security suite |
| TASK-012 | EPIC-004 | Run the disposable action-level compatibility matrix | Planned | Exact-artifact Darwin arm64 qualification transcript |
| TASK-013 | EPIC-004 | Obtain independent security and compatibility review | Planned | Adjudicated findings with no open release blocker |
| TASK-014 | EPIC-005 | Prove clean-clone CI, Plugin Doctor, and tool inventory | Planned | Clean environment transcript |
| TASK-015 | EPIC-005 | Prove pinned disabled installation, enablement, disablement, and removal | Planned | Disposable-profile lifecycle transcript |
| TASK-016 | EPIC-005 | Complete maintainer, security, compatibility, upgrade, and rollback documentation | Planned | Documentation review checklist |
| TASK-017 | EPIC-005 | Prepare an exact-commit release handoff | Planned | Immutable review target and release checklist; tag and publication remain separately authorized |

## Sequencing

Within EPIC-001, TASK-001 precedes TASK-002, and TASK-002 precedes TASK-003.
EPIC-002 depends on that foundation. EPIC-003 depends on the runner boundary.
EPIC-004 qualifies the complete public surface. EPIC-005 consumes the accepted
qualification evidence. Parallel work is allowed only where a dossier states
that contracts and evidence ownership do not overlap.
