"""TASK-025 runtime sync result contract and safe presentation checks."""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "contracts/v0.2.0"
COMMANDS = {
    "sync capabilities": "agent_dispatch_sync_capabilities",
    "sync status": "agent_dispatch_sync_status",
    "sync service inspect": "agent_dispatch_sync_service_inspect",
}


def _case(name: str, case_id: str) -> dict:
    cases = json.loads(
        (RESULTS / f"fixtures/results/{name}.cases.json").read_text(encoding="utf-8")
    )["cases"]
    return next(case["instance"] for case in cases if case["id"] == case_id)


def _run(plugin, command: str, result: dict, *, warnings: list[str] | None = None):
    spec = next(
        action
        for tool in plugin.registry.tool_specs()
        for action in tool.actions
        if action.expected_command == command
    )
    envelope = {
        "api_version": "agent-dispatch.cli/v1",
        "command": command,
        "ok": True,
        "result": result,
        "warnings": warnings or [],
        "trace_id": "",
    }
    outcome = plugin.runner._Outcome(
        timed_out=False, overflowed=False, exit_code=0, stdout=json.dumps(envelope).encode()
    )
    trust = plugin.runner.RunnerTrust(Path("/usr/bin/true"), Path("/tmp/config"), 10, 1024)
    return plugin.runner._map_completed_process(
        "agent_dispatch_" + command.replace(" ", "_"), outcome, spec, trust
    )


@pytest.mark.parametrize("command,name", COMMANDS.items())
def test_runtime_matches_result_oracle_and_rejects_invalid_fixtures(plugin, command, name):
    schema = json.loads(
        (RESULTS / f"schemas/results/{name}.result.json").read_text(encoding="utf-8")
    )
    cases = json.loads(
        (RESULTS / f"fixtures/results/{name}.cases.json").read_text(encoding="utf-8")
    )["cases"]
    for case in cases:
        expected = case["expect"] == "valid"
        assert Draft202012Validator(schema).is_valid(case["instance"]) is expected
        wrapped = _run(plugin, command, case["instance"])
        assert wrapped["ok"] is expected, case["id"]
        if not expected:
            assert wrapped["error"]["code"] == "contract_mismatch"
            assert "agent_dispatch" not in wrapped


@pytest.mark.parametrize(
    ("case_id", "path"),
    [
        ("sync-status-enabled", ("group_id",)),
        ("sync-status-enabled", ("config_revision",)),
        (
            "sync-status-public-commit-with-secret-neighbor",
            ("latest_verification", "target_commit"),
        ),
    ],
)
def test_runtime_rejects_trailing_newline_in_result_identity(plugin, case_id, path):
    status = copy.deepcopy(_case("agent_dispatch_sync_status", case_id))
    field = status
    for key in path[:-1]:
        field = field[key]
    field[path[-1]] += "\n"
    wrapped = _run(plugin, "sync status", status)
    assert wrapped["ok"] is False
    assert wrapped["error"]["code"] == "contract_mismatch"
    assert "agent_dispatch" not in wrapped


def test_sync_result_must_be_an_object(plugin):
    wrapped = _run(plugin, "sync status", [])
    assert wrapped["ok"] is False
    assert wrapped["error"]["code"] == "contract_mismatch"
    assert "agent_dispatch" not in wrapped


@pytest.mark.parametrize(
    ("number", "valid"), [(7, True), (7.0, True), (-1.0, False), (1.5, False), (True, False)]
)
def test_result_integer_fields_follow_json_schema_semantics(plugin, number, valid):
    status = copy.deepcopy(_case("agent_dispatch_sync_status", "sync-status-enabled"))
    status["control_revision"] = number
    status["peer_inbox_pending"] = 2.0
    wrapped = _run(plugin, "sync status", status)
    assert wrapped["ok"] is valid
    if valid:
        assert wrapped["agent_dispatch"]["result"]["control_revision"] == number
        assert wrapped["agent_dispatch"]["result"]["peer_inbox_pending"] == 2.0
    else:
        assert wrapped["error"]["code"] == "contract_mismatch"
        assert "agent_dispatch" not in wrapped


def test_status_preserves_distinct_projections_and_only_public_identities(plugin):
    status = copy.deepcopy(
        _case("agent_dispatch_sync_status", "sync-status-public-commit-with-secret-neighbor")
    )
    status["health"]["listener"] = {"state": "unknown", "reason": "peer_offline"}
    status["latest_publication"] = {"present": False}
    status["latest_delivery"] = {"present": False}
    status["latest_import"] = {"present": False}
    status["latest_verification"]["reason"] = "Bearer secret-shaped-neighbor"
    wrapped = _run(
        plugin,
        "sync status",
        status,
        warnings=["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
    )
    assert wrapped["ok"] is True
    shown = wrapped["agent_dispatch"]["result"]
    assert shown["config_revision"] == status["config_revision"]
    assert (
        shown["latest_verification"]["target_commit"]
        == status["latest_verification"]["target_commit"]
    )
    assert shown["latest_verification"]["reason"] == "Bearer [redacted]"
    assert shown["expected_nodes"] == status["expected_nodes"]
    assert shown["health"]["listener"] == {"state": "unknown", "reason": "peer_offline"}
    assert wrapped["agent_dispatch"]["warnings"] == ["[redacted]"]
    assert "fresh_pair_verified" not in json.dumps(wrapped)


def test_blocked_stale_and_four_latest_targets_remain_separate(plugin):
    status = copy.deepcopy(
        _case("agent_dispatch_sync_status", "sync-status-public-commit-with-secret-neighbor")
    )
    status["state"] = "blocked"
    status["reason"] = "target_changed"
    status["health"]["verification"] = {"state": "stale", "reason": "target_changed"}
    status["peer_inbox_pending"] = 2
    for key, digit in zip(
        ("latest_publication", "latest_delivery", "latest_import", "latest_verification"),
        "bcde",
        strict=True,
    ):
        status[key] = copy.deepcopy(status["latest_verification"])
        status[key]["target_commit"] = digit * 40
    wrapped = _run(plugin, "sync status", status)
    assert wrapped["ok"] is True
    shown = wrapped["agent_dispatch"]["result"]
    assert (shown["state"], shown["reason"]) == ("blocked", "target_changed")
    assert shown["health"]["verification"] == {"state": "stale", "reason": "target_changed"}
    assert shown["peer_inbox_pending"] == 2
    for key in ("latest_publication", "latest_delivery", "latest_import", "latest_verification"):
        assert shown[key]["target_commit"] == status[key]["target_commit"]
        assert shown[key]["reason"] == "Bearer [redacted]"
    assert len({shown[key]["target_commit"] for key in status if key.startswith("latest_")}) == 4


def test_nonpublic_hash_and_path_are_redacted_without_listener_inference(plugin):
    service = copy.deepcopy(_case("agent_dispatch_sync_service_inspect", "sync-service-loaded"))
    service["label"] = "a" * 64
    service["definition_path"] = "/home/operator/.ssh/private-key"
    wrapped = _run(plugin, "sync service inspect", service)
    assert wrapped["ok"] is True
    shown = wrapped["agent_dispatch"]["result"]
    assert shown["label"] == "[redacted]"
    assert shown["definition_path"] == "[redacted]"
    assert shown["expected_digest"] == "sha256:[redacted]"
    assert shown["loaded"] is True
    assert "listener" not in shown


def test_drifted_service_definition_remains_visible_as_drift(plugin):
    drift = _case("agent_dispatch_sync_service_inspect", "sync-service-drift")
    wrapped = _run(plugin, "sync service inspect", drift)
    assert wrapped["ok"] is True
    shown = wrapped["agent_dispatch"]["result"]
    assert shown["present"] is True
    assert shown["loaded"] is True
    assert shown["definition_matches"] is False
    assert shown["healthy"] is False
    assert shown["installed_digest"] == "sha256:[redacted]"
    assert "listener" not in shown


@pytest.mark.parametrize(
    ("command", "name", "case_id", "change"),
    [
        (
            "sync service inspect",
            "agent_dispatch_sync_service_inspect",
            "sync-service-loaded",
            lambda value: value.__setitem__("label", "x" * 129),
        ),
        (
            "sync service inspect",
            "agent_dispatch_sync_service_inspect",
            "sync-service-loaded",
            lambda value: value.pop("group_id"),
        ),
        (
            "sync status",
            "agent_dispatch_sync_status",
            "sync-status-enabled",
            lambda value: value.__setitem__("control_revision", -1),
        ),
        (
            "sync status",
            "agent_dispatch_sync_status",
            "sync-status-enabled",
            lambda value: value["latest_publication"].__setitem__("job_id", "unexpected"),
        ),
        (
            "sync status",
            "agent_dispatch_sync_status",
            "sync-status-disabled",
            lambda value: value.__setitem__("membership_mode", "normal"),
        ),
    ],
)
def test_uncovered_schema_constraints_reject_invalid_results(
    plugin, command, name, case_id, change
):
    value = copy.deepcopy(_case(name, case_id))
    change(value)
    schema = json.loads(
        (RESULTS / f"schemas/results/{name}.result.json").read_text(encoding="utf-8")
    )
    assert not Draft202012Validator(schema).is_valid(value)
    wrapped = _run(plugin, command, value)
    assert wrapped["ok"] is False
    assert wrapped["error"]["code"] == "contract_mismatch"
    assert "agent_dispatch" not in wrapped


@pytest.mark.parametrize("failure", ["missing", "corrupt"])
def test_unavailable_result_schema_fails_closed(plugin, monkeypatch, failure):
    original_open = Path.open

    def broken_open(path, *args, **kwargs):
        if path.name == "agent_dispatch_sync_status.result.json":
            if failure == "missing":
                raise FileNotFoundError("result schema unavailable")
            return io.StringIO('{"type":')
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", broken_open)
    plugin.envelopes._sync_result_schema.cache_clear()
    try:
        wrapped = _run(
            plugin,
            "sync status",
            _case("agent_dispatch_sync_status", "sync-status-enabled"),
        )
    finally:
        plugin.envelopes._sync_result_schema.cache_clear()
    assert wrapped["ok"] is False
    assert wrapped["error"]["code"] == "contract_mismatch"
    assert "agent_dispatch" not in wrapped


def test_capability_digest_is_exact_but_adjacent_hash_is_redacted(plugin):
    capability = copy.deepcopy(_case("agent_dispatch_sync_capabilities", "sync-capabilities-valid"))
    wrapped = _run(
        plugin,
        "sync capabilities",
        capability,
        warnings=["Bearer secret-shaped-neighbor"],
    )
    assert wrapped["ok"] is True
    assert wrapped["agent_dispatch"]["result"]["contract_digest"] == capability["contract_digest"]
    assert wrapped["agent_dispatch"]["warnings"] == ["Bearer [redacted]"]


def test_failed_sync_envelope_never_receives_public_identity_exemption(plugin):
    command = "sync status"
    spec = next(
        action
        for tool in plugin.registry.tool_specs()
        for action in tool.actions
        if action.expected_command == command
    )
    secret = "f" * 64
    envelope = {
        "api_version": "agent-dispatch.cli/v1",
        "command": command,
        "ok": False,
        "error": {
            "code": "upstream_error",
            "category": "failure",
            "message": secret,
            "retryable": False,
        },
        "warnings": [secret],
        "trace_id": secret,
    }
    outcome = plugin.runner._Outcome(
        timed_out=False,
        overflowed=False,
        exit_code=1,
        stdout=json.dumps(envelope).encode(),
    )
    trust = plugin.runner.RunnerTrust(Path("/usr/bin/true"), Path("/tmp/config"), 10, 1024)
    wrapped = plugin.runner._map_completed_process(
        "agent_dispatch_sync_status", outcome, spec, trust
    )
    assert wrapped["ok"] is False
    assert wrapped["agent_dispatch"]["error"]["message"] == "[redacted]"
    assert wrapped["agent_dispatch"]["warnings"] == ["[redacted]"]
    assert wrapped["agent_dispatch"]["trace_id"] == "[redacted]"
