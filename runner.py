"""The sole process-execution boundary (EPIC-002 secure runner).

This is the only module allowed to create a process. Before any inspection
command runs, the trust gate resolves immutable plugin configuration and
verifies the host platform, the absolute non-symlink executable and trusted
configuration paths, the executable SHA-256 identity, and the supported
Agent Dispatch version. The bounded executor then runs exactly one fixed
argv in a fresh process group with a neutral working directory, a minimal
environment allowlist, closed extra descriptors, and concurrent bounded
draining of both streams; the deadline and the byte ceilings terminate the
whole process group through the TERM-then-force-kill ladder and discard
every captured byte. Completed output is validated against the frozen
closed envelope boundary with command identity and exit consistency, every
string is redacted under the five frozen rules, and diagnostics stay
bounded. Failures map onto the frozen closed error set and never raise
into Hermes.

Every limit and compatibility constant is derived from the frozen catalog
(ADR-001); nothing here hand-edits a derived view of the command surface.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform as platform_module
import re
import select
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:  # The static view matches the degenerate top-level import.
    import envelopes
    from registry import ActionSpec, PLUGIN_ROOT, load_catalog
elif "." in __package__:  # Normal path: imported as a plugin package module.
    from . import envelopes
    from .registry import ActionSpec, PLUGIN_ROOT, load_catalog
else:  # Degenerate top-level import of the plugin root file.
    import envelopes
    from registry import ActionSpec, PLUGIN_ROOT, load_catalog

RESULT_SCHEMA_VERSION = "agent-dispatch-plugin.result/v1"

BINARY_UNAVAILABLE = "binary_unavailable"
UNSUPPORTED_AGENT_DISPATCH_VERSION = "unsupported_agent_dispatch_version"
INVALID_ARGUMENT = "invalid_argument"
TIMEOUT = "timeout"
OUTPUT_TOO_LARGE = "output_too_large"
ADAPTER_USAGE_ERROR = "adapter_usage_error"
EXECUTION_FAILED = "execution_failed"
# The closed output-error vocabulary is owned by envelopes (ADR-006); these
# aliases keep one frozen copy of every code.
MALFORMED_JSON = envelopes.MALFORMED_JSON
CONTRACT_MISMATCH = envelopes.CONTRACT_MISMATCH
REDACTION_FAILURE = envelopes.REDACTION_FAILURE

NOT_CONFIGURED_MESSAGE = (
    "No Agent Dispatch executable is configured; inspection requires "
    "operator-provided binary_path, binary_sha256, and config_path."
)

# The execution environment is fixed in code (ADR-005): a system PATH, a
# writable temp directory, and nothing else — no HOME, no inherited Hermes
# or agent environment, no proxy or credential variables.
MINIMAL_ENVIRONMENT: dict[str, str] = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "TMPDIR": "/tmp",
}
NEUTRAL_CWD = PLUGIN_ROOT

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_VERSION_OUTPUT_MAX_BYTES = 65536
_DRAIN_CHUNK_BYTES = 65536
_WAIT_SLICE_SECONDS = 0.05


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


def _kill_probe_tree(process: subprocess.Popen[Any]) -> None:
    """Kill the whole probe process group and reap the direct child.

    The probe runs in its own session; a binary that forks helpers cannot
    leave them behind when the probe is discarded.
    """
    try:
        group = os.getpgid(process.pid)
    except ProcessLookupError:
        group = None
    if group is not None:
        try:
            os.killpg(group, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    process.wait()


def _verify_supported_version(trust: RunnerTrust) -> None:
    """Probe the executable identity through the real `version` subcommand.

    The probe reuses the configured deadline so a hung binary cannot pin the
    availability check beyond the operator-chosen bound, and its stdout is
    captured through a select loop capped at the frozen probe bound, so a
    hostile producer cannot balloon the plugin's memory before the size
    check. A binary that cannot answer, or answers outside the frozen
    range, is not trusted.
    """
    argv = (os.fspath(trust.binary_path), "version", "--json")
    try:
        process = subprocess.Popen(
            argv,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=MINIMAL_ENVIRONMENT,
            cwd=NEUTRAL_CWD,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as exc:
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the configured Agent Dispatch executable did not answer the version probe",
        ) from exc
    sink = bytearray()
    timed_out = False
    overflowed = False
    stdout = process.stdout
    if stdout is None:  # stdout=PIPE always provides a stream; stay typed and closed
        _kill_probe_tree(process)
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the configured Agent Dispatch executable did not answer the version probe",
        )
    descriptor = stdout.fileno()
    deadline = time.monotonic() + trust.timeout_seconds
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            ready, _, _ = select.select([descriptor], [], [], min(remaining, 0.1))
            if not ready:
                continue
            chunk = os.read(descriptor, _DRAIN_CHUNK_BYTES)
            if not chunk:
                break
            if len(sink) + len(chunk) > _VERSION_OUTPUT_MAX_BYTES:
                overflowed = True
                break
            sink += chunk
    finally:
        if timed_out or overflowed:
            _kill_probe_tree(process)
        else:
            # A binary can close stdout and still hang: the reap honors the
            # same deadline, and a late expiry discards the whole group.
            try:
                process.wait(timeout=max(0.0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_probe_tree(process)
        stdout.close()
    if timed_out:
        raise TrustFailure(
            BINARY_UNAVAILABLE,
            "the configured Agent Dispatch executable did not answer the version probe",
        )
    if overflowed:
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the Agent Dispatch version probe exceeded its bounded output",
        )
    if process.returncode != 0:
        raise TrustFailure(
            UNSUPPORTED_AGENT_DISPATCH_VERSION,
            "the Agent Dispatch version probe exited with a failure status",
        )
    version = _parse_version_output(bytes(sink))
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
    spec: ActionSpec,
    operation: str,
    params: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute exactly one fixed inspection command through the full boundary.

    The argv is the trusted executable, the action's registered template,
    and the trusted --config flag; shell is never used and no execution
    setting is reachable from model input. Both streams drain concurrently
    under the frozen byte ceilings; the deadline and any overflow terminate
    the whole process group through the TERM-then-force-kill ladder and
    discard every captured byte. Nothing is ever retried.
    """
    try:
        trust = resolve_trust(config)
    except TrustFailure as failure:
        return trust_failure_result(operation, failure)

    argv = (os.fspath(trust.binary_path),) + spec.resolve_argv(params)
    argv = argv + ("--config", os.fspath(trust.config_path))
    try:
        outcome = _execute_bounded(argv, trust)
    except OSError:
        return closed_error_result(
            operation,
            EXECUTION_FAILED,
            "the inspection process could not be started; no output was captured",
        )

    if outcome.timed_out:
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "ok": False,
            "operation": operation,
            "exit_code": -1,
            "error": {
                "code": TIMEOUT,
                "message": (
                    "the inspection exceeded its deadline and the process "
                    "group was terminated; captured output was discarded"
                ),
                "retryable": False,
            },
            "diagnostics": [
                f"deadline of {trust.timeout_seconds} seconds reached; "
                "terminated the process group and discarded all captured output"
            ],
        }
    if outcome.overflowed:
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "ok": False,
            "operation": operation,
            "exit_code": -1,
            "error": {
                "code": OUTPUT_TOO_LARGE,
                "message": (
                    "the inspection output exceeded a frozen byte ceiling; "
                    "the process group was terminated and captured output "
                    "was discarded"
                ),
                "retryable": False,
            },
            "diagnostics": [
                "a stream or combined byte ceiling was exceeded; terminated "
                "the process group and discarded all captured output"
            ],
        }

    return _map_completed_process(operation, outcome, spec, trust)


def _map_completed_process(
    operation: str, outcome: _Outcome, spec: ActionSpec, trust: RunnerTrust
) -> dict[str, Any]:
    """Map one completed process onto the closed wrapper shape.

    The envelope is validated against the frozen closed boundary with the
    action's expected command identity, every string inside it is redacted
    under the five frozen rules, and diagnostics are bounded and redacted;
    a failure inside the redaction pipeline itself closes as
    redaction_failure.
    """
    exit_code = outcome.exit_code if outcome.exit_code is not None else -1
    try:
        parsed = json.loads(outcome.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        return _malformed_with_stderr_tail(
            operation, exit_code, outcome, trust, "stdout was not parseable JSON"
        )
    try:
        envelope = envelopes.validate_envelope(parsed, spec.expected_command)
        if envelope["ok"] and exit_code != 0:
            raise envelopes.EnvelopeViolation(
                CONTRACT_MISMATCH,
                "the envelope reports success while the process exited with a failure status",
            )
        redacted, changed = envelopes.redact_envelope(envelope, _display_policy_paths(trust))
    except envelopes.EnvelopeViolation as violation:
        return _malformed_with_stderr_tail(
            operation, exit_code, outcome, trust, violation.message, violation.code
        )
    except Exception:
        return closed_error_result(
            operation,
            REDACTION_FAILURE,
            "the redaction pipeline failed; the inspection output was discarded",
            exit_code=exit_code,
        )

    diagnostics: list[str] = []
    if changed:
        diagnostics.append(
            "upstream output contained redactable content; sensitive strings "
            "were removed before returning the envelope"
        )
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "ok": envelope["ok"],
        "operation": operation,
        "exit_code": exit_code,
        "agent_dispatch": redacted,
        "diagnostics": diagnostics,
    }


def _malformed_with_stderr_tail(
    operation: str,
    exit_code: int,
    outcome: _Outcome,
    trust: RunnerTrust,
    reason: str,
    code: str = MALFORMED_JSON,
) -> dict[str, Any]:
    """Fail closed with a bounded, redacted stderr tail as diagnostics.

    Stderr never enters results raw; only bounded redacted lines from its
    tail are surfaced, and only when no validated envelope exists.
    """
    try:
        tail = outcome.stderr.decode("utf-8", errors="replace").splitlines()[-16:]
        diagnostics = envelopes.redact_diagnostics(tail, _display_policy_paths(trust))
    except Exception:
        return closed_error_result(
            operation,
            REDACTION_FAILURE,
            "the redaction pipeline failed",
            exit_code=exit_code,
        )
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "ok": False,
        "operation": operation,
        "exit_code": exit_code,
        "error": {
            "code": code,
            "message": f"the Agent Dispatch output was rejected: {reason}",
            "retryable": False,
        },
        "diagnostics": diagnostics,
    }


def _display_policy_paths(trust: RunnerTrust) -> tuple[str, ...]:
    """The absolute paths the display policy allows to appear verbatim."""
    return (os.fspath(trust.binary_path), os.fspath(trust.config_path))


@dataclass
class _DrainState:
    """Shared bounded-capture state between the two drain threads."""

    combined_cap: int
    combined_bytes: int = 0
    overflow: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass(frozen=True)
class _Outcome:
    """One terminal execution result; captured bytes are already discarded
    whenever timed_out or overflowed is set."""

    timed_out: bool
    overflowed: bool
    exit_code: int | None
    stdout: bytes
    stderr: bytes = b""


def _drain_stream(stream: Any, cap: int, state: _DrainState, sink: list[bytes]) -> None:
    """Drain one stream into a bounded sink, flagging the first overflow.

    Reads are unbuffered partial reads: each os.read returns whatever the
    pipe currently holds, so every partial chunk is checked against the
    ceilings immediately instead of blocking until a full buffer or EOF.
    The reader stops storing at the first byte that would cross its own or
    the combined ceiling; the executor terminates the group immediately.
    """
    descriptor = stream.fileno()
    try:
        while True:
            chunk = os.read(descriptor, _DRAIN_CHUNK_BYTES)
            if not chunk:
                break
            with state.lock:
                if state.overflow:
                    break
                if (
                    len(sink[0]) + len(chunk) > cap
                    or state.combined_bytes + len(chunk) > state.combined_cap
                ):
                    state.overflow = True
                    sink[0] = b""
                    break
                sink[0] += chunk
                state.combined_bytes += len(chunk)
    finally:
        stream.close()


def _terminate_process_group(process: subprocess.Popen[Any], grace_seconds: float) -> None:
    """Run the frozen TERM-then-force-kill ladder over the whole group."""
    try:
        group = os.getpgid(process.pid)
    except ProcessLookupError:
        group = None
    if group is not None:
        try:
            os.killpg(group, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    if group is not None:
        try:
            os.killpg(group, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    process.wait()


def _execute_bounded(argv: tuple[str, ...], trust: RunnerTrust) -> _Outcome:
    """Spawn one fresh process group and drain it under the frozen bounds."""
    limits = _limits()
    termination = limits["termination"]
    grace_seconds = float(termination["grace_period_seconds"])
    stdout_cap = min(int(limits["stdout_max_bytes"]), trust.max_output_bytes)
    stderr_cap = min(int(limits["stderr_max_bytes"]), trust.max_output_bytes)

    process = subprocess.Popen(
        argv,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=NEUTRAL_CWD,
        env=MINIMAL_ENVIRONMENT,
        close_fds=True,
        start_new_session=True,
    )
    state = _DrainState(combined_cap=trust.max_output_bytes)
    stdout_sink: list[bytes] = [b""]
    stderr_sink: list[bytes] = [b""]
    readers = [
        threading.Thread(target=_drain_stream, args=(s, c, state, k), daemon=True)
        for s, c, k in (
            (process.stdout, stdout_cap, stdout_sink),
            (process.stderr, stderr_cap, stderr_sink),
        )
    ]
    for reader in readers:
        reader.start()

    timed_out = False
    deadline = time.monotonic() + trust.timeout_seconds
    while True:
        try:
            process.wait(timeout=_WAIT_SLICE_SECONDS)
            break
        except subprocess.TimeoutExpired:
            pass
        with state.lock:
            overflow_now = state.overflow
        if overflow_now:
            _terminate_process_group(process, grace_seconds)
            break
        if time.monotonic() >= deadline:
            timed_out = True
            _terminate_process_group(process, grace_seconds)
            break

    for reader in readers:
        reader.join(timeout=grace_seconds + 5.0)

    # A stream can cross its ceiling in the same instant the process exits
    # (or through the pipe backlog after the reader stopped), so the overflow
    # flag is authoritative even when the wait loop observed a clean exit.
    with state.lock:
        overflowed = state.overflow

    exit_code = process.returncode
    if timed_out or overflowed:
        return _Outcome(timed_out=timed_out, overflowed=overflowed, exit_code=exit_code, stdout=b"")
    return _Outcome(
        timed_out=False,
        overflowed=False,
        exit_code=exit_code,
        stdout=stdout_sink[0],
        stderr=stderr_sink[0],
    )
