# EPIC-006 Linux Support and Existing-Tool Parity

Status: Adopted
Roadmap: EPIC-006 in docs/roadmap/README.md
Tasks: TASK-018, TASK-019, TASK-020, TASK-021, TASK-022
Depends on: EPIC-005 Completed; independent of Dispatch E20
Program position: G01 of `AD-WIKI-SYNC-PROGRAM/v1`
After completion: Dispatch E20 / E20-T1
Requirement coverage: P-001..P-004; X-021, X-025, X-028

## Provenance

Intake: `REQ-PLUGIN-WIKI-SYNC/v1` (sibling file
`../agent-dispatch-plugin.md` at admission). Inspected plugin baseline
`94d863e7a34ea682b3e347dc9d9ab629446e55e7` (`Open v0.1.1 development`).
Inspected companion core `fcd75f1b231e4403c39f5c873bce25b10d95754a`
(`v0.1.8`), which already publishes Linux amd64 and Linux arm64 artifacts.
This dossier admits only EPIC-006. It is not implementation evidence and
does not amend the frozen v0.1.0 PRD or catalog.

## Outcome

Make the existing ten-tool inspection plugin usable and correctly qualified
on Darwin arm64, Linux amd64, and Linux arm64 before any sync feature work.
Preserve Darwin behavior. Do not add tools, mutations, or a second execution
path.

## Delivery

- Admit a versioned Linux/platform contract amendment through existing
  change control, choose the next plugin release/contract baseline, and
  keep immutable v0.1.0 history.
- Extend the single trusted runner for supported Linux machine
  names/architectures: absolute non-symlink binary and config, digest,
  permissions, safe working directory, concurrent drain, timeout, and
  TERM/grace/KILL process-tree termination.
- Select the native schedule descriptor from trusted host capability:
  launchd on macOS, systemd on supported Linux. Public schedule input
  stays an approved route identity, not a free `--platform` flag.
- Qualify every existing public action on real advertised platforms
  through disposable Hermes profiles and pinned core artifacts. Mocking a
  platform name is not Linux support.
- Finish install/enable/disable/remove/upgrade/rollback guidance for the
  Linux candidate and hand Dispatch the exact qualified versions with
  next position E20-T1.

## Decisions to record

- Next plugin release and contract baseline; whether Linux uses a higher
  core capability floor than the retained Darwin range, stated and tested
  explicitly.
- Three-platform qualification matrix and actual Linux-capable core
  artifacts, including v0.1.8, qualified Hermes revisions, and retained
  Darwin combinations.
- Native schedule mapping derived from the trusted host/capability
  boundary, not a tool-supplied platform string.
- Minimal dependency resolution on Linux without arbitrary PATH or full
  ambient-environment inheritance.
- Readiness of real Darwin arm64, Linux amd64, and Linux arm64
  environments; missing mandatory capacity blocks the epic rather than
  completing it.

## Task order

TASK-018 precedes TASK-019, which precedes TASK-020, which precedes
TASK-021, which precedes TASK-022. Keep implementation, task-local tests,
review, and remediation inside the same active task.

### TASK-018: Admit the Linux amendment and program charter

Establish the first executable task and platform contract without a
circular dependency on future sync design. Reserve EPIC-007, EPIC-008,
and TASK-023 through TASK-032 on this roadmap so those identities are
not reused. Record G01 as the only active program position. Select
Linux-capable core artifacts including v0.1.8. Do not depend on Dispatch
sync schemas, widen core compatibility without evidence, or modify the
companion repository.

Evidence: reviewed contract amendment that identifies native schedule
behavior and the unchanged ten-tool security scope; a readiness record
that names real test environments or explicitly blocks missing capacity.

### TASK-019: Qualify the trusted runner on Linux

Extend runner verification and process lifecycle for supported Linux
hosts while keeping one execution boundary. Do not treat a patched
platform string as real Linux execution, and do not add `shell=True`,
arbitrary PATH inheritance, or a second subprocess helper.

Evidence: Linux and Darwin runner tests covering grandchildren, timeout,
overflow, symlink paths, digest replacement, and unsafe configuration;
bounded errors with no raw output, traceback, or credential leakage.

### TASK-020: Add native schedule mapping and contract parity

Keep the public schedule input limited to approved route identity.
Validate native result shapes and unsupported-capability errors against
the versioned contract. Do not invoke launchd-only commands on Linux or
weaken validation to accommodate new platform outputs.

Evidence: manifest/registry/schema/descriptor inventory parity for both
native mappings; happy-path and wrong-platform/capability negatives for
each.

### TASK-021: Run real platform and existing-action qualification

Exercise every public action branch through Hermes on real Darwin arm64,
Linux amd64, and Linux arm64 with synthetic Dispatch state and exact
trusted core artifacts. Do not substitute mocks or emulated platform
labels for a claimed architecture.

Evidence: each advertised action/platform combination linked to a real
transcript and artifact digest. Required missing environments keep the
epic Blocked.

### TASK-022: Close Linux operations and hand off to Dispatch

Finish source-directory lifecycle guidance, cold-review the immutable
Linux candidate, and set the next global position to Dispatch E20 /
E20-T1. Do not start sync inspection or management, activate production,
modify Hermes core, or publish a release merely because this task
completes.

Evidence: P-001..P-004 and existing repository gates pass within the
review budget; the handoff lists exact qualified versions/platforms; the
plugin remains a ten-tool inspection product.

## Acceptance

- Darwin arm64, Linux amd64, and Linux arm64 are supported through
  explicitly qualified combinations, with real environment identity for
  each advertised platform.
- Schedule inspection maps to launchd or systemd according to trusted
  native capability.
- The public inventory remains exactly the existing ten inspection tools.
- Secure installation, upgrade, and rollback evidence exists, and the
  Dispatch E20 handoff names the accepted revision and E20-T1.
- Required missing qualification environments leave the epic Blocked,
  not Completed.

## Non-goals

Sync tools, mutations, a peer listener, a Linux-specific shadow
execution path, starting EPIC-007 after this epic, editing the companion
Dispatch repository, publishing or activating a release, and treating a
mocked platform string as Linux support.

## This-machine verification scope

Recorded 2026-09-14 on this Darwin arm64 host:

- `make test` passed (prepare, 529 unit, 28 integration, Plugin Doctor e2e).
- OrbStack `linux/arm64` (`Linux aarch64`) ran the hermetic unit and
  integration suites: 556 passed, 1 skipped. The skip is
  `test_execute_only_binary_is_unreadable_for_the_digest` under uid 0
  (root can read mode 0111 files). Re-run that case as non-root on a
  real Linux arm64 host.
- Agent Dispatch `v0.1.8` linux-arm64 `version --json` ran in the same
  container and answered `{"name":"agent-dispatch","version":"v0.1.8"}`.
  `schedule inspect --help` documents `--platform launchd|systemd`.

This host cannot close advertised Linux qualification:

- real Hermes sessions on Linux arm64 (install Hermes on the OCI arm64
  machine and rerun Plugin Doctor plus the action matrix there);
- native Linux amd64 (no x86 host; OrbStack amd64 is translated
  `VirtualApple` and is not claimed);
- systemd user-schedule lifecycle (this Mac is launchd; typical
  containers have no systemd as PID 1).

Those gaps keep TASK-021 from completing. They do not block Darwin
regression evidence.

## Reserved identities

The intake program also defines EPIC-007 (sync inspection; TASK-023
through TASK-027; G09 after Dispatch E26) and EPIC-008 (constrained sync
management; TASK-028 through TASK-032; G10 after EPIC-007). Do not
allocate those identities to other work. TASK-018 places them on this
roadmap as Planned. Do not start them from this dossier.

## Handoff

When TASK-022 is accepted, the next owner is Dispatch E20 / E20-T1. Stop
plugin feature work until Dispatch E26 is accepted. Update the global
program position before any subsequent plugin epic.
