"""Skeleton tool handlers.

Every declared tool registers one skeleton handler here. There is no
business-domain behavior: handlers never create a process, never touch the
network, a database, or Agent Dispatch state, and every invocation fails
closed with the frozen binary_unavailable contract error until the EPIC-002
runner wires the real inspection path. The availability check hides the
toolset in normal sessions for the same reason.
"""

from __future__ import annotations

from typing import Any, Callable

if "." in __package__:  # Normal path: imported as a namespaced plugin submodule.
    from ..registry import ToolSpec
else:  # Degenerate top-level import of the plugin root file.
    from registry import ToolSpec

RESULT_SCHEMA_VERSION = "agent-dispatch-plugin.result/v1"

_UNAVAILABLE_MESSAGE = (
    "No Agent Dispatch executable is configured; inspection requires the "
    "runner and operator configuration that EPIC-002 delivers."
)


def availability_check() -> bool:
    """Hide the toolset until binary and version detection exist (EPIC-002)."""
    return False


def handler_for(spec: ToolSpec) -> Callable[..., dict[str, Any]]:
    """Build the closed skeleton result handler for one declared tool."""

    def handler(**_kwargs: Any) -> dict[str, Any]:
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "ok": False,
            "operation": spec.name,
            "exit_code": -1,
            "error": {
                "code": "binary_unavailable",
                "message": _UNAVAILABLE_MESSAGE,
                "retryable": False,
            },
            "diagnostics": [],
        }

    handler.__name__ = f"{spec.name}_skeleton"
    handler.__doc__ = f"Skeleton handler for {spec.name}; fails closed until EPIC-002."
    return handler
