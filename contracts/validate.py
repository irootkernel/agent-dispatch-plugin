#!/usr/bin/env python3
"""Deterministic offline validation of the frozen v0.1.0 contract source.

Validates contracts/v0.1.0 against the invariants frozen in docs/specs/PRD.md
(the oracle below), the JSON Schema metaschema, and the fixture catalog.
Requires only the pinned jsonschema toolchain; run:

    uv run --with jsonschema==4.26.0 --with referencing==0.37.0 contracts/validate.py

Exit status 0 means every check passed. The script never starts a process,
opens a database, or contacts the network. The oracle constants below are
part of the frozen surface: a canonical amendment must update them together
with the catalog and schemas.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent
VERSION_DIR = ROOT / "v0.1.0"

# Oracle: invariants frozen by docs/specs/PRD.md. The catalog is the artifact;
# this validator asserts artifact == oracle.
PRD_TOOLS = [
    "agent_dispatch_status",
    "agent_dispatch_doctor",
    "agent_dispatch_routes",
    "agent_dispatch_dispatches",
    "agent_dispatch_receipts",
    "agent_dispatch_event_show",
    "agent_dispatch_quarantine",
    "agent_dispatch_notifications",
    "agent_dispatch_schedule_inspect",
    "agent_dispatch_config",
]
PRD_ERROR_CODES = [
    "binary_unavailable",
    "unsupported_agent_dispatch_version",
    "invalid_argument",
    "timeout",
    "output_too_large",
    "malformed_json",
    "contract_mismatch",
    "adapter_usage_error",
    "execution_failed",
    "redaction_failure",
]
PRD_LIMITS = {
    "timeout_default": 30,
    "timeout_min": 1,
    "timeout_max": 300,
    "stdout_max_bytes": 1048576,
    "stderr_max_bytes": 65536,
    "combined_max_bytes": 1048576,
    "grace_period_seconds": 2,
}
PRD_PAGINATION = {"limit_min": 1, "limit_max": 100, "limit_default": 25}
PRD_COMPATIBILITY = {
    "agent_dispatch": ">=0.1.6,<0.2.0",
    "agent_dispatch_envelope": "agent-dispatch.cli/v1",
    "hermes": "0.20.5",
    "platform": "darwin/arm64",
}
PRD_WRAPPER_VERSION = "agent-dispatch-plugin.result/v1"

ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def load_json(path: Path):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)}: unreadable or invalid JSON: {exc}")
        return None


def resolve_argv(action: dict, instance: dict) -> list[str]:
    """Resolve an action's argv against an instance.

    A binding whose parameter is absent from the instance is skipped: the
    instance has already validated against the tool schema, so absence means
    the parameter is optional for that action.
    """
    argv: list[str] = list(action["argv_prefix"])
    for binding in action.get("value_bindings", ()):
        param = binding["param"]
        if param not in instance:
            continue
        if binding.get("positional"):
            argv.append(str(instance[param]))
        else:
            argv.extend([binding["flag"], str(instance[param])])
    for flag in action.get("optional_flags", ()):
        if instance.get(flag["param"]) is True:
            argv.extend(flag["tokens"])
    argv.extend(action["argv_suffix"])
    return argv


def check_catalog(catalog: dict) -> None:
    if catalog.get("schema_version") != "agent-dispatch-plugin.contracts/v1":
        fail("catalog: schema_version must be agent-dispatch-plugin.contracts/v1")
    if catalog.get("product_version") != "0.1.0":
        fail("catalog: product_version must be 0.1.0")
    if catalog.get("toolset") != "agent_dispatch":
        fail("catalog: toolset must be agent_dispatch")

    names = [tool["name"] for tool in catalog["tools"]]
    if names != PRD_TOOLS:
        fail(f"catalog: tool roster/order mismatch: {names}")
    if len(set(names)) != 10:
        fail("catalog: tool names must be unique and exactly ten")

    allowed = catalog["command_vocabulary"]["allowed"]
    denied = set(catalog["command_vocabulary"]["denied_subcommands"])
    forbidden_props = set(catalog["forbidden_input_properties"])
    identifier_pattern = catalog["identifier_grammar"]["pattern"]
    state_pattern = catalog["state_token_grammar"]["pattern"]
    state_max = catalog["state_token_grammar"]["max_length"]
    closed_enums = catalog["closed_enums"]
    offset_tools = {
        f"agent_dispatch_{name.split()[0]}"
        for name in catalog["pagination"]["offset"]["applies_to"]
    }

    for tool in catalog["tools"]:
        tool_name = tool["name"]
        schema_path = VERSION_DIR / tool["input_schema"]
        if not schema_path.is_file():
            fail(f"{tool_name}: missing input schema file {tool['input_schema']}")
            continue
        schema = load_json(schema_path)
        if schema is None:
            continue
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is not False:
            fail(f"{tool_name}: input schema must set additionalProperties false")
        overlap = forbidden_props & set(props)
        if overlap:
            fail(f"{tool_name}: schema declares forbidden properties {sorted(overlap)}")
        if ("offset" in props) != (tool_name in offset_tools):
            fail(
                f"{tool_name}: offset presence must match pagination.offset.applies_to "
                f"({sorted(offset_tools)})"
            )
        short = tool_name.removeprefix("agent_dispatch_")
        action_enum_key = f"{short}.action"
        if action_enum_key in closed_enums:
            declared = props.get("action", {}).get("enum")
            if declared != closed_enums[action_enum_key]:
                fail(
                    f"{tool_name}: action enum mismatch with catalog closed_enums.{action_enum_key}"
                )
        for prop, spec in props.items():
            if prop in catalog["identifier_grammar"]["applies_to"]:
                if spec.get("pattern") != identifier_pattern:
                    fail(f"{tool_name}.{prop}: identifier pattern mismatch")
                if spec.get("maxLength") != catalog["identifier_grammar"]["max_length"]:
                    fail(f"{tool_name}.{prop}: identifier maxLength mismatch")
            if prop == "state" and "enum" not in spec:
                if spec.get("pattern") != state_pattern:
                    fail(f"{tool_name}.{prop}: state token pattern mismatch")
                if spec.get("maxLength") != state_max:
                    fail(f"{tool_name}.{prop}: state token maxLength mismatch")
            enum_key = f"{short}.{prop}"
            if "enum" in spec:
                if enum_key not in closed_enums:
                    fail(
                        f"{tool_name}.{prop}: schema enum is not registered in catalog closed_enums"
                    )
                elif spec.get("enum") != closed_enums[enum_key]:
                    fail(f"{tool_name}.{prop}: enum mismatch with catalog closed_enums.{enum_key}")
            if "pattern" in spec and prop not in (
                set(catalog["identifier_grammar"]["applies_to"]) | {"state"}
            ):
                fail(f"{tool_name}.{prop}: schema pattern is not registered in a catalog grammar")
            if spec.get("type") == "integer" and prop == "limit":
                if spec.get("minimum") != PRD_PAGINATION["limit_min"]:
                    fail(f"{tool_name}.{prop}: limit minimum mismatch")
                if spec.get("maximum") != PRD_PAGINATION["limit_max"]:
                    fail(f"{tool_name}.{prop}: limit maximum mismatch")
                if spec.get("default") != PRD_PAGINATION["limit_default"]:
                    fail(f"{tool_name}.{prop}: limit default mismatch")
            if spec.get("type") == "integer" and prop == "offset":
                if spec.get("minimum") != 0:
                    fail(f"{tool_name}.{prop}: offset minimum mismatch")
                if spec.get("maximum") != catalog["pagination"]["offset"]["max"]:
                    fail(f"{tool_name}.{prop}: offset maximum mismatch")

        actions = tool["actions"]
        if not actions:
            fail(f"{tool_name}: at least one action is required")
        for action in actions:
            expected = action["expected_command"]
            parts = expected.split(" ")
            command, subcommand = parts[0], (parts[1] if len(parts) > 1 else None)
            if command not in allowed:
                fail(f"{tool_name}: command '{command}' is outside the allowed vocabulary")
            if subcommand is not None:
                if subcommand not in allowed[command]:
                    fail(f"{tool_name}: subcommand '{subcommand}' not allowed for '{command}'")
                if subcommand in denied:
                    fail(f"{tool_name}: denied subcommand '{subcommand}' reached")

        # every schema property must be consumed by some action binding
        bound_params: set[str] = set()
        for action in actions:
            bound_params.update(b["param"] for b in action.get("value_bindings", ()))
            bound_params.update(f["param"] for f in action.get("optional_flags", ()))
        if any("input_action_value" in a for a in actions):
            bound_params.add("action")
        unbound = set(props) - bound_params
        if unbound:
            fail(f"{tool_name}: schema properties not bound by any action: {sorted(unbound)}")

    flat_denied_hits: list[str] = []
    for tool in catalog["tools"]:
        for action in tool["actions"]:
            argv = resolve_argv(action, {})
            flat_denied_hits.extend(
                f"{tool['name']}/{action['id']}:{token}" for token in argv if token in denied
            )
    if flat_denied_hits:
        fail(f"catalog: denied subcommand tokens present in fixed argv: {flat_denied_hits}")

    if catalog["errors"]["codes"] != PRD_ERROR_CODES:
        fail("catalog: error codes must equal the closed PRD set in order")
    if catalog["errors"]["retryable"] is not False:
        fail("catalog: plugin errors must declare retryable false")
    if catalog["errors"]["message_max_length"] != 512:
        fail("catalog: error message bound must be 512")

    limits = catalog["limits"]
    if limits["timeout_seconds"] != {
        "default": PRD_LIMITS["timeout_default"],
        "min": PRD_LIMITS["timeout_min"],
        "max": PRD_LIMITS["timeout_max"],
    }:
        fail("catalog: timeout limits mismatch")
    if limits["stdout_max_bytes"] != PRD_LIMITS["stdout_max_bytes"]:
        fail("catalog: stdout ceiling mismatch")
    if limits["stderr_max_bytes"] != PRD_LIMITS["stderr_max_bytes"]:
        fail("catalog: stderr ceiling mismatch")
    if limits["combined_max_bytes"] != PRD_LIMITS["combined_max_bytes"]:
        fail("catalog: combined ceiling mismatch")
    if limits["termination"]["grace_period_seconds"] != PRD_LIMITS["grace_period_seconds"]:
        fail("catalog: termination grace period mismatch")

    compatibility = catalog["compatibility"]
    for key, expected in PRD_COMPATIBILITY.items():
        if compatibility.get(key) != expected:
            fail(f"catalog: compatibility.{key} mismatch")

    # one guarded read of every tool schema shared by both reverse checks
    tool_schemas: dict[str, dict | None] = {}
    for tool in catalog["tools"]:
        tool_schemas[tool["name"]] = load_json(VERSION_DIR / tool["input_schema"])
    if any(loaded is None for loaded in tool_schemas.values()):
        return  # the load failures are already recorded

    schema_enums: dict[str, list] = {}
    schema_properties: dict[str, set[str]] = {}
    for tool in catalog["tools"]:
        schema = tool_schemas[tool["name"]]
        assert schema is not None
        short = tool["name"].removeprefix("agent_dispatch_")
        schema_properties[tool["name"]] = set(schema.get("properties", {}))
        for prop, spec in schema.get("properties", {}).items():
            if "enum" in spec:
                schema_enums.setdefault(f"{short}.{prop}", []).append(spec["enum"])
    for enum_key, declared in catalog["closed_enums"].items():
        holders = schema_enums.get(enum_key)
        if not holders:
            fail(f"catalog closed_enums.{enum_key} matches no schema property enum")
        elif len(holders) != 1 or holders[0] != declared:
            fail(f"catalog closed_enums.{enum_key} does not match exactly one schema enum")
    all_properties: set[str] = set().union(*schema_properties.values())
    for registered in catalog["identifier_grammar"]["applies_to"]:
        if registered not in all_properties:
            fail(f"catalog grammar applies_to name {registered!r} matches no schema property")

    if catalog["wrapper"]["schema_version"] != PRD_WRAPPER_VERSION:
        fail("catalog: wrapper schema_version mismatch")
    if catalog["envelope"]["api_version"] != "agent-dispatch.cli/v1":
        fail("catalog: envelope api_version mismatch")
    if catalog["envelope"]["open_domain_member"] != "result":
        fail("catalog: envelope open domain member must be result")
    if len(catalog["redaction_rules"]) != 5:
        fail("catalog: exactly five redaction rules are frozen")


def build_registry() -> tuple[Registry, dict[str, dict]]:
    registry = Registry()
    schemas: dict[str, dict] = {}
    for schema_file in sorted((VERSION_DIR / "schemas").rglob("*.json")):
        schema = load_json(schema_file)
        if schema is None:
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001 - report any metaschema failure
            fail(f"{schema_file.relative_to(ROOT)}: invalid JSON Schema: {exc}")
            continue
        schema_id = schema.get("$id")
        if schema_id:
            registry = registry.with_resource(schema_id, Resource.from_contents(schema))
            schemas[schema_id] = schema
    return registry, schemas


def check_closed_boundaries(schemas: dict[str, dict], catalog: dict | None) -> None:
    if catalog is None:
        return  # the load failure is already recorded
    for subject in ("envelope", "wrapper", "error"):
        schema_id = f"urn:agent-dispatch-plugin:contracts:v0.1.0:{subject}"
        schema = schemas.get(schema_id)
        if schema is None:
            fail(f"schema: missing required schema {subject}")
            continue
        if schema.get("additionalProperties") is not False:
            fail(f"schema: {subject} must be a closed boundary")
        if subject == "envelope":
            error_member = schema["properties"]["error"]
            if error_member.get("additionalProperties") is not False:
                fail("schema: envelope.error must be a closed boundary")
        if subject == "wrapper":
            props = schema.get("properties", {})
            if set(props) != set(catalog["wrapper"]["members"]):
                fail(f"schema: wrapper member set mismatch: {sorted(props)}")
            required = set(schema.get("required", []))
            core = {"schema_version", "ok", "operation", "exit_code", "diagnostics"}
            if required != core:
                fail(f"schema: wrapper required members must be exactly {sorted(core)}")
            operation_enum = props.get("operation", {}).get("enum")
            if operation_enum != PRD_TOOLS:
                fail("schema: wrapper operation enum must equal the PRD tool roster in order")
            if "agent_dispatch" not in props or "error" not in props:
                fail("schema: wrapper must declare both the envelope and plugin error carriers")
            if not schema.get("allOf"):
                fail("schema: wrapper must declare its carrier rules")
            diagnostics = props.get("diagnostics", {})
            bounds = catalog["diagnostics_bounds"]
            if diagnostics.get("maxItems") != bounds["max_items"]:
                fail("schema: wrapper diagnostics maxItems mismatch with catalog bounds")
            items = diagnostics.get("items", {})
            if items.get("maxLength") != bounds["max_length_per_item"]:
                fail("schema: wrapper diagnostics item bound mismatch with catalog bounds")
        if subject == "error":
            code_enum = schema.get("properties", {}).get("code", {}).get("enum")
            if code_enum != PRD_ERROR_CODES:
                fail("schema: error code enum must equal the closed PRD set in order")
            message_bound = schema.get("properties", {}).get("message", {}).get("maxLength")
            if message_bound != catalog["errors"]["message_max_length"]:
                fail("schema: error message bound mismatch with catalog")


def check_fixtures(registry: Registry, catalog: dict) -> None:
    index_path = VERSION_DIR / "fixtures" / "catalog.json"
    index = load_json(index_path)
    if index is None:
        return
    if index.get("schema_version") != "agent-dispatch-plugin.fixtures/v1":
        fail("fixtures: index schema_version mismatch")

    validators: dict[str, Draft202012Validator] = {}
    seen_files: set[Path] = set()
    case_ids: set[str] = set()

    for subject in index["subjects"]:
        schema_path = VERSION_DIR / subject["schema"]
        cases_path = VERSION_DIR / subject["cases"]
        schema = load_json(schema_path)
        cases_doc = load_json(cases_path)
        if schema is None or cases_doc is None:
            continue
        seen_files.add(cases_path)
        schema_id = schema.get("$id", str(schema_path))
        validator = validators.get(schema_id)
        if validator is None:
            validator = Draft202012Validator(schema, registry=registry)
            validators[schema_id] = validator

        cases = cases_doc.get("cases")
        if not isinstance(cases, list):
            fail(f"fixtures: {subject['subject']} cases document has no cases array")
            continue
        valid_count = sum(1 for c in cases if c["expect"] == "valid")
        invalid_count = sum(1 for c in cases if c["expect"] == "invalid")
        if valid_count < 1 or invalid_count < 1:
            fail(f"fixtures: {subject['subject']} needs at least one valid and one invalid case")

        for case in cases:
            case_id = case["id"]
            if case_id in case_ids:
                fail(f"fixtures: duplicate case id {case_id}")
            case_ids.add(case_id)
            errors = list(validator.iter_errors(case["instance"]))
            is_valid = not errors
            if case["expect"] == "valid" and not is_valid:
                fail(f"fixtures: {case_id} expected valid but failed: {errors[0].message}")
            if case["expect"] == "invalid" and is_valid:
                fail(f"fixtures: {case_id} expected invalid but validated")

    orphan_files = {
        p.relative_to(VERSION_DIR)
        for p in (VERSION_DIR / "fixtures").rglob("*.json")
        if p != index_path and p not in seen_files
    }
    if orphan_files:
        fail(f"fixtures: case files missing from the index: {sorted(orphan_files)}")

    # argv resolution: every action resolves to a concrete, well-formed argv.
    for tool in catalog["tools"]:
        tool_cases = VERSION_DIR / "fixtures" / "tools" / f"{tool['name']}.cases.json"
        cases_doc = load_json(tool_cases)
        if cases_doc is None:
            continue
        tool_case_list = cases_doc.get("cases")
        if not isinstance(tool_case_list, list):
            fail(f"argv: {tool['name']} fixture cases document has no cases array")
            continue
        for action in tool["actions"]:
            wanted = action.get("input_action_value")
            candidates = [
                c["instance"]
                for c in tool_case_list
                if c["expect"] == "valid"
                and (wanted is None or c["instance"].get("action") == wanted)
            ]
            if not candidates:
                fail(f"argv: {tool['name']}/{action['id']} has no valid fixture to resolve against")
                continue
            argv = resolve_argv(action, candidates[0])
            if not argv:
                fail(f"argv: {tool['name']}/{action['id']} resolved an empty argv")
                continue
            if any((not isinstance(t, str)) or t == "" for t in argv):
                fail(f"argv: {tool['name']}/{action['id']} resolved a non-string or empty token")
            if argv[-2:] != ["--output", "json"]:
                fail(f"argv: {tool['name']}/{action['id']} must end with --output json")
            expected_command = action["expected_command"]
            depth = len(expected_command.split(" "))
            joined = " ".join(argv[:depth])
            if joined != expected_command:
                fail(
                    f"argv: {tool['name']}/{action['id']} argv identity '{joined}' "
                    f"does not match expected_command '{expected_command}'"
                )

    # every plugin error code is exercised by a valid error fixture
    error_cases = load_json(VERSION_DIR / "fixtures" / "error.cases.json")
    if error_cases is None:
        return  # the load failure is already recorded
    error_case_list = error_cases.get("cases")
    if not isinstance(error_case_list, list):
        fail("fixtures: error cases document has no cases array")
        return
    covered = {
        c["instance"]["code"]
        for c in error_case_list
        if c["expect"] == "valid" and "code" in c["instance"]
    }
    missing = set(PRD_ERROR_CODES) - covered
    if missing:
        fail(f"fixtures: error codes without a valid fixture: {sorted(missing)}")


def main() -> int:
    catalog = load_json(VERSION_DIR / "catalog.json")
    required_sections = (
        "tools",
        "identifier_grammar",
        "state_token_grammar",
        "closed_enums",
        "pagination",
        "command_vocabulary",
        "forbidden_input_properties",
        "wrapper",
        "envelope",
        "errors",
        "diagnostics_bounds",
        "limits",
        "compatibility",
        "redaction_rules",
    )
    if catalog is not None:
        missing = [
            section
            for section in required_sections
            if not isinstance(catalog.get(section), (dict, list))
        ]
        if missing:
            fail(f"catalog: required sections missing or malformed: {missing}")
            _report()
            return 1
        check_catalog(catalog)
    registry, schemas = build_registry()
    check_closed_boundaries(schemas, catalog)
    if catalog is not None:
        check_fixtures(registry, catalog)

    return _report()


def _report() -> int:
    if ERRORS:
        print(f"contracts validation FAILED with {len(ERRORS)} error(s):")
        for message in ERRORS:
            print(f"  - {message}")
        return 1
    print("contracts validation passed: catalog, schemas, and fixtures are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
