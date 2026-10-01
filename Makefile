PY_SOURCES := registry.py schemas.py envelopes.py runner.py __init__.py tools contracts/validate.py contracts/validate_v020.py scripts tests
# The typed runtime subset of PY_SOURCES: the static view checks every
# guarded runtime module and excludes the registration shim and the pytest
# tree (TESTING.md documents the same split).
MYPY_SOURCES := $(filter-out __init__.py tests,$(PY_SOURCES))

# Keep the separately prepared development environment intact: an automatic
# project sync would remove tools absent from the runtime-only uv.lock.
UV_RUN := uv run --frozen --no-sync

.PHONY: dev-sync dev-lock test test-prepare test-unit test-int test-e2e test-qualify

dev-sync:
	uv sync --locked
	uv pip sync --python .venv/bin/python --require-hashes requirements-dev.txt

dev-lock:
	uv pip compile --universal --python-version 3.11 --generate-hashes --output-file requirements-dev.txt requirements-dev.in

test:
	$(MAKE) test-prepare
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-e2e

test-prepare:
	$(UV_RUN) ruff format $(PY_SOURCES)
	$(UV_RUN) ruff check $(PY_SOURCES)
	$(UV_RUN) mypy $(MYPY_SOURCES)
	$(UV_RUN) python -m compileall -q $(PY_SOURCES)
	$(UV_RUN) contracts/validate.py
	$(UV_RUN) contracts/validate_v020.py
	$(UV_RUN) scripts/manifest_parity.py

test-unit:
	$(UV_RUN) pytest tests/unit

test-int:
	$(UV_RUN) pytest tests/integration

test-e2e:
	$(UV_RUN) pytest tests/e2e

# The real-artifact compatibility qualification (TASK-012): every public
# action through the real Hermes runtime (v0.20.5 or newer) and the
# host-selected pinned Agent Dispatch artifacts (Darwin arm64: v0.1.6 and
# v0.1.7 via AGENT_DISPATCH_QUALIFY_BINARY and
# AGENT_DISPATCH_QUALIFY_BINARY_V017; Linux arm64 and amd64: v0.1.8 via
# AGENT_DISPATCH_QUALIFY_BINARY_V018). Each host also requires its pinned
# v0.2.0 binary via AGENT_DISPATCH_QUALIFY_BINARY_V020 and a native user
# service manager. Not part of `make test`, which
# stays hermetic on the deterministic fake executable; this stage fails
# hard when the pinned prerequisites are absent (TESTING.md owns the
# contract).
test-qualify:
	$(UV_RUN) pytest tests/qualification
