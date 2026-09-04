"""Unit tests for the routes, schedule inspection, and config tools (TASK-008).

Action-level positive evidence drives each of the six action branches
through the real handler and runner boundary against a deterministic
trusted fake executable, asserting the exact fixed argv and the envelope
command identity; negative evidence proves every conditional-field,
identifier-grammar, enum, and probe_targets-placement violation rejects
with invalid_argument before the runner is reached; failure evidence maps
a domain rejection and malformed output onto the closed error contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

from conftest import HermesCtxStub, make_fake_binary

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"


def _wrapper_validator() -> Draft202012Validator:
    ref_registry = RefRegistry()
    for schema_file in sorted(CONTRACTS.glob("schemas/*.json")):
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        ref_registry = ref_registry.with_resource(schema["$id"], Resource.from_contents(schema))
    schema = json.loads((CONTRACTS / "schemas" / "wrapper.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=ref_registry)


@pytest.fixture(scope="module")
def wrapper():
    return _wrapper_validator()


def _tool(plugin, name):
    for spec in plugin.registry.tool_specs():
        if spec.name == name:
            return spec
    raise LookupError(name)


@pytest.fixture
def configured_ctx(plugin, fake_agent_dispatch):
    return HermesCtxStub(settings=fake_agent_dispatch["config"])


def _handler(plugin, ctx, name):
    return plugin.tools.handler_for(_tool(plugin, name), ctx)


@pytest.mark.parametrize(
    ("tool", "params", "expected_argv_tail"),
    [
        (
            "agent_dispatch_routes",
            {"action": "list"},
            ["route", "list", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_routes",
            {"action": "show", "route_id": "wiki-maintenance"},
            ["route", "show", "--route", "wiki-maintenance", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_routes",
            {"action": "preflight", "route_id": "wiki"},
            ["route", "preflight", "--route", "wiki", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_schedule_inspect",
            {"route_id": "wiki"},
            [
                "schedule",
                "inspect",
                "--route",
                "wiki",
                "--platform",
                "launchd",
                "--output",
                "json",
                "--config",
            ],
        ),
        (
            "agent_dispatch_config",
            {"action": "show"},
            ["config", "show", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_config",
            {"action": "validate"},
            ["config", "validate", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_config",
            {"action": "validate", "probe_targets": True},
            ["config", "validate", "--probe-targets", "--output", "json", "--config"],
        ),
    ],
    ids=[
        "route-list",
        "route-show",
        "route-preflight",
        "schedule-inspect",
        "config-show",
        "config-validate",
        "config-validate-probe",
    ],
)
def test_every_action_branch_succeeds_with_its_exact_fixed_mapping(
    plugin, configured_ctx, wrapper, tool, params, expected_argv_tail
):
    result = _handler(plugin, configured_ctx, tool)(**params)
    wrapper.validate(result)
    assert result["ok"] is True, (tool, params, result.get("error"))
    assert result["exit_code"] == 0
    assert result["operation"] == tool
    envelope = result["agent_dispatch"]
    assert envelope["ok"] is True
    # The command identity is the fixed two-token command path.
    assert envelope["command"] == " ".join(expected_argv_tail[:2])
    argv = envelope["result"]["argv"]
    assert argv[1:-1] == expected_argv_tail


def test_domain_rejection_carries_the_envelope_for_a_route_action(plugin, tmp_path, wrapper):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "reject", "exit": 4, "command": "route show"}
    )
    ctx = HermesCtxStub(settings=installation["config"])
    result = _handler(plugin, ctx, "agent_dispatch_routes")(action="show", route_id="wiki")
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["exit_code"] == 4
    envelope = result["agent_dispatch"]
    assert envelope["ok"] is False
    assert envelope["error"]["retryable"] is False
    assert "error" not in result


def test_malformed_output_closes_with_bounded_stderr_tail(plugin, tmp_path, wrapper):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "raw", "stdout": "not json\n", "stderr_lines": ["bad-route"]}
    )
    ctx = HermesCtxStub(settings=installation["config"])
    result = _handler(plugin, ctx, "agent_dispatch_config")(action="show")
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "malformed_json"
    assert "agent_dispatch" not in result
    assert result["diagnostics"] == ["bad-route"]


def _spy_never_reaches_the_runner(plugin, monkeypatch):
    calls: list[tuple] = []

    def spy(*args, **kwargs):
        calls.append(args)
        raise AssertionError("the runner boundary must not be reached by an invalid request")

    monkeypatch.setattr(plugin.runner, "run_inspection", spy)
    return calls


@pytest.mark.parametrize(
    ("tool", "params"),
    [
        # Conditional fields: route_id is rejected on list and required on
        # show and preflight; probe_targets is valid only for validate.
        ("agent_dispatch_routes", {"action": "list", "route_id": "wiki"}),
        ("agent_dispatch_routes", {"action": "show"}),
        ("agent_dispatch_routes", {"action": "preflight"}),
        ("agent_dispatch_config", {"action": "show", "probe_targets": True}),
        ("agent_dispatch_config", {"action": "validate", "probe_targets": "yes"}),
        # Closed action enums.
        ("agent_dispatch_routes", {"action": "enable", "route_id": "wiki"}),
        ("agent_dispatch_config", {"action": "rewrite"}),
        ("agent_dispatch_schedule_inspect", {"action": "inspect", "route_id": "wiki"}),
        # Identifier grammar: option prefixes, whitespace, overlength,
        # traversal separators, and trailing control bytes.
        ("agent_dispatch_routes", {"action": "show", "route_id": "--route"}),
        ("agent_dispatch_routes", {"action": "show", "route_id": "wiki maintenance"}),
        ("agent_dispatch_routes", {"action": "show", "route_id": "a" * 129}),
        ("agent_dispatch_routes", {"action": "show", "route_id": "wiki\n"}),
        ("agent_dispatch_routes", {"action": "show", "route_id": "../etc/passwd"}),
        ("agent_dispatch_schedule_inspect", {"route_id": "-x"}),
        ("agent_dispatch_schedule_inspect", {"route_id": "a b"}),
        ("agent_dispatch_schedule_inspect", {}),
        ("agent_dispatch_schedule_inspect", {"route_id": "wiki", "platform": "systemd"}),
    ],
)
def test_invalid_requests_are_rejected_before_the_runner(
    plugin, monkeypatch, tool, params, wrapper
):
    """Schema violations close as invalid_argument with no process creation."""
    calls = _spy_never_reaches_the_runner(plugin, monkeypatch)
    result = _handler(plugin, HermesCtxStub(settings={"binary_path": "/nope"}), tool)(**params)
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["exit_code"] == -1
    assert result["operation"] == tool
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["retryable"] is False
    assert result["diagnostics"] == []
    assert calls == []


def test_identifier_values_never_reach_the_error_message(plugin, monkeypatch):
    _spy_never_reaches_the_runner(plugin, monkeypatch)
    marker = "../etc/passwd"
    result = _handler(plugin, HermesCtxStub(), "agent_dispatch_routes")(
        action="show", route_id=marker
    )
    assert marker not in json.dumps(result)


def test_valid_requests_still_delegate_through_the_spy(plugin, configured_ctx, monkeypatch):
    """The spy wiring stays sound: a valid route request delegates exactly once."""
    real = plugin.runner.run_inspection
    calls: list[tuple] = []

    def recording(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(plugin.runner, "run_inspection", recording)
    result = _handler(plugin, configured_ctx, "agent_dispatch_routes")(
        action="preflight", route_id="wiki"
    )
    assert result["ok"] is True
    assert len(calls) == 1
