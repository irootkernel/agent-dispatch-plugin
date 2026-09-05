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
including object keys and base64url encodings). Captured tool output is
therefore safe to record as evidence, provided the capture itself adds
nothing.

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
