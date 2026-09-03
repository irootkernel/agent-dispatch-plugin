"""Integration tests: cross-module registration and the deterministic gates."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from conftest import load_plugin

ROOT = Path(__file__).resolve().parent.parent.parent


class RecordingContext:
    def __init__(self, settings: dict | None = None) -> None:
        self.registered: dict[str, dict] = {}
        self._settings: dict = dict(settings or {})

    def get_config(self, key: str, default=None):
        return self._settings.get(key, default)

    def register_tool(self, **kwargs) -> None:
        name = kwargs["name"]
        assert name not in self.registered, f"{name} registered twice"
        self.registered[name] = kwargs


def test_registration_through_the_hermes_style_loader_registers_ten_tools():
    module = load_plugin("hermes_plugins.agent_dispatch_plugin_integration")
    ctx = RecordingContext()
    module.register(ctx)

    roster = list(module.registry.expected_inventory())
    assert sorted(ctx.registered) == sorted(roster)
    assert len(roster) == 10
    for name, kwargs in ctx.registered.items():
        assert kwargs["toolset"] == "agent_dispatch"
        assert kwargs["schema"].get("additionalProperties") is False
        assert callable(kwargs["handler"])
        assert callable(kwargs["check_fn"])
        assert kwargs["description"].strip()
        assert not kwargs.get("override")


def test_registered_availability_and_handlers_route_through_the_trust_gate(tmp_path):
    """Registration wires every tool to the shared runner trust gate."""
    from conftest import make_fake_binary

    module = load_plugin("hermes_plugins.agent_dispatch_plugin_trust")
    installation = make_fake_binary(tmp_path)
    hidden_ctx = RecordingContext()
    module.register(hidden_ctx)
    assert all(kwargs["check_fn"]() is False for kwargs in hidden_ctx.registered.values())
    for name, kwargs in hidden_ctx.registered.items():
        spec = next(s for s in module.registry.tool_specs() if s.name == name)
        action = spec.actions[0]
        params = {"action": action.input_action_value} if action.input_action_value else {}
        result = kwargs["handler"](**params)
        assert result["error"]["code"] == "binary_unavailable", name

    exposed_ctx = RecordingContext(installation["config"])
    module.register(exposed_ctx)
    assert all(kwargs["check_fn"]() is True for kwargs in exposed_ctx.registered.values())


def test_contracts_validation_gate_runs_green():
    result = subprocess.run(
        ["uv", "run", "contracts/validate.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "contracts validation passed" in result.stdout


def test_manifest_parity_gate_runs_green():
    result = subprocess.run(
        ["uv", "run", "scripts/manifest_parity.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "manifest/registry parity passed" in result.stdout


def test_register_registers_nothing_partial_when_a_schema_is_unreadable(
    fresh_plugin_with_unreadable_schemas,
):
    """The registers-nothing-partial invariant holds through register() itself."""
    module = fresh_plugin_with_unreadable_schemas
    ctx = RecordingContext()
    with pytest.raises(module.registry.ContractSourceError):
        module.register(ctx)
    assert ctx.registered == {}, "a failed registration must not stay partial"
