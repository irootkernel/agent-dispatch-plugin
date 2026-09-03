"""Unit tests for the fail-closed skeleton handlers and the frozen result schemas."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"


def _validators() -> dict[str, Draft202012Validator]:
    ref_registry = RefRegistry()
    validators: dict[str, Draft202012Validator] = {}
    for schema_file in sorted(CONTRACTS.glob("schemas/*.json")):
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        ref_registry = ref_registry.with_resource(schema["$id"], Resource.from_contents(schema))
        validators[schema["$id"].rsplit(":", 1)[-1]] = Draft202012Validator(
            schema, registry=ref_registry
        )
    return validators


def test_availability_check_hides_the_toolset(plugin):
    assert plugin.tools.availability_check() is False


def test_every_handler_result_validates_against_the_frozen_wrapper(plugin):
    wrapper = _validators()["wrapper"]
    for spec in plugin.registry.tool_specs():
        wrapper.validate(plugin.tools.handler_for(spec)())


def test_every_handler_fails_closed_with_the_frozen_error_contract(plugin):
    error_validator = _validators()["error"]
    for spec in plugin.registry.tool_specs():
        result = plugin.tools.handler_for(spec)(action="list", route_id="../evil")
        assert result["ok"] is False
        assert result["exit_code"] == -1
        assert result["operation"] == spec.name
        error_validator.validate(result["error"])
        assert result["error"]["code"] == "binary_unavailable"
        assert result["error"]["retryable"] is False


def test_handlers_never_reflect_caller_arguments(plugin):
    message = plugin.tools._UNAVAILABLE_MESSAGE
    for spec in plugin.registry.tool_specs():
        result = plugin.tools.handler_for(spec)(anything="ignored", flags=["--evil"])
        assert result["diagnostics"] == []
        assert result["error"]["message"] == message


def test_wrapper_and_error_fixture_cases_behave_as_labeled():
    validators = _validators()
    for subject, case_file in (
        ("wrapper", "wrapper.cases.json"),
        ("error", "error.cases.json"),
        ("envelope", "envelope.cases.json"),
    ):
        cases = json.loads((CONTRACTS / "fixtures" / case_file).read_text(encoding="utf-8"))
        for case in cases["cases"]:
            errors = list(validators[subject].iter_errors(case["instance"]))
            if case["expect"] == "valid":
                assert not errors, (case["id"], errors[0].message)
            else:
                assert errors, case["id"]


def test_runner_boundary_stays_fail_closed(plugin):
    """The reserved process-execution boundary must raise until EPIC-002."""
    import importlib

    runner = importlib.import_module(plugin.__name__ + ".runner")
    action = plugin.registry.tool_specs()[0].actions[0]
    with pytest.raises(RuntimeError, match="EPIC-002"):
        runner.run_inspection(action, {}, {})


@pytest.mark.parametrize(
    ("module_file", "top_name"),
    [
        ("registry.py", "registry"),
        ("schemas.py", "schemas"),
        ("runner.py", "runner"),
    ],
)
def test_guarded_modules_import_on_the_degenerate_top_level_path(module_file, top_name):
    """The dual-import guards must keep a packageless load working."""
    created: list[str] = []
    try:
        for dependency in ("registry", "schemas", "runner"):
            if dependency not in sys.modules:
                spec = importlib.util.spec_from_file_location(dependency, ROOT / f"{dependency}.py")
                module = importlib.util.module_from_spec(spec)
                sys.modules[dependency] = module
                created.append(dependency)
                spec.loader.exec_module(module)
        assert hasattr(sys.modules[top_name], "__file__")
    finally:
        for name in created:
            sys.modules.pop(name, None)


def test_tools_package_imports_on_the_degenerate_top_level_path():
    """tools resolves its registry dependency without a namespaced parent."""
    if "tools" in sys.modules:
        return  # already proven by whichever test imported it first
    saved = {k: v for k, v in sys.modules.items() if k in ("registry", "tools")}
    for k in saved:
        del sys.modules[k]
    try:
        spec = importlib.util.spec_from_file_location(
            "tools", ROOT / "tools" / "__init__.py", submodule_search_locations=[]
        )
        tools = types.ModuleType("tools")
        tools.__package__ = "tools"
        sys.modules["tools"] = tools
        spec.loader.exec_module(tools)
        assert callable(tools.handler_for)
    finally:
        for k in ("tools", "registry"):
            if k not in saved:
                sys.modules.pop(k, None)
        sys.modules.update(saved)
