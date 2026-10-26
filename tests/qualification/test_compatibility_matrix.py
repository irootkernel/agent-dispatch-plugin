"""Real Hermes action qualification for legacy and exact sync providers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import runner

from _qualification import (
    CONTRACTS,
    CONTRACTS_SYNC,
    ROUTE_ID,
    _disposable_hermes_home,
    _enable_disposable_sync,
    _expected_commands,
    _fake_hermes_target,
    _run,
    _seed_disposable_state,
    _wrapper_validator,
)


def test_compatibility_matrix_qualifies_every_public_action(
    tmp_path, qualified_binary, qualification_runtime
):
    _hermes, venv_python = qualification_runtime
    sandbox = tmp_path / "qualification"
    sandbox.mkdir()

    binary = qualified_binary.path
    sync_provider = qualified_binary.sync_provider
    _fake_hermes_target(sandbox)
    ids = _seed_disposable_state(binary, sandbox)
    sync_group_id = "qual-" + hashlib.sha256(str(sandbox).encode()).hexdigest()[:16]
    home = _disposable_hermes_home(
        sandbox,
        binary,
        sandbox / "config.yaml",
        sync_group_id=sync_group_id if sync_provider else None,
    )

    success_cases = [
        ("agent_dispatch_status", {}),
        ("agent_dispatch_routes", {"action": "list"}),
        ("agent_dispatch_routes", {"action": "show", "route_id": ROUTE_ID}),
        ("agent_dispatch_routes", {"action": "preflight", "route_id": ROUTE_ID}),
        (
            "agent_dispatch_dispatches",
            {"action": "list", "route": ROUTE_ID, "state": "ready", "limit": 10, "offset": 0},
        ),
        ("agent_dispatch_dispatches", {"action": "show", "dispatch_id": ids["dispatch_id"]}),
        (
            "agent_dispatch_receipts",
            {"action": "list", "kind": "work", "route": ROUTE_ID, "limit": 10},
        ),
        ("agent_dispatch_receipts", {"action": "show", "receipt_id": ids["receipt_id"]}),
        ("agent_dispatch_event_show", {"aggregate_id": ids["aggregate_id"]}),
        ("agent_dispatch_quarantine", {"action": "list", "state": "held", "limit": 10}),
        ("agent_dispatch_quarantine", {"action": "show", "quarantine_id": ids["quarantine_id"]}),
        ("agent_dispatch_notifications", {"state": "pending", "sink": "ops-log", "limit": 10}),
        ("agent_dispatch_schedule_inspect", {"route_id": ROUTE_ID}),
        ("agent_dispatch_config", {"action": "show"}),
        ("agent_dispatch_config", {"action": "validate"}),
        ("agent_dispatch_config", {"action": "validate", "probe_targets": True}),
    ]
    success_cases += [
        ("agent_dispatch_doctor", {"probe_targets": True}),
        ("agent_dispatch_doctor", {}),
    ]
    if sync_provider:
        success_cases += [
            ("agent_dispatch_sync_capabilities", {}),
            ("agent_dispatch_sync_status", {}),
            ("agent_dispatch_sync_service_inspect", {}),
        ]

    manifest = sandbox / "manifest.json"
    manifest.write_text(
        json.dumps([{"tool": tool, "args": args} for tool, args in success_cases]),
        encoding="utf-8",
    )
    driver = Path(__file__).resolve().parent / "_hermes_driver.py"
    driver_env = {
        **os.environ,
        "HERMES_HOME": str(home),
        "HERMES_BUNDLED_PLUGINS": str(home / "bundled"),
        "HERMES_ENABLE_PROJECT_PLUGINS": "0",
        "HERMES_QUIET": "1",
    }
    driven = _run(
        [str(venv_python), str(driver), str(manifest)],
        env=driver_env,
        timeout=300,
        cwd=str(sandbox),
    )
    assert driven.returncode == 0, driven.stdout[-2000:] + driven.stderr[-2000:]
    driven_data = json.loads(driven.stdout)
    registered = driven_data["registered"]
    available = driven_data["available"]
    assert len(registered) == 13
    assert len(available) == (13 if sync_provider else 10)
    assert set(available).issubset(registered)
    results = {
        (entry["tool"], json.dumps(entry["args"], sort_keys=True)): json.loads(entry["raw"])
        for entry in driven_data["results"]
    }
    assert len(results) == len(success_cases)

    contracts = CONTRACTS_SYNC if sync_provider else CONTRACTS
    wrapper = _wrapper_validator(contracts)
    commands = _expected_commands(contracts)
    for tool, args in success_cases:
        result = results[(tool, json.dumps(args, sort_keys=True))]
        wrapper.validate(result)
        assert result["ok"] is True, (tool, args, result.get("error"))
        if tool == "agent_dispatch_doctor":
            assert result["exit_code"] == 3, (tool, args)
            findings = result["agent_dispatch"]["result"]["findings"]
            assert any(f["code"] == "watchman_unavailable" for f in findings)
            assert result["agent_dispatch"]["result"]["findings_count"] == len(findings)
        else:
            assert result["exit_code"] == 0, (tool, args)
        assert result["operation"] == tool
        envelope = result["agent_dispatch"]
        assert envelope["ok"] is True, (tool, args)
        assert envelope["api_version"] == "agent-dispatch.cli/v1"
        action_value = args.get("action")
        expected = commands[(tool, action_value if action_value is not None else None)]
        assert envelope["command"] == expected, (tool, args, envelope["command"])

    # The synthetic state is real: the seeded rows surface through the
    # qualified actions, and the absent native schedule is the documented
    # successful inspection (present=false with ok:true). On linux/arm64 the
    # inspect result is the systemd descriptor shape.
    dispatches = results[
        (
            "agent_dispatch_dispatches",
            json.dumps(
                {"action": "list", "route": ROUTE_ID, "state": "ready", "limit": 10, "offset": 0},
                sort_keys=True,
            ),
        )
    ]
    listed = json.dumps(dispatches["agent_dispatch"]["result"])
    assert ids["dispatch_id"] in listed
    receipts = results[
        (
            "agent_dispatch_receipts",
            json.dumps(
                {"action": "list", "kind": "work", "route": ROUTE_ID, "limit": 10}, sort_keys=True
            ),
        )
    ]
    assert json.dumps(receipts["agent_dispatch"]["result"]).count("receipt_id") >= 1
    quarantine = results[
        (
            "agent_dispatch_quarantine",
            json.dumps({"action": "list", "state": "held", "limit": 10}, sort_keys=True),
        )
    ]
    assert ids["quarantine_id"] in json.dumps(quarantine["agent_dispatch"]["result"])
    notifications = results[
        (
            "agent_dispatch_notifications",
            json.dumps({"state": "pending", "sink": "ops-log", "limit": 10}, sort_keys=True),
        )
    ]
    assert json.dumps(notifications["agent_dispatch"]["result"]).count("notification_id") >= 1
    schedule = results[
        ("agent_dispatch_schedule_inspect", json.dumps({"route_id": ROUTE_ID}, sort_keys=True))
    ]
    schedule_result = schedule["agent_dispatch"]["result"]
    assert schedule_result["present"] is False
    if runner._host_platform().startswith("linux/"):
        service = schedule_result["service_path"]
        timer = schedule_result["timer_path"]
        label = schedule_result["label"]
        assert service.endswith(".service")
        assert timer.endswith(".timer")
        assert ".config/systemd/user/" in service
        assert ".config/systemd/user/" in timer
        assert Path(service).stem == Path(timer).stem == label
    if sync_provider:
        status = results[("agent_dispatch_sync_status", "{}")]["agent_dispatch"]["result"]
        assert status["state"] == "disabled"
        assert status["group_id"] == sync_group_id
        assert status["side_effects"] == []
        service = results[("agent_dispatch_sync_service_inspect", "{}")]["agent_dispatch"]["result"]
        assert service["present"] is False and service["loaded"] is False
        assert service["side_effects"] == []


def test_sync_provider_enabled_partial_pair_via_fresh_hermes(
    tmp_path, sync_binary, qualification_runtime
):
    _hermes, venv_python = qualification_runtime
    sandbox = tmp_path / "enabled-pair"
    sandbox.mkdir()
    _fake_hermes_target(sandbox)
    _seed_disposable_state(sync_binary, sandbox)
    config = sandbox / "config.yaml"
    group_id = "qual-" + hashlib.sha256(str(sandbox).encode()).hexdigest()[:16]
    _enable_disposable_sync(config, group_id)
    checked = _run(
        [str(sync_binary), "config", "validate", "--config", str(config), "--output", "json"],
        env={**os.environ, "HOME": str(sandbox / "home")},
    )
    assert checked.returncode == 0, checked.stderr
    home = _disposable_hermes_home(sandbox, sync_binary, config, sync_group_id=group_id)
    cases = [
        {"tool": "agent_dispatch_sync_capabilities", "args": {}},
        {"tool": "agent_dispatch_sync_status", "args": {}},
        {"tool": "agent_dispatch_sync_service_inspect", "args": {}},
    ]
    manifest = sandbox / "manifest.json"
    manifest.write_text(json.dumps(cases), encoding="utf-8")
    driven = _run(
        [str(venv_python), str(Path(__file__).with_name("_hermes_driver.py")), str(manifest)],
        env={
            **os.environ,
            "HERMES_HOME": str(home),
            "HERMES_BUNDLED_PLUGINS": str(home / "bundled"),
            "HERMES_ENABLE_PROJECT_PLUGINS": "0",
            "HERMES_QUIET": "1",
        },
        timeout=180,
        cwd=str(sandbox),
    )
    assert driven.returncode == 0, driven.stdout[-2000:] + driven.stderr[-2000:]
    output = json.loads(driven.stdout)
    assert len(output["registered"]) == len(output["available"]) == 13
    wrapper = _wrapper_validator(CONTRACTS_SYNC)
    for entry in output["results"]:
        result = json.loads(entry["raw"])
        wrapper.validate(result)
        assert result["ok"] is True, result
        assert result["agent_dispatch"]["result"]["side_effects"] == []
    status = json.loads(output["results"][1]["raw"])["agent_dispatch"]["result"]
    assert status["state"] == "active"
    assert status["import_acknowledgement_current"] is False
    assert status["health"]["verification"]["state"] == "unknown"
    assert status["health"]["listener"]["state"] == "unavailable"
    assert len(status["expected_nodes"]) == 2
    assert all(
        status[f"latest_{kind}"]["present"] is False
        for kind in ("publication", "delivery", "import", "verification")
    )


def test_sync_provider_without_group_keeps_ten_available(
    tmp_path, sync_binary, qualification_runtime
):
    _hermes, venv_python = qualification_runtime
    sandbox = tmp_path / "without-group"
    sandbox.mkdir()
    config = sandbox / "config.yaml"
    seed = _run(
        [
            str(sync_binary),
            "init",
            "--resource-root",
            str(sandbox / "resources"),
            "--instance-id",
            "qual-no-group",
            "--state-dir",
            str(sandbox / "state"),
            "--config",
            str(config),
        ],
        env={**os.environ, "HOME": str(sandbox)},
    )
    assert seed.returncode == 0, seed.stderr
    home = _disposable_hermes_home(sandbox, sync_binary, config)
    manifest = sandbox / "manifest.json"
    manifest.write_text("[]", encoding="utf-8")
    driven = _run(
        [str(venv_python), str(Path(__file__).with_name("_hermes_driver.py")), str(manifest)],
        env={
            **os.environ,
            "HERMES_HOME": str(home),
            "HERMES_BUNDLED_PLUGINS": str(home / "bundled"),
            "HERMES_ENABLE_PROJECT_PLUGINS": "0",
            "HERMES_QUIET": "1",
        },
        timeout=120,
        cwd=str(sandbox),
    )
    assert driven.returncode == 0, driven.stdout[-2000:] + driven.stderr[-2000:]
    inventory = json.loads(driven.stdout)
    assert len(inventory["registered"]) == 13
    assert len(inventory["available"]) == 10
    assert all(not name.startswith("agent_dispatch_sync_") for name in inventory["available"])
