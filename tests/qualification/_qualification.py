"""Shared isolated state, profiles, commands and validators for qualification.

All seeding uses the selected real executable inside disposable paths. Hermes
profiles remain isolated, and downstream targets answer only probe surfaces.
The fixture owns artifact identity; these helpers never select a provider.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"
CONTRACTS_SYNC = ROOT / "contracts" / "v0.3.0"

ROUTE_ID = "wiki-maintenance"
PROFILE = "wiki-maintainer"


def _run(argv, *, env=None, timeout=90, stdin_text=None, cwd=None):
    result = subprocess.run(
        argv,
        capture_output=True,
        env=env,
        timeout=timeout,
        input=stdin_text,
        cwd=cwd,
        text=True,
    )
    return result


def _fake_hermes_target(sandbox: Path) -> Path:
    """The controlled fake downstream Hermes target (PRD isolation model).

    Answers only the surfaces Agent Dispatch probes: the --version first
    line, the kanban assignees and list JSON shapes, the create-surface
    help text, and the profile-scoped enabled-skill table. No real Hermes
    state, board, or network is ever touched.
    """
    target = sandbox / "fake-hermes"
    target.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        'if args == ["--version"]:\n'
        '    print("Hermes Agent v0.20.5 (2026.8.19)")\n'
        '    print("Install directory: disposable qualification sandbox")\n'
        '    print("Install method: controlled-fake")\n'
        "    raise SystemExit(0)\n"
        'if args[0:2] == ["kanban", "--board"] and args[3:5] == ["assignees", "--json"]:\n'
        '    print(\'[{"name": "wiki-maintainer", "on_disk": true, "counts": {}}]\')\n'
        "    raise SystemExit(0)\n"
        'if args[0:2] == ["kanban", "--board"] and args[3:5] == ["list", "--json"]:\n'
        '    print("[]")\n'
        "    raise SystemExit(0)\n"
        'if args[0:2] == ["kanban", "--board"] and args[3:5] == ["create", "-h"]:\n'
        '    print("usage: hermes kanban --board BOARD create TITLE [flags]")\n'
        "    for flag in (\n"
        '        "--assignee", "--body", "--created-by", "--idempotency-key", "--json",\n'
        '        "--max-retries", "--max-runtime", "--mutex-key", "--priority", "--skill",\n'
        '        "--workspace",\n'
        "    ):\n"
        '        print(f"  {flag} VALUE    create-surface flag")\n'
        "    raise SystemExit(0)\n"
        'if args[-3:] == ["skills", "list", "--enabled-only"]:\n'
        '    print("\u2502 Name     \u2502 Category \u2502 Source \u2502 Trust   \u2502 Status  \u2502")\n'
        '    print("\u2502 llm-wiki \u2502 agent    \u2502 plugin \u2502 trusted \u2502 enabled \u2502")\n'
        "    raise SystemExit(0)\n"
        'print("fake-hermes: unsupported surface", file=sys.stderr)\n'
        "raise SystemExit(22)\n",
        encoding="utf-8",
    )
    target.chmod(0o755)
    return target


def _seed_disposable_state(binary: Path, sandbox: Path) -> dict[str, str]:
    """Build and seed the disposable Agent Dispatch profile; return ids.

    Every command runs with HOME inside the sandbox so home-resolved state
    (including the hermes capability cache) stays disposable, and the
    downstream target is the controlled fake. Nothing outside the sandbox
    is read or written.
    """
    home = sandbox / "home"
    (home / ".config").mkdir(parents=True)
    vault = sandbox / "vault"
    (vault / "notes").mkdir(parents=True)
    note = vault / "notes" / "alpha.md"
    note.write_text("synthetic qualification note\n", encoding="utf-8")
    vault.chmod(0o700)
    state = sandbox / "state"
    state.mkdir()
    config = sandbox / "config.yaml"
    seed_env = {**os.environ, "HOME": str(home)}

    def agent_dispatch(*args, stdin_text=None):
        return _run(
            [str(binary), *args],
            env=seed_env,
            stdin_text=stdin_text,
        )

    init = agent_dispatch(
        "init",
        "--resource-root",
        str(vault),
        "--instance-id",
        "qual-matrix",
        "--state-dir",
        str(state),
        "--config",
        str(config),
    )
    assert init.returncode == 0, init.stderr

    text = config.read_text(encoding="utf-8")
    replacements = (
        ("      sinks: []", "      sinks:\n        - id: ops-log\n          type: log"),
        ("      drain:\n        mode: after-command", "      drain:\n        mode: manual"),
        ("    executable: hermes\n", f"    executable: {sandbox / 'fake-hermes'}\n"),
        (f"  {ROUTE_ID}:\n    enabled: false", f"  {ROUTE_ID}:\n    enabled: true"),
    )
    for before, after in replacements:
        assert text.count(before) == 1, f"init template drift at replacement: {before!r}"
        text = text.replace(before, after, 1)
        assert after in text
    config.write_text(text, encoding="utf-8")

    validated = agent_dispatch("config", "validate", "--config", str(config), "--output", "json")
    assert validated.returncode == 0 and json.loads(validated.stdout)["ok"], validated.stderr

    # The two-key production gate: learn the computed route revision from
    # the gate's own rejection, then acknowledge exactly that value.
    probe = agent_dispatch(
        "route",
        "enable",
        "--route",
        ROUTE_ID,
        "--config",
        str(config),
        "--yes",
        "--acknowledge-production-gate",
        "probe",
    )
    # The gate's rejection is a JSON envelope on stderr, so the revision's
    # quotes arrive backslash-escaped in the raw bytes.
    match = re.search(r'computed route revision \\"([0-9a-f]+)\\"', probe.stdout + probe.stderr)
    assert match, probe.stdout + probe.stderr
    enabled = agent_dispatch(
        "route",
        "enable",
        "--route",
        ROUTE_ID,
        "--config",
        str(config),
        "--yes",
        "--acknowledge-production-gate",
        match.group(1),
    )
    assert enabled.returncode == 0 and json.loads(enabled.stdout)["ok"], enabled.stderr

    trigger_name = re.search(r"trigger_name:\s*(\S+)", text)
    assert trigger_name, "the generated config declares no trigger name"

    def dispatch_fixture(fixture: str, clock: str):
        watchman_env = {
            **seed_env,
            "WATCHMAN_SINCE": "c:0:1",
            "WATCHMAN_TRIGGER": trigger_name.group(1),
            "WATCHMAN_ROOT": str(vault),
            "WATCHMAN_CLOCK": clock,
        }
        return _run(
            [
                str(binary),
                "dispatch",
                "--route",
                ROUTE_ID,
                "--input",
                "watchman",
                "--no-submit",
                "--config",
                str(config),
            ],
            env=watchman_env,
            stdin_text=fixture,
        )

    seeded = dispatch_fixture(
        json.dumps(
            [{"name": "notes/alpha.md", "exists": True, "new": True, "type": "f", "size": 27}]
        ),
        "c:1:1",
    )
    assert seeded.returncode == 0, seeded.stderr
    dispatch_id = json.loads(seeded.stdout)["result"]["dispatch_id"]

    began = agent_dispatch(
        "work",
        "begin",
        "--dispatch-id",
        dispatch_id,
        "--run-id",
        "r1",
        "--config",
        str(config),
        "--output",
        "json",
    )
    assert began.returncode == 0 and json.loads(began.stdout)["ok"], began.stderr
    manifest = json.dumps(
        [
            {
                "path": "notes/alpha.md",
                "after_digest": "sha256:" + hashlib.sha256(note.read_bytes()).hexdigest(),
            }
        ]
    )
    completed = agent_dispatch(
        "work",
        "complete",
        "--dispatch-id",
        dispatch_id,
        "--run-id",
        "r1",
        "--status",
        "completed",
        "--manifest",
        "-",
        "--config",
        str(config),
        "--output",
        "json",
        stdin_text=manifest,
    )
    assert completed.returncode == 0, completed.stderr
    # Upstream quirk (v0.1.6): work complete's envelope reports a receipt
    # id that receipts list/show never serve; the durable receipt is the
    # begin-time row, so resolve the id from the list surface itself.
    receipts_rows = json.loads(
        agent_dispatch(
            "receipts", "list", "--kind", "work", "--config", str(config), "--output", "json"
        ).stdout
    )["result"]["receipts"]
    assert receipts_rows, "work completion persisted no work receipt"
    receipt_id = receipts_rows[0]["receipt_id"]

    quarantined = dispatch_fixture(
        json.dumps(
            [{"name": "raw/secret.md", "exists": True, "new": True, "type": "f", "size": 80}]
        ),
        "c:2:1",
    )
    assert quarantined.returncode == 0, quarantined.stderr
    assert json.loads(quarantined.stdout)["result"]["disposition"] == "quarantine"

    held = agent_dispatch("quarantine", "list", "--config", str(config), "--output", "json")
    quarantine_rows = json.loads(held.stdout)["result"]["quarantine"]
    assert quarantine_rows, "the protected-path fixture seeded no held quarantine case"
    quarantine_id = quarantine_rows[0]["quarantine_id"]

    shown = agent_dispatch(
        "dispatches", "show", dispatch_id, "--config", str(config), "--output", "json"
    )
    aggregate_matches = re.findall(r'"aggregate_id":\s*"([^"]+)"', shown.stdout)
    assert aggregate_matches, "dispatches show carries no aggregate reference"
    return {
        "dispatch_id": dispatch_id,
        "receipt_id": receipt_id,
        "quarantine_id": quarantine_id,
        "aggregate_id": aggregate_matches[0],
    }


def _disposable_hermes_home(
    sandbox: Path, binary: Path, config: Path, *, sync_group_id: str | None = None
) -> Path:
    home = sandbox / "hermes-home"
    plugins = home / "plugins"
    plugins.mkdir(parents=True)
    bundled = home / "bundled"
    bundled.mkdir()
    shutil.copytree(
        ROOT,
        plugins / "agent-dispatch-plugin",
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc"),
        dirs_exist_ok=True,
    )
    settings = {
        "binary_path": str(binary),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "config_path": str(config),
        "timeout_seconds": 30,
    }
    if sync_group_id is not None:
        settings["sync_group_id"] = sync_group_id
    # Write through the entries block with correct indentation.
    config_text = (
        "plugins:\n"
        "  enabled: [agent-dispatch-plugin]\n"
        "  entries:\n"
        "    agent-dispatch-plugin:\n"
        "      settings:\n"
        f"        binary_path: {json.dumps(settings['binary_path'])}\n"
        f"        binary_sha256: {json.dumps(settings['binary_sha256'])}\n"
        f"        config_path: {json.dumps(settings['config_path'])}\n"
        f"        timeout_seconds: {settings['timeout_seconds']}\n"
        + (f"        sync_group_id: {json.dumps(sync_group_id)}\n" if sync_group_id else "")
    )
    (home / "config.yaml").write_text(config_text, encoding="utf-8")
    return home


def _expected_commands(contracts: Path = CONTRACTS) -> dict[tuple[str, str | None], str]:
    catalog = json.loads((contracts / "catalog.json").read_text(encoding="utf-8"))
    commands: dict[tuple[str, str | None], str] = {}
    for tool in catalog["tools"]:
        for action in tool["actions"]:
            key = (tool["name"], action.get("input_action_value"))
            commands[key] = action["expected_command"]
    return commands


def _wrapper_validator(contracts: Path = CONTRACTS) -> Draft202012Validator:
    ref_registry = RefRegistry()
    for schema_file in sorted(contracts.glob("schemas/*.json")):
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        ref_registry = ref_registry.with_resource(schema["$id"], Resource.from_contents(schema))
    schema = json.loads((contracts / "schemas" / "wrapper.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=ref_registry)


def _enable_disposable_sync(config: Path, group_id: str) -> None:
    """Configure two synthetic members without resolving credentials or peers."""
    document = yaml.safe_load(config.read_text(encoding="utf-8"))
    local = document["instance"]["id"]
    document["resources"]["vault-main"]["git"]["mode"] = "optional"
    document["sync"] = {
        "enabled": True,
        "group_id": group_id,
        "resource": "vault-main",
        "remote_name": "origin",
        "remote_repository_digest": "sha256:" + "a" * 64,
        "content_ref": "refs/heads/wiki-sync",
        "membership_ref": f"refs/agent-dispatch/membership/{group_id}",
        "local_instance_id": local,
        "administrator_key": "SHA256:" + "A" * 43,
        "publisher_signing_key_ref": "env:QUAL_PUBLISHER_KEY",
        "administrator_signing_key_ref": "env:QUAL_ADMINISTRATOR_KEY",
        "nodes": [
            {
                "instance_id": local,
                "state_incarnation_id": f"{local}-state-001",
                "endpoint": "https://qual-local.ts.net",
                "publisher_key": "SHA256:" + "B" * 42 + "A",
                "credential_ref": "env:QUAL_LOCAL_PEER_KEY",
            },
            {
                "instance_id": "qual-peer",
                "state_incarnation_id": "qual-peer-state-001",
                "endpoint": "https://qual-peer.ts.net",
                "publisher_key": "SHA256:" + "C" * 42 + "A",
                "credential_ref": "env:QUAL_REMOTE_PEER_KEY",
            },
        ],
        "bounds": {
            "queue": 1000,
            "history_commits": 1000,
            "subprocess_seconds": 120,
            "subprocess_bytes": 1048576,
        },
    }
    config.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
