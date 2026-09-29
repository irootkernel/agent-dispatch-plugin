"""TASK-024 fixed sync command and fresh admission checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import HermesCtxStub, make_fake_binary


def _provider(
    plugin,
    broken_catalog,
    tmp_path: Path,
    *,
    probe_command="sync capabilities",
    probe_raw=False,
    probe_mode="normal",
    mutate_capability=None,
    mutate_results=None,
):
    log = tmp_path / "invocations.jsonl"
    provider = plugin.registry.load_catalog()["sync_provider"]
    capability = json.loads(
        (
            plugin.registry.CONTRACTS_VERSION_DIR
            / "fixtures/results/agent_dispatch_sync_capabilities.cases.json"
        ).read_text(encoding="utf-8")
    )["cases"][0]["instance"]
    if mutate_capability is not None:
        mutate_capability(capability)
    results = {
        command: json.loads(
            (
                plugin.registry.CONTRACTS_VERSION_DIR / f"fixtures/results/{name}.cases.json"
            ).read_text(encoding="utf-8")
        )["cases"][0]["instance"]
        for command, name in (
            ("sync status", "agent_dispatch_sync_status"),
            ("sync service inspect", "agent_dispatch_sync_service_inspect"),
        )
    }
    if mutate_results is not None:
        mutate_results(results)
    body = f"""#!/usr/bin/env python3
import json
import sys
import time
args = sys.argv[1:]
with open({str(log)!r}, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(args) + "\\n")
if args == ["version", "--json"]:
    print(json.dumps({{"name":"agent-dispatch","version":"v0.2.0"}}))
elif args == ["sync", "capabilities", "--output", "json"]:
    if {probe_mode!r} == "sleep":
        time.sleep(2)
    elif {probe_mode!r} == "overflow":
        print("x" * 1100000)
    elif {probe_mode!r} == "deep":
        print("[" * 1500 + "0" + "]" * 1500)
    elif {probe_raw!r}:
        print("invalid JSON")
    else:
        print(json.dumps({{"api_version":"agent-dispatch.cli/v1","command":{probe_command!r},"ok":True,"result":{capability!r},"warnings":[],"trace_id":""}}))
        if {probe_mode!r} == "exit":
            raise SystemExit(7)
else:
    command = " ".join(args[:3] if args[:3] == ["sync", "service", "inspect"] else args[:2])
    print(json.dumps({{"api_version":"agent-dispatch.cli/v1","command":command,"ok":True,"result":{results!r}[command],"warnings":[],"trace_id":""}}))
"""
    installation = make_fake_binary(tmp_path, version="v0.2.0", body=body)
    host = plugin.runner._host_platform()
    broken_catalog(
        lambda catalog: catalog["sync_provider"]["artifact_sha256"].__setitem__(
            host, installation["digest"]
        )
    )
    config = {**installation["config"], "sync_group_id": "pair"}
    return config, log, provider


def _lines(log: Path):
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def test_registration_availability_and_exact_argv(plugin, broken_catalog, tmp_path):
    config, log, _ = _provider(plugin, broken_catalog, tmp_path)
    specs = {spec.name: spec for spec in plugin.registry.tool_specs()}
    assert len(specs) == 13
    legacy = make_fake_binary(tmp_path / "legacy")
    for settings, count in (
        ({}, 0),
        (legacy["config"], 10),
        (config | {"sync_group_id": None}, 10),
        (config, 13),
    ):
        ctx = HermesCtxStub(settings)
        available = sum(
            plugin.tools.make_availability_check(ctx, spec)() for spec in specs.values()
        )
        assert available == count

    expected = {
        "agent_dispatch_sync_capabilities": ["sync", "capabilities", "--output", "json"],
        "agent_dispatch_sync_status": [
            "sync",
            "status",
            "--group",
            "pair",
            "--output",
            "json",
            "--config",
            config["config_path"],
        ],
        "agent_dispatch_sync_service_inspect": [
            "sync",
            "service",
            "inspect",
            "--group",
            "pair",
            "--output",
            "json",
            "--config",
            config["config_path"],
        ],
    }
    for name, argv in expected.items():
        before = len(_lines(log))
        result = json.loads(plugin.tools.handler_for(specs[name], HermesCtxStub(config))({}))
        assert result["ok"] is True, result
        commands = [line for line in _lines(log)[before:] if line[:1] != ["version"]]
        assert commands == [expected["agent_dispatch_sync_capabilities"], argv]


def test_handler_preserves_validated_status_identity_and_redacts_neighbor(
    plugin, broken_catalog, tmp_path
):
    cases = json.loads(
        (
            plugin.registry.CONTRACTS_VERSION_DIR
            / "fixtures/results/agent_dispatch_sync_status.cases.json"
        ).read_text(encoding="utf-8")
    )["cases"]
    public_status = next(
        case["instance"]
        for case in cases
        if case["id"] == "sync-status-public-commit-with-secret-neighbor"
    )
    config, _, _ = _provider(
        plugin,
        broken_catalog,
        tmp_path,
        mutate_results=lambda results: results.__setitem__("sync status", public_status),
    )
    spec = next(s for s in plugin.registry.tool_specs() if s.name == "agent_dispatch_sync_status")
    wrapped = json.loads(plugin.tools.handler_for(spec, HermesCtxStub(config))({}))
    assert wrapped["ok"] is True
    shown = wrapped["agent_dispatch"]["result"]
    assert shown["config_revision"] == public_status["config_revision"]
    assert (
        shown["latest_verification"]["target_commit"]
        == public_status["latest_verification"]["target_commit"]
    )
    assert shown["latest_verification"]["reason"] == "Bearer [redacted]"


@pytest.mark.parametrize("command", ["sync status", "sync service inspect"])
def test_handler_discards_invalid_sync_success(plugin, broken_catalog, tmp_path, command):
    def corrupt(results):
        results[command]["side_effects"] = ["write"]

    config, log, _ = _provider(plugin, broken_catalog, tmp_path, mutate_results=corrupt)
    name = "agent_dispatch_" + command.replace(" ", "_")
    spec = next(s for s in plugin.registry.tool_specs() if s.name == name)
    wrapped = json.loads(plugin.tools.handler_for(spec, HermesCtxStub(config))({}))
    assert wrapped["ok"] is False
    assert wrapped["error"]["code"] == "contract_mismatch"
    assert "agent_dispatch" not in wrapped
    assert len(_lines(log)) == 3  # version, fresh capability probe, requested read


@pytest.mark.parametrize("group", [None, "", "-pair", "Pair", "pair/other", "x" * 64])
def test_invalid_group_denies_command(plugin, broken_catalog, tmp_path, group):
    config, log, _ = _provider(plugin, broken_catalog, tmp_path)
    config["sync_group_id"] = group
    spec = next(s for s in plugin.registry.tool_specs() if s.name == "agent_dispatch_sync_status")
    result = json.loads(plugin.tools.handler_for(spec, HermesCtxStub(config))({}))
    assert result["ok"] is False
    assert _lines(log) == []


@pytest.mark.parametrize(
    ("probe_command", "probe_raw"),
    [("status", False), ("sync capabilities", True)],
)
def test_probe_failure_never_spawns_requested_command(
    plugin, broken_catalog, tmp_path, probe_command, probe_raw
):
    config, log, _ = _provider(
        plugin, broken_catalog, tmp_path, probe_command=probe_command, probe_raw=probe_raw
    )
    spec = next(
        s for s in plugin.registry.tool_specs() if s.name == "agent_dispatch_sync_service_inspect"
    )
    result = json.loads(plugin.tools.handler_for(spec, HermesCtxStub(config))({}))
    assert result["error"]["code"] == "contract_mismatch"
    assert not any(line[:3] == ["sync", "service", "inspect"] for line in _lines(log))


def test_unallowlisted_v020_binary_is_unavailable(plugin, tmp_path):
    installation = make_fake_binary(tmp_path, version="v0.2.0")
    assert plugin.runner.probe_availability(installation["config"]) is False
    with pytest.raises(plugin.runner.TrustFailure) as error:
        plugin.runner.resolve_trust(installation["config"])
    assert error.value.code == "binary_unavailable"


def test_legacy_binary_with_group_denies_sync_without_spawning_command(
    plugin, tmp_path, monkeypatch
):
    installation = make_fake_binary(tmp_path)
    config = installation["config"] | {"sync_group_id": "pair"}
    specs = {spec.name: spec for spec in plugin.registry.tool_specs()}
    ctx = HermesCtxStub(config)
    monkeypatch.setattr(
        plugin.runner,
        "_execute_bounded",
        lambda *_args: pytest.fail("legacy core must not spawn a sync command"),
    )
    assert sum(plugin.tools.make_availability_check(ctx, spec)() for spec in specs.values()) == 10
    result = json.loads(plugin.tools.handler_for(specs["agent_dispatch_sync_status"], ctx)({}))
    assert result["error"]["code"] == "unsupported_agent_dispatch_version"


@pytest.mark.parametrize("probe_mode", ["exit", "sleep", "overflow", "deep"])
def test_bounded_probe_failure_denies_command(plugin, broken_catalog, tmp_path, probe_mode):
    config, log, _ = _provider(plugin, broken_catalog, tmp_path, probe_mode=probe_mode)
    if probe_mode == "sleep":
        config["timeout_seconds"] = 1
    spec = next(s for s in plugin.registry.tool_specs() if s.name == "agent_dispatch_sync_status")
    result = json.loads(plugin.tools.handler_for(spec, HermesCtxStub(config))({}))
    assert result["error"]["code"] == "contract_mismatch"
    assert not any(line[:2] == ["sync", "status"] for line in _lines(log))


@pytest.mark.parametrize("mutation", ["missing", "false", "malformed", "effects"])
def test_invalid_capability_denies_command(plugin, broken_catalog, tmp_path, mutation):
    def change(result):
        if mutation == "missing":
            del result["capabilities"]["status_read"]
        elif mutation == "false":
            result["capabilities"]["service_inspect"] = False
        elif mutation == "malformed":
            result["capabilities"]["publication"] = "yes"
        else:
            result["side_effects"] = ["mutation"]

    config, log, _ = _provider(plugin, broken_catalog, tmp_path, mutate_capability=change)
    spec = next(s for s in plugin.registry.tool_specs() if s.name == "agent_dispatch_sync_status")
    result = json.loads(plugin.tools.handler_for(spec, HermesCtxStub(config))({}))
    assert result["error"]["code"] == "contract_mismatch"
    assert not any(line[:2] == ["sync", "status"] for line in _lines(log))


def test_capability_drift_after_cached_visibility_denies_direct_dispatch(
    plugin, broken_catalog, tmp_path
):
    config, log, _ = _provider(plugin, broken_catalog, tmp_path)
    spec = next(s for s in plugin.registry.tool_specs() if s.name == "agent_dispatch_sync_status")
    ctx = HermesCtxStub(config)
    assert plugin.tools.make_availability_check(ctx, spec)() is True
    # A changed expected digest makes the next fresh probe fail, even when Hermes
    # previously cached the tool as visible and dispatches the handler directly.
    plugin.registry.load_catalog()["sync_provider"]["contract_digest"] = "sha256:" + "0" * 64
    result = json.loads(plugin.tools.handler_for(spec, ctx)({}))
    assert result["ok"] is False
    assert result["error"]["code"] == "contract_mismatch"
    assert not any(line[:2] == ["sync", "status"] for line in _lines(log))
