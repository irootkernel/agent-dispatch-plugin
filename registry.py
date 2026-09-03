"""Declarative tool registry derived from the frozen contract source.

The catalog at contracts/v0.1.0/catalog.json is the single handwritten
authority (ADR-001). This module is its derived in-memory view: it parses the
catalog once and exposes the tool roster, per-action command mappings, and
the expected inventory that plugin.yaml and parity checks are generated from.
It performs no I/O beyond reading the contract files and never touches the
network, a database, or Agent Dispatch state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

PLUGIN_ROOT = Path(__file__).resolve().parent
CONTRACTS_VERSION_DIR = PLUGIN_ROOT / "contracts" / "v0.1.0"
CATALOG_PATH = CONTRACTS_VERSION_DIR / "catalog.json"
TOOLSET = "agent_dispatch"


class ContractSourceError(RuntimeError):
    """The frozen contract source is missing or malformed.

    Registration must fail loudly rather than guess a partial roster; this
    error is raised before any tool is registered and never carries
    sensitive content.
    """


@dataclass(frozen=True)
class ActionSpec:
    """One fixed action-to-command mapping for a tool."""

    action_id: str
    input_action_value: str | None
    argv_prefix: tuple[str, ...]
    value_bindings: tuple[Mapping[str, Any], ...]
    optional_flags: tuple[Mapping[str, Any], ...]
    argv_suffix: tuple[str, ...]
    expected_command: str

    def resolve_argv(self, params: Mapping[str, Any]) -> tuple[str, ...]:
        """Resolve the concrete argv for this action from validated params.

        Bindings whose parameter is absent are skipped; the caller is
        responsible for having validated params against the tool's input
        schema first, which is what makes absence equal optionality.
        """
        argv: list[str] = list(self.argv_prefix)
        for binding in self.value_bindings:
            param = binding["param"]
            if param not in params:
                continue
            if binding.get("positional"):
                argv.append(str(params[param]))
            else:
                argv.extend([binding["flag"], str(params[param])])
        for flag in self.optional_flags:
            if params.get(flag["param"]) is True:
                argv.extend(flag["tokens"])
        argv.extend(self.argv_suffix)
        return tuple(argv)


@dataclass(frozen=True)
class ToolSpec:
    """One declared inspection tool and its fixed command surface."""

    name: str
    description: str
    input_schema_relative_path: str
    actions: tuple[ActionSpec, ...]

    @property
    def input_schema_path(self) -> Path:
        return CONTRACTS_VERSION_DIR / self.input_schema_relative_path

    def load_input_schema(self) -> dict[str, Any]:
        try:
            with self.input_schema_path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractSourceError(
                f"{self.name}: input schema unavailable: {exc}"
            ) from exc


@lru_cache(maxsize=1)
def load_catalog() -> Mapping[str, Any]:
    """Parse the frozen catalog exactly once per process."""
    try:
        with CATALOG_PATH.open(encoding="utf-8") as handle:
            catalog = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractSourceError(
            f"frozen contract source unavailable: {CATALOG_PATH.name}: {exc}"
        ) from exc
    if catalog.get("schema_version") != "agent-dispatch-plugin.contracts/v1":
        raise ContractSourceError("unsupported contract source schema version")
    if catalog.get("toolset") != TOOLSET:
        raise ContractSourceError("catalog toolset mismatch")
    return catalog


@lru_cache(maxsize=1)
def tool_specs() -> tuple[ToolSpec, ...]:
    """Return every declared tool spec in frozen catalog order.

    Performs the complete structural validation — catalog shape, every
    action mapping, and every input schema file — before returning, so
    registration either proceeds with the full roster or fails with
    ContractSourceError before any tool is registered.
    """
    catalog = load_catalog()
    tools = catalog.get("tools")
    if not isinstance(tools, list) or not tools:
        raise ContractSourceError("catalog tools must be a non-empty list")
    specs: list[ToolSpec] = []
    for tool in tools:
        if not isinstance(tool, Mapping):
            raise ContractSourceError("catalog tool entries must be objects")
        for field in ("name", "description", "input_schema", "actions"):
            if field not in tool:
                raise ContractSourceError(f"catalog tool entry missing {field!r}")
        actions: list[ActionSpec] = []
        for action in tool["actions"]:
            if not isinstance(action, Mapping):
                raise ContractSourceError("catalog action entries must be objects")
            for field in ("id", "argv_prefix", "argv_suffix", "expected_command"):
                if field not in action:
                    raise ContractSourceError(
                        f"catalog action entry for {tool['name']} missing {field!r}"
                    )
            for field in ("argv_prefix", "argv_suffix"):
                if not isinstance(action[field], list) or not all(
                    isinstance(token, str) for token in action[field]
                ):
                    raise ContractSourceError(
                        f"{tool['name']}/{action['id']}: {field} must be a string array"
                    )
            actions.append(
                ActionSpec(
                    action_id=action["id"],
                    input_action_value=action.get("input_action_value"),
                    argv_prefix=tuple(action["argv_prefix"]),
                    value_bindings=tuple(action.get("value_bindings", ())),
                    optional_flags=tuple(action.get("optional_flags", ())),
                    argv_suffix=tuple(action["argv_suffix"]),
                    expected_command=action["expected_command"],
                )
            )
        specs.append(
            ToolSpec(
                name=tool["name"],
                description=tool["description"],
                input_schema_relative_path=tool["input_schema"],
                actions=tuple(actions),
            )
        )
    names = [spec.name for spec in specs]
    if len(names) != 10 or len(set(names)) != len(names):
        raise ContractSourceError(
            "the frozen roster must contain exactly ten unique tools"
        )
    for spec in specs:  # fail before registration on any unreadable schema
        schema = spec.load_input_schema()
        if not isinstance(schema, dict):
            raise ContractSourceError(
                f"{spec.name}: input schema file is not a JSON object"
            )
    return tuple(specs)


def expected_inventory() -> tuple[str, ...]:
    """The canonical expected tool inventory, in catalog order."""
    return tuple(spec.name for spec in tool_specs())


def toolset() -> str:
    return TOOLSET
