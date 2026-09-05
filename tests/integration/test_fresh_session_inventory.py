"""Integration test: fresh-session inventory parity and the smoke transcript.

TASK-010. A brand-new interpreter process — no cached imports from the
test session — loads the plugin exactly the way the Hermes directory
loader does, registers it against a recording context, and prints the
inventory plus one smoke inspection result as JSON. The parent test
asserts the fresh session registers exactly the ten catalog tools in
catalog order and that the smoke inspection completes through the full
trust-gated boundary. The deterministic transcript is the printed JSON;
the e2e Plugin Doctor check independently proves the same inventory over
the public CLI.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import make_fake_binary

ROOT = Path(__file__).resolve().parent.parent.parent

# Executed in a fresh interpreter. The loader block mirrors the Hermes
# directory loader (spec_from_file_location over the repo root) so nothing
# is inherited from the pytest session's module cache.
FRESH_SESSION_SCRIPT = r"""
import importlib.util
import json
import sys
import types

root = sys.argv[1]
binary_path, digest, config_path = sys.argv[2], sys.argv[3], sys.argv[4]

module_name = "hermes_plugins.agent_dispatch_plugin"
ns = types.ModuleType("hermes_plugins")
ns.__path__ = []
ns.__package__ = "hermes_plugins"
sys.modules["hermes_plugins"] = ns
spec = importlib.util.spec_from_file_location(
    module_name, root + "/__init__.py", submodule_search_locations=[root]
)
module = importlib.util.module_from_spec(spec)
module.__package__ = module_name
module.__path__ = [root]
sys.modules[module_name] = module
spec.loader.exec_module(module)


class RecordingContext:
    def __init__(self):
        self.registered = {}

    def register_tool(self, **kwargs):
        self.registered[kwargs["name"]] = kwargs

    def get_config(self, key, default=None):
        settings = {
            "binary_path": binary_path,
            "binary_sha256": digest,
            "config_path": config_path,
        }
        return settings.get(key, default)


ctx = RecordingContext()
module.register(ctx)

status = ctx.registered["agent_dispatch_status"]
smoke = json.loads(status["handler"]({}))
transcript = {
    "inventory": list(module.registry.expected_inventory()),
    "registered": list(ctx.registered),
    "smoke_ok": smoke["ok"],
    "smoke_operation": smoke["operation"],
    "smoke_exit_code": smoke["exit_code"],
    "smoke_command": smoke["agent_dispatch"]["command"],
}
print(json.dumps(transcript))
"""


def test_fresh_session_registers_ten_tools_and_smokes_one_inspection(tmp_path):
    installation = make_fake_binary(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            FRESH_SESSION_SCRIPT,
            str(ROOT),
            installation["config"]["binary_path"],
            installation["config"]["binary_sha256"],
            installation["config"]["config_path"],
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    transcript = json.loads(result.stdout.splitlines()[-1])

    catalog = json.loads(
        (ROOT / "contracts" / "v0.1.0" / "catalog.json").read_text(encoding="utf-8")
    )
    roster = [tool["name"] for tool in catalog["tools"]]
    assert transcript["inventory"] == roster
    assert len(roster) == 10 and len(set(roster)) == 10
    # Registration follows catalog order, preserved by dict insertion order.
    assert transcript["registered"] == roster

    # The smoke inspection: one real execution through the trust gate, the
    # bounded runner, and the closed output boundary, not a fixture replay.
    assert transcript["smoke_ok"] is True
    assert transcript["smoke_operation"] == "agent_dispatch_status"
    assert transcript["smoke_exit_code"] == 0
    assert transcript["smoke_command"] == "status"
