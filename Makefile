PY_SOURCES := registry.py schemas.py envelopes.py runner.py __init__.py tools contracts/validate.py scripts tests
# The typed runtime subset of PY_SOURCES: the static view checks every
# guarded runtime module and excludes the registration shim and the pytest
# tree (TESTING.md documents the same split).
MYPY_SOURCES := $(filter-out __init__.py tests,$(PY_SOURCES))

.PHONY: test test-prepare test-unit test-int test-e2e test-qualify

test:
	$(MAKE) test-prepare
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-e2e

test-prepare:
	uv run ruff format $(PY_SOURCES)
	uv run ruff check $(PY_SOURCES)
	uv run mypy $(MYPY_SOURCES)
	uv run python -m compileall -q $(PY_SOURCES)
	uv run contracts/validate.py
	uv run scripts/manifest_parity.py

test-unit:
	uv run pytest tests/unit

test-int:
	uv run pytest tests/integration

test-e2e:
	uv run pytest tests/e2e

# The real-artifact compatibility qualification (TASK-012): every public
# action through the real Hermes runtime (v0.20.5 or newer) and the pinned
# Agent Dispatch v0.1.6 and v0.1.7 release artifacts, supplied through
# AGENT_DISPATCH_QUALIFY_BINARY and AGENT_DISPATCH_QUALIFY_BINARY_V017.
# Not part of `make test`, which
# stays hermetic on the deterministic fake executable; this stage fails
# hard when the pinned prerequisites are absent (TESTING.md owns the
# contract).
test-qualify:
	uv run pytest tests/qualification
