"""Tool handlers over the EPIC-002 runner trust gate.

Every declared tool registers one handler here. Handlers never create a
process themselves and never touch the network, a database, or Agent
Dispatch state: they resolve the immutable plugin configuration through the
Hermes config API and hand it to the runner trust gate, which owns every
trust failure as a closed contract error. While the bounded execution path
is still being delivered by EPIC-002, a trusted configuration also fails
closed with the frozen execution error; the availability check exposes the
toolset only when the real binary, configuration, and version checks pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:  # The static view matches the degenerate top-level import.
    import runner
    from registry import ToolSpec
elif "." in __package__:  # Normal path: imported as a namespaced plugin submodule.
    from .. import runner
    from ..registry import ToolSpec
else:  # Degenerate top-level import of the plugin root file.
    import runner
    from registry import ToolSpec

RESULT_SCHEMA_VERSION = "agent-dispatch-plugin.result/v1"

# The five immutable settings from the frozen plugin config schema; nothing
# else from the Hermes config tree is ever read.
_SETTING_KEYS = (
    "binary_path",
    "binary_sha256",
    "config_path",
    "timeout_seconds",
    "max_output_bytes",
)

_EXECUTION_PENDING_MESSAGE = (
    "The runner trust gate passed, but the bounded inspection path is not "
    "wired yet; no process was created."
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


def handler_for(spec: ToolSpec, ctx: Any) -> Callable[..., dict[str, Any]]:
    """Build the closed fail-closed handler for one declared tool."""

    def handler(**_kwargs: Any) -> dict[str, Any]:
        try:
            runner.resolve_trust(runner_config(ctx))
        except runner.TrustFailure as failure:
            return runner.trust_failure_result(spec.name, failure)
        return runner.closed_error_result(
            spec.name, runner.EXECUTION_FAILED, _EXECUTION_PENDING_MESSAGE
        )

    handler.__name__ = f"{spec.name}_handler"
    handler.__doc__ = f"Fail-closed handler for {spec.name} over the runner trust gate."
    return handler
