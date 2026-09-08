#!/usr/bin/env python3
"""Generate and verify plugin.yaml from the frozen contract source.

ADR-001: plugin.yaml is a derived view. Run with --write to regenerate it
from contracts/v0.1.0/catalog.json after an approved contract change; run
without arguments to verify manifest, registry, registration, expected
inventory, and command-vocabulary parity for exactly the ten declared
tools.

    uv run scripts/manifest_parity.py           # verify (exit 1 on mismatch)
    uv run scripts/manifest_parity.py --write   # regenerate plugin.yaml

Verification loads the plugin package exactly the way Hermes loads a
directory plugin (spec_from_file_location with the repo root as the package
path) and drives register(ctx) against a recording context, so the parity
statement covers the real registration path, not a reimplementation.
"""

from __future__ import annotations

import importlib.util
import sys
import types
import tomllib
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
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot build the plugin module spec for the parity run")
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


def command_vocabulary_errors(catalog: dict) -> list[str]:
    """Every action template token must stay inside the frozen vocabulary.

    The registration path derives each action's argv from the catalog, so
    the parity statement covers the command allowlist too: each action's
    expected_command resolves inside command_vocabulary.allowed and no
    template token — prefix, flag, optional flag, or suffix — appears in
    the denied subcommand list. Bound values are grammar-validated request
    content, not template tokens, and are outside this structural check.
    """
    vocabulary = catalog.get("command_vocabulary") or {}
    allowed = vocabulary.get("allowed") or {}
    denied = set(vocabulary.get("denied_subcommands") or ())
    errors: list[str] = []
    for tool in catalog["tools"]:
        for action in tool["actions"]:
            where = f"{tool['name']}/{action['id']}"
            argv = list(action["argv_prefix"])
            argv += [
                binding["flag"]
                for binding in action.get("value_bindings", ())
                if not binding.get("positional")
            ]
            argv += [token for flag in action.get("optional_flags", ()) for token in flag["tokens"]]
            argv += list(action["argv_suffix"])
            leaked = sorted(token for token in argv if token in denied)
            if leaked:
                errors.append(f"{where}: argv template carries denied subcommands {leaked}")
            expected = action["expected_command"]
            # The executed argv starts from argv_prefix, so parity covers the
            # command execution actually builds, not just the declared label:
            # the prefix must be exactly the expected command's tokens (a
            # merged single token like "route show" fails), and the label
            # must resolve inside the vocabulary — a two-word command inside
            # its head's subcommand list, a single-word command only where
            # the vocabulary makes it a whole command rather than a bare
            # head that requires a subcommand.
            prefix = list(action["argv_prefix"])
            if prefix != expected.split(" "):
                errors.append(
                    f"{where}: argv_prefix {prefix!r} does not equal expected_command {expected!r}"
                )
            if " " in expected:
                head, sub = expected.split(" ", 1)
                if head not in allowed or sub not in allowed.get(head, []):
                    errors.append(
                        f"{where}: expected_command {expected!r} is outside the allowed vocabulary"
                    )
            elif allowed.get(expected) != [expected]:
                errors.append(
                    f"{where}: expected_command {expected!r} is outside the allowed vocabulary"
                )
    return errors


def main() -> int:
    try:
        module = load_plugin_module()
        catalog = module.registry.load_catalog()
    except Exception as exc:  # a malformed contract source must fail boundedly
        print(f"parity error: the frozen contract source is unreadable: {exc}")
        return 1
    if not isinstance(catalog.get("plugin"), dict):
        print("parity error: the frozen catalog has no plugin block")
        return 1
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
    try:
        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"parity error: plugin.yaml is not parseable YAML: {exc}")
        return 1
    if not isinstance(manifest, dict):
        manifest = {}
        errors.append("plugin.yaml is empty or not a mapping")
    elif manifest != expected_manifest:
        errors.append("plugin.yaml does not equal the catalog-derived manifest")

    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text())
    version = catalog["plugin"]["version"]
    if project["project"]["version"] != version:
        errors.append("Python project version does not match catalog plugin.version")
    package = [p for p in lock["package"] if p["name"] == catalog["plugin"]["name"]]
    if len(package) != 1 or package[0]["version"] != version:
        errors.append("lockfile project version does not match catalog plugin.version")

    ctx = RecordingContext()
    try:
        module.register(ctx)
    except module.registry.ContractSourceError as exc:
        print(f"parity error: registration rejected the frozen contract source: {exc}")
        return 1

    inventory = list(module.registry.expected_inventory())
    provides = manifest.get("provides_tools", [])
    registered = list(ctx.registered)
    roster = [tool["name"] for tool in catalog["tools"]]
    schema_files = sorted(
        path.name[: -len(".input.json")]
        for path in (REPO_ROOT / "contracts" / "v0.1.0" / "schemas" / "tools").glob("*.input.json")
    )

    if not (len(roster) == 10 and len(set(roster)) == 10):
        errors.append(f"catalog roster is not exactly ten unique tools: {roster}")
    if inventory != roster:
        errors.append(f"registry inventory != catalog roster: {inventory}")
    if provides != roster:
        errors.append(f"manifest provides_tools != catalog roster: {provides}")
    if sorted(registered) != sorted(roster):
        errors.append(f"registered tools != catalog roster: {registered}")
    if schema_files != sorted(roster):
        errors.append(f"tool schema files != catalog roster: {schema_files}")

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

    errors.extend(command_vocabulary_errors(catalog))

    if errors:
        print(f"manifest/registry parity FAILED with {len(errors)} error(s):")
        for message in errors:
            print(f"  - {message}")
        return 1
    print(
        "manifest/registry parity passed: catalog, plugin.yaml, registration, "
        "expected inventory, and the command vocabulary agree on exactly ten tools"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
