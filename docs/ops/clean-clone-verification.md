# Clean-Clone Verification Runbook: CI, Plugin Doctor, and Tool Inventory

Target: the `agent-dispatch-plugin` v0.1.0 complete deterministic gate set
from a fresh clone of an exact revision.
Environment: Darwin arm64 host; Hermes v0.20.5 on `PATH` for the Plugin
Doctor e2e stage; `uv` resolving the pinned `uv.lock`. No credentials, no
network beyond the package cache, and no repository-local state are
involved.

## Exact identities

| Component | Identity |
|---|---|
| Hermes (e2e only) | v0.20.5 (build 2026.8.19), on `PATH` |
| Python | any `uv`-provided CPython satisfying `requires-python >=3.11` |
| Test framework | pytest 9.0.2 with the dev group pinned in `uv.lock` |
| Host | darwin/arm64 |

## Recorded defect and remediation (found by this stage)

The deterministic suite originally passed only when the repository
directory name was **not** a valid Python identifier (for example the
hyphenated working name `agent-dispatch-plugin`). pytest 9's
`resolve_package_path` stops at the first package directory whose name is
not an identifier; with a hyphenated root it fell back to importing the
plugin's `__init__.py` as a plain module, which put the repository root on
`sys.path` and made the guarded modules' degenerate top-level imports
(`import registry`) resolve by accident. Cloning into any
identifier-named directory (for example `clone`) instead made pytest
collect the root as a package, the repository root never reached
`sys.path`, and all 508 unit tests errored with
`ModuleNotFoundError: No module named 'registry'`.

The remediation pins the repository root explicitly for pytest
(`pythonpath = ["."]` in `pyproject.toml`), so every clone location
imports identically. The recorded transcript below is reproduced from an
identifier-named clean clone.

## Reproduction

```bash
# 1. Clone the exact revision under review into any directory name.
git clone <repository-source> <any-directory>
cd <any-directory>
git checkout <exact-revision>

# 2. Resolve the pinned environment and run the complete gate set.
uv sync
make test
```

`make test` runs, in order and fail-fast: `test-prepare` (ruff format,
ruff check, mypy, byte-compilation, the frozen contract oracle
`contracts/validate.py`, and the manifest/registry parity gate
`scripts/manifest_parity.py`), `test-unit` (508 deterministic unit
tests), `test-int` (28 integration tests, including the fresh-session
tool inventory), and `test-e2e` (`hermes plugins doctor <root> --ci` over
a temporary `HERMES_HOME` with outbound sockets blocked).

## Clean-environment transcript

Recorded from a clean local clone of the release-candidate revision into
an identifier-named directory (proving the remediated import path):

| Stage | Result |
|---|---|
| `uv sync` | environment resolved from `uv.lock`, exit 0 |
| `test-prepare` | ruff format unchanged; ruff, mypy (8 files), compileall clean; contracts oracle and manifest/registry parity passed |
| `test-unit` | 508 passed |
| `test-int` | 28 passed |
| `test-e2e` | Plugin Doctor: `OK: runtime discovery, manifest parsing, import, and registration passed`, `10 tool(s), 0 hook(s)` |

The fresh-session inventory transcript (from the integration stage) is
the single-line JSON the fresh interpreter prints after registering the
plugin through the Hermes directory loader: exactly the ten catalog tools
in catalog order, followed by one smoke inspection
(`agent_dispatch_status` → `status`) returning the frozen wrapper with
`smoke_ok: true`.

## Success verification

`make test` exits 0 from a clone under any directory name at the exact
revision, the Plugin Doctor reports ten tools and zero hooks, and the
fresh-session inventory registers exactly the ten frozen tools in catalog
order with the smoke inspection succeeding.
