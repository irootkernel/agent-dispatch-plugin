"""Model-facing schema access derived from the frozen contract source.

The JSON parameter schemas and tool descriptions served to Hermes are the
frozen contracts/v0.1.0 artifacts; this layer only reads them. It composes
no schema of its own and adds no properties (ADR-001: derived views carry no
independent authority).
"""

from __future__ import annotations

from typing import Any

from .registry import ContractSourceError, ToolSpec, load_catalog


def input_schema(spec: ToolSpec) -> dict[str, Any]:
    """Return the frozen input schema for one tool."""
    return spec.load_input_schema()


def describe(spec: ToolSpec) -> str:
    """Return the frozen model-facing description for one tool."""
    return spec.description


def plugin_description() -> str:
    """Return the concise operational plugin description from the catalog.

    Fails loudly like every other derived view: a malformed plugin block
    must never surface as a plausible-looking placeholder.
    """
    plugin = load_catalog().get("plugin")
    if not isinstance(plugin, dict) or not isinstance(plugin.get("description"), str):
        raise ContractSourceError("catalog plugin.description is missing or malformed")
    return plugin["description"]
