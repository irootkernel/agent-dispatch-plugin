"""E2E: the Hermes Plugin Doctor inspects the plugin through its public CLI.

The production-equivalent artifact is this repository as a Hermes plugin
directory; the public interface is the `hermes plugins doctor` command. The
doctor itself reproduces a non-production environment (temporary home,
blocked outbound sockets), so this test creates no resources of its own and
fails with the exact missing prerequisite when Hermes is unavailable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_plugin_doctor_validates_the_skeleton_over_the_public_cli():
    hermes = shutil.which("hermes")
    assert hermes is not None, (
        "missing prerequisite: the Hermes Agent CLI (v0.20.5) must be on PATH "
        "for the Plugin Doctor end-to-end check"
    )
    result = subprocess.run(
        [hermes, "plugins", "doctor", str(ROOT), "--ci"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "OK: runtime discovery, manifest parsing, import, and registration passed" in result.stdout
    )
    assert "10 tool(s), 0 hook(s)" in result.stdout
