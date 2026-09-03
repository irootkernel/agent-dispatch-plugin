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
make test-prepare   # format, lint, byte-compilation, contracts gate, parity gate
make test-unit      # uv run pytest tests/unit
make test-int       # uv run pytest tests/integration
make test-e2e       # uv run pytest tests/e2e
```

The aggregate calls each stage handler exactly once through recursive
`$(MAKE)` invocations and stays serial under parallel Make.

## Stage Mapping

- `test-prepare`: `ruff format` (meaning-preserving formatting) over the
  Python sources, `ruff check` (static analysis), `python -m compileall`
  (byte-compilation), then the two deterministic offline gates:
  `contracts/validate.py` (frozen contract oracle) and
  `scripts/manifest_parity.py` (manifest/registry/inventory parity through
  the real registration path).
- `test-unit`: `tests/unit` — one logical unit per test module:
  the registry derivation from the frozen catalog (`test_registry.py`), the
  model-facing schema layer (`test_schemas.py`), and the fail-closed
  skeleton handlers validated against the frozen wrapper and error schemas
  (`test_tools.py`).
- `test-int`: `tests/integration` — cross-module cooperation: registering
  the plugin through the Hermes-style directory loader, and running the two
  repository gates as subprocesses.
- `test-e2e`: `tests/e2e` — the Hermes Plugin Doctor validates the plugin
  directory through its public CLI on a real Hermes v0.20.5 installation.

## Test Frameworks

| Language | Layer | Framework | Evidence | Runner command |
|---|---|---|---|---|
| Python | unit | pytest (canonical) | pyproject.toml + uv.lock (pytest==9.0.2) | `uv run pytest tests/unit` |
| Python | integration | pytest (canonical) | same | `uv run pytest tests/integration` |
| Python | e2e | pytest (canonical) | same | `uv run pytest tests/e2e` |

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

## Language Diagnostics

- Static analysis: `ruff check` (pinned `ruff==0.14.7`).
- Byte-compilation: `python -m compileall`.
- Runtime/race diagnostics: not applicable — Python has no native race
  detector; concurrency diagnostics are not warranted for this
  registration-inert skeleton (no threads, no subprocesses in the plugin).
- Type checking: no type checker is established yet; the runner work in
  EPIC-002 will select one when typed execution code exists.

## Legacy Waivers

None.
