# Testing

## Contract

This repository is enrolled in `aquarium-test-contract/v1`. The selected
profile uses the `make` profile: a single-language Python root where the
Makefile owns orchestration. The executable handlers in the Makefile are
authoritative; disagreement between this document and the Makefile is a
blocking contract defect.

## Canonical Commands

```bash
make test           # aggregate: prepare, unit, integration, e2e in order, fail-fast
make test-prepare   # format, lint, type checking, byte-compilation, contracts gate, parity gate
make test-unit      # uv run pytest tests/unit
make test-int       # uv run pytest tests/integration
make test-e2e       # uv run pytest tests/e2e
make test-qualify   # uv run pytest tests/qualification (real pinned artifacts; see below)
```

The aggregate calls each stage handler exactly once through recursive
`$(MAKE)` invocations and stays serial under parallel Make.

## Stage Mapping

- `test-prepare`: `ruff format` (meaning-preserving formatting) over the
  Python sources, `ruff check` (static analysis), `mypy` (type checking over
  the typed runtime subset, derived from the same source enumeration in the
  Makefile), `python -m compileall`
  (byte-compilation), then the two deterministic offline gates:
  `contracts/validate.py` (frozen contract oracle) and
  `scripts/manifest_parity.py` (manifest/registry/inventory parity through
  the real registration path).
- `test-unit`: `tests/unit` — one logical unit per test module:
  the registry derivation from the frozen catalog (`test_registry.py`), the
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
  deterministic fake Agent Dispatch executables (`test_runner.py`), the
  bounded process-group execution — argv, environment, deadline, stream
  limits, termination, and no-retry — against behavior-scripted fakes
  (`test_execution.py`), and the closed output boundary — frozen-fixture
  envelope validation, carrier rules, diagnostic bounds, and seeded-secret
  redaction (`test_validation.py`).
- `test-int`: `tests/integration` — cross-module cooperation: registering
  the plugin through the Hermes-style directory loader, a fresh-interpreter
  session registering the ten-tool inventory and completing one smoke
  inspection through the full boundary (`test_fresh_session_inventory.py`),
  and running the two repository gates as subprocesses.
- `test-e2e`: `tests/e2e` — the Hermes Plugin Doctor validates the plugin
  directory through its public CLI on a real Hermes installation (v0.20.5 or
  newer).

## Test Frameworks

| Language | Layer | Framework | Evidence | Runner command |
|---|---|---|---|---|
| Python | unit | pytest (canonical) | pyproject.toml + uv.lock (pytest==9.0.2) | `uv run pytest tests/unit` |
| Python | integration | pytest (canonical) | same | `uv run pytest tests/integration` |
| Python | e2e | pytest (canonical) | same | `uv run pytest tests/e2e` |
| Python | qualification | pytest (canonical) | same | `uv run pytest tests/qualification` |

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
  driver) and the pinned Agent Dispatch v0.1.6 darwin/arm64 release
  artifact, supplied through `AGENT_DISPATCH_QUALIFY_BINARY` or found on
  `PATH` and verified byte-exactly against the pinned SHA-256 before
  anything runs.
- Public interface: the qualification matrix seeds a disposable profile
  (temporary `HERMES_HOME`, temporary Agent Dispatch configuration and
  state, controlled fake downstream Hermes target) and dispatches every
  advertised action through the real Hermes runtime deterministically —
  no model, no network, no live state.
- Prerequisite refusal: the stage fails with the exact missing
  prerequisite when the host platform, Hermes version, or pinned
  artifact is absent; there is no skip path.
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
  compatibility matrix (TASK-012): every advertised public action of all
  ten tools dispatched through the real Hermes runtime (v0.20.5 or newer)
  (plugin discovery plus `model_tools.handle_function_call` over a
  disposable `HERMES_HOME`) invoking the real pinned Agent Dispatch
  v0.1.6 release artifact against synthetic state seeded through Agent
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
