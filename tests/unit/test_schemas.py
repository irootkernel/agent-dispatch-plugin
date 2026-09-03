"""Unit tests for the model-facing schema layer."""

from __future__ import annotations

import pytest


def test_every_input_schema_is_a_closed_object_schema(plugin):
    for spec in plugin.registry.tool_specs():
        schema = plugin.schemas.input_schema(spec)
        assert schema.get("type") == "object"
        assert schema.get("additionalProperties") is False, spec.name


def test_descriptions_are_nonempty_and_match_the_catalog(plugin):
    catalog = plugin.registry.load_catalog()
    frozen = {tool["name"]: tool["description"] for tool in catalog["tools"]}
    for spec in plugin.registry.tool_specs():
        assert plugin.schemas.describe(spec) == frozen[spec.name]
        assert plugin.schemas.describe(spec).strip()


def test_plugin_description_equals_the_catalog_value(plugin):
    assert (
        plugin.schemas.plugin_description()
        == plugin.registry.load_catalog()["plugin"]["description"]
    )


def test_plugin_description_fails_loud_on_missing_block(plugin, broken_catalog):
    broken_catalog(lambda catalog: catalog.pop("plugin"))
    with pytest.raises(plugin.registry.ContractSourceError):
        plugin.schemas.plugin_description()
