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


# A deterministic Agent Dispatch double. It answers the trust gate's
# `version --json` probe and then plays one scripted inspection behavior
# chosen by the trusted config file's "behavior" object, so every execution
# test stays offline and reproducible.
_FAKE_BINARY_TEMPLATE = """#!/usr/bin/env python3
import json
import os
import signal
import subprocess
import sys
import time

ARGS = sys.argv[1:]


def behavior():
    try:
        if ARGS[-2:-1] == ["--config"]:
            with open(ARGS[-1], encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                return loaded.get("behavior", {})
    except Exception:
        pass
    return {}


if ARGS[:1] == ["version"]:
    print(json.dumps({"name": "agent-dispatch", "version": "v{version}"}))
    raise SystemExit(0)

SPEC = behavior()
KIND = SPEC.get("kind", "echo")

# Every behavior counts its own invocation when asked, so no-retry proofs
# can span failure modes with one counter file.
if "count_file" in SPEC:
    with open(SPEC["count_file"], "a", encoding="utf-8") as handle:
        handle.write("invoked\\n")


def envelope(ok=True, result=None):
    args = list(ARGS)
    if args[-2:-1] == ["--config"]:
        args = args[:-2]
    if args[-2:] == ["--output", "json"]:
        args = args[:-2]
    words = [token for token in args if not token.startswith("-")]
    command = SPEC.get("command") or " ".join(words[:2])
    payload = {
        "api_version": "agent-dispatch.cli/v1",
        "command": command,
        "ok": ok,
        "result": result if result is not None else {},
        "warnings": [],
        "trace_id": "",
    }
    if not ok:
        payload.pop("result")
        payload["error"] = {
            "code": "config_invalid",
            "category": "configuration",
            "message": "scripted rejection",
            "retryable": False,
        }
    print(json.dumps(payload))


if KIND == "echo":
    envelope(result={
        "argv": list(sys.argv),
        "env": dict(os.environ),
        "cwd": os.getcwd(),
    })
elif KIND == "sleep":
    sys.stdout.write(SPEC.get("prefix", ""))
    sys.stdout.flush()
    time.sleep(float(SPEC.get("seconds", 30)))
elif KIND == "stdout_overflow":
    sys.stdout.write("x" * int(SPEC["bytes"]) + "\\n")
    sys.stdout.flush()
    time.sleep(30)
elif KIND == "stderr_overflow":
    sys.stderr.write("x" * int(SPEC["bytes"]) + "\\n")
    sys.stderr.flush()
    time.sleep(30)
elif KIND == "combined_overflow":
    sys.stdout.write("o" * int(SPEC["stdout_bytes"]))
    sys.stderr.write("e" * int(SPEC["stderr_bytes"]))
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(30)
elif KIND == "trap":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    child = subprocess.Popen(["/bin/sleep", "60"], start_new_session=False)
    with open(SPEC["child_pid_file"], "w", encoding="utf-8") as handle:
        handle.write(str(child.pid))
    sys.stdout.write("ignoring TERM\\n")
    sys.stdout.flush()
    time.sleep(60)
elif KIND == "reject":
    envelope(ok=False)
    raise SystemExit(int(SPEC.get("exit", 3)))
elif KIND == "garbage":
    sys.stdout.write("this is not json\\n")
    raise SystemExit(0)
elif KIND == "raw":
    for line in SPEC.get("stderr_lines", []):
        sys.stderr.write(line + "\\n")
    sys.stderr.flush()
    if "envelope" in SPEC:
        print(json.dumps(SPEC["envelope"]))
    else:
        sys.stdout.write(SPEC.get("stdout", "not json\\n"))
    raise SystemExit(int(SPEC.get("exit", 0)))
elif KIND == "flood_exit":
    # Flood past the stream ceiling and exit immediately, so the executor's
    # wait loop observes a clean exit before the overflow flag is read.
    sys.stdout.write("x" * int(SPEC["bytes"]))
    sys.stdout.flush()
    raise SystemExit(0)
else:
    envelope()
raise SystemExit(0)
"""


def make_fake_binary(
    directory: Path,
    version: str = "v0.1.6",
    body: str | None = None,
    behavior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a trusted-looking fake Agent Dispatch executable with config.

    Returns the binary path, the trusted config file path, the matching
    lowercase SHA-256 digest, and the resolved five-setting plugin config.
    The default script answers the ``version --json`` probe and plays the
    config-file ``behavior`` script for inspections; a custom body replaces
    the whole script for negative probes.
    """
    trusted = directory / "trusted"
    trusted.mkdir(parents=True, exist_ok=True)
    binary = trusted / "agent-dispatch"
    if body is None:
        body = _FAKE_BINARY_TEMPLATE.replace("{version}", version.lstrip("v"))
    binary.write_text(body, encoding="utf-8")
    binary.chmod(0o755)
    config_file = trusted / "agent-dispatch.json"
    config_file.write_text(
        json.dumps({"behavior": behavior} if behavior is not None else {}),
        encoding="utf-8",
    )
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


def valid_params_for_action(spec, action) -> dict[str, Any]:
    """The smallest schema-valid request that selects one action.

    Derived from the tool's frozen input schema: top-level required members
    plus the conditional members the ``allOf``/``if``/``then`` blocks require
    for this action value. Used by handler tests that need a request the
    derived validation layer will accept.
    """
    schema = spec.load_input_schema()
    params: dict[str, Any] = {name: "x" for name in schema.get("required", ()) if name != "action"}
    value = action.input_action_value
    if value is None:
        return params
    params["action"] = value
    for entry in schema.get("allOf", ()):
        condition = entry.get("if") or {}
        constraint = (condition.get("properties") or {}).get("action")
        if constraint is None:
            selects = True
        elif "const" in constraint:
            selects = constraint["const"] == value
        elif "enum" in constraint:
            selects = value in constraint["enum"]
        else:
            selects = True
        if selects and "action" in params:
            for name in (entry.get("then") or {}).get("required", ()):
                params[name] = "x"
    return params


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
