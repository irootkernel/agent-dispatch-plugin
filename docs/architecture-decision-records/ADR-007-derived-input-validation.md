# ADR-007: Derived Input Validation Before Process Creation

Status: Accepted

## Context

The PRD requires invalid identifiers to be "rejected before process creation
when invalid" and closed input objects (`additionalProperties: false`) for
every tool. TASK-001 froze the per-tool input schemas as the authority for
those constraints, and the EPIC-003 dossier requires negative coverage of
conditional fields, identifier grammars, enums, pagination, and prohibited
properties "without process creation". Until EPIC-003 the handler layer
matched only the `action` member; the runner's argv resolution bound
whatever parameters were present, so schema enforcement lived entirely in
the Hermes-side schema the plugin serves. Defense in depth demands the
plugin itself reject out-of-contract requests before the runner boundary.

The runtime is dependency-free (pyproject has no runtime dependencies), so
the pinned jsonschema toolchain cannot be used inside the plugin process.

## Decision

- `tools/inputs.py` interprets the frozen input schemas with the standard
  library only. It supports exactly the schema subset the frozen inputs use
  — object boundaries (`properties`, `additionalProperties: false` pinned
  explicitly, `maxProperties`), per-property scalar `type`, `enum`,
  `pattern`, `maxLength`, `minimum`, `maximum`, `required`, and
  `allOf`/`if`/`then` conditionals (including `not`/`anyOf`
  forbidden-member bodies) — and raises `ContractVocabularyError` on any
  keyword outside that subset at every structural level the evaluator reads
  (top level, property subschemas, and each conditional body), on non-scalar
  `type` values, and on a missing or permissive `additionalProperties` pin,
  so a future contract change can never be silently under-validated or
  silently stricter than the frozen authority.
- The schemas remain the sole authority (ADR-001): the interpreter composes
  no constraint of its own, and the frozen fixture corpus plus the pinned
  jsonschema cross-check in the unit layer prove agreement case by case.
- Every handler validates its request against its tool's frozen schema
  before anything else runs. A violation returns the closed
  `invalid_argument` wrapper result through `runner.closed_error_result`
  and never reaches `runner.run_inspection`.
- Rejection reasons name schema vocabulary only — property names from the
  frozen schemas and constraint descriptions — never caller-provided
  values, so the message stays bounded and redaction-safe by construction.
- Integer semantics follow the frozen authority exactly: JSON Schema
  defines "integer" mathematically, so a zero-fraction number such as 5.0
  validates as the integer 5 and is canonicalized to that encoding before
  the fixed argv binding, keeping the plugin neither stricter nor looser
  than the schema Hermes validates against.

## Consequences

- Prohibited execution settings (the catalog's
  `forbidden_input_properties`) and every unknown member are rejected with
  no process created, satisfying the PRD's pre-process rejection rule at
  the plugin layer rather than only at the Hermes schema layer.
- The EPIC-002 runner boundary is unchanged: it keeps validating envelopes,
  not requests, and remains the only process creator.
- A canonical contract amendment that extends the schema vocabulary must
  extend this interpreter in the same change; the loud vocabulary guard
  turns drift into an immediate failure instead of a validation gap.
- Tests replay the complete frozen fixture corpus through the interpreter
  and compare verdicts with jsonschema, so interpreter drift is caught by
  `make test-unit`.

## Alternatives

- Validating only inside Hermes via the registered schema: rejected as a
  single point of enforcement outside the plugin's own boundary.
- A runtime jsonschema dependency: rejected because v0.1.0 ships a
  dependency-free runtime.
- Hand-written per-tool validators driven by the catalog: rejected as a
  second authority drifting from the frozen schemas (ADR-001).

## Verification

`tests/unit/test_input_validation.py` cross-checks the interpreter against
the frozen schemas over the complete fixture corpus, the prohibited
property list, and numeric/grammar boundaries;
`tests/unit/test_tools_status_doctor.py` proves handler-level rejection
happens before the runner is reached and that valid requests still
delegate.
