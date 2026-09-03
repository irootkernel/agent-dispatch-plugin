"""The sole process-execution boundary (stub).

When EPIC-002 implements the hardened runner, this will be the only module
allowed to create a process: fixed argv built from registry action specs,
shell disabled, trusted absolute non-symlink binary and config paths with a
verified SHA-256, bounded concurrent stream draining, deadline and
process-group termination, envelope validation against the frozen contracts,
and closed redacted errors. Nothing in the skeleton calls into this module;
the skeleton handlers fail closed without creating any process.
"""

from __future__ import annotations

from typing import Any, Mapping

if "." in __package__:  # Normal path: imported as a plugin package module.
    from .registry import ActionSpec
else:  # Degenerate top-level import of the plugin root file.
    from registry import ActionSpec

BOUNDARY_UNIMPLEMENTED = (
    "runner.run_inspection is implemented by EPIC-002; the skeleton never "
    "creates a process and no handler calls this boundary."
)


def run_inspection(
    spec: ActionSpec, params: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    """Execute one fixed inspection command (not implemented in the skeleton)."""
    raise RuntimeError(BOUNDARY_UNIMPLEMENTED)
