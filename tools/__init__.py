"""Tool handlers over the EPIC-002 runner boundary.

Every declared tool registers one handler here. Handlers never create a
process themselves and never touch the network, a database, or Agent
Dispatch state: they validate the request against the tool's frozen input
schema before anything else runs (ADR-007), resolve the immutable plugin
configuration through the Hermes config API, select the registered action
for the validated request, and delegate to the sole process boundary in
runner.run_inspection. No caller-driven failure raises into Hermes — every
one comes back as a closed fail-closed wrapper result. A frozen-contract
defect raises loudly instead (ADR-007's ContractVocabularyError), because a
silently under-validated contract is worse than a visible one.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:  # The static view matches the degenerate top-level import.
    import runner
    from registry import ActionSpec, ToolSpec
elif "." in __package__:  # Normal path: imported as a namespaced plugin submodule.
    from .. import runner
    from ..registry import ActionSpec, ToolSpec
else:  # Degenerate top-level import of the plugin root file.
    import runner
    from registry import ActionSpec, ToolSpec
# inputs.py lives inside this package, so one relative import serves both
# runtime paths: the namespaced plugin package and the degenerate tools package.
from . import inputs

# The five immutable settings from the frozen plugin config schema; nothing
# else from the Hermes config tree is ever read.
_SETTING_KEYS = (
    "binary_path",
    "binary_sha256",
    "config_path",
    "timeout_seconds",
    "max_output_bytes",
)


def runner_config(ctx: Any) -> dict[str, Any]:
    """Read the five immutable plugin settings through the Hermes config API.

    Any config-system failure reads as an unconfigured plugin so both the
    availability check and handlers fail closed.
    """
    try:
        return {key: ctx.get_config(key) for key in _SETTING_KEYS}
    except Exception:
        return {}


def make_availability_check(ctx: Any) -> Callable[[], bool]:
    """Build the availability probe that gates the toolset per session.

    The toolset is exposed only when the runner trust gate verifies the
    platform, the configured executable identity, the trusted configuration,
    and the supported Agent Dispatch version.
    """

    def check() -> bool:
        return runner.probe_availability(runner_config(ctx))

    check.__name__ = "agent_dispatch_availability"
    check.__doc__ = "Real binary, configuration, and version trust detection."
    return check


def resolve_action(spec: ToolSpec, params: dict[str, Any]) -> ActionSpec | None:
    """Select the one registered action a validated request maps to.

    Multi-action tools match their frozen action value; a single-action tool
    with no action parameter accepts exactly its one registered action.
    """
    requested = params.get("action")
    for action in spec.actions:
        if action.input_action_value is not None:
            if action.input_action_value == requested:
                return action
        elif len(spec.actions) == 1:
            return action
    return None


def handler_for(spec: ToolSpec, ctx: Any) -> Callable[..., str]:
    """Build the closed fail-closed handler for one declared tool.

    The Hermes v0.20.5 dispatcher invokes every tool handler with the
    request object as one positional argument (plus internal context
    keywords the handler ignores) and accepts only a string result, so
    the handler returns the closed wrapper result as its JSON encoding.
    """

    def handler(args: dict[str, Any] | None = None, **_context: Any) -> str:
        params = dict(args or {})
        reason = inputs.validate_tool_input(spec, params)
        if reason is not None:
            return json.dumps(
                runner.closed_error_result(spec.name, runner.INVALID_ARGUMENT, reason)
            )
        action = resolve_action(spec, params)
        if action is None:
            return json.dumps(
                runner.closed_error_result(
                    spec.name,
                    runner.INVALID_ARGUMENT,
                    f"{spec.name}: the request does not map to one registered action",
                )
            )
        # JSON Schema treats 5.0 as the integer 5; canonical validated
        # numbers keep the bound argv identical to the equivalent request.
        canonical = inputs.canonicalize_tool_input(spec, params)
        return json.dumps(runner.run_inspection(action, spec.name, canonical, runner_config(ctx)))

    handler.__name__ = f"{spec.name}_handler"
    handler.__doc__ = f"Fail-closed handler for {spec.name} over the runner boundary."
    return handler
