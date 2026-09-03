"""Shared fixtures: load the plugin exactly the way the Hermes loader does.

The Hermes plugin modules live at the repository root and import
package-relatively, so they load correctly only under a parent namespace
package. The ``plugin`` fixture reproduces that import path for every test
layer. ``broken_catalog`` mutates the frozen catalog, points the registry at
the copy, and clears the caches as one atomic step so no test depends on the
caching call order. ``HermesCtxStub`` and ``make_fake_binary`` back the
runner trust tests with a bounded config double and deterministic fake
Agent Dispatch executables.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shlex
import sys
import types
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_MODULE = "hermes_plugins.agent_dispatch_plugin"


class HermesCtxStub:
    """Bounded Hermes plugin-context double exposing only get_config."""

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self._settings: dict[str, Any] = dict(settings or {})

    def get_config(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)


def make_fake_binary(
    directory: Path, version: str = "v0.1.6", body: str | None = None
) -> dict[str, Any]:
    """Build a trusted-looking fake Agent Dispatch executable with config.

    Returns the binary path, the trusted config file path, the matching
    lowercase SHA-256 digest, and the resolved five-setting plugin config.
    The default body answers the ``version --json`` probe; a custom body
    replaces the whole script for negative probes.
    """
    trusted = directory / "trusted"
    trusted.mkdir(parents=True, exist_ok=True)
    binary = trusted / "agent-dispatch"
    if body is None:
        payload = json.dumps({"name": "agent-dispatch", "version": version})
        body = f"#!/bin/sh\nprintf '%s' {shlex.quote(payload)}\n"
    binary.write_text(body, encoding="utf-8")
    binary.chmod(0o755)
    config_file = trusted / "agent-dispatch.json"
    config_file.write_text("{}\n", encoding="utf-8")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    config = {
        "binary_path": str(binary),
        "binary_sha256": digest,
        "config_path": str(config_file),
    }
    return {
        "binary": binary,
        "config_file": config_file,
        "digest": digest,
        "config": config,
    }


def load_plugin(module_name: str = PLUGIN_MODULE) -> types.ModuleType:
    """Import the plugin package the way the Hermes directory loader does."""
    if "hermes_plugins" not in sys.modules:
        ns = types.ModuleType("hermes_plugins")
        ns.__path__ = []
        ns.__package__ = "hermes_plugins"
        sys.modules["hermes_plugins"] = ns
    for name in [n for n in sys.modules if n == module_name or n.startswith(module_name + ".")]:
        del sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        module_name,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = module_name
    module.__path__ = [str(ROOT)]
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def plugin():
    return load_plugin()


@pytest.fixture
def pristine_registry(plugin):
    """Yield the registry module with cleared caches; clear again on teardown."""
    plugin.registry.load_catalog.cache_clear()
    plugin.registry.tool_specs.cache_clear()
    yield plugin.registry
    plugin.registry.load_catalog.cache_clear()
    plugin.registry.tool_specs.cache_clear()


@pytest.fixture
def broken_catalog(plugin, pristine_registry, tmp_path, monkeypatch):
    """Atomically install a mutated catalog copy for the registry under test.

    Returns a writer: call it with the mutation, then exercise the registry.
    The cache clear rides inside the writer so a snapshot read can never
    serve a stale catalog to the next assertion.
    """

    def install(mutate) -> Path:
        catalog: dict[str, Any] = json.loads(json.dumps(pristine_registry.load_catalog()))
        mutate(catalog)
        catalog_file = tmp_path / "catalog.json"
        catalog_file.write_text(json.dumps(catalog), encoding="utf-8")
        monkeypatch.setattr(pristine_registry, "CATALOG_PATH", catalog_file)
        pristine_registry.load_catalog.cache_clear()
        pristine_registry.tool_specs.cache_clear()
        return catalog_file

    return install


@pytest.fixture
def fresh_plugin_with_unreadable_schemas(monkeypatch):
    """Load a fresh plugin instance whose schemas cannot be read.

    Cache management rides in the fixture setup and teardown symmetrically
    with pristine_registry, so tests never touch lru_cache internals.
    """
    module = load_plugin(PLUGIN_MODULE + "_atomicity")
    module.registry.load_catalog.cache_clear()
    module.registry.tool_specs.cache_clear()
    monkeypatch.setattr(module.registry, "CONTRACTS_VERSION_DIR", ROOT / "contracts" / "nowhere")
    yield module
    module.registry.load_catalog.cache_clear()
    module.registry.tool_specs.cache_clear()


@pytest.fixture
def unconfigured_ctx():
    """A Hermes context whose plugin settings are entirely absent."""
    return HermesCtxStub()


@pytest.fixture
def fake_agent_dispatch(tmp_path):
    """A default in-range fake Agent Dispatch installation under tmp_path."""
    return make_fake_binary(tmp_path)
