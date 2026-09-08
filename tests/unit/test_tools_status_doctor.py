"""Unit tests for the status and doctor tools over the full boundary (TASK-007).

Success evidence drives each action through the real handler and runner
boundary against a deterministic trusted fake executable; failure evidence
maps domain rejections and malformed output onto the closed error contract;
negative input evidence proves the handler rejects requests outside the
frozen schema before the runner is ever reached.
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
    handler = plugin.tools.handler_for(_tool(plugin, name), ctx)
    return lambda args: json.loads(handler(dict(args)))


def test_status_success_through_the_full_boundary(
    plugin, configured_ctx, fake_agent_dispatch, wrapper
):
    result = _handler(plugin, configured_ctx, "agent_dispatch_status")({})
    wrapper.validate(result)
    assert result["ok"] is True
    assert result["operation"] == "agent_dispatch_status"
    assert result["exit_code"] == 0
    envelope = result["agent_dispatch"]
    assert envelope["ok"] is True
    assert envelope["command"] == "status"
    assert "error" not in result
    # The fixed command mapping: binary, status, the frozen suffix, --config.
    argv = envelope["result"]["argv"]
    assert argv[1:] == [
        "status",
        "--output",
        "json",
        "--config",
        str(fake_agent_dispatch["config_file"]),
    ]


def test_doctor_success_with_and_without_target_probing(plugin, configured_ctx, wrapper):
    for params in ({}, {"probe_targets": False}, {"probe_targets": True}):
        result = _handler(plugin, configured_ctx, "agent_dispatch_doctor")(dict(params))
        wrapper.validate(result)
        assert result["ok"] is True
        assert result["operation"] == "agent_dispatch_doctor"
        envelope = result["agent_dispatch"]
        assert envelope["command"] == "doctor"
        argv = envelope["result"]["argv"]
        expected = ["doctor"]
        if params.get("probe_targets") is True:
            expected.append("--probe-targets")
        expected += ["--output", "json", "--config", argv[-1]]
        assert argv[1:] == expected


def test_domain_rejection_carries_the_envelope_not_a_plugin_error(
    plugin, tmp_path, monkeypatch, wrapper
):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "reject", "exit": 3, "command": "doctor"}
    )
    ctx = HermesCtxStub(settings=installation["config"])
    result = _handler(plugin, ctx, "agent_dispatch_doctor")({})
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["exit_code"] == 3
    envelope = result["agent_dispatch"]
    assert envelope["ok"] is False
    assert envelope["error"]["retryable"] is False
    assert "error" not in result


def test_malformed_output_closes_with_bounded_stderr_tail(plugin, tmp_path, wrapper):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "raw", "stdout": "not json\n", "stderr_lines": ["boom"]}
    )
    ctx = HermesCtxStub(settings=installation["config"])
    result = _handler(plugin, ctx, "agent_dispatch_status")({})
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "malformed_json"
    assert "agent_dispatch" not in result
    assert result["diagnostics"] == ["boom"]


def _spy_never_reaches_the_runner(plugin, monkeypatch):
    calls: list[tuple] = []

    def spy(*args, **kwargs):
        calls.append(args)
        raise AssertionError("the runner boundary must not be reached by an invalid request")

    monkeypatch.setattr(plugin.runner, "run_inspection", spy)
    return calls


@pytest.mark.parametrize(
    ("name", "params"),
    [
        ("agent_dispatch_status", {"anything": "ignored"}),
        ("agent_dispatch_status", {"flags": ["--evil"]}),
        ("agent_dispatch_doctor", {"probe_targets": "yes"}),
        ("agent_dispatch_doctor", {"probe_targets": 1}),
        ("agent_dispatch_doctor", {"action": "inspect"}),
        ("agent_dispatch_doctor", {"command": "/bin/sh"}),
    ],
)
def test_invalid_requests_are_rejected_before_the_runner(
    plugin, monkeypatch, name, params, wrapper
):
    """Schema violations close as invalid_argument with no process creation."""
    calls = _spy_never_reaches_the_runner(plugin, monkeypatch)
    result = _handler(plugin, HermesCtxStub(settings={"binary_path": "/nope"}), name)(dict(params))
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["exit_code"] == -1
    assert result["operation"] == name
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["retryable"] is False
    assert result["diagnostics"] == []
    assert calls == []


def test_invalid_requests_never_reflect_caller_values(plugin, monkeypatch):
    _spy_never_reaches_the_runner(plugin, monkeypatch)
    result = _handler(plugin, HermesCtxStub(), "agent_dispatch_status")({"anything": "ignored"})
    assert "ignored" not in json.dumps(result)


def test_valid_requests_still_reach_the_runner_after_the_spy(plugin, configured_ctx, monkeypatch):
    """The spy wiring itself is sound: valid input delegates through it."""
    real = plugin.runner.run_inspection
    calls: list[tuple] = []

    def recording(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(plugin.runner, "run_inspection", recording)
    result = _handler(plugin, configured_ctx, "agent_dispatch_status")({})
    assert result["ok"] is True
    assert len(calls) == 1


@pytest.mark.parametrize("params", [{}, {"probe_targets": False}, {"probe_targets": True}])
@pytest.mark.parametrize("exit_code", [0, 3])
def test_doctor_findings_preserve_exit_and_redact(plugin, tmp_path, wrapper, params, exit_code):
    envelope = {
        "api_version": "agent-dispatch.cli/v1",
        "command": "doctor",
        "ok": True,
        "result": {
            "findings": [
                {
                    "code": "watchman_unavailable",
                    "severity": "error",
                    "summary": "Bearer super-secret-value",
                }
            ],
            "findings_count": 1,
        },
    }
    installation = make_fake_binary(
        tmp_path,
        behavior={
            "kind": "raw",
            "stdout": json.dumps(envelope),
            "exit": exit_code,
            "stderr_lines": ["private stderr must not be returned"],
        },
    )
    result = _handler(
        plugin, HermesCtxStub(settings=installation["config"]), "agent_dispatch_doctor"
    )(params)
    wrapper.validate(result)
    assert result["ok"] is True
    assert result["exit_code"] == exit_code
    assert result["agent_dispatch"]["result"]["findings_count"] == 1
    assert result["agent_dispatch"]["result"]["findings"][0]["severity"] == "error"
    assert "super-secret-value" not in json.dumps(result)
    assert "private stderr" not in json.dumps(result)
    assert "error" not in result


@pytest.mark.parametrize(
    ("command", "exit_code", "stdout"),
    [
        ("doctor", 4, None),
        ("doctor", 2, None),
        ("status", 3, None),
        ("doctor", 3, "not json"),
    ],
)
def test_doctor_exception_does_not_admit_other_failures(
    plugin, tmp_path, wrapper, command, exit_code, stdout
):
    payload = (
        stdout
        if stdout is not None
        else json.dumps(
            {
                "api_version": "agent-dispatch.cli/v1",
                "command": command,
                "ok": True,
                "result": {"findings": []},
            }
        )
    )
    installation = make_fake_binary(
        tmp_path,
        behavior={
            "kind": "raw",
            "stdout": payload,
            "exit": exit_code,
        },
    )
    result = _handler(
        plugin, HermesCtxStub(settings=installation["config"]), "agent_dispatch_doctor"
    )({})
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == ("malformed_json" if stdout else "contract_mismatch")
    assert "agent_dispatch" not in result
