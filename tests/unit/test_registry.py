"""Unit tests for the declarative registry derived from the frozen catalog."""

from __future__ import annotations

import pytest

PRD_ROSTER = [
    "agent_dispatch_status",
    "agent_dispatch_doctor",
    "agent_dispatch_routes",
    "agent_dispatch_dispatches",
    "agent_dispatch_receipts",
    "agent_dispatch_event_show",
    "agent_dispatch_quarantine",
    "agent_dispatch_notifications",
    "agent_dispatch_schedule_inspect",
    "agent_dispatch_config",
]

COMMAND_NOUNS = {
    "status",
    "doctor",
    "route",
    "dispatches",
    "receipts",
    "events",
    "quarantine",
    "notifications",
    "schedule",
    "config",
}


def test_roster_is_exactly_ten_unique_tools_in_prd_order(plugin):
    specs = plugin.registry.tool_specs()
    names = [spec.name for spec in specs]
    assert names == PRD_ROSTER
    assert len(set(names)) == 10


def test_expected_inventory_matches_roster(plugin):
    assert list(plugin.registry.expected_inventory()) == PRD_ROSTER


def test_every_tool_declares_at_least_one_action_with_command_identity(plugin):
    for spec in plugin.registry.tool_specs():
        assert spec.actions, spec.name
        for action in spec.actions:
            assert action.expected_command.split(" ")[0] in COMMAND_NOUNS
            assert list(action.argv_prefix) == action.expected_command.split(" ")


def _tool(plugin, name):
    return next(s for s in plugin.registry.tool_specs() if s.name == name)


def _action(plugin, name, action_id):
    spec = _tool(plugin, name)
    return next(a for a in spec.actions if a.action_id == action_id)


def test_resolve_argv_list_with_all_documented_filters(plugin):
    action = _action(plugin, "agent_dispatch_dispatches", "list")
    argv = action.resolve_argv({"route": "wiki", "state": "unknown", "limit": 25, "offset": 100})
    assert argv == (
        "dispatches",
        "list",
        "--route",
        "wiki",
        "--state",
        "unknown",
        "--limit",
        "25",
        "--offset",
        "100",
        "--output",
        "json",
    )


def test_resolve_argv_list_with_defaults_skips_absent_bindings(plugin):
    action = _action(plugin, "agent_dispatch_dispatches", "list")
    assert action.resolve_argv({}) == ("dispatches", "list", "--output", "json")


def test_resolve_argv_show_uses_positional_identifier(plugin):
    action = _action(plugin, "agent_dispatch_dispatches", "show")
    assert action.resolve_argv({"dispatch_id": "d_7f3a"}) == (
        "dispatches",
        "show",
        "d_7f3a",
        "--output",
        "json",
    )


def test_resolve_argv_routes_show_uses_flagged_identifier(plugin):
    action = _action(plugin, "agent_dispatch_routes", "show")
    assert action.resolve_argv({"route_id": "wiki"}) == (
        "route",
        "show",
        "--route",
        "wiki",
        "--output",
        "json",
    )


def test_resolve_argv_optional_flag_only_when_strictly_true(plugin):
    action = _action(plugin, "agent_dispatch_doctor", "inspect")
    assert action.resolve_argv({}) == ("doctor", "--output", "json")
    assert action.resolve_argv({"probe_targets": False}) == ("doctor", "--output", "json")
    assert action.resolve_argv({"probe_targets": True}) == (
        "doctor",
        "--probe-targets",
        "--output",
        "json",
    )


def test_resolve_argv_schedule_keeps_fixed_platform_suffix(plugin):
    action = _action(plugin, "agent_dispatch_schedule_inspect", "inspect")
    assert action.resolve_argv({"route_id": "wiki"}) == (
        "schedule",
        "inspect",
        "--route",
        "wiki",
        "--platform",
        "launchd",
        "--output",
        "json",
    )


def test_no_denied_subcommand_is_reachable_from_any_action(plugin):
    denied = set(plugin.registry.load_catalog()["command_vocabulary"]["denied_subcommands"])
    for spec in plugin.registry.tool_specs():
        for action in spec.actions:
            argv = action.resolve_argv({})
            assert not denied.intersection(argv), (spec.name, action.action_id)


def test_malformed_roster_fails_loud_before_registration(plugin, broken_catalog):
    def truncate_roster(catalog):
        catalog["tools"] = catalog["tools"][:3]

    broken_catalog(truncate_roster)
    with pytest.raises(plugin.registry.ContractSourceError):
        plugin.registry.tool_specs()


def test_missing_input_schema_fails_loud_before_registration(
    plugin, pristine_registry, broken_catalog, monkeypatch, tmp_path
):
    broken_catalog(lambda catalog: None)
    monkeypatch.setattr(pristine_registry, "CONTRACTS_VERSION_DIR", tmp_path / "nowhere")
    with pytest.raises(plugin.registry.ContractSourceError):
        pristine_registry.tool_specs()


@pytest.mark.parametrize(
    ("corruption", "description"),
    [
        (
            lambda catalog: catalog.update(schema_version="agent-dispatch-plugin.contracts/v9"),
            "wrong schema version",
        ),
        (
            lambda catalog: catalog.update(toolset="agent_dispatch_admin"),
            "toolset mismatch",
        ),
    ],
)
def test_catalog_level_corruption_fails_loud(plugin, broken_catalog, corruption, description):
    broken_catalog(corruption)
    with pytest.raises(plugin.registry.ContractSourceError):
        plugin.registry.load_catalog()


def test_unreadable_catalog_fails_loud(plugin, pristine_registry, tmp_path, monkeypatch):
    monkeypatch.setattr(pristine_registry, "CATALOG_PATH", tmp_path / "absent.json")
    pristine_registry.load_catalog.cache_clear()
    with pytest.raises(plugin.registry.ContractSourceError):
        pristine_registry.load_catalog()
