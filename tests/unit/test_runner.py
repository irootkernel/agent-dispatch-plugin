"""Unit tests for the runner trust gate (TASK-004).

Every positive path runs against a deterministic fake Agent Dispatch
executable; every negative path proves one closed rejection. The tests
derive the expected bounds from the frozen catalog instead of restating
PRD numbers.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from conftest import HermesCtxStub, make_fake_binary


@pytest.fixture
def runner(plugin):
    return plugin.runner


def _expect_failure(runner, config, code):
    with pytest.raises(runner.TrustFailure) as excinfo:
        runner.resolve_trust(config)
    assert excinfo.value.code == code
    return excinfo.value


def test_unresolved_config_fails_closed_with_binary_unavailable(runner):
    failure = _expect_failure(runner, {}, runner.BINARY_UNAVAILABLE)
    assert failure.message == runner.NOT_CONFIGURED_MESSAGE
    assert runner.probe_availability({}) is False


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"binary_path": 123}, "adapter_usage_error"),
        ({"binary_path": ""}, "adapter_usage_error"),
        ({"binary_sha256": "ZZ" * 32}, "adapter_usage_error"),
        (
            {"binary_sha256": "ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789"},
            "adapter_usage_error",
        ),
        ({"timeout_seconds": 0}, "adapter_usage_error"),
        ({"timeout_seconds": 301}, "adapter_usage_error"),
        ({"timeout_seconds": True}, "adapter_usage_error"),
        ({"timeout_seconds": "30"}, "adapter_usage_error"),
        ({"max_output_bytes": 1048577}, "adapter_usage_error"),
    ],
)
def test_structurally_invalid_settings_reject_as_adapter_usage(
    runner, fake_agent_dispatch, overrides, code
):
    config = {**fake_agent_dispatch["config"], **overrides}
    assert runner.probe_availability(config) is False
    _expect_failure(runner, config, code)


def test_relative_paths_reject_as_adapter_usage(runner, fake_agent_dispatch):
    config = dict(fake_agent_dispatch["config"])
    config["binary_path"] = "relative/agent-dispatch"
    _expect_failure(runner, config, runner.ADAPTER_USAGE_ERROR)


def test_symlinked_binary_rejects(runner, fake_agent_dispatch, tmp_path):
    link = tmp_path / "agent-dispatch-link"
    os.symlink(fake_agent_dispatch["binary"], link)
    config = dict(fake_agent_dispatch["config"])
    config["binary_path"] = str(link)
    _expect_failure(runner, config, runner.BINARY_UNAVAILABLE)


def test_symlinked_parent_directory_rejects(runner, tmp_path):
    real_parent = tmp_path / "real"
    linked_parent = tmp_path / "linked"
    real_parent.mkdir()
    os.symlink(real_parent, linked_parent)
    installation = make_fake_binary(real_parent)
    config = dict(installation["config"])
    config["binary_path"] = str(linked_parent / "trusted" / "agent-dispatch")
    _expect_failure(runner, config, runner.BINARY_UNAVAILABLE)


def test_missing_or_nonexecutable_binary_rejects(runner, fake_agent_dispatch):
    config = dict(fake_agent_dispatch["config"])
    config["binary_path"] = str(fake_agent_dispatch["binary"].parent / "absent")
    _expect_failure(runner, config, runner.BINARY_UNAVAILABLE)

    config = dict(fake_agent_dispatch["config"])
    fake_agent_dispatch["binary"].chmod(0o644)
    try:
        _expect_failure(runner, config, runner.BINARY_UNAVAILABLE)
    finally:
        fake_agent_dispatch["binary"].chmod(0o755)


def test_missing_trusted_config_file_rejects(runner, fake_agent_dispatch):
    config = dict(fake_agent_dispatch["config"])
    config["config_path"] = str(fake_agent_dispatch["config_file"].parent / "absent.json")
    _expect_failure(runner, config, runner.BINARY_UNAVAILABLE)


def test_digest_mismatch_rejects(runner, fake_agent_dispatch):
    config = dict(fake_agent_dispatch["config"])
    other = hashlib.sha256(b"not this binary").hexdigest()
    config["binary_sha256"] = other
    _expect_failure(runner, config, runner.BINARY_UNAVAILABLE)


def test_platform_gate_rejects_unsupported_hosts(runner, fake_agent_dispatch, monkeypatch):
    monkeypatch.setattr(runner.sys, "platform", "linux")
    _expect_failure(runner, fake_agent_dispatch["config"], runner.BINARY_UNAVAILABLE)


def test_in_range_version_resolves_trust(runner, fake_agent_dispatch):
    trust = runner.resolve_trust(fake_agent_dispatch["config"])
    assert trust.binary_path == Path(fake_agent_dispatch["config"]["binary_path"])
    assert trust.timeout_seconds == 30
    assert trust.max_output_bytes == 1048576
    assert runner.probe_availability(fake_agent_dispatch["config"]) is True


@pytest.mark.parametrize("version", ["v0.1.5", "v0.2.0", "v1.0.0"])
def test_out_of_range_versions_reject(runner, tmp_path, version):
    installation = make_fake_binary(tmp_path, version=version)
    _expect_failure(runner, installation["config"], runner.UNSUPPORTED_AGENT_DISPATCH_VERSION)


@pytest.mark.parametrize(
    "body",
    [
        "#!/bin/sh\nprintf '%s' 'not json'\n",
        '#!/bin/sh\nprintf \'%s\' \'{"name":"other","version":"v0.1.6"}\'\n',
        '#!/bin/sh\nprintf \'%s\' \'{"name":"agent-dispatch","version":"x"}\'\n',
        "#!/bin/sh\nexit 3\n",
        "#!/bin/sh\nsleep 5\n",
    ],
    ids=["garbage", "wrong-name", "unparseable-version", "failure-exit", "no-answer"],
)
def test_unanswerable_version_probes_fail_closed(runner, tmp_path, body):
    installation = make_fake_binary(tmp_path, body=body)
    config = dict(installation["config"])
    config["timeout_seconds"] = 1
    if body == "#!/bin/sh\nsleep 5\n":
        _expect_failure(runner, config, runner.BINARY_UNAVAILABLE)
    elif body == "#!/bin/sh\nexit 3\n":
        _expect_failure(runner, config, runner.UNSUPPORTED_AGENT_DISPATCH_VERSION)
    else:
        _expect_failure(runner, config, runner.UNSUPPORTED_AGENT_DISPATCH_VERSION)


def test_configured_bounds_are_honored(runner, fake_agent_dispatch):
    config = {**fake_agent_dispatch["config"], "timeout_seconds": 5, "max_output_bytes": 4096}
    trust = runner.resolve_trust(config)
    assert trust.timeout_seconds == 5
    assert trust.max_output_bytes == 4096


def test_trust_failure_result_is_closed(runner):
    failure = runner.TrustFailure(runner.BINARY_UNAVAILABLE, "bounded message")
    result = runner.trust_failure_result("agent_dispatch_status", failure)
    assert result["schema_version"] == runner.RESULT_SCHEMA_VERSION
    assert result["ok"] is False
    assert result["operation"] == "agent_dispatch_status"
    assert result["exit_code"] == -1
    assert result["error"] == {
        "code": "binary_unavailable",
        "message": "bounded message",
        "retryable": False,
    }
    assert result["diagnostics"] == []


def test_availability_probe_through_the_tools_layer(plugin, fake_agent_dispatch):
    """The availability check exposes the toolset exactly when trust passes."""
    hidden = plugin.tools.make_availability_check(HermesCtxStub())
    assert hidden() is False

    settings = dict(fake_agent_dispatch["config"])
    settings["timeout_seconds"] = 5
    exposed = plugin.tools.make_availability_check(HermesCtxStub(settings))
    assert exposed() is True


def test_handler_fails_closed_without_configuration(plugin, unconfigured_ctx):
    spec = plugin.registry.tool_specs()[0]
    result = plugin.tools.handler_for(spec, unconfigured_ctx)(action="list")
    assert result["error"]["code"] == "binary_unavailable"
    assert result["error"]["message"] == plugin.runner.NOT_CONFIGURED_MESSAGE


def test_handler_fails_closed_after_a_passing_trust_gate(plugin, fake_agent_dispatch):
    """A trusted configuration still creates no process until execution lands."""
    ctx = HermesCtxStub(fake_agent_dispatch["config"])
    spec = plugin.registry.tool_specs()[0]
    result = plugin.tools.handler_for(spec, ctx)(action="list")
    assert result["ok"] is False
    assert result["error"]["code"] == plugin.runner.EXECUTION_FAILED
    assert result["exit_code"] == -1


def test_runner_config_reads_only_the_five_settings(plugin):
    ctx = HermesCtxStub({"binary_path": "/bin/x", "unrelated": "value"})
    resolved = plugin.tools.runner_config(ctx)
    assert resolved == {
        "binary_path": "/bin/x",
        "binary_sha256": None,
        "config_path": None,
        "timeout_seconds": None,
        "max_output_bytes": None,
    }


def test_runner_config_fails_closed_on_a_broken_config_system(plugin):
    class BrokenCtx:
        def get_config(self, key, default=None):
            raise RuntimeError("config system unavailable")

    assert plugin.tools.runner_config(BrokenCtx()) == {}
