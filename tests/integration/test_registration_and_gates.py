"""Integration tests: cross-module registration and the deterministic gates."""

from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import load_plugin

ROOT = Path(__file__).resolve().parent.parent.parent


class RecordingContext:
    def __init__(self) -> None:
        self.registered: dict[str, dict] = {}

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
