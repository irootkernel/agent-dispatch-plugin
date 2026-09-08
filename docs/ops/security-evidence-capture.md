# Security Evidence Capture Guide

Target: capturing operational evidence (transcripts, diagnostics,
review records) from the plugin and its qualification stages without
leaking secrets or machine-specific trust assumptions. The plugin's own
output boundary is closed and redacted by construction; this guide owns
the operator-side capture discipline.

## What the boundary already guarantees

Every tool result passes the frozen wrapper contract
(`agent-dispatch-plugin.result/v1`) with bounded, redacted diagnostics
(`docs/specs/contracts.md` names the five redaction rules; the unit
suite proves seeded secrets never survive the boundary in any position,
including object keys and base64url encodings). Review captured output before sharing: the frozen redaction vocabulary
is bounded, and the [deferred filename limitation](../deferred-feedback/README.md)
remains. A passing redaction test does not authorize publishing private data.

## Capture rules

1. Capture tool output, not process telemetry. Record the wrapper JSON
   the dispatcher returns; never capture `argv`, environment, or stream
   dumps from the process boundary — the runner's contracts are the
   security-relevant facts and they are asserted by the suites, not by
   transcripts.
2. Use disposable profiles for anything seeded. The qualification and
   lifecycle stages build their profiles under temporary directories and
   seed Agent Dispatch state through its own commands inside the
   sandbox; an operator capturing equivalent evidence uses the same
   isolation and never points a capture at a live configuration.
3. Pin identities, not locations. Transcripts record artifact
   identities (version, tag, commit, SHA-256) — never absolute paths,
   hostnames, user names, or live profile locations. Placeholders such
   as `<plugin-directory>` keep a transcript reproducible on any host.
4. Never record credentials. No API key, token, password, or secret
   stem belongs in a transcript, a runbook, a commit message, or an
   evidence package. If a capture would require one, the capture is out
   of scope for this plugin (it has none by design: the runtime is
   dependency-free and offline).
5. Keep machine-local tool state out of Git. `.mulgae/local.yaml`,
   `.podway/runtime/`, `.venv/`, and transcripts under temporary
   directories are ignored or transient by policy; only shared policy
   files (`.mulgae/config.yaml`, `.podway/config.yaml`, procedures) are
   tracked.

## What is committed as evidence

Committed evidence is the deterministic transcript summary a runbook
records (gate names, counts, exit codes, artifact identities) plus the
tests that assert the same facts mechanically. Promoted evidence
packages under `evidence/aquarium/` carry only bounded structured
projections with verified digests; raw logs, provider reports, and
transcripts never enter the repository.

## Review and recovery

Owner: plugin maintainers. The operator needs permission to inspect the target
profile and share the resulting evidence. Before capture, confirm the target is
disposable for any seeded procedure and choose an artifact identity rather than
a live path. Before sharing, inspect the bounded output for sensitive values,
confirm the identities and commands are sufficient to reproduce the issue, and
exclude raw logs. No credentials are needed for the documented qualification.

If the capture includes sensitive data, stop sharing and discard the local
capture; reproduce with sanitized synthetic data. If already disclosed, notify
the responsible maintainer through the appropriate private channel and follow
the owning secret authority's recovery procedure. Do not copy the sensitive
value into an issue or this documentation.
