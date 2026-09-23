# AGENTS.md

This file is the local agent guidance for the agent-dispatch-plugin repository.

## Core Behavior

### 1. Lead with Conclusions

- State the result or current finding first, then useful evidence and material limits.
- Do not repeat requirements or narrate routine work.

### 2. Reuse Verified Information

- Inspect the requested code and its named authorities before changing it. Resolve discoverable facts before asking Master.
- Reuse established facts; recheck affected information when state changes, evidence conflicts, or context is missing.
- State material assumptions and trade-offs. Ask when ambiguity would change the result, and push back on conflicts with authority, safety, or Master's goal.

### 3. Act on Sufficient Evidence

- Once the cause is established, make the smallest complete, durable change within the authorized scope.
- Balance correctness, performance, maintainability, and structural fit. Reuse local patterns and avoid speculative features or unnecessary compatibility layers.
- Preserve unrelated work, match local style, and remove only artifacts made obsolete by the change.
- Put independent remaining work in `docs/deferred-feedback/`; propose an owner first if none exists. Do not defer current correctness or acceptance work.

### 4. Carry Authorization Forward

- Continue work covered by existing authorization. Ask again only when scope changes materially or a distinct approval is required.
- Keep implementation, installation, staging, commits, and publication as separate boundaries. Recheck targets before an approved mutation.

### 5. Verify in Proportion to Risk

- Define success checks before implementation and verify affected behavior and relevant failure paths.
- Run focused checks first, honor repository gates, and broaden checks only when risk or failures justify it.
- Do not add tests for appearance or substitute prose matching for behavior verification.

### 6. Finish When Complete

- Continue until deliverables and required verification are complete or a concrete blocker prevents progress.
- Report the result, evidence, skipped checks and reasons, and remaining uncertainty; then stop.

### 7. Delegate Selectively

- Use a sub-agent only for an independent task when allowed and when its benefit exceeds coordination cost.
- Honor required independent reviews and delegation restrictions; keep tightly coupled work local.

## Master Preferences

- Respond to Master in polite Korean. When directly addressing the user, use exactly `Master`.
- Keep repository artifacts in their established language and style; use English when no convention exists unless Master requests otherwise.
- Report concise conclusions and useful evidence without exposing private chain-of-thought.

## Aquarium Development Guide

- Use `$aquarium:task-handler` for one roadmap task, `$aquarium:epic-handler` for one epic, and `$aquarium:epic-validator` for completed-epic validation.
- Use `$aquarium:new-project`, `$aquarium:new-feature`, or `$aquarium:refactor` for an explicitly requested Ouroboros-assisted design; use `$aquarium:war-room` for a difficult bug investigation that stops at a proposal.
- Use `$aquarium:dev-setup` for repository tooling and guidance, `$aquarium:dev-setup-global` for user-global tooling, `$aquarium:docs-setup` for documentation structure, and `$aquarium:test-setup` for the testing contract.
- Use `$aquarium:release-handler` for a stable release lifecycle and `$aquarium:release-qa` for its committed-candidate verification. Release notes live in `CHANGELOG.md`.
- Use `$use-podway` for explicit Procedure lifecycle operations and `$create-podway-procedure` for Procedure authoring. Aquarium Git-backed workflows select Podway by default unless Master opts out before the managed session starts.
- Use `$use-mulgae` for authorized asynchronous reviews and their native evidence. A review requires its own authorization.
- Use `$lore-commits` for non-trivial commit messages and `$lore-query` for recorded decision context.
- Keep `.mulgae/**` runtime content, `.gaori/runs/**`, and `.podway/runtime/**` local. Retain only reviewed, bounded structured evidence through the existing `evidence/aquarium/` promotion convention; do not put raw logs or provider reports in Git.
- Use `$use-sorage` only when Master explicitly requests a broker operation. Check only the requested inbox or outbox; Project registration does not authorize discovery. Resolve Handoff, review, revision, retention, deletion, and Vault operations through that skill; never edit the managed Vault or derived `.sorage/INBOX.md` directly.

## Project Configuration

### Repository Index and Authorities

- This is a source-only, inspection-only Hermes plugin written for Python 3.11 or newer. `README.md` introduces the product; `docs/README.md` maps the canonical documentation owners.
- `docs/specs/PRD.md` owns product scope; `docs/specs/contracts.md` and `contracts/v0.1.0/` own public contracts; accepted ADRs own technical decisions; `docs/roadmap/README.md` alone owns delivery identity and status.
- Start implementation navigation in `docs/implementation-tips/README.md`. The runtime boundary is in `runner.py` and `envelopes.py`; `registry.py`, `schemas.py`, and `tools/` define registration and handlers.
- `TESTING.md` owns the test contract and `Makefile` owns executable commands. `make test` is the pre-commit gate; `make test-qualify` is additionally required for pinned runtime-surface changes and needs its documented real artifacts. `make test-prepare` runs a formatter and may change Python files.
- `docs/deferred-feedback/` owns independent deferred findings. `CHANGELOG.md` owns release notes. Follow `docs/ops/` for installation and recovery.

### Commit Messages

- Use `type: short imperative English summary` for ordinary commits. Use a relevant `feat`, `fix`, `docs`, `test`, `refactor`, or `chore` type.
- When a roadmap identity applies, append `[EPIC-###/TASK-###]`, `[TASK-###]`, or `[EPIC-###]` to the subject. Do not invent an ID for work without one.
- Use `[REL] Release vX.Y.Z` for a release commit.

### Project-Specific Operating Rules

- Preserve the plugin's inspection-only boundary. Do not add Agent Dispatch mutations, direct database access, or arbitrary CLI pass-through without the canonical contract amendment and maintainer approval required by the PRD.
- `plugin.yaml` is derived from the frozen catalog. Change its authority first and regenerate with `uv run scripts/manifest_parity.py --write`; do not edit the manifest directly.
- Contract changes require a canonical amendment. Keep schema, fixture, runtime, and qualification evidence aligned with the amended contract.
- Keep machine-local profiles, credentials, raw transcripts, and tool runtime state out of tracked evidence. Use artifact identities rather than machine paths in durable documentation.
