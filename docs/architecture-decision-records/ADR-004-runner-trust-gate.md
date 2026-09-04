# ADR-004: Runner Trust Gate — Path Verification, Time-of-Check, and Version Probing

Status: Accepted

## Context

The PRD requires runner.py to admit only a configured absolute non-symlink
Agent Dispatch executable after verifying its lowercase SHA-256, to use only
a trusted absolute non-symlink configuration path, and to reject binaries
outside the frozen compatibility range `>=0.1.6,<0.2.0` on the supported
darwin/arm64 platform. The catalog fixes the version range, the platform
string, and the timeout bounds; the EPIC-002 dossier names safe non-symlink
path verification and time-of-check handling as a decision to record. The
catalog command vocabulary contains no `version` subcommand, so the probing
mechanism had to be established against the real binary.

## Decision

- **Trust resolution is one gate.** `runner.resolve_trust(config)` validates
  the platform, the five immutable plugin settings, both trusted paths, the
  executable digest, and the binary version, in that order, and returns one
  frozen `RunnerTrust` identity or raises `TrustFailure` carrying a closed
  error code. `runner.probe_availability(config)` exposes the same gate as
  the boolean the Hermes availability check needs; no other module resolves
  trust or spawns a process.
- **Path verification is component-wise and symlink-intolerant.** Both
  configured paths must be absolute, every filesystem component from the
  leaf to the root must not be a symlink (`lstat` semantics), the executable
  must be a regular executable file, and the trusted configuration must be
  a regular file. The digest is read through `open` with `O_NOFOLLOW` so the
  hashed bytes cannot follow a last-instant symlink swap.
- **Time-of-check handling.** Verification and spawn use the same verified
  absolute path within one `run_inspection` call, and the digest is
  re-verified on every trust resolution rather than cached. The residual
  window between verification and `exec` cannot be closed portably on
  Darwin without a fork+`fexecve` dance; the accepted residual risk is a
  same-user attacker swapping the file inside that window, which is outside
  the threat model of a same-user Hermes installation. Any change to the
  binary between calls is caught at the next call's digest check.
- **Version probing uses the real `version` subcommand.** Verified against
  the installed Agent Dispatch v0.1.6: the binary rejects `--version`
  (`command_unknown`, exit 0) and directs callers to
  `agent-dispatch version --json`, which answers
  `{"name":"agent-dispatch","version":"v0.1.6"}`. The probe runs the
  verified executable with argv `["version", "--json"]`, bounds its output
  (64 KiB), parses `v?MAJOR.MINOR.PATCH`, and requires
  `low <= version < high` with both bounds derived from the frozen catalog.
- **Failure mapping is closed.** Platform mismatch, missing or unlinked or
  unreadable or non-executable or digest-mismatched executable, missing
  trusted configuration, an unanswerable probe, and unconfigured plugin
  settings map to `binary_unavailable`; structurally invalid settings
  (types, ranges, non-lowercase digests, relative paths) map to
  `adapter_usage_error`; a probe that answers outside the frozen range, or
  with an unusable payload or failure exit, maps to
  `unsupported_agent_dispatch_version`. All messages are bounded, name only
  the failing check, and never echo paths, digests, or captured output.

## Consequences

- Availability and handlers share one trust authority: the toolset is
  exposed exactly when the gate passes, and every trust rejection surfaces
  as one frozen closed error with no exception escaping into Hermes.
- The version probe spawns one process per trust resolution; that is the
  only process the gate creates and it is bounded by the configured
  deadline.
- A binary that silences or bloats the probe fails closed; there is no
  bypass, cache, or retry.
- Digest re-verification makes each inspection pay one file read of the
  executable; the executable is small, so this is accepted as the price of
  the time-of-check posture.
- Residual risk (recorded during the EPIC-003 whole-epic review): a window
  remains between the digest read and the exec by path, so a local process
  with write permission on the operator-configured binary path or a parent
  directory could swap the file in between. The threat model treats such a
  process as operator-trusted (it could equally rewrite the Hermes config
  or the plugin source), the digest read uses O_NOFOLLOW, and the full
  ancestor symlink walk precedes it. Fd-passing execution is not portable
  to Darwin and a verified-copy scheme is not warranted under the current
  trust model; revisit only if that model widens.

## Alternatives

- Trust-once caching keyed by (path, mtime): rejected — mtime is attacker
  controllable and weakens the per-call verification posture.
- Deriving the version from the envelope of a live inspection: rejected —
  the gate must reject an unsupported binary before any inspection runs.
- `realpath`-based symlink resolution: rejected — it would silently accept
  symlinked configuration, which the PRD forbids.

## Verification

`tests/unit/test_runner.py` proves every mapping above with deterministic
fake Agent Dispatch executables (in-range, out-of-range, wrong name,
garbage, failure exit, no answer, symlinked binary, symlinked parent,
missing and non-executable files, digest mismatch, relative paths, invalid
settings, platform monkeypatch) and `tests/unit/test_tools.py` plus
`tests/integration/test_registration_and_gates.py` prove the availability
and handler wiring through the real registration path.
