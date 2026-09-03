"""The sole process-execution boundary (EPIC-002 secure runner).

This is the only module allowed to create a process. Before any inspection
command runs, the trust gate resolves immutable plugin configuration and
verifies the host platform, the absolute non-symlink executable and trusted
configuration paths, the executable SHA-256 identity, and the supported
Agent Dispatch version. Trust failures map onto the frozen closed error set
and never raise into Hermes.

Every limit and compatibility constant is derived from the frozen catalog
(ADR-001); nothing here hand-edits a derived view of the command surface.
The bounded process-group execution and envelope validation arrive with the
remaining EPIC-002 tasks; until then run_inspection fails closed after the
trust gate.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform as platform_module
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:  # The static view matches the degenerate top-level import.
    from registry import ActionSpec, load_catalog
elif "." in __package__:  # Normal path: imported as a plugin package module.
    from .registry import ActionSpec, load_catalog
else:  # Degenerate top-level import of the plugin root file.
    from registry import ActionSpec, load_catalog

RESULT_SCHEMA_VERSION = "agent-dispatch-plugin.result/v1"

BINARY_UNAVAILABLE = "binary_unavailable"
UNSUPPORTED_AGENT_DISPATCH_VERSION = "unsupported_agent_dispatch_version"
ADAPTER_USAGE_ERROR = "adapter_usage_error"
EXECUTION_FAILED = "execution_failed"

BOUNDARY_UNIMPLEMENTED = (
    "runner.run_inspection executes the bounded process group from the EPIC-002 "
    "process-runner task onward; the trust gate is the only active stage."
)

NOT_CONFIGURED_MESSAGE = (
    "No Agent Dispatch executable is configured; inspection requires "
    "operator-provided binary_path, binary_sha256, and config_path."
)

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_VERSION_OUTPUT_MAX_BYTES = 65536


class TrustFailure(Exception):
    """One closed trust-gate failure waiting to become a plugin error.

    The code is always one of the frozen error codes and the message is
    already bounded and redaction-safe: it names the failing check, never
    the resolved paths, digests, or captured process output.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class RunnerTrust:
    """The verified execution identity one inspection command may use."""

    binary_path: Path
    config_path: Path
    timeout_seconds: int
    max_output_bytes: int


@lru_cache(maxsize=1)
def _limits() -> Mapping[str, Any]:
    limits = load_catalog().get("limits")
    if not isinstance(limits, Mapping):
        raise TrustFailure(ADAPTER_USAGE_ERROR, "the frozen catalog does not declare runner limits")
    return limits


@lru_cache(maxsize=1)
def _supported_version_range() -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Parse the frozen `agent_dispatch` compatibility range into bounds."""
    spec = load_catalog().get("compatibility", {}).get("agent_dispatch")
    match = re.fullmatch(r">=(\d+)\.(\d+)\.(\d+),<(\d+)\.(\d+)\.(\d+)", str(spec))
    if match is None:
        raise TrustFailure(
            ADAPTER_USAGE_ERROR,
            "the frozen catalog declares an unsupported version-range shape",
        )
    low = (int(match[1]), int(match[2]), int(match[3]))
    high = (int(match[4]), int(match[5]), int(match[6]))
    return low, high


def closed_error_result(
    operation: str, code: str, message: str, exit_code: int = -1
) -> dict[str, Any]:
    """Build the frozen fail-closed wrapper result for one plugin error."""
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "ok": False,
        "operation": operation,
        "exit_code": exit_code,
        "error": {"code": code, "message": message, "retryable": False},
        "diagnostics": [],
    }


def trust_failure_result(operation: str, failure: TrustFailure) -> dict[str, Any]:
    """Map one trust failure onto the closed wrapper result shape."""
    return closed_error_result(operation, failure.code, failure.message)


def _required_string(config: Mapping[str, Any], key: str) -> str | None:
    value = config.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise TrustFailure(
            ADAPTER_USAGE_ERROR, f"plugin setting {key!r} must be a non-empty string"
        )
    return value


def _bounded_int(
    config: Mapping[str, Any], key: str, default: int, minimum: int, maximum: int
) -> int:
    value = config.get(key)
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise TrustFailure(ADAPTER_USAGE_ERROR, f"plugin setting {key!r} must be an integer")
    if not minimum <= value <= maximum:
        raise TrustFailure(
            ADAPTER_USAGE_ERROR,
            f"plugin setting {key!r} must be between {minimum} and {maximum}",
        )
    return value


def _verify_platform() -> None:
    expected = str(load_catalog().get("compatibility", {}).get("platform", ""))
    machine = platform_module.machine().lower()
    if expected == "darwin/arm64":
        supported = sys.platform == "darwin" and machine in ("arm64", "aarch64")
    else:  # pragma: no cover - the frozen catalog pins darwin/arm64 for v0.1.0
        supported = False
    if not supported:
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "this plugin build supports Darwin arm64 hosts only",
        )


def _verify_unlinked_absolute_path(raw: str, setting: str) -> Path:
    """Accept one absolute path whose every component is not a symlink."""
    if not os.path.isabs(raw):
        raise TrustFailure(
            ADAPTER_USAGE_ERROR, f"plugin setting {setting!r} must be an absolute path"
        )
    path = Path(raw)
    probe = path
    while probe != probe.parent:
        if probe.is_symlink():
            raise TrustFailure(
                BINARY_UNAVAILABLE,
                f"the trusted {setting} path or one of its parents is a symlink",
            )
        probe = probe.parent
    return path


def _verify_binary_digest(path: Path, expected_digest: str) -> None:
    digest = hashlib.sha256()
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise TrustFailure(
            BINARY_UNAVAILABLE, "the configured Agent Dispatch executable is unreadable"
        ) from exc
    try:
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(descriptor)
    if digest.hexdigest() != expected_digest:
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the configured Agent Dispatch executable does not match its pinned SHA-256 identity",
        )


def _parse_version_output(stdout: bytes) -> tuple[int, int, int]:
    """Parse the binary's `version --json` payload into a version tuple."""
    if len(stdout) > _VERSION_OUTPUT_MAX_BYTES:
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the Agent Dispatch version probe returned an oversized payload",
        )
    try:
        payload = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the Agent Dispatch version probe did not return valid JSON",
        ) from exc
    if not isinstance(payload, Mapping) or payload.get("name") != "agent-dispatch":
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the Agent Dispatch version probe returned an unexpected payload",
        )
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", str(payload.get("version", "")))
    if match is None:
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the Agent Dispatch version probe returned an unparseable version",
        )
    return (int(match[1]), int(match[2]), int(match[3]))


def _verify_supported_version(trust: RunnerTrust) -> None:
    """Probe the executable identity through the real `version` subcommand.

    The probe reuses the configured deadline so a hung binary cannot pin the
    availability check beyond the operator-chosen bound. A binary that cannot
    answer, or answers outside the frozen range, is not trusted.
    """
    try:
        completed = subprocess.run(
            [os.fspath(trust.binary_path), "version", "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=trust.timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the configured Agent Dispatch executable did not answer the version probe",
        ) from exc
    if completed.returncode != 0:
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the Agent Dispatch version probe exited with a failure status",
        )
    version = _parse_version_output(completed.stdout)
    low, high = _supported_version_range()
    if not low <= version < high:
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the configured Agent Dispatch executable is outside the supported version range",
        )


def resolve_trust(config: Mapping[str, Any]) -> RunnerTrust:
    """Resolve and verify the immutable execution identity from config.

    Raises TrustFailure with a closed error code for every rejection; the
    caller decides whether that becomes a fail-closed wrapper or a hidden
    toolset.
    """
    _verify_platform()
    binary_raw = _required_string(config, "binary_path")
    config_raw = _required_string(config, "config_path")
    digest_raw = _required_string(config, "binary_sha256")
    if binary_raw is None or config_raw is None or digest_raw is None:
        raise TrustFailure(BINARY_UNAVAILABLE, NOT_CONFIGURED_MESSAGE)
    if not _SHA256_HEX.fullmatch(digest_raw):
        raise TrustFailure(
            ADAPTER_USAGE_ERROR,
            "plugin setting 'binary_sha256' must be a lowercase 64-character SHA-256 digest",
        )
    timeout_limits = _limits()["timeout_seconds"]
    timeout = _bounded_int(
        config,
        "timeout_seconds",
        int(timeout_limits["default"]),
        int(timeout_limits["min"]),
        int(timeout_limits["max"]),
    )
    combined_ceiling = int(_limits()["combined_max_bytes"])
    max_output = _bounded_int(config, "max_output_bytes", combined_ceiling, 1, combined_ceiling)

    binary_path = _verify_unlinked_absolute_path(binary_raw, "binary_path")
    config_path = _verify_unlinked_absolute_path(config_raw, "config_path")
    if not binary_path.is_file():
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the configured Agent Dispatch executable does not exist as a regular file",
        )
    if not os.access(binary_path, os.X_OK):
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the configured Agent Dispatch executable is not executable",
        )
    if not config_path.is_file():
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the trusted Agent Dispatch configuration file does not exist as a regular file",
        )
    _verify_binary_digest(binary_path, digest_raw)
    trust = RunnerTrust(
        binary_path=binary_path,
        config_path=config_path,
        timeout_seconds=timeout,
        max_output_bytes=max_output,
    )
    _verify_supported_version(trust)
    return trust


def probe_availability(config: Mapping[str, Any]) -> bool:
    """Report whether the trust gate currently passes for this config."""
    try:
        resolve_trust(config)
    except TrustFailure:
        return False
    return True


def run_inspection(
    spec: ActionSpec, params: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    """Execute one fixed inspection command (not implemented yet).

    The trust gate above is complete; the bounded process-group execution
    arrives with the next EPIC-002 task. Nothing calls this entrypoint until
    then: handlers fail closed through the trust gate instead, so this
    boundary still never creates a process.
    """
    raise RuntimeError(BOUNDARY_UNIMPLEMENTED)
