"""Unit tests for the fail-closed skeleton handlers and the frozen result schemas."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

from conftest import valid_params_for_action

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


def test_availability_check_hides_the_unconfigured_toolset(plugin, unconfigured_ctx):
    assert plugin.tools.make_availability_check(unconfigured_ctx)() is False


def test_every_handler_result_validates_against_the_frozen_wrapper(plugin, unconfigured_ctx):
    wrapper = _validators()["wrapper"]
    for spec in plugin.registry.tool_specs():
        wrapper.validate(json.loads(plugin.tools.handler_for(spec, unconfigured_ctx)({})))


def test_every_handler_fails_closed_with_the_frozen_error_contract(plugin, unconfigured_ctx):
    """Without operator configuration every registered action fails closed."""
    error_validator = _validators()["error"]
    for spec in plugin.registry.tool_specs():
        for action in spec.actions:
            params = valid_params_for_action(spec, action)
            result = json.loads(plugin.tools.handler_for(spec, unconfigured_ctx)(dict(params)))
            assert result["ok"] is False
            assert result["exit_code"] == -1
            assert result["operation"] == spec.name
            error_validator.validate(result["error"])
            assert result["error"]["code"] == "binary_unavailable"
            assert result["error"]["retryable"] is False


def test_handlers_never_reflect_caller_arguments(plugin, unconfigured_ctx):
    for spec in plugin.registry.tool_specs():
        result = json.loads(
            plugin.tools.handler_for(spec, unconfigured_ctx)(
                {"anything": "ignored", "flags": ["--evil"], "binary": "/bin/sh", "cwd": "/tmp"}
            )
        )
        assert result["diagnostics"] == []
        dumped = json.dumps(result)
        assert "ignored" not in dumped and "--evil" not in dumped and "/bin/sh" not in dumped


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
    """tools resolves its registry and runner dependencies without a parent."""
    wanted = ("registry", "runner", "tools")
    saved = {k: v for k, v in sys.modules.items() if k in wanted}
    for k in saved:
        del sys.modules[k]
    try:
        for dependency in ("registry", "runner"):
            spec = importlib.util.spec_from_file_location(dependency, ROOT / f"{dependency}.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[dependency] = module
            spec.loader.exec_module(module)
        tools_spec = importlib.util.spec_from_file_location(
            "tools", ROOT / "tools" / "__init__.py", submodule_search_locations=[]
        )
        tools = importlib.util.module_from_spec(tools_spec)
        tools.__package__ = "tools"
        tools.__path__ = [str(ROOT / "tools")]
        sys.modules["tools"] = tools
        tools_spec.loader.exec_module(tools)
        assert callable(tools.handler_for)
        assert tools.ToolSpec is sys.modules["registry"].ToolSpec
    finally:
        for k in wanted:
            sys.modules.pop(k, None)
        sys.modules.update(saved)
