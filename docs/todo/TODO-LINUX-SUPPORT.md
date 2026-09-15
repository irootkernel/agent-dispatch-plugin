# EPIC-006 Linux Support and Existing-Tool Parity

Status: Closed (EPIC-006 Completed)
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

Status: Completed. Close record: [TASK-018 close](#task-018-close).

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

Status: Completed. Close record: [TASK-019 close](#task-019-close).

Extend runner verification and process lifecycle for supported Linux
hosts while keeping one execution boundary. Do not treat a patched
platform string as real Linux execution, and do not add `shell=True`,
arbitrary PATH inheritance, or a second subprocess helper.

Evidence: Linux and Darwin runner tests covering grandchildren, timeout,
overflow, symlink paths, digest replacement, and unsafe configuration;
bounded errors with no raw output, traceback, or credential leakage.

### TASK-020: Add native schedule mapping and contract parity

Status: Completed. Close record: [TASK-020 close](#task-020-close).

Keep the public schedule input limited to approved route identity.
Validate native result shapes and unsupported-capability errors against
the versioned contract. Do not invoke launchd-only commands on Linux or
weaken validation to accommodate new platform outputs.

Evidence: manifest/registry/schema/descriptor inventory parity for both
native mappings; happy-path and wrong-platform/capability negatives for
each.

### TASK-021: Run real platform and existing-action qualification

Status: Completed. Close record: [TASK-021 close](#task-021-close).
Darwin arm64, linux/arm64 v0.1.7 (`e7f3375` / `vnic-doksuri`), and native
linux/amd64 v0.1.8 (`fa6f1cd` / `cursor`) are recorded. See also
[TASK-021 Darwin slice](#task-021-darwin-slice).

Exercise every public action branch through Hermes on real Darwin arm64,
Linux amd64, and Linux arm64 with synthetic Dispatch state and exact
trusted core artifacts. Do not substitute mocks or emulated platform
labels for a claimed architecture.

Evidence: each advertised action/platform combination linked to a real
transcript and artifact digest. Required missing environments keep the
epic Blocked.

### TASK-022: Close Linux operations and hand off to Dispatch

Status: Completed. Close record: [TASK-022 close](#task-022-close).

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

Recorded 2026-09-15 on a native linux/arm64 host (non-root, systemd as
PID 1). Identities and reproduction live in
[qualification-linux-arm64](../implementation-tips/qualification-linux-arm64.md).

- `make test-prepare`, 529 unit (0 skipped; the execute-only digest case
  ran), 28 integration, and Plugin Doctor e2e passed on Hermes >=0.20.5.
- The disposable compatibility matrix and installation lifecycle
  (`make test-qualify`) run against Agent Dispatch v0.1.7 linux-arm64
  SHA-256 `5493b1a13d28fa28eee850617be7c745d47898b87a7c3c4ea114f5c1cf2481c0`.
  Every advertised public action returned the frozen wrapper; doctor
  preserved findings at exit 3 (`watchman_unavailable`); schedule inspect
  selected systemd with `present=false`.
- This does not install, load, or repair a systemd user timer.

This arm64 host cannot itself supply every advertised environment:

- native Linux amd64 (recorded on a separate x86_64 host; see
  [TASK-021 close](#task-021-close));
- Agent Dispatch v0.1.6 linux-arm64 (artifact absent; not claimed);
- Darwin arm64 `make test-qualify` on the same candidate (wrong host;
  Darwin is recorded separately).

Those gaps do not erase the linux/arm64 v0.1.7 record above or prior
Darwin qualification.

## TASK-018 close

Recorded 2026-09-15. This section is the TASK-018 review record. It does
not close TASK-019 or TASK-020. Runner and native-schedule code that
landed in `5d8d8f5851700563627b55ad5269810daac182d9` remains those later
tasks' implementation, not this charter's completion.

### Reviewed contract amendment

Inspected living catalog `contracts/v0.1.0/catalog.json` (plugin version
0.1.1) against `docs/specs/PRD.md` and `docs/specs/contracts.md`:

- `compatibility.platforms` is `darwin/arm64`, `linux/amd64`, and
  `linux/arm64`. Darwin arm64 remains the qualified release host.
  linux/arm64 has a v0.1.7 TASK-021 record; linux/amd64 has a v0.1.8
  TASK-021 record. Remaining linux-arm64 older artifacts stay unverified
  and are not claimed.
- `product_version` is `0.1.0`. Schema URNs remain under
  `contracts/v0.1.0/`. The published v0.1.0 tag is unchanged.
- The public inventory is exactly the existing ten inspection tools.
  No tool was added or removed. Denied mutation vocabulary is unchanged.
- `native_schedule_platform` is true only on
  `agent_dispatch_schedule_inspect` / `inspect`. The model input remains
  `route_id`; `--platform` is not a schema property. The trusted host
  selects `launchd` on macOS and `systemd` on Linux.
- Agent Dispatch compatibility stays `>=0.1.6,<0.2.0` on every
  advertised platform. Linux does not raise that floor. Hermes stays
  `>=0.20.5`. Envelope identity stays `agent-dispatch.cli/v1`.
- The companion Agent Dispatch repository was not modified.

### Linux-capable core artifacts

Darwin qualification pins remain Agent Dispatch v0.1.6 and v0.1.7
darwin/arm64 as recorded in
[qualification-darwin-arm64.md](../implementation-tips/qualification-darwin-arm64.md).

linux/arm64 TASK-021 evidence already records Agent Dispatch **v0.1.7**
in [qualification-linux-arm64.md](../implementation-tips/qualification-linux-arm64.md).
Agent Dispatch **v0.1.8** from companion commit
`fcd75f1b231e4403c39f5c873bce25b10d95754a` remains the selected highest
compatible published core below 0.2.0 for remaining Linux claims. A later
compatible 0.1.x may replace it only through a later task that records
the new identity.

### Readiness

The [this-machine verification scope](#this-machine-verification-scope)
plus the Darwin `make test` run on 2026-09-15 are the TASK-018 readiness
record:

| Environment | Status |
|---|---|
| Darwin arm64 | Ready (qualified release host; `make test` passed here on 2026-09-15) |
| Native linux/arm64 | Recorded: hermetic suite and v0.1.7 `make test-qualify` on a non-root host with systemd as PID 1 |
| OrbStack linux/arm64 | Historical hermetic-only pass; not a substitute for the native record |
| Native linux/amd64 | Recorded: v0.1.8 `make test-qualify` on host `cursor` (plugin `fa6f1cd`) |
| Agent Dispatch v0.1.6 linux-arm64 | Missing |
| systemd user-timer install/load | Not in the recorded inspect (`present=false`) |

Missing mandatory capacity keeps TASK-021 In Progress. It does not block
this charter. TASK-019 and TASK-020 stay Planned.

### Program position and reserved identities

`docs/roadmap/README.md` now records G01 as the only active plugin
program slot, EPIC-006 as In Progress, TASK-018 as Completed, TASK-021
as the active task, and EPIC-007, EPIC-008, and TASK-023 through
TASK-032 as Planned register rows. Do not start those reserved identities
from this dossier.

## TASK-019 close

Recorded 2026-09-15. This section is the TASK-019 review record. It does
not close TASK-020 or TASK-021. Native-schedule mapping that already
landed in `5d8d8f5851700563627b55ad5269810daac182d9` remains TASK-020's
implementation. The linux/arm64 v0.1.7 Hermes matrix remains TASK-021's
partial record.

### Single execution boundary

Inspected `runner.py` against the TASK-019 constraints:

- Process creation stays in `runner.py` only: two `subprocess.Popen`
  sites (the version probe and the bounded inspection). Runtime modules
  `envelopes.py`, `registry.py`, `schemas.py`, `__init__.py`,
  `tools/__init__.py`, and `tools/inputs.py` create no process.
- Both sites set `shell=False`, `env=MINIMAL_ENVIRONMENT`
  (`PATH=/usr/bin:/bin:/usr/sbin:/sbin`, `TMPDIR=/tmp`),
  `cwd=NEUTRAL_CWD`, `close_fds=True`, and `start_new_session=True`.
  There is no second subprocess helper and no inherited Hermes, HOME,
  D-Bus, SSH-agent, or cloud-credential environment.
- `_host_platform()` reads this process (`sys.platform` and
  `platform.machine()`): `linux` plus `arm64`/`aarch64` or
  `amd64`/`x86_64` yields `linux/arm64` or `linux/amd64`; Darwin arm64
  is unchanged. A monkeypatched platform string is not Linux execution.

No runner behavior change was required. The `5d8d8f5` admission already
extended the gate; this task supplies the real-host proof.

### Runner evidence

Real-host tests in `tests/unit/test_runner.py` and
`tests/unit/test_execution.py` cover the dossier classes without
patching the platform string:

| Class | Proof |
|---|---|
| Real host | `test_real_host_platform_resolves_trust_without_monkeypatch` on this linux/arm64 process (no `sys.platform` patch). The tests added in this close are written to run on Darwin without a platform monkeypatch; they have not been executed on Darwin |
| Grandchildren | `test_term_to_force_kill_kills_the_whole_process_group`; `test_version_probe_timeout_kills_the_whole_process_tree` (these pre-existing classes also ran in the Darwin arm64 `make test` on 2026-09-15) |
| Timeout | `test_deadline_returns_timeout_and_discards_output` (partial output and seeded secret discarded) |
| Overflow | stdout, stderr, combined, and configured-ceiling `output_too_large` with captured bytes discarded |
| Symlink paths | binary, parent directory, and trusted config symlink each close as `binary_unavailable` without echoing the path or digest |
| Digest replacement | `test_digest_is_reverified_on_every_call` |
| Unsafe configuration | relative paths, directory-as-config, missing/non-executable files, invalid settings |
| Isolation | both Popen sites asserted at runtime; parent `AWS_SECRET_ACCESS_KEY`, `SSH_AUTH_SOCK`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`, and `HOME` never enter the child |
| Closed errors | timeout, overflow, malformed stdout, and trust failures carry no raw stdout, no plugin traceback, and no seeded secret |

The alias monkeypatch matrix remains mapping evidence only
(`aarch64`/`x86_64` names). Linux child environment extras are at most
`LC_CTYPE` from the interpreter; PATH stays the frozen allowlist.

### Host record

This close ran on the same native linux/arm64 non-root host recorded in
[this-machine verification scope](#this-machine-verification-scope).
After the close-record and assertion edits, `make test` on 2026-09-15
collected 535 unit (0 skipped; the execute-only digest case ran), 28
integration, and Plugin Doctor e2e, all passing. `make test-qualify` is
not this task. linux/amd64 hardware is absent and is not claimed.
Darwin class coverage for tests that already existed (grandchildren,
timeout, overflow, binary and parent symlink, digest replacement,
unsafe settings) is the Darwin arm64 `make test` on 2026-09-15. The 529
unit count in the this-machine section is native linux/arm64, not that
Darwin run. Tests added in this close are proven on this linux/arm64
process only.

### Program position

After this close, EPIC-006 stays In Progress. TASK-018 and TASK-019 are
Completed. The next sequenced task is TASK-020 (Planned). TASK-018 had
held TASK-021 In Progress with a partial linux/arm64 v0.1.7 record;
this close parks TASK-021 as Blocked on the remaining advertised
environments (linux/amd64, Agent Dispatch v0.1.6 linux-arm64, Darwin
candidate qualify) so X-025 stays one active task. That qualify record
is retained and is not this close. Starting TASK-020 occupies the G01
execution slot.

## TASK-020 close

Recorded 2026-09-16. This section is the TASK-020 review record. It does
not close TASK-021 and does not start TASK-022. Real systemd and launchd
inspect interiors through Hermes remain TASK-021 evidence.

### Mapping and public input

The living catalog already selected the native descriptor from the
trusted host (`native_schedule_platform` only on
`agent_dispatch_schedule_inspect` / `inspect`). Public input stays
`route_id`. `--platform` is not a schema property. Envelope command
identity stays `schedule inspect` for both mappings.

| Host | Argv platform | Proof |
|---|---|---|
| Darwin | `launchd` | `test_resolve_argv_schedule_selects_launchd_on_darwin` |
| Linux | `systemd` | `test_resolve_argv_schedule_selects_systemd_on_linux`; `test_linux_schedule_argv_never_selects_launchd` |
| Other | closed | `test_native_schedule_platform_rejects_unsupported_hosts` |

Wrong-platform negatives: model `platform` values `launchd` and
`systemd` reject as `invalid_argument` before the runner. Capability
negative: an unsupported `sys.platform` raises `ContractSourceError`
and never emits a platform token. Manifest/registry/schema/descriptor
parity is the existing `scripts/manifest_parity.py` and
`contracts/validate.py` gates.

The envelope `result` interior stays open. This close does not add a
systemd or launchd result schema and does not treat the linux/arm64
`present=false` inspect as TASK-020 completion.

### Documentation

The README no longer describes schedule inspection as launchd-only.
Requirements still name Darwin arm64 as the qualified operator host.

### Program position

After this close, EPIC-006 stays In Progress. TASK-018, TASK-019, and
TASK-020 are Completed. TASK-021 remains Blocked on linux/amd64, Agent
Dispatch v0.1.6 linux-arm64, and Darwin candidate qualify. There is no
In Progress task. Starting TASK-021 requires those environments; do not
start it from this close.

## TASK-021 Darwin slice

Recorded 2026-09-16. This is not TASK-021 completion.

### Darwin arm64 candidate qualify

`make test-qualify` passed on this Darwin arm64 host (4 passed:
v0.1.6 and v0.1.7 compatibility matrix plus installation lifecycle).
Hermes v0.21.0 (2026.8.31). Identities:
[qualification-darwin-arm64.md](../implementation-tips/qualification-darwin-arm64.md).

### Qualification fixture

`tests/qualification/conftest.py` now admits `linux/amd64` with Agent
Dispatch **v0.1.8** linux-amd64 SHA-256
`ac844117af9cb10d5e7a18b5294336283e03e44bd8ab3c59aa500d0ad4b6ce7d`
(`AGENT_DISPATCH_QUALIFY_BINARY_V018`). linux/arm64 stays on v0.1.7
(`AGENT_DISPATCH_QUALIFY_BINARY_V017`). GitHub releases v0.1.6 and
v0.1.7 published Darwin arm64 only, so v0.1.6 linux artifacts are not
claimed.

### Remaining for Linux hosts

| Host | Command |
|---|---|
| native linux/amd64 | Recorded 2026-09-16 on `cursor` against `fa6f1cd` (Hermes v0.21.3, AD v0.1.8). See [qualification-linux-amd64.md](../implementation-tips/qualification-linux-amd64.md). |
| linux/arm64 | Re-run on candidate `e7f3375` 2026-09-16 (`vnic-doksuri`, Hermes v0.21.2, AD v0.1.7). See [qualification-linux-arm64.md](../implementation-tips/qualification-linux-arm64.md). |

Native linux/amd64 evidence now exists. TASK-021 close is
[TASK-021 close](#task-021-close). Do not start TASK-022 from the Darwin
slice alone.


## TASK-021 close

Recorded 2026-09-16. This section closes TASK-021 after all three
advertised platforms have real-host qualification evidence.

### Platform records

| Platform | Artifact | Plugin source | Evidence |
|---|---|---|---|
| Darwin arm64 | Agent Dispatch v0.1.6 + v0.1.7 | Darwin candidate (2026-09-16) | [qualification-darwin-arm64.md](../implementation-tips/qualification-darwin-arm64.md) |
| linux/arm64 | Agent Dispatch v0.1.7 | `e7f3375` on `vnic-doksuri` | [qualification-linux-arm64.md](../implementation-tips/qualification-linux-arm64.md) |
| linux/amd64 | Agent Dispatch v0.1.8 | `fa6f1cd` on `cursor` | [qualification-linux-amd64.md](../implementation-tips/qualification-linux-amd64.md) |

### linux/amd64 host evidence

On native linux/amd64 host `cursor` (uid 1000, `uname` Linux x86_64):

- Hermes Agent v0.21.3 (2026.9.14) · upstream `f13a87e6`
- Agent Dispatch v0.1.8 linux-amd64 SHA-256
  `ac844117af9cb10d5e7a18b5294336283e03e44bd8ab3c59aa500d0ad4b6ce7d`
- `make test-qualify` exit 0 (2 passed: v0.1.8 compatibility matrix and
  installation lifecycle)

Translated amd64 and Darwin binaries are not claimed. Agent Dispatch
v0.1.6 / v0.1.7 linux-amd64 artifacts were not published and are not
claimed. linux/arm64 older artifacts beyond the recorded v0.1.7 slice
remain unverified and are not claimed.

### What this close does not start

TASK-022 (Linux ops / Dispatch E20 handoff) stays Planned. Do not start
EPIC-007 or EPIC-008 from this close.

## TASK-022 close

Recorded 2026-09-16. This section is the TASK-022 review record and the
EPIC-006 cold review. It does not tag v0.1.1, start EPIC-007, or edit
the companion repository.

### P-001..P-004

| Requirement | Evidence |
|---|---|
| P-001 Versioned Linux/platform contract | Living catalog platforms and host-selected schedule; TASK-018 close |
| P-002 Trusted runner on Linux with Darwin regression | TASK-019 close; Darwin `make test` 542 unit |
| P-003 Native schedule mapping and parity | TASK-020 close |
| P-004 Real platform/action qualify and install/rollback | TASK-021 close; Linux lifecycle runbooks below |

### Linux operations

Source-directory install, enable, disable, remove, upgrade, and rollback
on Linux: [install-lifecycle-linux.md](../ops/install-lifecycle-linux.md)
and [upgrade-rollback-linux.md](../ops/upgrade-rollback-linux.md).
Disabled-by-default and Darwin-only rollback `binary_unavailable` are
the existing `make test-qualify` transcripts, not new live-profile runs.

### Cold review

Reviewed the Linux candidate against the three advertised platforms and
this ops/handoff set:

- Ten inspection tools only; no sync or mutation tools.
- Public schedule input remains `route_id`.
- Qualify pins and digests match the recorded host tables.
- README still names published v0.1.0 as Darwin; living candidate
  documents Linux combinations without a tag.
- No unresolved mandatory acceptance condition.

Findings: none that block EPIC-006 close. TASK-022 does not publish a
release.

### Dispatch handoff

Exact versions and platforms:
[dispatch-e20-handoff.md](../implementation-tips/dispatch-e20-handoff.md).
Next global position: **Dispatch E20 / E20-T1**.

## Reserved identities

The intake program also defines EPIC-007 (sync inspection; TASK-023
through TASK-027; G09 after Dispatch E26) and EPIC-008 (constrained sync
management; TASK-028 through TASK-032; G10 after EPIC-007). Do not
allocate those identities to other work. TASK-018 placed them on the
roadmap register as Planned. Do not start them from this dossier.

## Handoff

TASK-022 is accepted. The next owner is Dispatch E20 / E20-T1. Stop
plugin feature work until Dispatch E26 is accepted. Update the global
program position before any subsequent plugin epic. See
[dispatch-e20-handoff.md](../implementation-tips/dispatch-e20-handoff.md).
