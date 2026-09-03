"""Unit tests for the bounded process-group runner (TASK-005).

Every test drives the full boundary — trust gate, fixed argv, neutral
environment, concurrent bounded draining, deadline, and the
TERM-then-force-kill ladder — against deterministic fake Agent Dispatch
executables whose scripted behavior lives in the trusted config file.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from conftest import HermesCtxStub, make_fake_binary


@pytest.fixture
def runner(plugin):
    return plugin.runner


def _tool(plugin, name):
    for spec in plugin.registry.tool_specs():
        if spec.name == name:
            return spec
    raise LookupError(name)


def _action(plugin, name, action_id):
    tool = _tool(plugin, name)
    for action in tool.actions:
        if action.action_id == action_id:
            return action
    raise LookupError(action_id)


def _run(plugin, runner, name, action_id, installation, params=None):
    action = _action(plugin, name, action_id)
    config = dict(installation["config"])
    config["timeout_seconds"] = config.get("timeout_seconds", 10)
    return runner.run_inspection(action, name, params or {}, config)


def test_fixed_argv_never_uses_a_shell(plugin, runner, fake_agent_dispatch):
    """The child argv is exactly the pinned binary, the registered template,
    the bound values, the frozen suffix, and the trusted --config flag."""
    result = _run(
        plugin,
        runner,
        "agent_dispatch_quarantine",
        "list",
        fake_agent_dispatch,
        {"state": "held", "limit": 5},
    )
    assert result["ok"] is True
    argv = result["agent_dispatch"]["result"]["argv"]
    assert argv[0] == fake_agent_dispatch["config"]["binary_path"]
    assert argv[1:3] == ["quarantine", "list"]
    assert "--state" in argv and argv[argv.index("--state") + 1] == "held"
    assert "--limit" in argv and argv[argv.index("--limit") + 1] == "5"
    assert argv[-4:-2] == ["--output", "json"]
    assert argv[-2:] == ["--config", fake_agent_dispatch["config"]["config_path"]]
    assert all(token != "-c" for token in argv)


def test_positional_binding_lands_in_the_registered_slot(plugin, runner, fake_agent_dispatch):
    result = _run(
        plugin,
        runner,
        "agent_dispatch_dispatches",
        "show",
        fake_agent_dispatch,
        {"dispatch_id": "disp-abc123"},
    )
    argv = result["agent_dispatch"]["result"]["argv"]
    assert argv[1:3] == ["dispatches", "show"]
    assert argv[3] == "disp-abc123"


# The macOS system python3 shim (Xcode Command Line Tools) injects these
# into every child it execs; they are an artifact of the fake's shebang,
# not a leak from the Hermes or pytest environment.
_PYTHON3_SHIM_INJECTED = {
    "CPATH",
    "LC_CTYPE",
    "LIBRARY_PATH",
    "MANPATH",
    "SDKROOT",
    "__CF_USER_TEXT_ENCODING",
}


def _raw_echo(plugin, runner, installation):
    """Run the echo fake through the executor and return its parsed result."""
    trust = runner.resolve_trust(installation["config"])
    argv = (
        os.fspath(trust.binary_path),
        "status",
        "--output",
        "json",
        "--config",
        os.fspath(trust.config_path),
    )
    outcome = runner._execute_bounded(argv, trust)
    assert outcome.timed_out is False and outcome.overflowed is False
    return json.loads(outcome.stdout)["result"]


def test_environment_is_the_fixed_minimal_allowlist(plugin, runner, fake_agent_dispatch):
    raw = _raw_echo(plugin, runner, fake_agent_dispatch)
    child_env = raw["env"]
    leaked = {
        key: value
        for key, value in child_env.items()
        if key not in _PYTHON3_SHIM_INJECTED
        and (key, value) not in runner.MINIMAL_ENVIRONMENT.items()
    }
    assert leaked == {}
    assert set(child_env) - set(_PYTHON3_SHIM_INJECTED) == set(runner.MINIMAL_ENVIRONMENT)


def test_working_directory_is_neutral_and_trusted(plugin, runner, fake_agent_dispatch):
    raw = _raw_echo(plugin, runner, fake_agent_dispatch)
    assert Path(raw["cwd"]) == runner.NEUTRAL_CWD


def test_the_public_wrapper_redacts_echoed_absolute_paths(plugin, runner, fake_agent_dispatch):
    """Defense in depth: the echoed environment and cwd never survive the
    output boundary verbatim."""
    result = _run(plugin, runner, "agent_dispatch_status", "inspect", fake_agent_dispatch)
    dumped = json.dumps(result)
    assert str(runner.NEUTRAL_CWD) not in dumped
    assert "/tmp" not in dumped


def test_model_inputs_never_reach_execution_settings(plugin, runner, fake_agent_dispatch):
    """Forbidden properties are ordinary ignored params; only registered
    bindings and values can influence the argv."""
    result = _run(
        plugin,
        runner,
        "agent_dispatch_routes",
        "list",
        fake_agent_dispatch,
        {"cwd": "/tmp", "env": {"x": "1"}, "flags": ["--evil"], "binary": "/bin/sh"},
    )
    argv = result["agent_dispatch"]["result"]["argv"]
    assert "--evil" not in argv
    assert "/bin/sh" not in argv
    assert "cwd" not in argv and "env" not in argv


def test_deadline_returns_timeout_and_discards_output(plugin, runner, tmp_path):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "sleep", "seconds": 30, "prefix": '{"partial":'}
    )
    config = {**installation["config"], "timeout_seconds": 1}
    action = _action(plugin, "agent_dispatch_status", "inspect")
    started = time.monotonic()
    result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
    elapsed = time.monotonic() - started
    assert elapsed < 5
    assert result["ok"] is False
    assert result["exit_code"] == -1
    assert result["error"]["code"] == "timeout"
    assert result["diagnostics"] == [
        "deadline of 1 seconds reached; terminated the process group and "
        "discarded all captured output"
    ]
    assert "agent_dispatch" not in result
    assert "partial" not in json.dumps(result)


def test_stdout_overflow_returns_output_too_large(plugin, runner, tmp_path):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "stdout_overflow", "bytes": 2 * 1048576}
    )
    config = {**installation["config"], "timeout_seconds": 10}
    action = _action(plugin, "agent_dispatch_status", "inspect")
    started = time.monotonic()
    result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
    elapsed = time.monotonic() - started
    assert elapsed < 10
    assert result["error"]["code"] == "output_too_large"
    assert "xxxx" not in json.dumps(result)
    assert "agent_dispatch" not in result


def test_stderr_overflow_returns_output_too_large(plugin, runner, tmp_path):
    installation = make_fake_binary(tmp_path, behavior={"kind": "stderr_overflow", "bytes": 65537})
    config = {**installation["config"], "timeout_seconds": 10}
    action = _action(plugin, "agent_dispatch_status", "inspect")
    result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
    assert result["error"]["code"] == "output_too_large"


def test_combined_overflow_below_per_stream_caps_returns_output_too_large(plugin, runner, tmp_path):
    installation = make_fake_binary(
        tmp_path,
        behavior={
            "kind": "combined_overflow",
            "stdout_bytes": 1000000,
            "stderr_bytes": 50000,
        },
    )
    config = {**installation["config"], "timeout_seconds": 10}
    action = _action(plugin, "agent_dispatch_status", "inspect")
    result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
    assert result["error"]["code"] == "output_too_large"


def test_configured_ceiling_tightens_the_stream_cap(plugin, runner, tmp_path):
    installation = make_fake_binary(tmp_path, behavior={"kind": "stdout_overflow", "bytes": 8192})
    config = {**installation["config"], "timeout_seconds": 10, "max_output_bytes": 4096}
    action = _action(plugin, "agent_dispatch_status", "inspect")
    result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
    assert result["error"]["code"] == "output_too_large"


def test_stdout_exactly_at_the_ceiling_is_not_an_overflow(plugin, runner, tmp_path):
    """The frozen ceilings are inclusive: exactly 1048576 stdout bytes pass
    the ceiling check (the flood is then rejected as malformed output, not
    as an overflow), while one byte more is output_too_large."""
    for name, extra, expected in (
        ("at-cap", 0, "malformed_json"),
        ("over-cap", 1, "output_too_large"),
    ):
        installation = make_fake_binary(
            tmp_path / name, behavior={"kind": "flood_exit", "bytes": 1048576 + extra}
        )
        config = {**installation["config"], "timeout_seconds": 10}
        action = _action(plugin, "agent_dispatch_status", "inspect")
        result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
        assert result["error"]["code"] == expected, name


def test_stderr_exactly_at_the_ceiling_is_not_an_overflow(plugin, runner, tmp_path):
    """Exactly 65536 stderr bytes (one line of 65535 plus its newline) stay
    inside the frozen per-stream ceiling; 65537 bytes overflow it."""
    for name, line_length, expected in (
        ("at-cap", 65535, "malformed_json"),
        ("over-cap", 65536, "output_too_large"),
    ):
        installation = make_fake_binary(
            tmp_path / name,
            behavior={
                "kind": "raw",
                "stdout": "not json\n",
                "stderr_lines": ["y" * line_length],
                "exit": 0,
            },
        )
        config = {**installation["config"], "timeout_seconds": 10}
        action = _action(plugin, "agent_dispatch_status", "inspect")
        result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
        assert result["error"]["code"] == expected, name


def test_combined_streams_exactly_at_the_ceiling_is_not_an_overflow(plugin, runner, tmp_path):
    """stdout 988576 plus stderr 60000 is exactly the 1048576 combined
    ceiling and stays inside; one more stdout byte overflows the combined
    bound while each stream stays under its own cap."""
    for name, stdout_bytes, expected in (
        ("at-cap", 988576, "malformed_json"),
        ("over-cap", 988577, "output_too_large"),
    ):
        installation = make_fake_binary(
            tmp_path / name,
            behavior={
                "kind": "raw",
                "stdout": "x" * stdout_bytes,
                "stderr_lines": ["y" * 59999],
                "exit": 0,
            },
        )
        config = {**installation["config"], "timeout_seconds": 10}
        action = _action(plugin, "agent_dispatch_status", "inspect")
        result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
        assert result["error"]["code"] == expected, name


def test_term_to_force_kill_kills_the_whole_process_group(plugin, runner, tmp_path):
    child_pid_file = tmp_path / "child.pid"
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "trap", "child_pid_file": str(child_pid_file)}
    )
    config = {**installation["config"], "timeout_seconds": 1}
    action = _action(plugin, "agent_dispatch_status", "inspect")
    started = time.monotonic()
    result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
    elapsed = time.monotonic() - started
    # TERM is ignored by the fake, so the two-second grace must expire before
    # the force kill: bounded by deadline + grace + scheduler slack.
    assert elapsed >= 3.0 and elapsed < 10.0
    assert result["error"]["code"] == "timeout"
    child_pid = int(child_pid_file.read_text(encoding="utf-8"))
    for _ in range(60):
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail("a child of the terminated process group is still present")


def test_no_retry_under_every_failure_mode(plugin, runner, tmp_path):
    """One call is one process across failure modes: a timed-out, a
    malformed-output, a domain-rejection, and a successful call each invoke
    the executable exactly once (the version probe reads no behavior config
    and never counts)."""
    count_file = tmp_path / "count.log"
    counter = {"count_file": str(count_file)}
    status = _action(plugin, "agent_dispatch_status", "inspect")

    def install(name, behavior):
        installation = make_fake_binary(tmp_path / name, behavior={**behavior, **counter})
        return {**installation["config"], "timeout_seconds": 10}

    sleepy = install("sleepy", {"kind": "sleep", "seconds": 30})
    sleepy["timeout_seconds"] = 2  # startup under load stays inside the window
    garbage = install("garbage", {"kind": "raw", "stdout": "not json\n"})
    rejection = install("reject", {"kind": "reject", "exit": 3})
    echo = install("echo", {})

    results = [
        runner.run_inspection(status, "agent_dispatch_status", {}, sleepy),
        runner.run_inspection(status, "agent_dispatch_status", {}, garbage),
        runner.run_inspection(status, "agent_dispatch_status", {}, rejection),
        runner.run_inspection(status, "agent_dispatch_status", {}, echo),
    ]
    assert results[0]["error"]["code"] == "timeout"
    assert results[1]["error"]["code"] == "malformed_json"
    assert results[2]["agent_dispatch"]["error"]["code"] == "config_invalid"
    assert results[3]["ok"] is True
    assert count_file.read_text(encoding="utf-8").count("invoked") == 4


def test_domain_rejection_carries_the_envelope_and_exit_status(plugin, runner, tmp_path):
    installation = make_fake_binary(tmp_path, behavior={"kind": "reject", "exit": 3})
    config = {**installation["config"], "timeout_seconds": 10}
    action = _action(plugin, "agent_dispatch_routes", "show")
    result = runner.run_inspection(action, "agent_dispatch_routes", {"route_id": "missing"}, config)
    assert result["ok"] is False
    assert result["exit_code"] == 3
    assert result["agent_dispatch"]["ok"] is False
    assert result["agent_dispatch"]["error"]["code"] == "config_invalid"
    assert "error" not in result  # the envelope is the sole carrier


def test_malformed_stdout_fails_closed(plugin, runner, tmp_path):
    installation = make_fake_binary(tmp_path, behavior={"kind": "garbage"})
    config = {**installation["config"], "timeout_seconds": 10}
    action = _action(plugin, "agent_dispatch_status", "inspect")
    result = runner.run_inspection(action, "agent_dispatch_status", {}, config)
    assert result["error"]["code"] == "malformed_json"
    assert "this is not json" not in json.dumps(result)


def test_spawn_failure_fails_closed_without_output(
    plugin, runner, fake_agent_dispatch, monkeypatch
):
    def refused(*args, **kwargs):
        raise OSError("spawn refused")

    monkeypatch.setattr(runner, "_execute_bounded", refused)
    action = _action(plugin, "agent_dispatch_status", "inspect")
    result = runner.run_inspection(
        action, "agent_dispatch_status", {}, fake_agent_dispatch["config"]
    )
    assert result["error"]["code"] == "execution_failed"
    assert result["exit_code"] == -1


def test_handler_routes_one_action_end_to_end(plugin, fake_agent_dispatch):
    ctx = HermesCtxStub(fake_agent_dispatch["config"])
    spec = _tool(plugin, "agent_dispatch_schedule_inspect")
    result = plugin.tools.handler_for(spec, ctx)(action="inspect", route_id="wiki-maintenance")
    assert result["ok"] is True
    argv = result["agent_dispatch"]["result"]["argv"]
    assert argv[1:5] == ["schedule", "inspect", "--route", "wiki-maintenance"]
    assert argv[5:7] == ["--platform", "launchd"]


def test_handler_rejects_unregistered_actions(plugin, fake_agent_dispatch):
    ctx = HermesCtxStub(fake_agent_dispatch["config"])
    spec = _tool(plugin, "agent_dispatch_routes")
    result = plugin.tools.handler_for(spec, ctx)(action="destroy")
    assert result["error"]["code"] == "invalid_argument"
    assert result["exit_code"] == -1


def test_single_action_tool_resolves_without_an_action_parameter(plugin, fake_agent_dispatch):
    ctx = HermesCtxStub(fake_agent_dispatch["config"])
    spec = _tool(plugin, "agent_dispatch_status")
    result = plugin.tools.handler_for(spec, ctx)()
    assert result["ok"] is True
    assert result["operation"] == "agent_dispatch_status"
