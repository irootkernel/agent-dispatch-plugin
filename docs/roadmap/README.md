# Initial Roadmap

Lifecycle: Planned -> In Progress -> In Review -> Completed. Deferred and
Blocked are explicit terminal or waiting states. Completion requires the
evidence named by the Detailed SOT, not prose assertion.

## Epic register

| Epic | Outcome | Status | Detailed SOT |
|---|---|---|---|
| EPIC-001 | Establish canonical contracts and a testable plugin skeleton | Completed | Canonical Outcomes: contracts/v0.1.0/catalog.json, docs/specs/contracts.md, docs/architecture-decision-records/ADR-001-declarative-contract-registry.md, plugin.yaml, scripts/manifest_parity.py, TESTING.md, Makefile |
| EPIC-002 | Build the single secure process and validation boundary | Completed | Canonical Outcomes: runner.py, envelopes.py, docs/architecture-decision-records/ADR-004-runner-trust-gate.md, docs/architecture-decision-records/ADR-005-bounded-process-group-runner.md, docs/architecture-decision-records/ADR-006-closed-errors-diagnostics-redaction.md, TESTING.md |
| EPIC-003 | Deliver the exact ten inspection tools and parity evidence | Completed | Canonical Outcomes: tools/__init__.py, tools/inputs.py, docs/architecture-decision-records/ADR-007-derived-input-validation.md, scripts/manifest_parity.py, tests/unit/test_input_validation.py, tests/unit/test_tools_status_doctor.py, tests/unit/test_tools_routes_schedule_config.py, tests/unit/test_tools_dispatch_family.py, tests/integration/test_fresh_session_inventory.py, TESTING.md |
| EPIC-004 | Prove security and compatibility release gates | Completed | Canonical Outcomes: tests/unit/test_security_negatives.py, tests/qualification/test_compatibility_matrix.py, tests/qualification/_hermes_driver.py, docs/implementation-tips/qualification-darwin-arm64.md, tools/__init__.py, TESTING.md, Makefile |
| EPIC-005 | Prove clean-clone distribution, rollback, and release readiness | Completed | Canonical Outcomes: pyproject.toml, tests/qualification/test_install_lifecycle.py, docs/implementation-tips/clean-clone-verification.md, docs/ops/install-lifecycle-darwin-arm64.md, docs/ops/upgrade-rollback-darwin-arm64.md, docs/implementation-tips/maintainer-guide.md, docs/ops/security-evidence-capture.md, docs/ops/troubleshooting.md, docs/implementation-tips/release-handoff.md, README.md, TESTING.md |
| EPIC-006 | Linux support and existing-tool parity | Planned | docs/todo/TODO-LINUX-SUPPORT.md |

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
| TASK-010 | EPIC-003 | Prove manifest, registry, command, and fresh-session inventory parity | Completed | Exact ten-tool parity and smoke transcript |
| TASK-011 | EPIC-004 | Prove injection, traversal, secret, limit, malformed-output, and no-retry negatives | Completed | Deterministic security suite |
| TASK-012 | EPIC-004 | Run the disposable action-level compatibility matrix | Completed | Exact-artifact Darwin arm64 qualification transcript |
| TASK-013 | EPIC-004 | Obtain independent security and compatibility review | Completed | Adjudicated findings with no open release blocker |
| TASK-014 | EPIC-005 | Prove clean-clone CI, Plugin Doctor, and tool inventory | Completed | Clean environment transcript |
| TASK-015 | EPIC-005 | Prove pinned disabled installation, enablement, disablement, and removal | Completed | Disposable-profile lifecycle transcript |
| TASK-016 | EPIC-005 | Complete maintainer, security, compatibility, upgrade, and rollback documentation | Completed | Documentation review checklist |
| TASK-017 | EPIC-005 | Prepare an exact-commit release handoff | Completed | Immutable review target and release checklist; tag and publication remain separately authorized |
| TASK-018 | EPIC-006 | Admit the Linux amendment and program charter | Planned | Reviewed platform amendment, reserved later identities, and qualification readiness record |
| TASK-019 | EPIC-006 | Qualify the trusted runner on Linux | Planned | Linux and Darwin runner tests for isolation, trust, timeout, and redaction |
| TASK-020 | EPIC-006 | Add native schedule mapping and contract parity | Planned | Launchd/systemd descriptor parity with matching tests and documentation |
| TASK-021 | EPIC-006 | Run real platform and existing-action qualification | Planned | Action-level transcripts on Darwin arm64, Linux amd64, and Linux arm64 |
| TASK-022 | EPIC-006 | Close Linux operations and hand off to Dispatch | Planned | Lifecycle guidance, cold review, and Dispatch E20 / E20-T1 handoff |

## Sequencing

Within EPIC-001, TASK-001 precedes TASK-002, and TASK-002 precedes TASK-003.
EPIC-002 depends on that foundation. EPIC-003 depends on the runner boundary.
EPIC-004 qualifies the complete public surface. EPIC-005 consumes the accepted
qualification evidence. EPIC-006 follows that completed sequence and does not
depend on Dispatch sync work. Within EPIC-006, TASK-018 precedes TASK-019,
TASK-019 precedes TASK-020, TASK-020 precedes TASK-021, and TASK-021 precedes
TASK-022. After TASK-022 the next global position is Dispatch E20 / E20-T1.
The wiki-sync program reserves EPIC-007, EPIC-008, and TASK-023 through
TASK-032; do not allocate those identities. TASK-018 admits them onto this
register. Parallel work is allowed only where a dossier states that contracts
and evidence ownership do not overlap.
