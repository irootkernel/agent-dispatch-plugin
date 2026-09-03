# ADR-001: Declarative Contract Registry and Generated-Artifact Ownership

Status: Accepted

## Context

The PRD requires that manifest, registry, schemas, fixed command descriptors,
and expected tool inventory agree on exactly ten tools, and the implementation
tips require deriving manifest, registry parity, schema inventory, and command
descriptors from one declarative source. TASK-001 freezes the contracts;
TASK-002 creates the Python package, manifest, and registry skeleton.

## Decision

`contracts/v0.1.0/catalog.json` is the single handwritten declarative
authority for the tool roster, action-to-command mappings, identifier and
state grammars, closed enums, pagination bounds, command vocabulary, wrapper,
envelope, and error contracts, limits, compatibility matrix, and redaction
rules, alongside the JSON Schema files and deterministic fixtures it indexes.

Handwritten artifacts: `contracts/v0.1.0/**` (catalog, schemas, fixtures) and
`contracts/validate.py`.

Derived artifacts, which must never be hand-edited and must be regenerated or
parity-checked from the catalog at build or test time: the `plugin.yaml`
`provides_tools` list, the Python tool registration table, the expected tool
inventory used by parity checks, and any generated command descriptor table.
TASK-002 implements the loader and the parity checks that keep these derived
views equal to the catalog.

## Consequences

- Exactly one place changes when a contract changes; parity failures indicate
  a stale derived artifact.
- The validation gate `uv run --with jsonschema contracts/validate.py` is the
  deterministic offline oracle for the frozen contracts.
- Generated views carry no independent authority; a mismatch between a
  generated view and the catalog is a defect in the derivation, never a reason
  to edit the generated file.

## Alternatives

- Handwritten parallel lists in manifest, registry, and tests: rejected as a
  three-way drift risk the PRD explicitly forbids.
- Generating the catalog from Python code: rejected because the contracts must
  be testable and reviewable before the package exists and must outlive
  implementation changes.

## Verification

`contracts/validate.py` (invoked as `uv run --with jsonschema==4.26.0
--with referencing==0.37.0 contracts/validate.py`) asserts roster, mapping,
vocabulary, enum, grammar, and boundary invariants; TASK-002 adds
manifest/registry/inventory parity checks driven by the same catalog.
