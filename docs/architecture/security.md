# Security Boundaries

This page explains the implemented v0.1.0 controls. The [PRD](../specs/PRD.md),
[frozen contracts](../specs/contracts.md), and accepted ADRs own requirements
and decisions; this guide introduces no new permissions or behavior.

## Trust and responsibility

Hermes owns profile settings and activation. Agent Dispatch owns routing,
state, migration, retry decisions, and receipt semantics. The plugin reads no
domain database and exposes no arbitrary CLI command, mutation, hook, daemon,
or worker receipt submission surface. Model input selects only validated tool
arguments, never the executable, configuration path, environment, or working
directory. Receipt presence does not by itself establish work success.

The operator supplies three required settings: `binary_path`, `binary_sha256`,
and `config_path`. Timeout and output settings have bounded defaults. Trust is
checked for availability and every inspection; verification is not cached.
Registration itself reads contract files and creates no Agent Dispatch process.

## Controls and verification

Paths below are relative to the repository root.

| Boundary | Implemented control | Code and verification |
|---|---|---|
| Input and command selection | Closed schemas, literal identifiers, conditional action requirements, fixed argv, denied mutation vocabulary | `tools/inputs.py`, `registry.py`; `tests/unit/test_input_validation.py`, `tests/unit/test_security_negatives.py`, `scripts/manifest_parity.py` |
| Binary and config identity | Darwin arm64 gate, absolute regular paths without symlinked components, executable SHA-256 and version verification | `runner.py`; `tests/unit/test_runner.py`; ADR-004 |
| Process isolation | No shell, neutral working directory, fixed PATH and TMPDIR without inherited HOME or credentials, closed extra descriptors | `runner.py`; `tests/unit/test_execution.py`, `tests/unit/test_security_negatives.py`; ADR-005 |
| Resource bounds | Concurrent draining, bounded stdout/stderr and combined bytes, deadline, process-group TERM then kill, no automatic retry | `runner.py`; `tests/unit/test_execution.py`, `tests/unit/test_security_negatives.py`; ADR-005 |
| Result integrity | Closed envelope and wrapper validation, expected command and exit consistency, bounded diagnostics, redaction, no raw partial output on failure | `envelopes.py`, `runner.py`; `tests/unit/test_validation.py`, `tests/unit/test_security_negatives.py`; ADR-003 and ADR-006 |
| Hermes integration | Ten declared tools, separate plugin/toolset activation, availability checks, JSON-string handler results | `__init__.py`, `tools/__init__.py`; `tests/integration/test_fresh_session_inventory.py`, `tests/qualification/test_install_lifecycle.py` |

## Limits and operational effects

[ADR-004](../architecture-decision-records/ADR-004-runner-trust-gate.md) records
the residual same-user file-swap window between verification and execution.
The current trust model treats local writers to the configured executable or
plugin profile as operator-trusted; the digest gate is not a sandbox against
that attacker.

Inspection can cause Agent Dispatch to migrate an older store or refresh
capability evidence. Interactive CLI activation does not authorize automatic
route changes, retries, or remediation. Doctor's fixed-PATH limitation is
recorded in the [qualification guide](../implementation-tips/qualification-darwin-arm64.md);
consult the [release acceptance gap](../implementation-tips/release-handoff.md#compatibility-acceptance-gap)
before interpreting historical qualification as release readiness.

Output redaction is bounded by the frozen rules. See
[deferred feedback](../deferred-feedback/README.md) for the known protected-path
filename limitation, and [evidence capture](../ops/security-evidence-capture.md)
for operator-side handling. Never copy raw process streams, credentials, or
live profile contents into support reports. Escalate a boundary violation to
plugin maintainers with sanitized artifact identities and the failing test or
bounded error.
