# ADR-008: Preserve Doctor Findings at Exit Code 3

Status: Accepted

## Context

Agent Dispatch v0.1.6 and v0.1.7 intentionally emit an `ok: true` doctor
findings envelope with exit code 3 when error-severity findings exist.
The fixed child PATH makes Homebrew Watchman unavailable, exposing this
normal diagnostic outcome. Rejecting it hides the findings the tool exists
to inspect. The maintainer approved this amendment before the first release.

## Decision

Only `agent_dispatch_doctor` with the validated command identity `doctor`
accepts an `ok: true` envelope at exit code 3 as well as 0. Preserve the
actual exit code and the original domain values after existing redaction.
Wrapper `ok` means retrieval succeeded, not that diagnostic findings are
healthy. Do not parse stderr as a second carrier or reinterpret findings.
All other success/nonzero combinations remain `contract_mismatch`.

The schema, catalog semantics, fixtures, and PRD are rebaselined together
in the unpublished v0.1.0 contract. This narrows the amendment to one
command's documented exit behavior. The fixed environment and trust gates
remain unchanged. This amends ADR-003's success exit rule only.

## Alternatives

Expanding PATH would add executable lookup authority and would still reject
legitimate doctor error findings. Treating every nonzero success envelope
as acceptable would hide mismatches in unrelated commands. Both are rejected.

## Verification

Unit tests exercise exits 0 and 3 with both probe settings, redaction,
malformed envelopes, wrong command identities, and other exit codes.
Wrapper fixtures enforce the doctor-only exception. Qualification invokes
both variants through real Hermes against both pinned Agent Dispatch
releases and requires the Watchman findings at exit 3 to reach the caller.
