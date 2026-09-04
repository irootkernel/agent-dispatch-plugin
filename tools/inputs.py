"""Derived input validation for the frozen tool schemas (EPIC-003).

The handler layer validates every request against its tool's frozen input
schema before any process is created: closed object boundaries, closed
property sets, types, enums, the identifier and state-token grammars,
length and pagination bounds, and the conditional per-action parameter
requirements. The frozen schemas remain the only authority (ADR-001); this
module is a stdlib-only interpreter of the exact schema subset they use and
composes no constraint of its own — including JSON Schema's mathematical
integer semantics, under which a zero-fraction number such as 5.0 is the
integer 5 and is canonicalized to that encoding before argv binding.

Rejections return one bounded, redaction-safe reason string naming schema
vocabulary only — never a caller-provided value — which the handler maps
onto the closed ``invalid_argument`` error before the runner boundary is
reached.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:  # The static view matches the degenerate top-level import.
    from registry import ToolSpec
else:  # Only the schema payload is touched at runtime, so no import is needed.
    ToolSpec = Any

# The schema subset the frozen inputs are permitted to use. A schema that
# reaches for anything outside this vocabulary at load time is a contract
# defect, not a validation nuance: failing loudly here keeps the interpreter
# from silently under-validating a future contract change. The guard walks
# every structural level the evaluator reads — the top level, property
# subschemas, and each allOf/if/then/not/anyOf body — so drift anywhere in
# the frozen shape fails before any request is judged. Each level admits
# exactly the keywords the evaluator consumes there; the top level admits
# no constraint keyword because none is read there.
_TOP_LEVEL_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "title",
        "description",
        "type",
        "properties",
        "additionalProperties",
        "maxProperties",
        "required",
        "allOf",
    }
)
_PROPERTY_KEYWORDS = frozenset(
    {
        "type",
        "enum",
        "pattern",
        "maxLength",
        "minimum",
        "maximum",
        "default",
        "title",
        "description",
    }
)
_ENTRY_KEYWORDS = frozenset({"if", "then"})
_IF_KEYWORDS = frozenset({"properties", "required"})
_MATCH_KEYWORDS = frozenset({"const", "enum"})
_THEN_KEYWORDS = frozenset({"required", "not"})
_NOT_KEYWORDS = frozenset({"required", "anyOf"})
_ANYOF_KEYWORDS = frozenset({"required"})


@lru_cache(maxsize=64)
def _compiled(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern)


class ContractVocabularyError(RuntimeError):
    """The frozen input schema reached outside the supported subset.

    Raised before any request is judged so a future contract change can never
    be silently under-validated by this interpreter. The message carries only
    schema vocabulary, never request content.
    """


def _reject_unsupported(schema: Mapping[str, Any], allowed: frozenset[str], where: str) -> None:
    unsupported = set(schema) - allowed
    if unsupported:
        raise ContractVocabularyError(
            f"the frozen input schema for {where} uses unsupported keywords: {sorted(unsupported)}"
        )


def _check_vocabulary(schema: Mapping[str, Any], tool: str) -> None:
    """Walk the whole frozen shape and reject any keyword the evaluator skips.

    Every structural level the validator reads states its own closed
    vocabulary: the top level, each property subschema, and each
    allOf/if/then/not/anyOf body. A non-scalar ``type``, a permissive or
    absent ``additionalProperties`` pin, or a constraint hidden where the
    evaluator would ignore it fails loudly here instead of silently
    diverging from the frozen authority.
    """
    _reject_unsupported(schema, _TOP_LEVEL_KEYWORDS, tool)
    schema_type = schema.get("type")
    if schema_type is not None and schema_type != "object":
        raise ContractVocabularyError(
            f"the frozen input schema for {tool} must declare type object"
        )
    # The validator enforces a closed member set unconditionally, so a schema
    # that does not pin additionalProperties false would license members the
    # frozen authority permits; that divergence fails loudly too.
    if "additionalProperties" not in schema or schema["additionalProperties"] is not False:
        raise ContractVocabularyError(
            f"the frozen input schema for {tool} must close additionalProperties"
        )
    for name, property_schema in (schema.get("properties") or {}).items():
        if not isinstance(property_schema, Mapping):
            raise ContractVocabularyError(
                f"the frozen input schema for {tool} property {name!r} is not an object"
            )
        _reject_unsupported(property_schema, _PROPERTY_KEYWORDS, f"{tool} property {name!r}")
        property_type = property_schema.get("type")
        if property_type is not None and not isinstance(property_type, str):
            raise ContractVocabularyError(
                f"the frozen input schema for {tool} property {name!r} must declare one scalar type"
            )
    for entry in schema.get("allOf", ()):
        if not isinstance(entry, Mapping):
            raise ContractVocabularyError(
                f"the frozen input schema for {tool} allOf entry is not an object"
            )
        _reject_unsupported(entry, _ENTRY_KEYWORDS, f"{tool} allOf entry")
        condition = entry.get("if") or {}
        _reject_unsupported(condition, _IF_KEYWORDS, f"{tool} allOf if body")
        for name, constraint in (condition.get("properties") or {}).items():
            _reject_unsupported(constraint, _MATCH_KEYWORDS, f"{tool} if constraint {name!r}")
        consequence = entry.get("then") or {}
        _reject_unsupported(consequence, _THEN_KEYWORDS, f"{tool} allOf then body")
        forbidden = consequence.get("not")
        if forbidden is not None:
            _reject_unsupported(forbidden, _NOT_KEYWORDS, f"{tool} then not body")
            for alternative in forbidden.get("anyOf", ()):
                _reject_unsupported(alternative, _ANYOF_KEYWORDS, f"{tool} not anyOf entry")


def _is_integer(value: Any) -> bool:
    # JSON booleans are Python ints; the schemas mean integer exclusively.
    # JSON Schema defines "integer" mathematically, so a number with a zero
    # fractional part (5.0) is an integer exactly like 5.
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and value.is_integer()


def _type_name(property_schema: Mapping[str, Any]) -> str:
    return str(property_schema.get("type", ""))


def _check_property(name: str, value: Any, property_schema: Mapping[str, Any]) -> str | None:
    """Check one declared property against its frozen subschema."""
    expected_type = _type_name(property_schema)
    if expected_type == "string":
        if not isinstance(value, str):
            return f"parameter {name!r} must be a string"
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            return f"parameter {name!r} must be a boolean"
    elif expected_type == "integer":
        if not _is_integer(value):
            return f"parameter {name!r} must be an integer"
    if "enum" in property_schema and value not in property_schema["enum"]:
        return f"parameter {name!r} must be one of its frozen values"
    if isinstance(value, str):
        pattern = property_schema.get("pattern")
        if pattern is not None and _compiled(str(pattern)).fullmatch(value) is None:
            return f"parameter {name!r} violates its frozen grammar"
        max_length = property_schema.get("maxLength")
        if max_length is not None and len(value) > int(max_length):
            return f"parameter {name!r} exceeds its frozen length bound"
    if _is_integer(value):
        minimum = property_schema.get("minimum")
        if minimum is not None and value < int(minimum):
            return f"parameter {name!r} is below its frozen minimum"
        maximum = property_schema.get("maximum")
        if maximum is not None and value > int(maximum):
            return f"parameter {name!r} is above its frozen maximum"
    return None


def _condition_matches(params: Mapping[str, Any], condition: Mapping[str, Any]) -> bool:
    """Evaluate one ``if`` condition: property constraints plus presence."""
    for name, constraint in (condition.get("properties") or {}).items():
        if name not in params:
            continue
        if "const" in constraint and params[name] != constraint["const"]:
            return False
        if "enum" in constraint and params[name] not in constraint["enum"]:
            return False
    return all(name in params for name in condition.get("required", ()))


def _required_conflict(params: Mapping[str, Any], schema: Mapping[str, Any]) -> bool:
    """Evaluate a ``then`` body: required members minus forbidden members."""
    for name in schema.get("required", ()):
        if name not in params:
            return True
    forbidden = schema.get("not")
    if forbidden is None:
        return False
    if "required" in forbidden and all(name in params for name in forbidden["required"]):
        return True
    for alternative in forbidden.get("anyOf", ()):
        if all(name in params for name in alternative.get("required", ())):
            return True
    return False


def validate_input(schema: Mapping[str, Any], params: Mapping[str, Any], tool: str) -> str | None:
    """Validate one request against its frozen input schema.

    Returns ``None`` when the request satisfies every frozen constraint and
    one bounded reason string otherwise. The reason names schema vocabulary
    only, so it is safe to surface in a closed error message.
    """
    _check_vocabulary(schema, tool)
    properties = schema.get("properties") or {}
    unknown = set(params) - set(properties)
    if unknown:
        return f"{tool}: the request carries members outside the frozen input schema"
    max_properties = schema.get("maxProperties")
    if max_properties is not None and len(params) > int(max_properties):
        return f"{tool}: the request carries more members than the frozen input allows"
    for name in schema.get("required", ()):
        if name not in params:
            return f"{tool}: the request is missing required parameter {name!r}"
    for name, value in params.items():
        reason = _check_property(name, value, properties[name])
        if reason is not None:
            return f"{tool}: {reason}"
    for entry in schema.get("allOf", ()):
        if _condition_matches(params, entry.get("if") or {}):
            if _required_conflict(params, entry.get("then") or {}):
                return f"{tool}: the request violates the frozen conditional parameter requirements"
    return None


def validate_tool_input(spec: ToolSpec, params: Mapping[str, Any]) -> str | None:
    """Validate one request against its tool's frozen input schema."""
    return validate_input(spec.load_input_schema(), params, spec.name)


def canonicalize_input(schema: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
    """Return validated params with integer-typed numbers in canonical form.

    JSON Schema treats 5.0 as the integer 5, so a validated zero-fraction
    float is converted to its canonical integer encoding before the request
    reaches argv binding; every other value passes through unchanged. The
    caller must validate first: a non-integral float is not canonicalized
    here, it is rejected by validation.
    """
    canonical = dict(params)
    for name, property_schema in (schema.get("properties") or {}).items():
        if property_schema.get("type") != "integer" or name not in canonical:
            continue
        value = canonical[name]
        if isinstance(value, float) and not isinstance(value, bool) and value.is_integer():
            canonical[name] = int(value)
    return canonical


def canonicalize_tool_input(spec: ToolSpec, params: Mapping[str, Any]) -> dict[str, Any]:
    """Canonicalize one validated request for its tool's fixed argv binding."""
    return canonicalize_input(spec.load_input_schema(), params)
