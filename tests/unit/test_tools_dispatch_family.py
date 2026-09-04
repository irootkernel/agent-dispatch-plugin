"""Unit tests for the dispatch-family inspection tools (TASK-009).

Action-level positive evidence drives every dispatches, receipts, event
show, quarantine, and notifications action branch (with documented
filters) through the real handler and runner boundary against a
deterministic trusted fake executable; negative evidence proves pagination
bounds, identifier and state-token grammars, closed kind and state enums,
and filter placement reject before any process is created; the read-only
proof shows no reachable argv carries a denied mutation subcommand and
receipts maps only to its two inspection commands; failure evidence maps
domain rejections and malformed output onto the closed error contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry as RefRegistry
from referencing import Resource

from conftest import HermesCtxStub, make_fake_binary

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS = ROOT / "contracts" / "v0.1.0"


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


@pytest.fixture
def configured_ctx(plugin, fake_agent_dispatch):
    return HermesCtxStub(settings=fake_agent_dispatch["config"])


def _handler(plugin, ctx, name):
    return plugin.tools.handler_for(_tool(plugin, name), ctx)


@pytest.mark.parametrize(
    ("tool", "params", "expected_argv_tail"),
    [
        (
            "agent_dispatch_dispatches",
            {"action": "list"},
            ["dispatches", "list", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_dispatches",
            {"action": "list", "route": "wiki", "state": "dispatched", "limit": 2, "offset": 4},
            [
                "dispatches",
                "list",
                "--route",
                "wiki",
                "--state",
                "dispatched",
                "--limit",
                "2",
                "--offset",
                "4",
                "--output",
                "json",
                "--config",
            ],
        ),
        (
            "agent_dispatch_dispatches",
            {"action": "show", "dispatch_id": "d-123.abc:x@y"},
            ["dispatches", "show", "d-123.abc:x@y", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_receipts",
            {"action": "list"},
            ["receipts", "list", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_receipts",
            {
                "action": "list",
                "route": "wiki",
                "dispatch": "d-1",
                "kind": "execution_projection",
                "limit": 100,
                "offset": 1000000,
            },
            [
                "receipts",
                "list",
                "--route",
                "wiki",
                "--dispatch",
                "d-1",
                "--kind",
                "execution_projection",
                "--limit",
                "100",
                "--offset",
                "1000000",
                "--output",
                "json",
                "--config",
            ],
        ),
        (
            "agent_dispatch_receipts",
            {"action": "show", "receipt_id": "r.9"},
            ["receipts", "show", "r.9", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_event_show",
            {"aggregate_id": "agg-1"},
            ["events", "show", "agg-1", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_quarantine",
            {"action": "list"},
            ["quarantine", "list", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_quarantine",
            {"action": "list", "route": "wiki", "state": "released", "limit": 25},
            [
                "quarantine",
                "list",
                "--route",
                "wiki",
                "--state",
                "released",
                "--limit",
                "25",
                "--output",
                "json",
                "--config",
            ],
        ),
        (
            "agent_dispatch_quarantine",
            {"action": "show", "quarantine_id": "q-7"},
            ["quarantine", "show", "q-7", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_notifications",
            {},
            ["notifications", "list", "--output", "json", "--config"],
        ),
        (
            "agent_dispatch_notifications",
            {"route": "wiki", "state": "pending", "sink": "slack-ops", "limit": 3},
            [
                "notifications",
                "list",
                "--route",
                "wiki",
                "--state",
                "pending",
                "--sink",
                "slack-ops",
                "--limit",
                "3",
                "--output",
                "json",
                "--config",
            ],
        ),
    ],
    ids=[
        "dispatches-list",
        "dispatches-list-filtered",
        "dispatches-show",
        "receipts-list",
        "receipts-list-filtered",
        "receipts-show",
        "events-show",
        "quarantine-list",
        "quarantine-list-filtered",
        "quarantine-show",
        "notifications-list",
        "notifications-list-filtered",
    ],
)
def test_every_dispatch_family_action_branch_succeeds_with_its_exact_fixed_mapping(
    plugin, configured_ctx, wrapper, tool, params, expected_argv_tail
):
    result = _handler(plugin, configured_ctx, tool)(**params)
    wrapper.validate(result)
    assert result["ok"] is True, (tool, params, result.get("error"))
    assert result["exit_code"] == 0
    assert result["operation"] == tool
    envelope = result["agent_dispatch"]
    assert envelope["ok"] is True
    assert envelope["command"] == " ".join(expected_argv_tail[:2])
    argv = envelope["result"]["argv"]
    assert argv[1:-1] == expected_argv_tail


@pytest.mark.parametrize(
    ("tool", "params"),
    [
        # Pagination bounds: limit 1..100, offset 0..1,000,000 where bound.
        ("agent_dispatch_dispatches", {"action": "list", "limit": 0}),
        ("agent_dispatch_dispatches", {"action": "list", "limit": 101}),
        ("agent_dispatch_dispatches", {"action": "list", "offset": -1}),
        ("agent_dispatch_dispatches", {"action": "list", "offset": 1000001}),
        ("agent_dispatch_receipts", {"action": "list", "limit": True}),
        ("agent_dispatch_quarantine", {"action": "list", "limit": 0}),
        ("agent_dispatch_quarantine", {"action": "list", "limit": 101}),
        ("agent_dispatch_notifications", {"limit": 0}),
        ("agent_dispatch_notifications", {"limit": 101}),
        ("agent_dispatch_notifications", {"limit": True}),
        # Quarantine and notifications support no offset at all.
        ("agent_dispatch_quarantine", {"action": "list", "offset": 0}),
        ("agent_dispatch_notifications", {"offset": 0}),
        # Identifier grammar across every dispatch-family identifier.
        ("agent_dispatch_dispatches", {"action": "show", "dispatch_id": "-x"}),
        ("agent_dispatch_dispatches", {"action": "show", "dispatch_id": "a b"}),
        ("agent_dispatch_dispatches", {"action": "show", "dispatch_id": "a" * 129}),
        ("agent_dispatch_dispatches", {"action": "show"}),
        ("agent_dispatch_dispatches", {"action": "list", "dispatch_id": "d-1"}),
        ("agent_dispatch_dispatches", {"action": "list", "route": "../etc/passwd"}),
        ("agent_dispatch_receipts", {"action": "show", "receipt_id": "../secrets"}),
        ("agent_dispatch_receipts", {"action": "show"}),
        ("agent_dispatch_event_show", {"aggregate_id": "agg\n"}),
        ("agent_dispatch_event_show", {}),
        ("agent_dispatch_quarantine", {"action": "show", "quarantine_id": "-q"}),
        ("agent_dispatch_quarantine", {"action": "list", "route": "wiki ops"}),
        ("agent_dispatch_notifications", {"sink": "slack ops"}),
        # State-token grammar where upstream does not enumerate values.
        ("agent_dispatch_dispatches", {"action": "list", "state": "Dispatched"}),
        ("agent_dispatch_dispatches", {"action": "list", "state": "d" * 65}),
        ("agent_dispatch_notifications", {"state": "PENDING"}),
        # Closed upstream enums: receipt kinds and quarantine states.
        ("agent_dispatch_receipts", {"action": "list", "kind": "worker"}),
        ("agent_dispatch_receipts", {"action": "list", "kind": "ACCEPTANCE"}),
        ("agent_dispatch_quarantine", {"action": "list", "state": "dropped"}),
        # Closed action enums and show-only or list-only placement.
        ("agent_dispatch_dispatches", {"action": "retry", "dispatch_id": "d-1"}),
        ("agent_dispatch_receipts", {"action": "submit", "receipt_id": "r-1"}),
        ("agent_dispatch_quarantine", {"action": "release", "quarantine_id": "q-1"}),
        ("agent_dispatch_notifications", {"action": "drain"}),
        ("agent_dispatch_receipts", {"action": "list", "receipt_id": "r-1"}),
        ("agent_dispatch_quarantine", {"action": "show", "route": "wiki"}),
        ("agent_dispatch_receipts", {"action": "show", "route": "wiki", "receipt_id": "r-1"}),
        ("agent_dispatch_dispatches", {"action": "show", "dispatch_id": "d-1", "route": "wiki"}),
    ],
)
def test_invalid_requests_are_rejected_before_the_runner(
    plugin, monkeypatch, tool, params, wrapper
):
    """Schema violations close as invalid_argument with no process creation."""
    calls = []

    def spy(*args, **kwargs):
        calls.append(args)
        raise AssertionError("the runner boundary must not be reached by an invalid request")

    monkeypatch.setattr(plugin.runner, "run_inspection", spy)
    result = _handler(plugin, HermesCtxStub(settings={"binary_path": "/nope"}), tool)(**params)
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["exit_code"] == -1
    assert result["operation"] == tool
    assert result["error"]["code"] == "invalid_argument"
    assert result["diagnostics"] == []
    assert calls == []


def test_no_reachable_argv_carries_a_denied_mutation_subcommand(plugin):
    """The read-only proof: every action template token stays inside the
    frozen allowed vocabulary, receipts maps only to list and show, and no
    denied mutation subcommand is reachable in a command slot — validated
    values cannot masquerade as flags (the grammar's lead byte is
    alphanumeric) and occupy only value slots, never a command slot."""
    catalog = plugin.registry.load_catalog()
    vocabulary = catalog["command_vocabulary"]
    allowed = vocabulary["allowed"]
    denied = set(vocabulary["denied_subcommands"])
    for spec in plugin.registry.tool_specs():
        for action in spec.actions:
            argv = list(action.argv_prefix)
            argv += [b["flag"] for b in action.value_bindings if not b.get("positional")]
            argv += [token for flag in action.optional_flags for token in flag["tokens"]]
            argv += list(action.argv_suffix)
            leaked = {token for token in argv if token in denied}
            assert not leaked, (spec.name, action.action_id, leaked)
            if " " in action.expected_command:
                head, sub = action.expected_command.split(" ", 1)
                assert head in allowed and sub in allowed[head], action.expected_command
            else:
                assert action.expected_command in allowed, action.expected_command
    receipts = _tool(plugin, "agent_dispatch_receipts")
    assert sorted(a.expected_command for a in receipts.actions) == [
        "receipts list",
        "receipts show",
    ]


def test_option_prefixed_values_reject_before_the_runner(plugin, monkeypatch):
    """Values carrying an option prefix never reach argv construction: the
    grammar rejects them first, so nothing can smuggle a flag."""
    calls = []
    monkeypatch.setattr(
        plugin.runner,
        "run_inspection",
        lambda *a, **k: calls.append(a),
    )
    handler = _handler(plugin, HermesCtxStub(), "agent_dispatch_receipts")
    for value in ("--retry", "submit ", "complete\n", "-", "-x", "--"):
        result = handler(action="show", receipt_id=value)
        assert result["error"]["code"] == "invalid_argument", value
    assert calls == []


def test_domain_rejection_carries_the_envelope_for_receipts(plugin, tmp_path, wrapper):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "reject", "exit": 5, "command": "receipts show"}
    )
    ctx = HermesCtxStub(settings=installation["config"])
    result = _handler(plugin, ctx, "agent_dispatch_receipts")(action="show", receipt_id="r.9")
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["exit_code"] == 5
    envelope = result["agent_dispatch"]
    assert envelope["ok"] is False
    assert envelope["error"]["retryable"] is False
    assert "error" not in result


def test_malformed_output_closes_with_bounded_stderr_tail(plugin, tmp_path, wrapper):
    installation = make_fake_binary(
        tmp_path, behavior={"kind": "raw", "stdout": "not json\n", "stderr_lines": ["bad-dispatch"]}
    )
    ctx = HermesCtxStub(settings=installation["config"])
    result = _handler(plugin, ctx, "agent_dispatch_dispatches")(action="show", dispatch_id="d-1")
    wrapper.validate(result)
    assert result["ok"] is False
    assert result["error"]["code"] == "malformed_json"
    assert "agent_dispatch" not in result
    assert result["diagnostics"] == ["bad-dispatch"]


def test_valid_dispatch_requests_delegate_exactly_once(plugin, configured_ctx, monkeypatch):
    """The spy wiring stays sound: a valid filtered request delegates once."""
    real = plugin.runner.run_inspection
    calls: list[tuple] = []

    def recording(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(plugin.runner, "run_inspection", recording)
    result = _handler(plugin, configured_ctx, "agent_dispatch_notifications")(route="wiki", limit=5)
    assert result["ok"] is True
    assert len(calls) == 1
