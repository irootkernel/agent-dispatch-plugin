"""Unit tests for the derived input-validation layer (TASK-007).

The frozen per-tool fixture cases are replayed through the stdlib-only
derived interpreter and cross-checked against the frozen schema under the
pinned jsonschema toolchain, proving the interpreter agrees with the frozen
authority on the complete corpus: closed property sets, enums, the
identifier and state-token grammars, pagination bounds, and the conditional
per-action requirements. Prohibited model-provided execution settings are
driven from the catalog's frozen list.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"


def _schema_path(tool: str) -> Path:
    return CONTRACTS / "schemas" / "tools" / f"{tool}.input.json"


def _load_schema(tool: str) -> dict:
    return json.loads(_schema_path(tool).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validators():
    return {
        schema_file.name[: -len(".input.json")]: Draft202012Validator(
            json.loads(schema_file.read_text(encoding="utf-8"))
        )
        for schema_file in sorted((CONTRACTS / "schemas" / "tools").glob("*.input.json"))
    }


@pytest.fixture(scope="module")
def inputs(plugin):
    return plugin.tools.inputs


def _minimal_valid_params(spec) -> dict:
    """The smallest request the frozen schema accepts for one tool."""
    schema = spec.load_input_schema()
    params: dict = {name: "x" for name in schema.get("required", ()) if name != "action"}
    action_values = [a.input_action_value for a in spec.actions if a.input_action_value]
    if action_values:
        params["action"] = action_values[0]
    return params


def _cases():
    for case_file in sorted((CONTRACTS / "fixtures" / "tools").glob("*.cases.json")):
        tool = case_file.name[: -len(".cases.json")]
        for case in json.loads(case_file.read_text(encoding="utf-8"))["cases"]:
            yield pytest.param(tool, case, id=case["id"])


@pytest.mark.parametrize(("tool", "case"), list(_cases()))
def test_derived_interpreter_agrees_with_the_frozen_schema_on_every_fixture_case(
    inputs, validators, tool, case
):
    """Each frozen case must receive the same verdict from both authorities."""
    reason = inputs.validate_input(_load_schema(tool), case["instance"], tool)
    schema_errors = list(validators[tool].iter_errors(case["instance"]))
    if case["expect"] == "valid":
        assert reason is None, (case["id"], reason)
        assert not schema_errors, (case["id"], schema_errors[0].message)
    else:
        assert reason is not None, case["id"]
        assert schema_errors, case["id"]


def test_every_frozen_fixture_case_is_replayed():
    """The corpus must stay complete: every tool contributes at least one case."""
    case_files = sorted((CONTRACTS / "fixtures" / "tools").glob("*.cases.json"))
    assert len(case_files) == 10


def test_prohibited_execution_settings_are_rejected_for_every_tool(inputs, plugin):
    """Every frozen prohibited property is outside every closed property set."""
    catalog = plugin.registry.load_catalog()
    forbidden = catalog["forbidden_input_properties"]
    assert forbidden, "the frozen catalog must declare prohibited input properties"
    for spec in plugin.registry.tool_specs():
        minimal = _minimal_valid_params(spec)
        for name in forbidden:
            reason = inputs.validate_tool_input(spec, minimal | {name: "x"})
            assert reason is not None, (spec.name, name)


def test_reasons_never_reflect_request_values(inputs):
    """A rejection reason names schema vocabulary only, never caller values."""
    marker = "SENTINEL VALUE !7f3a"
    schema = _load_schema("agent_dispatch_routes")
    grammar = inputs.validate_input(
        schema, {"action": "show", "route_id": marker}, "agent_dispatch_routes"
    )
    assert grammar is not None and marker not in grammar
    unknown = inputs.validate_input(schema, {"action": "list", marker: 1}, "agent_dispatch_routes")
    assert unknown is not None and marker not in unknown
    wrong_type = inputs.validate_input(
        schema, {"action": "show", "route_id": ["array"]}, "agent_dispatch_routes"
    )
    assert wrong_type is not None and "array" not in wrong_type


def test_unsupported_schema_vocabulary_fails_loudly(inputs):
    schema = {
        "type": "object",
        "properties": {"x": {"type": "string", "minLength": 1}},
        "additionalProperties": False,
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(schema, {}, "probe-tool")


def test_top_level_vocabulary_guard_fails_loudly(inputs):
    """A keyword the evaluator never reads at the top level raises too."""
    schema = {"type": "object", "properties": {}, "additionalProperties": False, "oneOf": []}
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(schema, {}, "probe-tool")


def test_conditional_body_vocabulary_drift_fails_loudly(inputs):
    """Constraints hidden inside allOf/if/then bodies raise, not silently skip."""
    drifted = {
        "type": "object",
        "properties": {"action": {"enum": ["a"]}, "x": {"type": "string"}},
        "additionalProperties": False,
        "required": ["action"],
        "allOf": [
            {
                "if": {"properties": {"action": {"const": "a"}}, "required": ["action"]},
                "then": {"required": ["x"], "properties": {"x": {"minLength": 2}}},
            }
        ],
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(drifted, {"action": "a"}, "probe-tool")
    patterned_if = {
        "type": "object",
        "properties": {"action": {"enum": ["a"]}},
        "additionalProperties": False,
        "required": ["action"],
        "allOf": [
            {
                "if": {"properties": {"action": {"pattern": "^a"}}, "required": ["action"]},
                "then": {"not": {"required": []}},
            }
        ],
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(patterned_if, {"action": "a"}, "probe-tool")


def test_deepest_conditional_vocabulary_drift_fails_loudly(inputs):
    """Drift inside then.not bodies and not.anyOf alternatives raises too."""
    drifted_not = {
        "type": "object",
        "properties": {"action": {"enum": ["a"]}},
        "additionalProperties": False,
        "required": ["action"],
        "allOf": [
            {
                "if": {"properties": {"action": {"const": "a"}}, "required": ["action"]},
                "then": {"not": {"required": ["x"], "minLength": 1}},
            }
        ],
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(drifted_not, {"action": "a"}, "probe-tool")
    drifted_anyof = {
        "type": "object",
        "properties": {"action": {"enum": ["a"]}},
        "additionalProperties": False,
        "required": ["action"],
        "allOf": [
            {
                "if": {"properties": {"action": {"const": "a"}}, "required": ["action"]},
                "then": {"not": {"anyOf": [{"required": ["x"], "pattern": "^x"}]}},
            }
        ],
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(drifted_anyof, {"action": "a"}, "probe-tool")


def test_top_level_constraint_keywords_fail_loudly(inputs):
    """A constraint keyword the evaluator never reads at the top level raises."""
    schema = {
        "type": "object",
        "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
        "additionalProperties": False,
        "anyOf": [{"required": ["a"]}, {"required": ["b"]}],
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(schema, {}, "probe-tool")
    top_level_const = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
        "const": {},
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(top_level_const, {}, "probe-tool")


def test_non_scalar_types_and_open_member_sets_fail_loudly(inputs):
    """Type arrays and permissive additionalProperties diverge loudly."""
    type_array = {
        "type": "object",
        "properties": {"x": {"type": ["string", "null"]}},
        "additionalProperties": False,
    }
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(type_array, {"x": None}, "probe-tool")
    open_members = {"type": "object", "properties": {}, "additionalProperties": True}
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(open_members, {}, "probe-tool")
    unpinned = {"type": "object", "properties": {}}
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(unpinned, {}, "probe-tool")
    non_object = {"type": "array", "items": {}}
    with pytest.raises(inputs.ContractVocabularyError):
        inputs.validate_input(non_object, [], "probe-tool")


def test_max_properties_rejection_branch_is_covered(inputs):
    """A request of known-but-too-many members reaches the maxProperties branch."""
    schema = {
        "type": "object",
        "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
        "additionalProperties": False,
        "maxProperties": 1,
    }
    assert inputs.validate_input(schema, {"a": "x"}, "probe-tool") is None
    reason = inputs.validate_input(schema, {"a": "x", "b": "y"}, "probe-tool")
    assert reason is not None and "more members" in reason


def test_state_token_and_pagination_bounds_follow_the_frozen_grammars(inputs):
    """Boundary values around every numeric and grammar bound stay covered."""
    schema = _load_schema("agent_dispatch_dispatches")

    def validate(params):
        return inputs.validate_input(schema, params, "agent_dispatch_dispatches")

    # The state-token grammar: lowercase lead byte, up to 64 characters.
    assert validate({"action": "list", "state": "d"}) is None
    assert validate({"action": "list", "state": "d" * 64}) is None
    assert validate({"action": "list", "state": "d" * 65}) is not None
    assert validate({"action": "list", "state": "Dispatched"}) is not None
    # Pagination boundaries: limit 1..100, offset 0..1,000,000; JSON booleans
    # are never integers even though Python bools subclass int.
    for boundary in (
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"offset": -1},
        {"offset": 1000001},
        {"offset": True},
    ):
        assert validate({"action": "list"} | boundary) is not None, boundary
    for boundary in ({"limit": 1}, {"limit": 100}, {"offset": 0}, {"offset": 1000000}):
        assert validate({"action": "list"} | boundary) is None, boundary


def test_minimal_valid_params_helper_is_honest(inputs, plugin):
    """The helper's requests must themselves validate for every tool."""
    for spec in plugin.registry.tool_specs():
        assert inputs.validate_tool_input(spec, _minimal_valid_params(spec)) is None
