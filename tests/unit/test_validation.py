"""Unit tests for the closed output boundary (TASK-006).

The frozen contract fixtures drive the envelope validation; seeded secrets
drive the five defense-in-depth redaction rules end to end through the
runner boundary; the wrapper carrier rule is proven against the frozen
wrapper schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

from conftest import make_fake_binary

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"

VALID_ENVELOPE = {
    "api_version": "agent-dispatch.cli/v1",
    "command": "status",
    "ok": True,
    "result": {"routes": []},
    "warnings": [],
    "trace_id": "",
}


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


@pytest.fixture
def runner(plugin):
    return plugin.runner


@pytest.fixture
def envelopes(plugin):
    return plugin.envelopes


def _status_action(plugin):
    for spec in plugin.registry.tool_specs():
        if spec.name == "agent_dispatch_status":
            return spec.actions[0]
    raise LookupError("status tool")


def _run_raw(plugin, runner, tmp_path, envelope=None, exit_code=0, stderr_lines=None, stdout=None):
    installation = make_fake_binary(
        tmp_path,
        behavior={
            "kind": "raw",
            "envelope": envelope,
            "exit": exit_code,
            "stderr_lines": stderr_lines or [],
            **({} if stdout is None else {"stdout": stdout}),
        },
    )
    config = {**installation["config"], "timeout_seconds": 10}
    return runner.run_inspection(_status_action(plugin), "agent_dispatch_status", {}, config)


def test_frozen_envelope_fixtures_drive_the_validator(envelopes):
    cases = json.loads((CONTRACTS / "fixtures" / "envelope.cases.json").read_text())
    for case in cases["cases"]:
        instance = case["instance"]
        expected_command = instance.get("command", "status")
        if case["expect"] == "valid":
            assert envelopes.validate_envelope(instance, expected_command) is instance
        else:
            with pytest.raises(envelopes.EnvelopeViolation):
                envelopes.validate_envelope(instance, expected_command)


def test_command_identity_mismatch_closes_as_contract_mismatch(plugin, runner, tmp_path):
    result = _run_raw(plugin, runner, tmp_path, envelope={**VALID_ENVELOPE, "command": "doctor"})
    assert result["error"]["code"] == "contract_mismatch"
    assert result["exit_code"] == 0
    assert "agent_dispatch" not in result


def test_exit_inconsistency_closes_as_contract_mismatch(plugin, runner, tmp_path):
    result = _run_raw(plugin, runner, tmp_path, envelope=VALID_ENVELOPE, exit_code=3)
    assert result["error"]["code"] == "contract_mismatch"


@pytest.mark.parametrize(
    "mutation",
    [
        {"unexpected_member": True},
        {
            "ok": False,
            "result": {"x": 1},
            "error": {"code": "c", "category": "configuration", "message": "m", "retryable": False},
        },
        {"ok": False},
        {
            "ok": True,
            "error": {"code": "c", "category": "configuration", "message": "m", "retryable": False},
        },
        {"command": ""},
        {"trace_id": "x" * 129},
        {"warnings": ["x" * 1025]},
        {"ok": False, "error": {"code": "c", "category": "configuration", "message": "m"}},
    ],
    ids=[
        "unknown-member",
        "both-carriers",
        "missing-error",
        "success-with-error",
        "empty-command",
        "oversized-trace",
        "oversized-warning",
        "open-error-object",
    ],
)
def test_structural_violations_close_as_contract_mismatch(plugin, runner, tmp_path, mutation):
    envelope = dict(VALID_ENVELOPE)
    envelope.update(mutation)
    result = _run_raw(plugin, runner, tmp_path, envelope=envelope)
    assert result["error"]["code"] == "contract_mismatch"


def test_domain_rejection_carries_the_envelope_and_exit_status(plugin, runner, tmp_path):
    rejection = {
        "api_version": "agent-dispatch.cli/v1",
        "command": "status",
        "ok": False,
        "error": {
            "code": "config_invalid",
            "category": "configuration",
            "message": "scripted rejection",
            "retryable": False,
        },
        "warnings": [],
        "trace_id": "",
    }
    result = _run_raw(plugin, runner, tmp_path, envelope=rejection, exit_code=3)
    assert result["ok"] is False
    assert result["exit_code"] == 3
    assert result["agent_dispatch"]["ok"] is False
    assert "error" not in result  # the envelope is the sole carrier


SEEDED_BEARER = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sig.sig"
SEEDED_HEX_TOKEN = "0f26a94c1b3e57d8f0a91c2e4b7d8a3c5e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
SEEDED_WEBHOOK = "https://hooks.example.com/services/T000000/B000000/XXXXXXXXXXXXXXXX"
SEEDED_SECRET_PATH = "/Users/operator/.ssh/id_ed25519"
SEEDED_ABSOLUTE_PATH = "/Users/operator/state/store.db"
SEEDED_API_KEY = "api_key: k8sSk2xQ4vBn7mZpL1wR6tYc0uJ3hF5aD9g"


def test_seeded_secrets_never_survive_the_output_boundary(plugin, runner, tmp_path):
    envelope = {
        **VALID_ENVELOPE,
        "warnings": [f"upstream warning with {SEEDED_BEARER}"],
        "result": {
            "authorization": SEEDED_BEARER,
            "webhook": SEEDED_WEBHOOK,
            "key": SEEDED_HEX_TOKEN,
            "material": SEEDED_API_KEY,
            "path": SEEDED_SECRET_PATH,
            "store": SEEDED_ABSOLUTE_PATH,
        },
    }
    result = _run_raw(plugin, runner, tmp_path, envelope=envelope)
    assert result["ok"] is True
    dumped = json.dumps(result)
    for seeded in (
        SEEDED_BEARER,
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        SEEDED_HEX_TOKEN,
        SEEDED_WEBHOOK,
        SEEDED_API_KEY.split(":")[1].strip(),
        SEEDED_SECRET_PATH,
        SEEDED_ABSOLUTE_PATH,
    ):
        assert seeded not in dumped, seeded
    assert any("redactable content" in line for line in result["diagnostics"])


def test_allowed_display_paths_survive_redaction(envelopes):
    text = "using /usr/local/bin/agent-dispatch with /etc/agent-dispatch.json"
    allowed = ("/usr/local/bin/agent-dispatch", "/etc/agent-dispatch.json")
    redacted = envelopes.redact_text(text, allowed)
    assert "/usr/local/bin/agent-dispatch" in redacted
    assert "/etc/agent-dispatch.json" in redacted


def test_each_redaction_rule_redacts_its_seed(envelopes):
    cases = [
        (f"authorization {SEEDED_BEARER}", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"),
        (f"reading secret at {SEEDED_SECRET_PATH}", ".ssh/id_ed25519"),
        (f"token {SEEDED_HEX_TOKEN}", SEEDED_HEX_TOKEN),
        (f"webhook {SEEDED_WEBHOOK}", "hooks.example.com"),
        (f"store at {SEEDED_ABSOLUTE_PATH}", "/Users/operator/state"),
    ]
    for text, must_vanish in cases:
        redacted = envelopes.redact_text(text)
        assert must_vanish not in redacted, text


def test_diagnostics_are_bounded_and_redacted(plugin, runner, tmp_path):
    stderr_lines = [f"line {i}: {SEEDED_HEX_TOKEN} {'y' * 600}" for i in range(20)]
    result = _run_raw(plugin, runner, tmp_path, stdout="not json\n", stderr_lines=stderr_lines)
    assert result["error"]["code"] == "malformed_json"
    assert len(result["diagnostics"]) == 16
    assert all(len(line) <= 512 for line in result["diagnostics"])
    dumped = json.dumps(result)
    assert SEEDED_HEX_TOKEN not in dumped
    assert "line 3" not in dumped  # only the bounded tail of 16 survives
    assert result["diagnostics"][-1].startswith("line 19")


def test_redaction_failure_closes_with_its_own_guard(plugin, runner, tmp_path, monkeypatch):
    def exploding(value, allowed_paths=()):
        raise RuntimeError("pipeline broken")

    monkeypatch.setattr(plugin.envelopes, "redact_envelope", exploding)
    monkeypatch.setattr(runner.envelopes, "redact_envelope", exploding)
    result = _run_raw(plugin, runner, tmp_path, envelope=VALID_ENVELOPE)
    assert result["error"]["code"] == "redaction_failure"
    assert "agent_dispatch" not in result
    assert result["exit_code"] == 0


def test_every_wrapper_shape_validates_against_the_frozen_schema(
    plugin, runner, tmp_path, fake_agent_dispatch
):
    wrapper_validator = _validators()["wrapper"]
    rejection = dict(VALID_ENVELOPE)
    rejection.pop("result")
    rejection["ok"] = False
    rejection["error"] = {
        "code": "config_invalid",
        "category": "configuration",
        "message": "scripted rejection",
        "retryable": False,
    }
    scenarios = [
        _run_raw(plugin, runner, tmp_path, envelope=VALID_ENVELOPE),
        _run_raw(plugin, runner, tmp_path, envelope=rejection),
        _run_raw(plugin, runner, tmp_path, stdout="garbage\n"),
        _run_raw(plugin, runner, tmp_path, envelope={**VALID_ENVELOPE, "command": "doctor"}),
    ]
    sleepy = make_fake_binary(tmp_path / "sleepy", behavior={"kind": "sleep", "seconds": 30})
    scenarios.append(
        runner.run_inspection(
            _status_action(plugin),
            "agent_dispatch_status",
            {},
            {**sleepy["config"], "timeout_seconds": 1},
        )
    )
    for result in scenarios:
        wrapper_validator.validate(result)
