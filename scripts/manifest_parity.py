#!/usr/bin/env python3
"""Generate and verify plugin.yaml from the frozen contract source.

ADR-001: plugin.yaml is a derived view. Run with --write to regenerate it
from contracts/v0.1.0/catalog.json after an approved contract change; run
without arguments to verify manifest, registry, registration, and expected
inventory parity for exactly the ten declared tools.

    uv run scripts/manifest_parity.py           # verify (exit 1 on mismatch)
    uv run scripts/manifest_parity.py --write   # regenerate plugin.yaml

Verification loads the plugin package exactly the way Hermes loads a
directory plugin (spec_from_file_location with the repo root as the package
path) and drives register(ctx) against a recording context, so the parity
statement covers the real registration path, not a reimplementation.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "plugin.yaml"
MODULE_NAME = "hermes_plugins.agent_dispatch_plugin"


def load_plugin_module() -> types.ModuleType:
    """Import the plugin package the way the Hermes loader does."""
    if "hermes_plugins" not in sys.modules:
        ns = types.ModuleType("hermes_plugins")
        ns.__path__ = []
        ns.__package__ = "hermes_plugins"
        sys.modules["hermes_plugins"] = ns
    for name in [n for n in sys.modules if n == MODULE_NAME or n.startswith(MODULE_NAME + ".")]:
        del sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        MODULE_NAME,
        REPO_ROOT / "__init__.py",
        submodule_search_locations=[str(REPO_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = MODULE_NAME
    module.__path__ = [str(REPO_ROOT)]
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


class RecordingContext:
    """Minimal stand-in for the Hermes registration context."""

    def __init__(self) -> None:
        self.registered: dict[str, dict] = {}

    def register_tool(self, **kwargs) -> None:
        name = kwargs["name"]
        if name in self.registered:
            raise SystemExit(f"parity error: {name} registered twice")
        self.registered[name] = kwargs


def build_manifest(catalog: dict) -> dict:
    plugin = catalog["plugin"]
    manifest = {
        "name": plugin["name"],
        "version": plugin["version"],
        "kind": plugin["kind"],
        "manifest_version": plugin["manifest_version"],
        "api_version": plugin["api_version"],
        "platforms": plugin["platforms"],
        "description": plugin["description"],
        "author": plugin["author"],
        "license": plugin["license"],
        "homepage": plugin["homepage"],
        "tags": plugin["tags"],
        "provides_tools": [tool["name"] for tool in catalog["tools"]],
        "config_schema": plugin["config_schema"],
    }
    return manifest


def main() -> int:
    module = load_plugin_module()
    catalog = json.loads(
        module.registry.CATALOG_PATH.read_text(encoding="utf-8")
    )
    expected_manifest = build_manifest(catalog)

    if "--write" in sys.argv[1:]:
        MANIFEST_PATH.write_text(
            yaml.safe_dump(expected_manifest, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print("plugin.yaml regenerated from the frozen catalog")
        return 0

    errors: list[str] = []
    if not MANIFEST_PATH.is_file():
        print("plugin.yaml is missing; run with --write to generate it")
        return 1
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        manifest = {}
        errors.append("plugin.yaml is empty or not a mapping")
    elif manifest != expected_manifest:
        errors.append("plugin.yaml does not equal the catalog-derived manifest")

    ctx = RecordingContext()
    module.register(ctx)

    inventory = list(module.registry.expected_inventory())
    provides = manifest.get("provides_tools", [])
    registered = list(ctx.registered)
    roster = [tool["name"] for tool in catalog["tools"]]

    if not (len(roster) == 10 and len(set(roster)) == 10):
        errors.append(f"catalog roster is not exactly ten unique tools: {roster}")
    if inventory != roster:
        errors.append(f"registry inventory != catalog roster: {inventory}")
    if provides != roster:
        errors.append(f"manifest provides_tools != catalog roster: {provides}")
    if sorted(registered) != sorted(roster):
        errors.append(f"registered tools != catalog roster: {registered}")

    for name, kwargs in ctx.registered.items():
        if kwargs.get("toolset") != module.registry.toolset():
            errors.append(f"{name}: wrong toolset {kwargs.get('toolset')!r}")
        if kwargs.get("override"):
            errors.append(f"{name}: override=True is forbidden")
        schema = kwargs.get("schema")
        if not isinstance(schema, dict) or schema.get("additionalProperties") is not False:
            errors.append(f"{name}: registered schema is not a closed object schema")
        if not callable(kwargs.get("handler")) or not callable(kwargs.get("check_fn")):
            errors.append(f"{name}: handler or check_fn missing")

    if errors:
        print(f"manifest/registry parity FAILED with {len(errors)} error(s):")
        for message in errors:
            print(f"  - {message}")
        return 1
    print(
        "manifest/registry parity passed: catalog, plugin.yaml, registration, "
        "and expected inventory agree on exactly ten tools"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
