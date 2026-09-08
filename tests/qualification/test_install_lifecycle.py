"""The disposable profile installation lifecycle (TASK-015, EPIC-005).

Proves the distribution lifecycle states the dossier names, through the
real Hermes CLI and runtime, v0.20.5 or newer, over one disposable
``HERMES_HOME``:
a pinned source-only installation starts disabled (no tool registration),
explicit plugin enablement registers exactly the ten frozen tools while
the trust gate keeps the toolset unavailable until the five settings are
seeded, explicit toolset enablement and disablement round-trip through
``hermes tools`` as a state independent of plugin enablement, plugin
disablement hides the tool surface again, and complete removal leaves no
plugin registration or tool inventory residue in a fresh session. The
recorded boundary: the v0.20.5 ``plugins install`` subcommand rejects
``manifest_version`` 2 repositories (its installer supports v1 only)
while the runtime directory loader and Plugin Doctor accept the frozen
manifest 2 contract, so pinned installation uses the documented
source-only plugin-directory mechanism.

The stage never touches the operator's live Hermes or Agent Dispatch
state: the profile, the pinned executable copy, and the Agent Dispatch
configuration all live in the sandbox. Like the compatibility matrix it
requires the pinned artifacts, is not part of ``make test``, and runs
through ``make test-qualify`` (TESTING.md owns the contract).
"""

from __future__ import annotations

import hashlib
import io
import zipfile
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"

MINIMUM_HERMES_VERSION = (0, 20, 5)
PLUGIN_NAME = "agent-dispatch-plugin"
TOOLSET = "agent_dispatch"

# Executed under the Hermes venv interpreter with HERMES_HOME
# pointed at the disposable profile: importing model_tools performs the
# real built-in and plugin discovery, and the observation reports the
# registration, availability, and one smoke dispatch through the real
# dispatcher.
LIFECYCLE_DRIVER_SCRIPT = r"""
import json
import os
import sys

os.environ.setdefault("HERMES_QUIET", "1")
import model_tools

names = sorted(n for n in model_tools.get_all_tool_names() if n.startswith("agent_dispatch"))
info = model_tools.get_available_toolsets().get("agent_dispatch")
available = bool((info or {}).get("available"))
smoke = {}
try:
    raw = model_tools.handle_function_call("agent_dispatch_status", {})
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    smoke = {
        "ok": parsed.get("ok"),
        "operation": parsed.get("operation"),
        "error": (parsed.get("error") or {}).get("code"),
    }
except Exception as exc:  # the dispatcher refuses unknown/unavailable tools
    smoke = {"refused": str(exc)[:160]}
print(json.dumps({"registered": names, "toolset_available": available, "smoke": smoke}))
"""


def _run(argv, *, env=None, timeout=120, cwd=None):
    return subprocess.run(argv, capture_output=True, env=env, timeout=timeout, cwd=cwd, text=True)


def _require_qualification_prerequisites():
    """Fail with the exact missing prerequisite; this stage never skips."""
    assert platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"), (
        "missing prerequisite: the installation lifecycle targets Darwin arm64 hosts"
    )
    hermes = shutil.which("hermes")
    assert hermes is not None, (
        "missing prerequisite: the Hermes Agent CLI (v0.20.5 or newer) must be on PATH "
        "for the installation lifecycle qualification"
    )
    version_output = _run([hermes, "--version"]).stdout
    first_line = version_output.splitlines()[0].strip()
    # v0.21.0+ appends upstream/local commit trailers after the build date,
    # so the identity check anchors the prefix rather than the whole line.
    version_match = re.match(r"Hermes Agent v(\d+)\.(\d+)\.(\d+) \(\d{4}\.\d+\.\d+\)", first_line)
    assert version_match, (
        f"missing prerequisite: unrecognized hermes --version line, got "
        f"{version_output.splitlines()[:1]}"
    )
    hermes_version = tuple(int(part) for part in version_match.groups())
    assert hermes_version >= MINIMUM_HERMES_VERSION, (
        f"missing prerequisite: Hermes must be v0.20.5 or newer, got "
        f"v{'.'.join(str(part) for part in hermes_version)}"
    )
    install_dir = None
    for line in version_output.splitlines():
        if line.startswith("Install directory:"):
            install_dir = line.split(":", 1)[1].strip()
    assert install_dir, "missing prerequisite: hermes --version names no install directory"
    venv_python = Path(install_dir) / "venv" / "bin" / "python"
    assert venv_python.is_file(), (
        f"missing prerequisite: the Hermes venv interpreter is expected at {venv_python}"
    )
    return hermes, venv_python


def _install_plugin_directory(home: Path) -> None:
    """Install the pinned plugin checkout as a source-only directory plugin."""
    destination = home / "plugins" / PLUGIN_NAME
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc"),
    )


def _profile_env(home: Path) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "HERMES_HOME": str(home),
            "HERMES_BUNDLED_PLUGINS": str(home / "bundled"),
            "HERMES_ENABLE_PROJECT_PLUGINS": "0",
            "HERMES_QUIET": "1",
        }
    )
    return env


def _hermes(hermes: str, home: Path, *args: str) -> subprocess.CompletedProcess:
    return _run([hermes, *args], env=_profile_env(home))


def _observe(venv_python: Path, home: Path, driver: Path) -> dict:
    result = _run(
        [str(venv_python), str(driver)],
        env=_profile_env(home),
        timeout=300,
    )
    assert result.returncode == 0, f"the lifecycle driver failed: {result.stdout}{result.stderr}"
    return json.loads(result.stdout.splitlines()[-1])


def _plugins_config(home: Path) -> dict:
    import yaml

    config_file = home / "config.yaml"
    if not config_file.is_file():
        return {}
    return yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}


def _seed_settings(home: Path, binary: Path, ad_config: Path) -> None:
    """Write the five frozen plugin settings through the profile config."""
    import yaml

    config_file = home / "config.yaml"
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    config["plugins"]["entries"][PLUGIN_NAME]["settings"] = {
        "binary_path": str(binary),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "config_path": str(ad_config),
        "timeout_seconds": 30,
    }
    config_file.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def test_install_lifecycle_proves_disabled_enable_disable_and_removal(tmp_path, qualified_binary):
    hermes, venv_python = _require_qualification_prerequisites()

    sandbox = tmp_path / "lifecycle-sandbox"
    sandbox.mkdir()
    driver = sandbox / "lifecycle_driver.py"
    driver.write_text(LIFECYCLE_DRIVER_SCRIPT, encoding="utf-8")
    binary = qualified_binary

    # Agent Dispatch configuration seeded through the binary's own command,
    # entirely inside the sandbox with absolute (non-symlinked) paths.
    ad_config = sandbox / "agent-dispatch-config.json"
    seed = _run(
        [
            str(binary),
            "init",
            "--resource-root",
            str(sandbox / "resources"),
            "--instance-id",
            "install-lifecycle",
            "--state-dir",
            str(sandbox / "state"),
            "--config",
            str(ad_config),
        ],
        env={**os.environ, "HOME": str(sandbox)},
    )
    assert seed.returncode == 0, f"agent-dispatch init failed: {seed.stdout}{seed.stderr}"

    catalog = json.loads((CONTRACTS / "catalog.json").read_text(encoding="utf-8"))
    roster = sorted(tool["name"] for tool in catalog["tools"])
    assert len(roster) == 10

    home = sandbox / "hermes-home"
    (home / "plugins").mkdir(parents=True)
    (home / "bundled").mkdir()

    # -- 1. Pinned installation starts disabled --------------------------------
    _install_plugin_directory(home)
    show = _hermes(hermes, home, "plugins", "show", PLUGIN_NAME)
    assert "Status: not enabled" in show.stdout, (
        f"the installed plugin must start disabled: {show.stdout}{show.stderr}"
    )
    assert PLUGIN_NAME not in (_plugins_config(home).get("plugins", {}).get("enabled") or [])
    observation = _observe(venv_python, home, driver)
    assert observation["registered"] == [], "a disabled plugin must register no tools"

    # -- 2. Explicit plugin enablement ------------------------------------------
    enabled = _hermes(hermes, home, "plugins", "enable", PLUGIN_NAME, "--no-allow-tool-override")
    assert enabled.returncode == 0 and "enabled" in enabled.stdout.lower(), (
        f"plugins enable failed: {enabled.stdout}{enabled.stderr}"
    )
    assert PLUGIN_NAME in (_plugins_config(home).get("plugins", {}).get("enabled") or [])

    # Without the five settings the trust gate keeps the toolset unavailable
    # even though registration happened.
    observation = _observe(venv_python, home, driver)
    assert observation["registered"] == roster, (
        "an enabled plugin registers exactly the ten frozen tools"
    )
    assert observation["toolset_available"] is False, (
        "the toolset must stay unavailable until the five settings are seeded"
    )
    assert observation["smoke"].get("ok") is False and observation["smoke"].get("error") == (
        "binary_unavailable"
    ), f"unseeded smoke must close as binary_unavailable: {observation['smoke']}"

    # With the five settings the trust gate opens and one real inspection
    # succeeds through the full boundary.
    _seed_settings(home, binary, ad_config)
    observation = _observe(venv_python, home, driver)
    assert observation["registered"] == roster
    assert observation["toolset_available"] is True
    assert observation["smoke"] == {
        "ok": True,
        "operation": "agent_dispatch_status",
        "error": None,
    }, f"the seeded smoke inspection must succeed: {observation['smoke']}"

    # -- 3. Explicit toolset enablement/disablement, independent state ---------
    disabled = _hermes(hermes, home, "tools", "disable", TOOLSET)
    assert disabled.returncode == 0 and "disabled" in disabled.stdout.lower(), (
        f"tools disable failed: {disabled.stdout}{disabled.stderr}"
    )
    listing = _hermes(hermes, home, "tools", "list")
    assert re.search(r"[✗x] disabled\s+" + TOOLSET, listing.stdout), (
        f"the toolset must report disabled: {listing.stdout}"
    )
    cli_toolsets = (_plugins_config(home).get("platform_toolsets", {}) or {}).get("cli") or []
    assert TOOLSET not in cli_toolsets, "a disabled toolset leaves the platform list"
    assert PLUGIN_NAME in (_plugins_config(home).get("plugins", {}).get("enabled") or []), (
        "toolset disablement must not disable the plugin"
    )

    toolset_enabled = _hermes(hermes, home, "tools", "enable", TOOLSET)
    assert toolset_enabled.returncode == 0 and "enabled" in toolset_enabled.stdout.lower(), (
        f"tools enable failed: {toolset_enabled.stdout}{toolset_enabled.stderr}"
    )
    listing = _hermes(hermes, home, "tools", "list")
    assert re.search(r"[✓] enabled\s+" + TOOLSET, listing.stdout), (
        f"the toolset must report enabled: {listing.stdout}"
    )
    cli_toolsets = (_plugins_config(home).get("platform_toolsets", {}) or {}).get("cli") or []
    assert TOOLSET in cli_toolsets, "an enabled plugin toolset joins the platform list"

    # Exercise a real source rollback and upgrade with identical profile settings.
    previous = "0c4e70e384bc9891bc15820c4e0b6a42ba700d5a"
    archive = subprocess.run(
        ["git", "archive", "--format=zip", previous],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    assert archive.returncode == 0, "rollback prerequisite: full Git history containing " + previous
    destination = home / "plugins" / PLUGIN_NAME
    profile_before = (home / "config.yaml").read_bytes()
    for revision in ("previous", "candidate"):
        assert _hermes(hermes, home, "tools", "disable", TOOLSET).returncode == 0
        assert _hermes(hermes, home, "plugins", "disable", PLUGIN_NAME).returncode == 0
        shutil.rmtree(destination)
        if revision == "previous":
            with zipfile.ZipFile(io.BytesIO(archive.stdout)) as files:
                files.extractall(destination)
        else:
            _install_plugin_directory(home)
        assert (
            _hermes(
                hermes, home, "plugins", "enable", PLUGIN_NAME, "--no-allow-tool-override"
            ).returncode
            == 0
        )
        assert _hermes(hermes, home, "tools", "enable", TOOLSET).returncode == 0
        assert (home / "config.yaml").read_bytes() == profile_before
        observation = _observe(venv_python, home, driver)
        assert observation["registered"] == roster
        assert observation["toolset_available"] is True
        assert observation["smoke"]["ok"] is True

    # -- 4. Plugin disablement hides the tool surface ---------------------------
    plugin_disabled = _hermes(hermes, home, "plugins", "disable", PLUGIN_NAME)
    assert plugin_disabled.returncode == 0 and "disabled" in plugin_disabled.stdout.lower(), (
        f"plugins disable failed: {plugin_disabled.stdout}{plugin_disabled.stderr}"
    )
    observation = _observe(venv_python, home, driver)
    assert observation["registered"] == [], "a disabled plugin must register no tools"

    # -- 5. Complete removal leaves no registration or inventory residue --------
    removed = _hermes(hermes, home, "plugins", "remove", PLUGIN_NAME)
    assert removed.returncode == 0 and "removed" in removed.stdout.lower(), (
        f"plugins remove failed: {removed.stdout}{removed.stderr}"
    )
    assert not (home / "plugins" / PLUGIN_NAME).exists(), (
        "removal must delete the installed plugin directory"
    )
    listing = _hermes(hermes, home, "plugins", "list")
    assert PLUGIN_NAME[:17] not in listing.stdout, (
        f"the removed plugin must not be listed: {listing.stdout}"
    )
    observation = _observe(venv_python, home, driver)
    assert observation["registered"] == [], "a removed plugin must register no tools"
    assert observation["toolset_available"] is False, (
        "a removed plugin leaves no tool inventory entry"
    )

    # The profile config keeps inert bookkeeping for the removed plugin; the
    # documented cleanup path removes it so nothing named agent-dispatch-plugin
    # remains anywhere in the profile.
    for key in (
        f"plugins.entries.{PLUGIN_NAME}",
        "plugins.disabled",
    ):
        unset = _hermes(hermes, home, "config", "unset", key)
        assert unset.returncode == 0, f"config unset {key} failed: {unset.stdout}{unset.stderr}"
    residue = json.dumps(_plugins_config(home))
    assert PLUGIN_NAME not in residue, (
        f"the cleaned profile must not reference the plugin: {residue}"
    )
    observation = _observe(venv_python, home, driver)
    assert observation["registered"] == []
