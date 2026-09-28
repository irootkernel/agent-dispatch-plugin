# Agent Dispatch Plugin Roadmap

Lifecycle: Planned -> In Progress -> In Review -> Completed. Deferred and
Blocked are explicit terminal or waiting states. Completion requires the
evidence named by the Detailed SOT, not prose assertion.

## Program position

The original `AD-WIKI-SYNC-PROGRAM/v1` G01-G11 schedule is historical intake,
not the current execution sequence. Plugin G01 (EPIC-006) and Dispatch
E20-E22 are Completed in their respective roadmaps. Dispatch ADR-0023
replaced the proposed N-member/E26 provider with an implemented two-node
v0.2.0 scope. The current Plugin remains inspection-only and rejects
Dispatch v0.2.0 until EPIC-007 amends the contract and qualifies its actions.

Active epic: none. EPIC-006 and TASK-018 through TASK-022 are Completed.
Next eligible work: **EPIC-007 / TASK-023** (Planned). EPIC-008 and
TASK-028 through TASK-032 retain their reserved identities but are Deferred;
they are not the successor to EPIC-007. The one-active-epic/task rule still
applies. Core implementation completion does not establish Plugin
qualification, release, or production activation.

`Planned` identifies the next work unit; it does not approve the v0.2.0
contract or authorize implementation. Record maintainer authorization to
begin TASK-023 and the provider identity under review before moving
EPIC-007 and TASK-023 to In Progress. TASK-023 must then obtain the canonical
amendment approval before runtime changes. A missing authorization or
properly stamped candidate keeps the task Planned or Blocked with the unmet
prerequisite.

## Epic register

| Epic | Outcome | Status | Detailed SOT |
|---|---|---|---|
| EPIC-001 | Establish canonical contracts and a testable plugin skeleton | Completed | Canonical Outcomes: contracts/v0.1.0/catalog.json, docs/specs/contracts.md, docs/architecture-decision-records/ADR-001-declarative-contract-registry.md, plugin.yaml, scripts/manifest_parity.py, TESTING.md, Makefile |
| EPIC-002 | Build the single secure process and validation boundary | Completed | Canonical Outcomes: runner.py, envelopes.py, docs/architecture-decision-records/ADR-004-runner-trust-gate.md, docs/architecture-decision-records/ADR-005-bounded-process-group-runner.md, docs/architecture-decision-records/ADR-006-closed-errors-diagnostics-redaction.md, TESTING.md |
| EPIC-003 | Deliver the exact ten inspection tools and parity evidence | Completed | Canonical Outcomes: tools/__init__.py, tools/inputs.py, docs/architecture-decision-records/ADR-007-derived-input-validation.md, scripts/manifest_parity.py, tests/unit/test_input_validation.py, tests/unit/test_tools_status_doctor.py, tests/unit/test_tools_routes_schedule_config.py, tests/unit/test_tools_dispatch_family.py, tests/integration/test_fresh_session_inventory.py, TESTING.md |
| EPIC-004 | Prove security and compatibility release gates | Completed | Canonical Outcomes: tests/unit/test_security_negatives.py, tests/qualification/test_compatibility_matrix.py, tests/qualification/_hermes_driver.py, docs/implementation-tips/qualification-darwin-arm64.md, tools/__init__.py, TESTING.md, Makefile |
| EPIC-005 | Prove clean-clone distribution, rollback, and release readiness | Completed | Canonical Outcomes: pyproject.toml, tests/qualification/test_install_lifecycle.py, docs/implementation-tips/clean-clone-verification.md, docs/ops/install-lifecycle-darwin-arm64.md, docs/ops/upgrade-rollback-darwin-arm64.md, docs/implementation-tips/maintainer-guide.md, docs/ops/security-evidence-capture.md, docs/ops/troubleshooting.md, docs/implementation-tips/release-handoff.md, README.md, TESTING.md |
| EPIC-006 | Linux support and existing-tool parity | Completed | docs/todo/TODO-LINUX-SUPPORT.md |
| EPIC-007 | Two-node sync inspection and diagnostics | Planned | [docs/todo/TODO-SYNC-INSPECTION.md](../todo/TODO-SYNC-INSPECTION.md) |
| EPIC-008 | Constrained sync management requests | Deferred | Reserved by TASK-018; no implemented request/query provider or approved Plugin mutation authority. Re-admit only through new core and Plugin contracts and separate authorization. |

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
| TASK-018 | EPIC-006 | Admit the Linux amendment and program charter | Completed | Reviewed living v0.1.1 platform amendment, reserved later identities, G01, v0.1.8 Linux artifact selection, and readiness record in [docs/todo/TODO-LINUX-SUPPORT.md](../todo/TODO-LINUX-SUPPORT.md#task-018-close) |
| TASK-019 | EPIC-006 | Qualify the trusted runner on Linux | Completed | Real-host Linux and Darwin runner tests for isolation, trust, timeout, and redaction; close record in [docs/todo/TODO-LINUX-SUPPORT.md](../todo/TODO-LINUX-SUPPORT.md#task-019-close) |
| TASK-020 | EPIC-006 | Add native schedule mapping and contract parity | Completed | Launchd/systemd argv mapping, wrong-platform and unsupported-host negatives, and close record in [docs/todo/TODO-LINUX-SUPPORT.md](../todo/TODO-LINUX-SUPPORT.md#task-020-close) |
| TASK-021 | EPIC-006 | Run real platform and existing-action qualification | Completed | Darwin: docs/implementation-tips/qualification-darwin-arm64.md; linux/arm64 v0.1.7 on e7f3375: docs/implementation-tips/qualification-linux-arm64.md; linux/amd64 v0.1.8 on fa6f1cd: docs/implementation-tips/qualification-linux-amd64.md; close in [docs/todo/TODO-LINUX-SUPPORT.md](../todo/TODO-LINUX-SUPPORT.md#task-021-close) |
| TASK-022 | EPIC-006 | Close Linux operations and hand off to Dispatch | Completed | Linux lifecycle runbooks, cold review, and Dispatch E20 / E20-T1 handoff in [docs/implementation-tips/dispatch-e20-handoff.md](../implementation-tips/dispatch-e20-handoff.md); close in [docs/todo/TODO-LINUX-SUPPORT.md](../todo/TODO-LINUX-SUPPORT.md#task-022-close) |
| TASK-023 | EPIC-007 | Admit the implemented two-node provider and versioned inspection contract | Planned | Approved PRD/contract amendment and superseding redaction ADR, pinned provider bundle, platform SHA allowlist, and registered/available inventory rules; see [dossier](../todo/TODO-SYNC-INSPECTION.md#task-023-admit-the-provider-and-contract) |
| TASK-024 | EPIC-007 | Add three fixed sync inspection tools | Planned | Fixed commands including config-flag exception, fresh handler capability gate, and thirteen-name registration versus 0/10/13 available-definition evidence; see [dossier](../todo/TODO-SYNC-INSPECTION.md#task-024-add-three-fixed-inspection-tools) |
| TASK-025 | EPIC-007 | Preserve sync evidence and safe presentation | Planned | Disabled, partial, stale, blocked, and service/listener distinctions plus exact approved identity fields and seeded-secret negatives; see [dossier](../todo/TODO-SYNC-INSPECTION.md#task-025-preserve-evidence-and-safe-presentation) |
| TASK-026 | EPIC-007 | Qualify the inspection surface through Hermes | Planned | Allowlisted exact-artifact action and failure evidence, including native service-manager inspection, on Darwin arm64, Linux amd64, and Linux arm64; see [dossier](../todo/TODO-SYNC-INSPECTION.md#task-026-qualify-through-hermes) |
| TASK-027 | EPIC-007 | Close inspection documentation and handoff | Planned | Accurate operations guidance, complete checks, and bounded cold review; see [dossier](../todo/TODO-SYNC-INSPECTION.md#task-027-close-documentation-and-handoff) |
| TASK-028 | EPIC-008 | Define and qualify management authorization | Deferred | Reserved identity; core request contract and separate Plugin authority required before replanning |
| TASK-029 | EPIC-008 | Implement the one constrained request tool | Deferred | Reserved identity; no current `sync request` provider command |
| TASK-030 | EPIC-008 | Handle accepted and unknown submissions correctly | Deferred | Reserved identity; no provider request identity or inspection surface |
| TASK-031 | EPIC-008 | Qualify management security and action-level behavior | Deferred | Reserved identity; management surface has not been admitted |
| TASK-032 | EPIC-008 | Close management and hand off the paired system | Deferred | Reserved identity; old Dispatch E27 handoff was superseded by ADR-0023 |

## Sequencing

Within EPIC-001, TASK-001 precedes TASK-002, and TASK-002 precedes TASK-003.
EPIC-002 depends on that foundation. EPIC-003 depends on the runner boundary.
EPIC-004 qualifies the complete public surface. EPIC-005 consumes the accepted
qualification evidence. EPIC-006 follows that completed sequence and does not
depend on Dispatch sync work. Within EPIC-006, TASK-018 precedes TASK-019,
TASK-019 precedes TASK-020, TASK-020 precedes TASK-021, and TASK-021 precedes
TASK-022. TASK-018 reserved EPIC-007, EPIC-008, and TASK-023 through
TASK-032 without reusing their identities. The historical Dispatch E20
handoff was fulfilled by the different, narrower E20-E22 sequence. EPIC-007
now proceeds in order from TASK-023 to TASK-027 against that implemented
provider. Each task's evidence and gate are owned by its adopted dossier.
EPIC-008 and its five tasks remain Deferred after EPIC-007; completion of
TASK-027 does not start them. Parallel work is allowed only where a dossier
states that contracts and evidence ownership do not overlap.
