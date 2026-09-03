"""agent-dispatch-plugin — inspection-only Hermes plugin (skeleton).

register(ctx) is the Hermes entrypoint. It derives the complete tool surface
from the frozen contract source through the declarative registry and
registers each tool under the dynamic agent_dispatch toolset with an
availability check that keeps the toolset hidden until the EPIC-002 runner
exists. Registration performs no network, database, migration, or Agent
Dispatch state activity; the only I/O is reading the frozen contract files.
"""

from __future__ import annotations

from typing import Any

if "." in __package__:  # The Hermes loader imports this directory as a package.
    from . import registry
    from . import schemas
    from . import tools as tool_handlers
else:  # Degenerate top-level import of the plugin root file.
    import registry
    import schemas
    import tools as tool_handlers

__all__ = ["register", "registry", "schemas", "toolset"]


def toolset() -> str:
    return registry.toolset()


def register(ctx: Any) -> None:
    """Register exactly the ten declared inspection tools.

    Fails loudly and registers nothing partial when the frozen contract
    source is unavailable: a malformed roster must never yield a silently
    reduced tool surface.
    """
    specs = registry.tool_specs()  # raises ContractSourceError when malformed
    for spec in specs:
        ctx.register_tool(
            name=spec.name,
            toolset=registry.toolset(),
            schema=schemas.input_schema(spec),
            handler=tool_handlers.handler_for(spec),
            check_fn=tool_handlers.availability_check,
            description=schemas.describe(spec),
        )
