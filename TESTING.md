# Testing

## Contract

This repository is enrolled in `aquarium-test-contract/v1`. The selected
profile uses the `make` profile: a single-language Python root where the
Makefile owns orchestration. The executable handlers in the Makefile are
authoritative; disagreement between this document and the Makefile is a
blocking contract defect.

## Canonical Commands

```bash
make dev-sync       # prepare .venv from the separately hash-locked development requirements
make dev-lock       # regenerate requirements-dev.txt after an intentional tool-pin change
make test           # aggregate: prepare, unit, integration, e2e in order, fail-fast
make test-prepare   # format, lint, type checking, byte-compilation, two contract gates, parity gate
make test-unit      # uv run --frozen --no-sync pytest tests/unit
make test-int       # uv run --frozen --no-sync pytest tests/integration
make test-e2e       # uv run --frozen --no-sync pytest tests/e2e
make test-qualify   # uv run --frozen --no-sync pytest tests/qualification (real pinned artifacts; see below)
```

Run `make dev-sync` before the checks. The runtime-only `pyproject.toml`
and `uv.lock` declare no third-party dependencies; the developer tools live
in `requirements-dev.in` and the hash-locked `requirements-dev.txt`.
`make dev-sync` prepares only this checkout's `.venv`. Test commands use
`uv run --frozen --no-sync` so the runtime-only lock does not remove those
tools. Hermes does not consume the development requirements files.

The aggregate calls each stage handler exactly once through recursive
`$(MAKE)` invocations and stays serial under parallel Make.

## Stage Mapping

- `test-prepare`: `ruff format` (meaning-preserving formatting) over the
  Python sources, `ruff check` (static analysis), `mypy` (type checking over
  the typed runtime subset, derived from the same source enumeration in the
  Makefile), `python -m compileall`
  (byte-compilation), then three deterministic offline gates:
  `contracts/validate.py` (frozen v0.1.0 contract oracle),
  `contracts/validate_v020.py` (approved v0.2.0 contract oracle), and
  `scripts/manifest_parity.py` (manifest/registry/inventory parity through
  the real registration path).
- `test-unit`: `tests/unit` — one logical unit per test module:
  the registry derivation from the active catalog (`test_registry.py`), the
  model-facing schema layer (`test_schemas.py`), the fail-closed handlers
  validated against the frozen wrapper and error schemas
  (`test_tools.py`), the derived input-validation layer cross-checked
  against the frozen schemas over the complete fixture corpus
  (`test_input_validation.py`), the status and doctor tools through the
  full boundary with pre-process rejection evidence
  (`test_tools_status_doctor.py`), the routes, schedule inspection, and
  config tools across every action branch with conditional-field,
  grammar, enum, and probe-placement negatives
  (`test_tools_routes_schedule_config.py`), the dispatch-family tools —
  dispatches, receipts, event show, quarantine, and notifications — with
  pagination, grammar, enum, and placement negatives plus the read-only
  denied-subcommand proof (`test_tools_dispatch_family.py`), the runner
  trust gate with
  deterministic fake Agent Dispatch executables (`test_runner.py`), including
  real-host platform resolution without monkeypatching `sys.platform` and
  the advertised-host alias matrix, the
  bounded process-group execution — argv, environment, deadline, stream
  limits, termination, no-retry, and the two `Popen` isolation sites —
  against behavior-scripted fakes
  (`test_execution.py`), and the closed output boundary — frozen-fixture
  envelope validation, carrier rules, diagnostic bounds, and seeded-secret
  redaction (`test_validation.py`), and the three sync result schemas,
  distinct status evidence, public identity exceptions, and secret-neighbor
  negatives (`test_sync_results.py`, `test_sync_tools.py`).
- `test-int`: `tests/integration` — cross-module cooperation: registering
  the plugin through the Hermes-style directory loader, a fresh-interpreter
  session registering the thirteen-tool inventory and completing one smoke
  inspection through the full boundary (`test_fresh_session_inventory.py`),
  and running the two repository gates as subprocesses.
- `test-e2e`: `tests/e2e` — the Hermes Plugin Doctor validates the plugin
  directory through its public CLI on a real Hermes installation (v0.20.5 or
  newer).

TASK-024 adds `test_sync_tools.py`: all thirteen names register, while a
trusted legacy binary exposes ten and an exact v0.2.0 artifact exposes
thirteen only with a valid group and fresh capability evidence. The tests
check each fixed argv, the capabilities config-flag exception, SHA denial,
and direct-dispatch failure after a cached visible state. TASK-026 native
Hermes qualification passed on Darwin arm64 and Linux arm64 for the
artifacts recorded in that historical gate. EPIC-007 acceptance uses those
two hosts; its whole-Epic validation completed after the ARM qualification. The Linux amd64
v0.2.0 gate belongs to deferred EPIC-009/TASK-033 and must pass before that
platform's support claim.

## Test Frameworks

| Language | Layer | Framework | Evidence | Runner command |
|---|---|---|---|---|
| Python | unit | pytest (canonical) | requirements-dev.in + requirements-dev.txt (pytest==9.0.2) | `uv run --frozen --no-sync pytest tests/unit` |
| Python | integration | pytest (canonical) | same | `uv run --frozen --no-sync pytest tests/integration` |
| Python | e2e | pytest (canonical) | same | `uv run --frozen --no-sync pytest tests/e2e` |
| Python | qualification | pytest (canonical) | same | `uv run --frozen --no-sync pytest tests/qualification` |

No framework waivers apply: every layer is newly established on pytest.

## Gaori Mapping

Gaori is not configured for this repository (no `.gaori/tester.yaml`).
When it is adopted, the mapping is: `make test-unit`, `make test-int`, and
`make test-e2e` each produce single-format pytest output (parser `pytest`);
`make test-prepare` and the aggregate produce mixed output (parser
`generic`).

## E2E Environment

- Artifact: this repository as a Hermes plugin directory (source-only).
- Public interface: `hermes plugins doctor <path> --ci`.
- Environment identity: the doctor itself runs the plugin under a temporary
  `HERMES_HOME` with outbound socket connects blocked; the test creates no
  resources, seeds nothing, and has no teardown beyond the doctor's own
  temporary directories.
- Prerequisite refusal: the test fails with the exact missing prerequisite
  when the Hermes CLI is absent from `PATH`; there is no skip path.
- Credentials: none.

## Qualification Environment

- Artifact identities: Hermes v0.20.5 or newer on `PATH` (the stage also
  locates the install's venv interpreter for the in-process dispatch
  driver) and the host-selected pinned Agent Dispatch artifacts: Darwin
  arm64 uses both v0.1.6 and v0.1.7 darwin/arm64 builds
  (`AGENT_DISPATCH_QUALIFY_BINARY` and `AGENT_DISPATCH_QUALIFY_BINARY_V017`);
  linux/arm64 uses the v0.1.8 linux-arm64 build
  (`AGENT_DISPATCH_QUALIFY_BINARY_V018`, SHA-256
  `3d06d4d35493ce51581bb8c61f4ffc3dfd700499863a492a337ab7fb762ddf8e`);
  linux/amd64 uses the v0.1.8
  linux-amd64 build (`AGENT_DISPATCH_QUALIFY_BINARY_V018`). Every host also
  requires its correctly stamped v0.2.0 binary at
  `AGENT_DISPATCH_QUALIFY_BINARY_V020`, built from reviewed source
  `ffc8715d030ed3978e2c34d700798815975917d9`. The v0.2.0 SHA-256 pins
  are Darwin arm64 `7f9e68f7033ed7750f1d6912d510f617d2a06fd58f5f18400b73d68280604508`,
  Linux amd64 `a749ad083c2028af3b0d500c95d448f5a90af80c5c6e9a70fe950b011393efb2`,
  and Linux arm64 `9ca8f030b7763f05c229c5792836ea86ad3f2a8cc97912e47dda8f8a687d2cec`.
  Each case
  verifies its pinned SHA-256 before its version probe. PATH is a fallback
  only when its binary matches that exact case; missing or mismatching
  prerequisites fail, never skip. Other hosts fail the platform
  prerequisite.
- Public interface: the qualification matrix seeds a disposable profile
  (temporary `HERMES_HOME`, temporary Agent Dispatch configuration and
  state, controlled fake downstream Hermes target) and dispatches every
  advertised action through the real Hermes runtime deterministically —
  no model, no peer network, no live Agent Dispatch state. The v0.2.0 cases
  verify 13 registered tools, 10/13 available definitions, disabled and
  enabled partial two-node status, and absent/loaded/drifted service
  inspection against the native user manager. The service check uses a
  unique synthetic group, cleans up its managed definition, and requires
  an active launchd GUI domain or systemd user manager. A native manager
  prerequisite failure does not count as a passing platform gate.
  Only `sync status` and `sync service inspect` receive the OS-derived
  account home and, when present on Linux, the UID-owned user runtime
  directory; ordinary actions and the probes keep the original fixed
  `PATH`/`TMPDIR` child environment.
- Prerequisite refusal: the stage fails with the exact missing
  prerequisite when the host platform (darwin/arm64, linux/amd64, or
  linux/arm64), Hermes version, pinned artifact, or native user manager is absent; there is no
  skip path.
- Credentials: none.

## Language Diagnostics

- Static analysis: `ruff check` (pinned `ruff==0.14.7`).
- Byte-compilation: `python -m compileall`.
- Runtime/race diagnostics: not applicable — Python has no native race
  detector; the runner uses threads only for bounded concurrent stream
  draining, which the execution tests exercise deterministically.
- `test-unit` addition: `test_security_negatives.py` — the consolidated
  deterministic security suite (TASK-011) walking every dossier negative
  class through the public handler boundary with a mechanically complete
  injection sweep over every catalog string binding.
- `test-qualify`: `tests/qualification` — the disposable action-level
  compatibility matrix (TASK-012/TASK-026): every advertised public action of
  the original ten tools and the three v0.2.0 sync reads dispatched through
  the real Hermes runtime (v0.20.5 or newer)
  (plugin discovery plus `model_tools.handle_function_call` over a
  disposable `HERMES_HOME`) invoking the host-selected pinned Agent Dispatch
  release artifacts against synthetic state seeded through Agent
  Dispatch's own commands; and the disposable installation lifecycle
  (TASK-015): disabled-by-default pinned installation, explicit plugin
  and toolset enablement and disablement as separate states, and complete
  removal with no registration or inventory residue, driven through the
  real Hermes CLI and a fresh-session runtime observer in one disposable
  profile. The stage is deliberately outside `make test`, which stays
  hermetic on the deterministic fake executable.
- Type checking: `mypy` (pinned `mypy==2.3.1` with the matching
  `types-jsonschema` and `types-pyyaml` stubs) over the runtime modules.
  The repository root is a hyphen-named Hermes plugin package, so the
  static view mirrors the degenerate top-level import path
  (`explicit_package_bases` in `pyproject.toml`); the root registration
  shim and the pytest tree remain under ruff and the executed suites.

## Legacy Waivers

None.

## First-release acceptance amendment

Both doctor variants must return the real validated findings envelope at
exit 3 when Watchman is unavailable in the fixed child environment. They
are successful diagnostic retrievals, not expected `contract_mismatch`
negatives. Unit fixtures cover exit 0, other exits, wrong command identity,
malformed output, and redaction. Every host-selected pinned artifact,
including v0.2.0, runs the complete matrix and lifecycle, including a
source rollback to pre-release commit
`0c4e70e384bc9891bc15820c4e0b6a42ba700d5a` and restoration of the candidate.
The lifecycle requires a full Git clone containing that commit; it preserves
profile settings and proves fresh-session registration after each swap.
Legacy Darwin artifacts pass the rollback smoke; Linux and v0.2.0 artifacts
remain unavailable under the old source until the candidate returns.
Archive installation itself is checked separately by Plugin
Doctor before release publication.
