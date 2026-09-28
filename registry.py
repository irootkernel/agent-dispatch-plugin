"""Declarative tool registry derived from the active versioned contract.

The catalog at contracts/v0.2.0/catalog.json is the active handwritten
authority (ADR-001). This module is its derived in-memory view: it parses the
catalog once and exposes the tool roster, per-action command mappings, and
the expected inventory that plugin.yaml and parity checks are generated from.
It performs no I/O beyond reading the contract files and never touches the
network, a database, or Agent Dispatch state.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping


def native_schedule_platform() -> str:
    """Select the fixed schedule inspector for this trusted host.

    The model never supplies ``--platform``. Darwin uses launchd; Linux uses
    systemd. Unsupported hosts never reach argv resolution: the runner trust
    gate rejects them first.
    """
    if sys.platform == "darwin":
        return "launchd"
    if sys.platform.startswith("linux"):
        return "systemd"
    raise ContractSourceError("no native schedule mapping for this host")


PLUGIN_ROOT = Path(__file__).resolve().parent
CONTRACTS_VERSION_DIR = PLUGIN_ROOT / "contracts" / "v0.2.0"
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
    native_schedule_platform_flag: bool = False
    trusted_value_bindings: tuple[Mapping[str, str], ...] = ()
    append_trusted_config: bool = True

    @property
    def requires_sync_attestation(self) -> bool:
        return self.expected_command.startswith("sync ")

    def resolve_argv(
        self, params: Mapping[str, Any], trusted_settings: Mapping[str, str] | None = None
    ) -> tuple[str, ...]:
        """Resolve the concrete argv for this action from validated params.

        The versioned contract oracle in contracts/validate_v020.py checks
        the trusted binding semantics and command fixtures.
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
        for binding in self.trusted_value_bindings:
            setting = binding["setting"]
            if trusted_settings is None or setting not in trusted_settings:
                raise ValueError(f"missing trusted {setting} setting")
            argv.extend([binding["flag"], trusted_settings[setting]])
        for flag in self.optional_flags:
            if params.get(flag["param"]) is True:
                argv.extend(flag["tokens"])
        if self.native_schedule_platform_flag:
            argv.extend(["--platform", native_schedule_platform()])
        argv.extend(self.argv_suffix)
        return tuple(argv)


@dataclass(frozen=True)
class ToolSpec:
    """One declared inspection tool and its fixed command surface."""

    name: str
    description: str
    input_schema_relative_path: str
    actions: tuple[ActionSpec, ...]
    # The schema parsed and validated once by tool_specs(); register() serves
    # this copy so no second filesystem read can interleave with registration.
    validated_input_schema: dict[str, Any] | None = field(default=None, compare=False, repr=False)

    @property
    def input_schema_path(self) -> Path:
        return CONTRACTS_VERSION_DIR / self.input_schema_relative_path

    def load_input_schema(self) -> dict[str, Any]:
        if self.validated_input_schema is not None:
            return self.validated_input_schema
        try:
            with self.input_schema_path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractSourceError(f"{self.name}: input schema unavailable: {exc}") from exc


@lru_cache(maxsize=1)
def load_catalog() -> Mapping[str, Any]:
    """Parse the active catalog exactly once per process."""
    try:
        with CATALOG_PATH.open(encoding="utf-8") as handle:
            catalog = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractSourceError(
            f"active contract source unavailable: {CATALOG_PATH.name}: {exc}"
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
        for field_name in ("name", "description", "input_schema", "actions"):
            if field_name not in tool:
                raise ContractSourceError(f"catalog tool entry missing {field_name!r}")
        for field_name in ("name", "description", "input_schema"):
            if not isinstance(tool[field_name], str) or not tool[field_name]:
                raise ContractSourceError(f"catalog tool {field_name!r} must be a non-empty string")
        if not isinstance(tool["actions"], list) or not tool["actions"]:
            raise ContractSourceError(f"{tool['name']}: actions must be a non-empty list")
        actions: list[ActionSpec] = []
        for action in tool["actions"]:
            if not isinstance(action, Mapping):
                raise ContractSourceError("catalog action entries must be objects")
            for field_name in ("id", "argv_prefix", "argv_suffix", "expected_command"):
                if field_name not in action:
                    raise ContractSourceError(
                        f"catalog action entry for {tool['name']} missing {field_name!r}"
                    )
            for field_name in ("id", "expected_command"):
                if not isinstance(action[field_name], str) or not action[field_name]:
                    raise ContractSourceError(
                        f"{tool['name']}/{action['id']}: {field_name!r} must be a non-empty string"
                    )
            for field_name in ("argv_prefix", "argv_suffix"):
                if not isinstance(action[field_name], list) or not all(
                    isinstance(token, str) for token in action[field_name]
                ):
                    raise ContractSourceError(
                        f"{tool['name']}/{action['id']}: {field_name} must be a string array"
                    )
            for binding in action.get("value_bindings", ()):
                if not isinstance(binding, Mapping) or not isinstance(binding.get("param"), str):
                    raise ContractSourceError(
                        f"{tool['name']}/{action['id']}: value bindings must be "
                        "mappings with a string param"
                    )
                if not binding.get("positional") and not isinstance(binding.get("flag"), str):
                    raise ContractSourceError(
                        f"{tool['name']}/{action['id']}: non-positional bindings "
                        "must declare a string flag"
                    )
            for flag in action.get("optional_flags", ()):
                if (
                    not isinstance(flag, Mapping)
                    or not isinstance(flag.get("param"), str)
                    or not isinstance(flag.get("tokens"), list)
                    or not all(isinstance(token, str) for token in flag["tokens"])
                ):
                    raise ContractSourceError(
                        f"{tool['name']}/{action['id']}: optional flags must be "
                        "mappings with a string param and a string-array tokens"
                    )
            native_flag = action.get("native_schedule_platform", False)
            if native_flag is not True and native_flag is not False:
                raise ContractSourceError(
                    f"{tool['name']}/{action['id']}: native_schedule_platform must be a boolean"
                )
            trusted_bindings = action.get("trusted_value_bindings", [])
            if not isinstance(trusted_bindings, list) or any(
                not isinstance(binding, Mapping)
                or binding.get("setting") != "sync_group_id"
                or binding.get("flag") != "--group"
                for binding in trusted_bindings
            ):
                raise ContractSourceError(f"{tool['name']}/{action['id']}: invalid trusted binding")
            append_config = action.get("append_trusted_config", True)
            if not isinstance(append_config, bool):
                raise ContractSourceError(f"{tool['name']}/{action['id']}: invalid config rule")
            actions.append(
                ActionSpec(
                    action_id=action["id"],
                    input_action_value=action.get("input_action_value"),
                    argv_prefix=tuple(action["argv_prefix"]),
                    value_bindings=tuple(action.get("value_bindings", ())),
                    optional_flags=tuple(action.get("optional_flags", ())),
                    argv_suffix=tuple(action["argv_suffix"]),
                    expected_command=action["expected_command"],
                    native_schedule_platform_flag=bool(native_flag),
                    trusted_value_bindings=tuple(trusted_bindings),
                    append_trusted_config=append_config,
                )
            )
        sync_named = tool["name"].startswith("agent_dispatch_sync_")
        if any(action.requires_sync_attestation != sync_named for action in actions):
            raise ContractSourceError(f"{tool['name']}: sync name and command disagree")
        if any(action.trusted_value_bindings and not sync_named for action in actions):
            raise ContractSourceError(f"{tool['name']}: trusted group requires sync attestation")
        if any(
            not action.append_trusted_config and action.expected_command != "sync capabilities"
            for action in actions
        ):
            raise ContractSourceError(f"{tool['name']}: invalid config omission")
        specs.append(
            ToolSpec(
                name=tool["name"],
                description=tool["description"],
                input_schema_relative_path=tool["input_schema"],
                actions=tuple(actions),
            )
        )
    names = [spec.name for spec in specs]
    if len(names) != 13 or len(set(names)) != len(names):
        raise ContractSourceError("the active roster must contain exactly thirteen unique tools")
    validated: list[ToolSpec] = []
    for spec in specs:  # fail before registration on any unreadable schema
        schema = spec.load_input_schema()
        if not isinstance(schema, dict):
            raise ContractSourceError(f"{spec.name}: input schema file is not a JSON object")
        object.__setattr__(spec, "validated_input_schema", schema)
        validated.append(spec)
    return tuple(validated)


def expected_inventory() -> tuple[str, ...]:
    """The canonical expected tool inventory, in catalog order."""
    return tuple(spec.name for spec in tool_specs())


def toolset() -> str:
    return TOOLSET
