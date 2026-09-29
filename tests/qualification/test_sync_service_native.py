"""Native user-manager qualification of the v0.2.0 read-only service tool."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import yaml

import pytest

import runner
from test_compatibility_matrix import (
    _disposable_hermes_home,
    _enable_disposable_sync,
    _fake_hermes_target,
    _run,
    _seed_disposable_state,
    _wrapper_validator,
    CONTRACTS_V020,
)


def _service(binary: Path, config: Path, group_id: str, action: str) -> dict:
    result = _run(
        [
            str(binary),
            "sync",
            "service",
            action,
            "--group",
            group_id,
            "--config",
            str(config),
            "--output",
            "json",
        ],
        env=runner._native_service_environment(),
        timeout=45,
    )
    assert result.returncode == 0, (action, result.stdout, result.stderr)
    envelope = json.loads(result.stdout)
    assert envelope["ok"] is True and envelope["command"] == f"sync service {action}"
    return envelope["result"]


def _native_loaded(label: str) -> bool:
    if runner._host_platform() == "darwin/arm64":
        command = ["launchctl", "print", f"gui/{os.getuid()}/{label}"]
    else:
        command = ["systemctl", "--user", "is-active", f"{label}.service"]
    return subprocess.run(command, capture_output=True, text=True, timeout=15).returncode == 0


def _await_native_state(label: str, loaded: bool) -> bool:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if _native_loaded(label) is loaded:
            return True
        time.sleep(0.1)
    return _native_loaded(label) is loaded


def _seed_local_membership(binary: Path, config: Path, sandbox: Path, group_id: str) -> None:
    """Create a signed synthetic bootstrap on the isolated local Git ref."""
    vault = sandbox / "vault"
    key = sandbox / "administrator-key"
    created = _run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)])
    assert created.returncode == 0, created.stderr
    fingerprint = _run(["ssh-keygen", "-lf", str(key) + ".pub"])
    assert fingerprint.returncode == 0, fingerprint.stderr
    document = yaml.safe_load(config.read_text(encoding="utf-8"))
    document["sync"]["administrator_key"] = fingerprint.stdout.split()[1]
    config.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    initialized = _run(["git", "-C", str(vault), "init", "-q"])
    assert initialized.returncode == 0, initialized.stderr

    planned = _run(
        [
            str(binary),
            "sync",
            "membership",
            "plan",
            "--group",
            group_id,
            "--change",
            "bootstrap",
            "--output",
            "json",
        ],
        env={**os.environ, "AGENT_DISPATCH_CONFIG": str(config)},
    )
    assert planned.returncode == 0, planned.stderr
    plan = json.loads(planned.stdout)["result"]["plan"]
    index = sandbox / "membership-index"
    git_env = {
        **os.environ,
        "GIT_INDEX_FILE": str(index),
        "GIT_AUTHOR_NAME": "Qualification",
        "GIT_AUTHOR_EMAIL": "qualification@invalid.example",
        "GIT_COMMITTER_NAME": "Qualification",
        "GIT_COMMITTER_EMAIL": "qualification@invalid.example",
    }

    def git(*args: str, stdin_text: str | None = None) -> str:
        result = _run(["git", "-C", str(vault), *args], env=git_env, stdin_text=stdin_text)
        assert result.returncode == 0, (args, result.stderr)
        return result.stdout.strip()

    for path, body in (
        (".agent-dispatch-sync/membership.json", plan["proposed_membership"]),
        (".agent-dispatch-sync/membership-plan.json", plan),
    ):
        blob = git(
            "hash-object", "-w", "--stdin", stdin_text=json.dumps(body, separators=(",", ":"))
        )
        git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}")
    tree = git("write-tree")
    commit = git(
        "-c",
        "gpg.format=ssh",
        "-c",
        f"user.signingKey={key}",
        "commit-tree",
        "-S" + str(key),
        tree,
        "-m",
        "Qualification membership bootstrap",
    )
    git("update-ref", document["sync"]["membership_ref"], commit)


def _inspect_through_hermes(home: Path, sandbox: Path, venv_python: Path) -> dict:
    manifest = sandbox / "service-inspect-manifest.json"
    manifest.write_text(
        json.dumps([{"tool": "agent_dispatch_sync_service_inspect", "args": {}}]),
        encoding="utf-8",
    )
    observed = _run(
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
    assert observed.returncode == 0, observed.stdout[-2000:] + observed.stderr[-2000:]
    payload = json.loads(observed.stdout)
    assert len(payload["registered"]) == len(payload["available"]) == 13
    result = json.loads(payload["results"][0]["raw"])
    _wrapper_validator(CONTRACTS_V020).validate(result)
    assert result["ok"] is True, result
    assert result["agent_dispatch"]["result"]["side_effects"] == []
    return result["agent_dispatch"]["result"]


@pytest.fixture
def short_service_sandbox():
    root = "/private/tmp" if runner._host_platform() == "darwin/arm64" else "/tmp"
    with tempfile.TemporaryDirectory(prefix="adq-", dir=root) as directory:
        yield Path(directory)


def test_native_service_absent_loaded_and_drifted(
    short_service_sandbox, v020_binary, qualification_runtime
):
    _hermes, venv_python = qualification_runtime
    sandbox = short_service_sandbox
    _fake_hermes_target(sandbox)
    _seed_disposable_state(v020_binary, sandbox)
    config = sandbox / "config.yaml"
    group_id = "qual-" + hashlib.sha256(str(sandbox).encode()).hexdigest()[:24]
    _enable_disposable_sync(config, group_id)
    _seed_local_membership(v020_binary, config, sandbox, group_id)
    home = _disposable_hermes_home(sandbox, v020_binary, config, sync_group_id=group_id)

    if runner._host_platform() == "darwin/arm64":
        ready = subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}"],
            capture_output=True,
            timeout=15,
        )
    else:
        ready = subprocess.run(
            ["systemctl", "--user", "show-environment"],
            capture_output=True,
            timeout=15,
        )
    assert ready.returncode == 0, "missing prerequisite: native user service manager"

    rendered = _service(v020_binary, config, group_id, "render")
    definition = Path(rendered["definition_path"])
    assert definition.is_absolute()
    assert definition.parent.is_relative_to(Path(runner._native_service_environment()["HOME"]))
    assert not definition.exists(), "qualification group label already has a definition"
    assert not _native_loaded(rendered["label"]), "qualification group label is already loaded"

    installed = False
    try:
        absent = _inspect_through_hermes(home, sandbox, venv_python)
        assert absent["present"] is False and absent["loaded"] is False
        _service(v020_binary, config, group_id, "install")
        installed = True
        assert _await_native_state(rendered["label"], True)
        loaded = _inspect_through_hermes(home, sandbox, venv_python)
        assert loaded["present"] is True and loaded["definition_matches"] is True
        assert loaded["loaded"] is True
        definition.write_text(
            rendered["definition"] + "\n# qualification drift\n", encoding="utf-8"
        )
        drifted = _inspect_through_hermes(home, sandbox, venv_python)
        assert drifted["present"] is True and drifted["definition_matches"] is False
        assert drifted["healthy"] is False
    finally:
        if definition.exists():
            definition.write_text(rendered["definition"], encoding="utf-8")
        if installed or definition.exists():
            _service(v020_binary, config, group_id, "uninstall")
        assert not definition.exists(), "qualification definition was not cleaned up"
        assert _await_native_state(rendered["label"], False), "qualification service remains loaded"
