"""Closed output validation and defense-in-depth redaction (EPIC-002).

This module validates completed Agent Dispatch output: the closed envelope
boundary derived from ``contracts/v0.1.0`` schemas, the closed wrapper carrier
rule, the bounded diagnostics pipeline, and redaction. For the three v0.2.0
sync reads, it loads and checks the closed result schemas from
``contracts/v0.2.0`` at runtime and fails closed if they are unavailable or
unsupported. It never creates a process or raises into Hermes; violations
become closed :class:`EnvelopeViolation` values mapped by the runner.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

ENVELOPE_API_VERSION = "agent-dispatch.cli/v1"

# The closed output-error codes live here once (ADR-006); the runner aliases
# these constants so no second copy of the frozen vocabulary exists.
MALFORMED_JSON = "malformed_json"
CONTRACT_MISMATCH = "contract_mismatch"
REDACTION_FAILURE = "redaction_failure"

_DIAGNOSTICS_MAX_ITEMS = 16
_DIAGNOSTICS_MAX_LENGTH = 512
_ENVELOPE_MEMBERS = frozenset(
    {"api_version", "command", "ok", "result", "error", "warnings", "trace_id"}
)
_ENVELOPE_ERROR_MEMBERS = frozenset({"code", "category", "message", "retryable"})

_REDACTED = "[redacted]"
_REDACTED_URL = "[redacted-url]"
_SYNC_RESULT_SCHEMAS = {
    "sync capabilities": "agent_dispatch_sync_capabilities.result.json",
    "sync status": "agent_dispatch_sync_status.result.json",
    "sync service inspect": "agent_dispatch_sync_service_inspect.result.json",
}
_SYNC_SCHEMA_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "title",
        "description",
        "type",
        "const",
        "enum",
        "properties",
        "required",
        "additionalProperties",
        "maxProperties",
        "items",
        "minItems",
        "maxItems",
        "maxLength",
        "pattern",
        "minimum",
        "allOf",
        "anyOf",
        "not",
        "if",
        "then",
        "else",
    }
)

# The five frozen redaction rules, expressed as deterministic patterns:
# authorization values, secret references that reveal protected paths,
# token-like strings, sensitive webhook URLs, and absolute paths outside
# the configured binary and config display policy.
_RE_AUTHORIZATION = re.compile(r"(?i)\b(bearer|basic|token)\s+[A-Za-z0-9._~+/=-]{8,}")
_RE_SECRET_REFERENCE = re.compile(
    r"(?i)\b(secret|password|credential|private[_-]?key|api[_-]?key)\b[^\S\n]*[:=@\s]+\S+"
)
_RE_TOKEN_HEX = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")
_RE_TOKEN_BASE64 = re.compile(r"(?<![0-9A-Za-z+/])[A-Za-z0-9+/_-]{40,}={0,2}(?![0-9A-Za-z+/=-])")
_RE_WEBHOOK_URL = re.compile(
    r"(?i)\bhttps?://(?:[a-z0-9-]+\.)*hooks\.[a-z0-9.-]+(?:/\S*)?|\bhttps?://\S*webhook\S*"
)
_RE_ABSOLUTE_PATH = re.compile(r"(?<![0-9A-Za-z_.-])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+")

# Protected-path vocabulary for secret references (rule 2): paths that must
# never survive into diagnostics or wrapped results.
_PROTECTED_PATH_HINTS = (
    ".ssh",
    ".gnupg",
    ".secrets",
    "credentials",
    "id_rsa",
    "id_ed25519",
    ".env",
)


class EnvelopeViolation(Exception):
    """One closed validation failure waiting to become a plugin error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@lru_cache(maxsize=3)
def _sync_result_schema(command: str) -> Mapping[str, Any]:
    path = (
        Path(__file__).resolve().parent
        / "contracts"
        / "v0.2.0"
        / "schemas"
        / "results"
        / _SYNC_RESULT_SCHEMAS[command]
    )
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    _check_sync_schema(schema)
    return schema


def _check_sync_schema(schema: Mapping[str, Any]) -> None:
    if not isinstance(schema, dict) or schema.keys() - _SYNC_SCHEMA_KEYWORDS:
        raise ValueError("unsupported sync result schema")
    for branch in schema.get("properties", {}).values():
        _check_sync_schema(branch)
    for name in ("items", "not", "if", "then", "else"):
        if name in schema:
            _check_sync_schema(schema[name])
    for name in ("allOf", "anyOf"):
        for branch in schema.get(name, ()):
            _check_sync_schema(branch)


def _schema_matches(value: Any, schema: Mapping[str, Any]) -> bool:
    """Evaluate the closed keyword subset used by the three frozen result schemas."""
    kind = schema.get("type")
    if (
        kind is not None
        and not {
            "object": lambda: isinstance(value, dict),
            "array": lambda: isinstance(value, list),
            "string": lambda: isinstance(value, str),
            "integer": lambda: type(value) is int,
            "boolean": lambda: type(value) is bool,
            "null": lambda: value is None,
        }[kind]()
    ):
        return False
    if "const" in schema and not (
        type(value) is type(schema["const"]) and value == schema["const"]
    ):
        return False
    if "enum" in schema and not any(
        type(value) is type(member) and value == member for member in schema["enum"]
    ):
        return False
    if isinstance(value, dict):
        if any(name not in value for name in schema.get("required", ())):
            return False
        if "maxProperties" in schema and len(value) > schema["maxProperties"]:
            return False
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and value.keys() - properties.keys():
            return False
        if any(
            not _schema_matches(item, properties[name])
            for name, item in value.items()
            if name in properties
        ):
            return False
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            return False
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            return False
        if "items" in schema and any(not _schema_matches(item, schema["items"]) for item in value):
            return False
    if isinstance(value, str):
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            return False
        # The closed result patterns are end-anchored. Python `$` accepts a
        # position before a final newline, unlike the intended ECMA boundary.
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            return False
    if type(value) is int and "minimum" in schema and value < schema["minimum"]:
        return False
    if "allOf" in schema and not all(_schema_matches(value, branch) for branch in schema["allOf"]):
        return False
    if "anyOf" in schema and not any(_schema_matches(value, branch) for branch in schema["anyOf"]):
        return False
    if "not" in schema and _schema_matches(value, schema["not"]):
        return False
    if "if" in schema:
        branch = "then" if _schema_matches(value, schema["if"]) else "else"
        if branch in schema and not _schema_matches(value, schema[branch]):
            return False
    return True


def validate_sync_result(result: Any, command: str) -> None:
    """Reject an invalid successful sync result before any identity exemption."""
    try:
        valid = _schema_matches(result, _sync_result_schema(command))
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        valid = False
    if not valid or not isinstance(result, dict) or result.get("side_effects") != []:
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the sync result violates its closed contract")


def validate_envelope(payload: Any, expected_command: str) -> Mapping[str, Any]:
    """Validate one parsed Agent Dispatch envelope against the frozen shape.

    Structural and consistency violations close as ``contract_mismatch``;
    anything that is not one JSON envelope object of the frozen protocol
    version closes as ``malformed_json``.
    """
    if not isinstance(payload, Mapping):
        raise EnvelopeViolation(MALFORMED_JSON, "the output was not one JSON envelope object")
    unknown = set(payload) - _ENVELOPE_MEMBERS
    if unknown:
        raise EnvelopeViolation(
            CONTRACT_MISMATCH,
            "the envelope carries members outside the frozen closed boundary",
        )
    for member in ("api_version", "command", "ok"):
        if member not in payload:
            raise EnvelopeViolation(
                CONTRACT_MISMATCH, f"the envelope is missing the {member!r} member"
            )
    if payload["api_version"] != ENVELOPE_API_VERSION:
        raise EnvelopeViolation(MALFORMED_JSON, "the envelope carries an unknown protocol version")
    command = payload["command"]
    if not isinstance(command, str) or not 1 <= len(command) <= 64:
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope command is not a bounded string")
    if not isinstance(payload["ok"], bool):
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope ok member is not boolean")

    if payload["ok"]:
        if "result" not in payload or "error" in payload:
            raise EnvelopeViolation(
                CONTRACT_MISMATCH, "the envelope carriers disagree with ok true"
            )
        if not isinstance(payload["result"], (dict, list)):
            raise EnvelopeViolation(
                CONTRACT_MISMATCH, "the envelope result is not an object or array"
            )
    else:
        if "error" not in payload or "result" in payload:
            raise EnvelopeViolation(
                CONTRACT_MISMATCH, "the envelope carriers disagree with ok false"
            )
        _validate_envelope_error(payload["error"])

    if "warnings" in payload:
        warnings = payload["warnings"]
        if not isinstance(warnings, list) or len(warnings) > 64:
            raise EnvelopeViolation(
                CONTRACT_MISMATCH, "the envelope warnings exceed the frozen bound"
            )
        if not all(isinstance(item, str) and len(item) <= 1024 for item in warnings):
            raise EnvelopeViolation(
                CONTRACT_MISMATCH, "an envelope warning exceeds its frozen bound"
            )
    if "trace_id" in payload:
        trace_id = payload["trace_id"]
        if not isinstance(trace_id, str) or len(trace_id) > 128:
            raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope trace id is not bounded")

    if command != expected_command:
        raise EnvelopeViolation(
            CONTRACT_MISMATCH,
            "the envelope command does not match the executed command",
        )
    return payload


def _validate_envelope_error(error: Any) -> None:
    if not isinstance(error, Mapping):
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope error is not an object")
    unknown = set(error) - _ENVELOPE_ERROR_MEMBERS
    if unknown:
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope error carries unknown members")
    for member in _ENVELOPE_ERROR_MEMBERS:
        if member not in error:
            raise EnvelopeViolation(CONTRACT_MISMATCH, f"the envelope error is missing {member!r}")
    if not isinstance(error["code"], str) or not 1 <= len(error["code"]) <= 64:
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope error code is not bounded")
    if not isinstance(error["category"], str) or not 1 <= len(error["category"]) <= 32:
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope error category is not bounded")
    if not isinstance(error["message"], str):
        raise EnvelopeViolation(CONTRACT_MISMATCH, "the envelope error message is malformed")
    if not isinstance(error["retryable"], bool):
        raise EnvelopeViolation(
            CONTRACT_MISMATCH, "the envelope error retryable flag is not boolean"
        )


def redact_text(
    text: str, allowed_paths: Iterable[str] = (), *, public_identity: bool = False
) -> str:
    """Redact one string under ADR-006 and the narrow ADR-009 exception.

    Allowed display-policy paths are masked first and restored last so their
    own characters are never partially rewritten by the other rules. Only a
    schema-validated sync public identity skips the two token-like patterns.
    """
    allowed = [path for path in allowed_paths if path]
    masks: dict[str, str] = {}
    masked = text
    for index, path in enumerate(allowed):
        mask = f"\x00allowed{index}\x00"
        if path in masked:
            masks[mask] = path
            masked = masked.replace(path, mask)
    masked = _RE_AUTHORIZATION.sub(lambda m: m[0].split(None, 1)[0] + " " + _REDACTED, masked)
    masked = _RE_WEBHOOK_URL.sub(_REDACTED_URL, masked)
    masked = _RE_SECRET_REFERENCE.sub(lambda m: m[0].split(None, 1)[0] + " " + _REDACTED, masked)
    if not public_identity:
        masked = _RE_TOKEN_HEX.sub(_REDACTED, masked)
        masked = _RE_TOKEN_BASE64.sub(_REDACTED, masked)
    masked = _redact_protected_paths(masked)
    for mask, path in masks.items():
        masked = masked.replace(mask, path)
    return masked


def _redact_protected_paths(text: str) -> str:
    """Redact absolute paths: everything except allowed display paths.

    Paths naming a protected location are fully redacted including any
    label; other absolute paths outside the display policy redact to their
    final component so a diagnostic can still name what was involved.
    """

    def replace(match: re.Match[str]) -> str:
        found = match[0]
        if any(hint in found.lower() for hint in _PROTECTED_PATH_HINTS):
            return _REDACTED
        tail = found.rsplit("/", 1)[-1]
        return f"[redacted-path:{tail}]" if tail else "[redacted-path]"

    return _RE_ABSOLUTE_PATH.sub(replace, text)


def redact_value(
    value: Any,
    allowed_paths: Iterable[str] = (),
    public_identity_paths: frozenset[tuple[str, ...]] = frozenset(),
    path: tuple[str, ...] = (),
) -> Any:
    """Recursively redact every string inside one parsed envelope.

    Object keys are redacted like values: a secret surfacing in a JSON key
    position must not survive the boundary either.
    """
    if isinstance(value, str):
        return redact_text(value, allowed_paths, public_identity=path in public_identity_paths)
    if isinstance(value, dict):
        return {
            redact_value(key, allowed_paths): redact_value(
                item, allowed_paths, public_identity_paths, (*path, key)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item, allowed_paths, public_identity_paths, path) for item in value]
    return value


def redact_envelope(
    envelope: Mapping[str, Any],
    allowed_paths: Iterable[str] = (),
    public_identity_paths: frozenset[tuple[str, ...]] = frozenset(),
) -> tuple[dict[str, Any], bool]:
    """Return the redacted envelope and whether any string changed."""
    redacted = redact_value(dict(envelope), allowed_paths, public_identity_paths)
    return redacted, redacted != envelope


def bound_diagnostics(lines: Iterable[str]) -> list[str]:
    """Bound one diagnostic list to the frozen 16-by-512 shape."""
    bounded: list[str] = []
    for line in lines:
        if len(bounded) >= _DIAGNOSTICS_MAX_ITEMS:
            break
        text = line if isinstance(line, str) else str(line)
        if not text:
            continue
        bounded.append(text[:_DIAGNOSTICS_MAX_LENGTH])
    return bounded


def redact_diagnostics(lines: Iterable[str], allowed_paths: Iterable[str] = ()) -> list[str]:
    """Bound and redact one diagnostic list in one pass."""
    return bound_diagnostics(redact_text(line, allowed_paths) for line in lines)
