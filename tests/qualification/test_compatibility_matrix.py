"""The disposable action-level compatibility matrix (TASK-012, EPIC-004).

Qualifies every advertised public action of all ten tools through the real
Hermes v0.20.5 runtime (plugin discovery plus ``handle_function_call``
dispatch over a disposable ``HERMES_HOME``) invoking the real pinned Agent
Dispatch v0.1.6 executable on Darwin arm64, against synthetic state seeded
through Agent Dispatch's own commands inside one disposable profile. The
suite never touches the operator's live Agent Dispatch configuration,
state database, or LaunchAgents: the state directory, configuration,
resource root, and HOME that Agent Dispatch resolves are pinned into the
sandbox (seeding commands otherwise run with an inherited environment),
and the downstream Hermes target is a controlled fake answering only the
surfaces Agent Dispatch probes — the isolation model the PRD names for
qualification.

One recorded boundary is asserted as a deterministic negative: ``doctor
--probe-targets`` reports the watchman daemon unreachable under the
plugin's frozen PATH allowlist and therefore exits 3 with an ok:true
findings envelope, which the plugin's frozen exit-consistency rule closes
as ``contract_mismatch``. The PRD's fixture clause supplements this
variant's success evidence (the deterministic fake in the unit suite
proves the mapping); the runbook records the boundary. This stage is not
part of ``make test``: it requires the pinned artifacts and runs through
``make test-qualify`` (TESTING.md owns the contract).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"

# The pinned release artifact identities (docs/ops/qualification runbook
# records the full provenance): Agent Dispatch v0.1.6, tag v0.1.6 at commit
# fc67cf540383e51cdcf4a1aff6c9f2a1b7d252a5, built by `make release
# VERSION=v0.1.6` — the byte-reproducible darwin/arm64 release build whose
# digest the tag's SHA256SUMS carries.
PINNED_AGENT_DISPATCH_SHA256 = "ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479"
PINNED_AGENT_DISPATCH_VERSION = "v0.1.6"
REQUIRED_HERMES_LINE = "Hermes Agent v0.20.5"

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


def _require_qualification_prerequisites():
    """Fail with the exact missing prerequisite; this stage never skips."""
    assert platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"), (
        "missing prerequisite: the qualification matrix targets Darwin arm64 hosts"
    )
    hermes = shutil.which("hermes")
    assert hermes is not None, (
        "missing prerequisite: the Hermes Agent CLI (v0.20.5) must be on PATH "
        "for the compatibility qualification"
    )
    version_output = _run([hermes, "--version"]).stdout
    first_line = version_output.splitlines()[0].strip()
    assert re.fullmatch(re.escape(REQUIRED_HERMES_LINE) + r" \(\d{4}\.\d+\.\d+\)", first_line), (
        f"missing prerequisite: Hermes must be exactly v0.20.5, got "
        f"{version_output.splitlines()[:1]}"
    )
    install_dir = None
    for line in version_output.splitlines():
        if line.startswith("Install directory:"):
            install_dir = line.split(":", 1)[1].strip()
    assert install_dir, "missing prerequisite: hermes --version names no install directory"
    venv_python = Path(install_dir) / "venv" / "bin" / "python"
    assert venv_python.is_file(), (
        f"missing prerequisite: the Hermes v0.20.5 venv interpreter is expected at {venv_python}"
    )
    return hermes, venv_python


def _pinned_executable(sandbox: Path) -> Path:
    source = os.environ.get("AGENT_DISPATCH_QUALIFY_BINARY") or shutil.which("agent-dispatch")
    assert source, (
        "missing prerequisite: set AGENT_DISPATCH_QUALIFY_BINARY to a copy of "
        "the pinned agent-dispatch v0.1.6 darwin/arm64 release artifact (or "
        "have it on PATH); its SHA-256 is verified against the pinned identity"
    )
    binary = sandbox / "agent-dispatch"
    shutil.copy2(source, binary)
    binary.chmod(0o755)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert digest == PINNED_AGENT_DISPATCH_SHA256, (
        "the provided Agent Dispatch executable does not match the pinned "
        f"v0.1.6 release digest (got {digest})"
    )
    probe = _run([str(binary), "version", "--json"])
    assert probe.returncode == 0 and json.loads(probe.stdout) == {
        "name": "agent-dispatch",
        "version": PINNED_AGENT_DISPATCH_VERSION,
    }, f"the pinned executable failed its version probe: {probe.stdout}{probe.stderr}"
    return binary


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
    text = text.replace(
        "      sinks: []", "      sinks:\n        - id: ops-log\n          type: log"
    )
    text = text.replace(
        "      drain:\n        mode: after-command", "      drain:\n        mode: manual"
    )
    text = text.replace("    executable: hermes\n", f"    executable: {sandbox / 'fake-hermes'}\n")
    text = text.replace(f"  {ROUTE_ID}:\n    enabled: false", f"  {ROUTE_ID}:\n    enabled: true")
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


def _disposable_hermes_home(sandbox: Path, binary: Path, config: Path) -> Path:
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
        "binary_sha256": PINNED_AGENT_DISPATCH_SHA256,
        "config_path": str(config),
        "timeout_seconds": 30,
    }
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
    )
    (home / "config.yaml").write_text(config_text, encoding="utf-8")
    return home


def _expected_commands() -> dict[tuple[str, str | None], str]:
    catalog = json.loads((CONTRACTS / "catalog.json").read_text(encoding="utf-8"))
    commands: dict[tuple[str, str | None], str] = {}
    for tool in catalog["tools"]:
        for action in tool["actions"]:
            key = (tool["name"], action.get("input_action_value"))
            commands[key] = action["expected_command"]
    return commands


def _wrapper_validator() -> Draft202012Validator:
    ref_registry = RefRegistry()
    for schema_file in sorted(CONTRACTS.glob("schemas/*.json")):
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        ref_registry = ref_registry.with_resource(schema["$id"], Resource.from_contents(schema))
    schema = json.loads((CONTRACTS / "schemas" / "wrapper.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=ref_registry)


def test_compatibility_matrix_qualifies_every_public_action(tmp_path):
    hermes, venv_python = _require_qualification_prerequisites()
    sandbox = tmp_path / "qualification"
    sandbox.mkdir()

    binary = _pinned_executable(sandbox)
    _fake_hermes_target(sandbox)
    ids = _seed_disposable_state(binary, sandbox)
    home = _disposable_hermes_home(sandbox, binary, sandbox / "config.yaml")

    success_cases = [
        ("agent_dispatch_status", {}),
        ("agent_dispatch_routes", {"action": "list"}),
        ("agent_dispatch_routes", {"action": "show", "route_id": ROUTE_ID}),
        ("agent_dispatch_routes", {"action": "preflight", "route_id": ROUTE_ID}),
        (
            "agent_dispatch_dispatches",
            {"action": "list", "route": ROUTE_ID, "state": "ready", "limit": 10, "offset": 0},
        ),
        ("agent_dispatch_dispatches", {"action": "show", "dispatch_id": ids["dispatch_id"]}),
        (
            "agent_dispatch_receipts",
            {"action": "list", "kind": "work", "route": ROUTE_ID, "limit": 10},
        ),
        ("agent_dispatch_receipts", {"action": "show", "receipt_id": ids["receipt_id"]}),
        ("agent_dispatch_event_show", {"aggregate_id": ids["aggregate_id"]}),
        ("agent_dispatch_quarantine", {"action": "list", "state": "held", "limit": 10}),
        ("agent_dispatch_quarantine", {"action": "show", "quarantine_id": ids["quarantine_id"]}),
        ("agent_dispatch_notifications", {"state": "pending", "sink": "ops-log", "limit": 10}),
        ("agent_dispatch_schedule_inspect", {"route_id": ROUTE_ID}),
        ("agent_dispatch_config", {"action": "show"}),
        ("agent_dispatch_config", {"action": "validate"}),
        ("agent_dispatch_config", {"action": "validate", "probe_targets": True}),
    ]
    # The recorded boundary: doctor probes the watchman daemon whenever the
    # configuration loads, and under the plugin's frozen PATH allowlist the
    # watchman binary is unreachable, so both doctor variants report the
    # error-severity finding, exit 3 with an ok:true findings envelope, and
    # the frozen exit-consistency rule closes them as contract_mismatch.
    # The PRD's fixture clause supplements their success evidence; the
    # runbook records the boundary and its remediation options.
    boundary_cases = [
        ("agent_dispatch_doctor", {"probe_targets": True}),
        ("agent_dispatch_doctor", {}),
    ]

    manifest = sandbox / "manifest.json"
    manifest.write_text(
        json.dumps(
            [{"tool": tool, "args": args} for tool, args in success_cases]
            + [{"tool": tool, "args": args} for tool, args in boundary_cases]
        ),
        encoding="utf-8",
    )
    driver = Path(__file__).resolve().parent / "_hermes_driver.py"
    driver_env = {
        **os.environ,
        "HERMES_HOME": str(home),
        "HERMES_BUNDLED_PLUGINS": str(home / "bundled"),
        "HERMES_ENABLE_PROJECT_PLUGINS": "0",
        "HERMES_QUIET": "1",
    }
    driven = _run(
        [str(venv_python), str(driver), str(manifest)],
        env=driver_env,
        timeout=300,
        cwd=str(sandbox),
    )
    assert driven.returncode == 0, driven.stdout[-2000:] + driven.stderr[-2000:]
    results = {
        (entry["tool"], json.dumps(entry["args"], sort_keys=True)): json.loads(entry["raw"])
        for entry in json.loads(driven.stdout)["results"]
    }
    assert len(results) == len(success_cases) + len(boundary_cases)

    wrapper = _wrapper_validator()
    commands = _expected_commands()
    for tool, args in success_cases:
        result = results[(tool, json.dumps(args, sort_keys=True))]
        wrapper.validate(result)
        assert result["ok"] is True, (tool, args, result.get("error"))
        assert result["exit_code"] == 0, (tool, args)
        assert result["operation"] == tool
        envelope = result["agent_dispatch"]
        assert envelope["ok"] is True, (tool, args)
        assert envelope["api_version"] == "agent-dispatch.cli/v1"
        action_value = args.get("action")
        expected = commands[(tool, action_value if action_value is not None else None)]
        assert envelope["command"] == expected, (tool, args, envelope["command"])

    # The synthetic state is real: the seeded rows surface through the
    # qualified actions, and the absent launchd schedule is the documented
    # successful inspection (present=false with ok:true).
    dispatches = results[
        (
            "agent_dispatch_dispatches",
            json.dumps(
                {"action": "list", "route": ROUTE_ID, "state": "ready", "limit": 10, "offset": 0},
                sort_keys=True,
            ),
        )
    ]
    listed = json.dumps(dispatches["agent_dispatch"]["result"])
    assert ids["dispatch_id"] in listed
    receipts = results[
        (
            "agent_dispatch_receipts",
            json.dumps(
                {"action": "list", "kind": "work", "route": ROUTE_ID, "limit": 10}, sort_keys=True
            ),
        )
    ]
    assert json.dumps(receipts["agent_dispatch"]["result"]).count("receipt_id") >= 1
    quarantine = results[
        (
            "agent_dispatch_quarantine",
            json.dumps({"action": "list", "state": "held", "limit": 10}, sort_keys=True),
        )
    ]
    assert ids["quarantine_id"] in json.dumps(quarantine["agent_dispatch"]["result"])
    notifications = results[
        (
            "agent_dispatch_notifications",
            json.dumps({"state": "pending", "sink": "ops-log", "limit": 10}, sort_keys=True),
        )
    ]
    assert json.dumps(notifications["agent_dispatch"]["result"]).count("notification_id") >= 1
    schedule = results[
        ("agent_dispatch_schedule_inspect", json.dumps({"route_id": ROUTE_ID}, sort_keys=True))
    ]
    assert schedule["agent_dispatch"]["result"]["present"] is False

    for tool, args in boundary_cases:
        boundary = results[(tool, json.dumps(args, sort_keys=True))]
        wrapper.validate(boundary)
        assert boundary["ok"] is False, (tool, args)
        assert boundary["error"]["code"] == "contract_mismatch", (tool, args)
        assert boundary["error"]["retryable"] is False
