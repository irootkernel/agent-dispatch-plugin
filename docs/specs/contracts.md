# Frozen v0.1.0 Public Contracts

Status: Frozen by TASK-001
Source of truth: `contracts/v0.1.0/`
Authority: docs/specs/PRD.md; this page binds the PRD to the frozen contract
artifacts and adds no behavior of its own.

## What is frozen

The complete v0.1.0 public contract surface lives in
`contracts/v0.1.0/catalog.json` with its JSON Schema and deterministic
fixtures:

- the exactly-ten-tool roster with model-facing descriptions;
- fixed action-to-command mappings with per-action `expected_command`
  identity and a command vocabulary allowlist plus denied-subcommand list;
- closed input constraints: action enums, conditional requirements, the
  identifier grammar, state-token grammar, closed receipt-kind and
  quarantine-state sets, and pagination bounds (limit 1–100 default 25,
  offset 0–1,000,000);
- the closed `agent-dispatch-plugin.result/v1` wrapper, the closed
  `agent-dispatch.cli/v1` envelope boundary with its open domain `result`
  interior, and the closed ten-code plugin error object with
  `retryable: false`;
- resource limits: timeout 1–300 s default 30, TERM plus a two-second grace
  then process-group kill, stdout 1,048,576 bytes, stderr 65,536 bytes,
  combined 1,048,576 bytes (configurable tighter, never higher);
- the compatibility matrix: Agent Dispatch >=0.1.6,<0.2.0 with
  `agent-dispatch.cli/v1`, Hermes exactly v0.20.5, darwin/arm64, standalone
  manifest v2 / API v1, initially unverified pending qualification;
- the five defense-in-depth redaction rules.

The supporting decisions are accepted in ADR-001 (declarative registry and
generated-artifact ownership), ADR-002 (identifier grammar, state tokens,
pagination, diagnostic bounds), and ADR-003 (closed result boundaries and
command-specific envelope identity).

## Deterministic gate

```bash
uv run --with jsonschema==4.26.0 --with referencing==0.37.0 contracts/validate.py
```

must pass before any contract change is committed. The gate is offline: no
process, database, network, or Agent Dispatch state is touched. The pinned
dependency versions and the PRD oracle constants inside `validate.py` are part
of the frozen surface; a canonical amendment must update the catalog, the
schemas, and the oracle together, and TASK-003 supersedes the pinned
invocation with the locked project toolchain.

## Upstream surface observations

The closed receipt-kind and quarantine-state sets, the envelope command-path
identity, the closed envelope error object, and the stdout-success versus
stderr-error stream policy were confirmed against the installed Agent
Dispatch v0.1.6 command help and disposable probes during TASK-001; they are
frozen in the catalog. During TASK-004 the remaining EPIC-002 duty was
verified against the real binary: `quarantine list` accepts and applies the
PRD-documented `--route` and `--limit` filters, and `notifications list`
supports no `--offset` filter — the binary's parser tolerates the flag but
silently ignores it (`--limit 2 --offset 2` returns the same leading page as
`--limit 2`). The frozen contract correctly omits the flag; the parser
tolerance is an upstream observation, not a contract change. TASK-004 also
verified the version surface: the binary rejects `--version` and answers
`agent-dispatch version --json`, which the runner trust gate now uses.

## Change control

Frozen for v0.1.0. Any change to the roster, mappings, schemas, error,
compatibility, or resource contracts requires explicit maintainer approval
and a canonical PRD amendment, then a new versioned contract directory with
updated fixtures. Qualification evidence may reject these contracts but may
not silently adapt them.
