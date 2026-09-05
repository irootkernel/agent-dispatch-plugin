"""The consolidated deterministic security suite (TASK-011, EPIC-004).

One module walks every dossier negative class through the complete public
boundary — schema validation, the trust gate, the bounded executor, envelope
validation, and redaction — and asserts the closed error contract plus the
absence of leakage for each:

- injection ....... test_injection_and_traversal_values_reject_...
                    test_denied_mutation_subcommands_stay_unreachable
- traversal ....... test_injection_and_traversal_values_reject_...
- symlink ......... test_symlinked_trust_paths_reject_at_the_gate
- digest .......... test_pinned_digest_negatives
- environment ..... test_the_execution_environment_is_the_fixed_allowlist
- secret .......... test_seeded_secrets_never_survive_any_boundary
- malformed-envelope test_malformed_envelope_negatives_close_closed
- command-mismatch .. test_command_identity_mismatch_closes_as_contract_mismatch
- output-limit .... test_output_limit_negatives
- timeout ......... test_timeout_negative_discards_partial_output
- termination ..... test_termination_negative_kills_the_whole_group
- no-retry ........ test_no_retry_under_every_failure_mode

Every case is offline and deterministic: the trusted fake Agent Dispatch
executable answers the version probe and plays one scripted behavior, so
the suite is reproducible evidence, not an environment probe.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

from conftest import HermesCtxStub, make_fake_binary

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"

# Hostile values every string binding must reject before the runner: option
# prefixes (flag smuggling), shell metacharacters, whitespace and control
# bytes, overlength, and path traversal in leading, inner, and absolute form.
HOSTILE_VALUES = (
    "--route",
    "-x",
    "--",
    "$(reboot)",
    "wiki ops",
    "wiki\n",
    "a" * 129,
    "../etc/passwd",
    "a/../b",
    "/etc/passwd",
)

# Every catalog string binding, with the minimal otherwise-valid request that
# carries it. The cross-coverage test below fails if the frozen catalog grows
# a string binding this sweep does not exercise.
INJECTION_SWEEP: tuple[tuple[str, dict[str, object], str], ...] = (
    ("agent_dispatch_routes", {"action": "show"}, "route_id"),
    ("agent_dispatch_routes", {"action": "preflight"}, "route_id"),
    ("agent_dispatch_dispatches", {"action": "list"}, "route"),
    ("agent_dispatch_dispatches", {"action": "list"}, "state"),
    ("agent_dispatch_dispatches", {"action": "show"}, "dispatch_id"),
    ("agent_dispatch_receipts", {"action": "list"}, "route"),
    ("agent_dispatch_receipts", {"action": "list"}, "dispatch"),
    ("agent_dispatch_receipts", {"action": "list"}, "kind"),
    ("agent_dispatch_receipts", {"action": "show"}, "receipt_id"),
    ("agent_dispatch_event_show", {}, "aggregate_id"),
    ("agent_dispatch_quarantine", {"action": "list"}, "route"),
    ("agent_dispatch_quarantine", {"action": "list"}, "state"),
    ("agent_dispatch_quarantine", {"action": "show"}, "quarantine_id"),
    ("agent_dispatch_notifications", {}, "route"),
    ("agent_dispatch_notifications", {}, "state"),
    ("agent_dispatch_notifications", {}, "sink"),
    ("agent_dispatch_schedule_inspect", {}, "route_id"),
)


def _wrapper_validator() -> Draft202012Validator:
    ref_registry = RefRegistry()
    for schema_file in sorted(CONTRACTS.glob("schemas/*.json")):
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        ref_registry = ref_registry.with_resource(schema["$id"], Resource.from_contents(schema))
    schema = json.loads((CONTRACTS / "schemas" / "wrapper.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=ref_registry)


@pytest.fixture(scope="module")
def wrapper():
    return _wrapper_validator()


def _tool(plugin, name):
    for spec in plugin.registry.tool_specs():
        if spec.name == name:
            return spec
    raise LookupError(name)


def _handler(plugin, ctx, name):
    return plugin.tools.handler_for(_tool(plugin, name), ctx)


def _configured(plugin, tmp_path, behavior=None, **settings):
    installation = make_fake_binary(tmp_path, behavior=behavior)
    config = {**installation["config"], **settings}
    return HermesCtxStub(settings=config), installation


def _sweep_id(value):
    if len(value) > 16:
        return f"overlength{len(value)}"
    return (
        value.strip()
        .replace("\n", "\\n")
        .replace("/", "_")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "_")
    )


@pytest.mark.parametrize("hostile", HOSTILE_VALUES, ids=_sweep_id)
@pytest.mark.parametrize(
    ("tool", "base", "param"),
    INJECTION_SWEEP,
    ids=[f"{t.split('_')[-1]}:{p}" for t, _, p in INJECTION_SWEEP],
)
def test_injection_and_traversal_values_reject_before_the_runner(
    plugin, monkeypatch, hostile, tool, base, param, wrapper
):
    """Option prefixes, shell metacharacters, and traversal strings never
    reach argv construction: the frozen grammar closes them first, the value
    never reflects into the closed error, and no process is created."""
    calls: list[tuple] = []
    monkeypatch.setattr(
        plugin.runner,
        "run_inspection",
        lambda *args, **kwargs: calls.append(args),
    )
    result = _handler(plugin, HermesCtxStub(), tool)(**{**base, param: hostile})
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["exit_code"] == -1
    assert result["operation"] == tool
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["retryable"] is False
    assert result["diagnostics"] == []
    assert calls == []
    assert hostile not in json.dumps(result)


def test_the_sweep_covers_every_string_binding_in_the_catalog(plugin):
    """The injection sweep is mechanically complete: every string-typed
    value binding the frozen catalog declares is exercised by it."""
    swept = {(tool, param) for tool, _, param in INJECTION_SWEEP}
    declared: set[tuple[str, str]] = set()
    for spec in plugin.registry.tool_specs():
        schema = spec.load_input_schema()
        properties = schema.get("properties") or {}
        for action in spec.actions:
            for binding in action.value_bindings:
                name = binding["param"]
                if properties.get(name, {}).get("type") == "string":
                    declared.add((spec.name, name))
    assert declared <= swept, sorted(declared - swept)


@pytest.mark.parametrize(
    ("tool", "params"),
    [
        ("agent_dispatch_dispatches", {"action": "retry", "dispatch_id": "d-1"}),
        ("agent_dispatch_receipts", {"action": "submit", "receipt_id": "r-1"}),
        ("agent_dispatch_quarantine", {"action": "release", "quarantine_id": "q-1"}),
        ("agent_dispatch_notifications", {"action": "drain"}),
        ("agent_dispatch_routes", {"action": "enable", "route_id": "wiki"}),
        ("agent_dispatch_config", {"action": "rewrite"}),
    ],
    ids=["retry", "submit", "release", "drain", "enable", "rewrite"],
)
def test_denied_mutation_subcommands_stay_unreachable(plugin, monkeypatch, tool, params):
    """The closed action enums keep every denied mutation subcommand out of
    the command slot: requests naming one close as invalid_argument with no
    process creation."""
    calls: list[tuple] = []
    monkeypatch.setattr(
        plugin.runner,
        "run_inspection",
        lambda *args, **kwargs: calls.append(args),
    )
    result = _handler(plugin, HermesCtxStub(), tool)(**params)
    assert result["error"]["code"] == "invalid_argument"
    assert calls == []


def test_symlinked_trust_paths_reject_at_the_gate(plugin, tmp_path, wrapper):
    """A symlinked executable, a symlinked trusted configuration file, and a
    symlinked parent directory each fail the trust gate closed."""
    real_dir = tmp_path / "real"
    installation = make_fake_binary(real_dir)

    binary_link = tmp_path / "binary-link"
    binary_link.symlink_to(installation["binary"])
    config_link = tmp_path / "config-link"
    config_link.symlink_to(installation["config_file"])
    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(real_dir)

    base = installation["config"]
    linked = [
        {**base, "binary_path": str(binary_link)},
        {**base, "config_path": str(config_link)},
        {
            **base,
            "binary_path": str(parent_link / "trusted" / "agent-dispatch"),
            "config_path": str(parent_link / "trusted" / "agent-dispatch.json"),
        },
    ]
    for config in linked:
        result = _handler(plugin, HermesCtxStub(settings=config), "agent_dispatch_status")()
        wrapper.validate(result)
        assert result["ok"] is False
        assert result["error"]["code"] == "binary_unavailable"
        assert result["error"]["retryable"] is False
        assert "symlink" in result["error"]["message"]


def test_pinned_digest_negatives(plugin, tmp_path, wrapper):
    """A wrong pinned digest rejects before any inspection runs, and the
    digest is re-verified on every call: swapping the executable bytes under
    an unchanged configuration fails the next call the same closed way."""

    wrong = make_fake_binary(tmp_path / "wrong", behavior={"kind": "echo"})
    pinned = wrong["config"]["binary_sha256"]
    flipped = ("0" if pinned[0] != "0" else "1") + pinned[1:]
    mismatched = {**wrong["config"], "binary_sha256": flipped}
    result = _handler(plugin, HermesCtxStub(settings=mismatched), "agent_dispatch_status")()
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "binary_unavailable"
    assert "SHA-256" in result["error"]["message"]

    ctx, installation = _configured(plugin, tmp_path / "swapped")
    handler = _handler(plugin, ctx, "agent_dispatch_status")
    first = handler()
    assert first["ok"] is True
    installation["binary"].write_bytes(
        installation["binary"].read_bytes() + b"\n# swapped after trust was established\n"
    )
    second = handler()
    wrapper.validate(second)
    assert second["ok"] is False
    assert second["error"]["code"] == "binary_unavailable"


def test_the_execution_environment_is_the_fixed_allowlist(plugin, tmp_path, monkeypatch):
    """The child environment is exactly PATH and TMPDIR: nothing inherited
    from Hermes, the agent, or this process. (The macOS python3 launcher
    shim adds its own six fixed variables after the exec, which the
    runner-level suite already pins; no caller-controlled value appears.)"""
    monkeypatch.setenv("EP004_POISON", "must-not-cross")
    monkeypatch.setenv("HOME", "/definitely/not/the/users/home")
    ctx, _ = _configured(plugin, tmp_path, behavior={"kind": "echo"})
    result = _handler(plugin, ctx, "agent_dispatch_status")()
    assert result["ok"] is True
    env = result["agent_dispatch"]["result"]["env"]
    shim_injected = {
        "CPATH",
        "LC_CTYPE",
        "LIBRARY_PATH",
        "MANPATH",
        "SDKROOT",
        "__CF_USER_TEXT_ENCODING",
    }
    assert set(env) - shim_injected == {"PATH", "TMPDIR"}
    assert "EP004_POISON" not in env
    assert "HOME" not in env


def test_seeded_secrets_never_survive_any_boundary(plugin, tmp_path, wrapper):
    """Bearer-style authorization strings, long hex tokens, and absolute
    paths are redacted from successful envelopes and from the bounded stderr
    tail of malformed output alike."""
    ctx, _ = _configured(
        plugin,
        tmp_path,
        behavior={
            "kind": "raw",
            "envelope": {
                "api_version": "agent-dispatch.cli/v1",
                "command": "status",
                "ok": True,
                "result": {
                    "note": "bearer Ab12Cd34Ef56Gh78 leaked here",
                    "key": "feedbeeffeedbeeffeedbeeffeedbeef",
                },
                "warnings": [],
                "trace_id": "",
            },
        },
    )
    result = _handler(plugin, ctx, "agent_dispatch_status")()
    wrapper.validate(result)
    assert result["ok"] is True
    serialized = json.dumps(result)
    assert "Ab12Cd34Ef56Gh78" not in serialized
    assert "feedbeeffeedbeef" not in serialized
    assert any("redactable content" in line for line in result["diagnostics"])

    leaky = make_fake_binary(
        tmp_path / "stderr",
        behavior={
            "kind": "raw",
            "stdout": "not json\n",
            "stderr_lines": [
                "token bearer Ab12Cd34Ef56Gh78",
                "hex feedbeeffeedbeeffeedbeeffeedbeef",
                "path /etc/agent-dispatch-secret.conf",
            ],
        },
    )
    result = _handler(plugin, HermesCtxStub(settings=leaky["config"]), "agent_dispatch_status")()
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "malformed_json"
    serialized = json.dumps(result)
    assert "Ab12Cd34Ef56Gh78" not in serialized
    assert "feedbeeffeedbeef" not in serialized
    assert "/etc/agent-dispatch-secret.conf" not in serialized


@pytest.mark.parametrize(
    ("behavior", "expected_code"),
    [
        ({"kind": "garbage"}, "malformed_json"),
        (
            {
                "kind": "raw",
                "envelope": {
                    "api_version": "agent-dispatch.cli/v2",
                    "command": "status",
                    "ok": True,
                    "result": {},
                    "warnings": [],
                    "trace_id": "",
                },
            },
            "malformed_json",
        ),
        (
            {
                "kind": "raw",
                "envelope": {
                    "api_version": "agent-dispatch.cli/v1",
                    "command": "status",
                    "ok": True,
                    "result": {},
                    "warnings": [],
                    "trace_id": "",
                },
                "exit": 4,
            },
            "contract_mismatch",
        ),
        (
            {
                "kind": "raw",
                "stdout": "[" * 20000 + "]" * 20000 + "\n",
            },
            "malformed_json",
        ),
        (
            {"kind": "raw", "stdout": "9" * 5000},
            "malformed_json",
        ),
    ],
    ids=[
        "garbage",
        "unknown-protocol",
        "success-with-failure-exit",
        "deep-nesting",
        "oversized-integer",
    ],
)
def test_malformed_envelope_negatives_close_closed(
    plugin, tmp_path, wrapper, behavior, expected_code
):
    ctx, _ = _configured(plugin, tmp_path, behavior=behavior)
    result = _handler(plugin, ctx, "agent_dispatch_status")()
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == expected_code
    assert result["error"]["retryable"] is False
    assert "agent_dispatch" not in result


def test_command_identity_mismatch_closes_as_contract_mismatch(plugin, tmp_path, wrapper):
    """An envelope whose command identity is not the action's fixed command
    closes as a contract mismatch instead of reaching the caller."""
    ctx, _ = _configured(
        plugin,
        tmp_path,
        behavior={
            "kind": "raw",
            "envelope": {
                "api_version": "agent-dispatch.cli/v1",
                "command": "status",
                "ok": True,
                "result": {},
                "warnings": [],
                "trace_id": "",
            },
        },
    )
    result = _handler(plugin, ctx, "agent_dispatch_routes")(action="show", route_id="wiki")
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "contract_mismatch"


@pytest.mark.parametrize(
    "behavior",
    [
        {"kind": "stdout_overflow", "bytes": 1048576 + 4096},
        {"kind": "stderr_overflow", "bytes": 65536 + 4096},
        {"kind": "combined_overflow", "stdout_bytes": 600000, "stderr_bytes": 600000},
    ],
    ids=["stdout", "stderr", "combined"],
)
def test_output_limit_negatives(plugin, tmp_path, wrapper, behavior):
    """Any stream or combined ceiling violation terminates the process group
    and discards every captured byte: the flood never reaches the caller."""
    ctx, _ = _configured(plugin, tmp_path, behavior=behavior)
    result = _handler(plugin, ctx, "agent_dispatch_status")()
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "output_too_large"
    assert result["error"]["retryable"] is False
    assert "xxxx" not in json.dumps(result)


def test_timeout_negative_discards_partial_output(plugin, tmp_path, wrapper):
    """A deadline overrun returns timeout, and the partial output written
    before the deadline is discarded rather than surfaced."""
    ctx, _ = _configured(
        plugin,
        tmp_path,
        behavior={"kind": "sleep", "prefix": "PARTIAL-PREFIX-LEAK", "seconds": 30},
        timeout_seconds=1,
    )
    started = time.monotonic()
    result = _handler(plugin, ctx, "agent_dispatch_status")()
    elapsed = time.monotonic() - started
    assert elapsed < 10.0
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "timeout"
    assert result["error"]["retryable"] is False
    assert "PARTIAL-PREFIX-LEAK" not in json.dumps(result)


def test_termination_negative_kills_the_whole_group(plugin, tmp_path):
    """A process that ignores TERM and forks a child is force-killed with
    its whole group once the grace period expires; nothing survives."""
    child_pid_file = tmp_path / "child.pid"
    ctx, _ = _configured(
        plugin,
        tmp_path,
        behavior={"kind": "trap", "child_pid_file": str(child_pid_file)},
        timeout_seconds=1,
    )
    started = time.monotonic()
    result = _handler(plugin, ctx, "agent_dispatch_status")()
    elapsed = time.monotonic() - started
    assert result["error"]["code"] == "timeout"
    assert elapsed >= 3.0 and elapsed < 10.0
    child_pid = int(child_pid_file.read_text(encoding="utf-8"))
    for _ in range(60):
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail("a child of the terminated process group is still present")


def test_no_retry_under_every_failure_mode(plugin, tmp_path):
    """One call is one process across failure modes: a timed-out, a
    malformed-output, a domain-rejection, and a successful call each invoke
    the executable exactly once (the version probe reads no behavior config
    and never counts)."""
    count_file = tmp_path / "count.log"
    counter = {"count_file": str(count_file)}

    def install(name, behavior, **settings):
        installation = make_fake_binary(tmp_path / name, behavior={**behavior, **counter})
        return HermesCtxStub(settings={**installation["config"], **settings})

    cases = [
        (install("sleepy", {"kind": "sleep", "seconds": 30}, timeout_seconds=2), "timeout"),
        (install("garbage", {"kind": "raw", "stdout": "not json\n"}), "malformed_json"),
        (install("reject", {"kind": "reject", "exit": 3}), "domain-rejection"),
        (install("echo", {}), "success"),
    ]
    codes = []
    for ctx, expected in cases:
        result = _handler(plugin, ctx, "agent_dispatch_status")()
        if expected == "success":
            assert result["ok"] is True
            codes.append(expected)
        elif expected == "domain-rejection":
            assert result["agent_dispatch"]["error"]["code"] == "config_invalid"
            codes.append(expected)
        else:
            assert result["error"]["code"] == expected
            codes.append(expected)
    assert count_file.read_text(encoding="utf-8").count("invoked") == len(cases)
