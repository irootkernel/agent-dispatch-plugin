PY_SOURCES := registry.py schemas.py envelopes.py runner.py __init__.py tools contracts/validate.py scripts tests
# The typed runtime subset of PY_SOURCES: the static view checks every
# guarded runtime module and excludes the registration shim and the pytest
# tree (TESTING.md documents the same split).
MYPY_SOURCES := $(filter-out __init__.py tests,$(PY_SOURCES))

.PHONY: test test-prepare test-unit test-int test-e2e

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
