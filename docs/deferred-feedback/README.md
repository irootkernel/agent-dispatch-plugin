# Deferred Feedback

This role records reviewed suggestions that are not accepted into the current
scope. Each entry must identify its source, disposition, rationale, revisit
condition, and any later roadmap identity.

Initial candidate topics:

- worker receipt submission, completion, and failure mutations;
- administrative mutation tools.

These candidates are not v0.1.0 requirements and have no initial epic or task.
Linux host support is adopted as EPIC-006. All other excluded surfaces remain
durable non-goals unless the PRD is amended.

## Entries

### Native service environment contract classification

Source: Mulgae TASK-026 review `r_01a0eb64-73e5-702d-9088-5a916da354bd`
finding F001 (Low). Disposition: deferred feedback. Owner: Plugin
maintainer. Rationale: the current catalog's two group-bound sync reads
are exactly ADR-010's native-service reads, so the catalog-derived runner
predicate gives the intended environment today. The equivalence is not
declared as a per-action contract field or checked as an invariant. Revisit:
before EPIC-008 adds a group-scoped sync command or any sync read changes
its group binding, amend the contract and decision record to declare and
validate the environment class explicitly. Roadmap identity: TASK-026
hardening follow-up; no new task ID allocated.

### TASK-026 qualification helper consolidation

Source: Mulgae TASK-026 review `r_01a0eb3f-d5e9-7c3f-b2dd-5efc5f40f818`
findings F002 and F003 (Low). Disposition: deferred feedback.
Owner: Plugin maintainer. Rationale: the qualification fixture verifies each
pinned binary digest, while the matrix and lifecycle tests re-identify v0.2.0
by hashing the same file; the native service test also imports private helpers
from another test module. Both are maintainability risks independent of the
current pinned ARM qualification and task acceptance. Revisit: before adding
another pinned Agent Dispatch version or restructuring the qualification suite,
carry the fixture's artifact identity to consumers and move shared disposable
state helpers into a dedicated helper module. Roadmap identity: TASK-026
follow-up; no new task ID allocated.

### Linux amd64 v0.2.0 sync inspection qualification

Source: Master narrowed TASK-026 completion and EPIC-007 acceptance on
2026-09-29 after Darwin arm64 and native Linux arm64 qualification.
Disposition: adopted as deferred EPIC-009/TASK-033.
Owner: Plugin maintainer. Rationale: no accessible native x86_64 Linux
host was available for the v0.2.0 Hermes and systemd user-manager matrix;
translated execution does not meet the platform gate. The older
linux/amd64 v0.1.8 qualification does not cover the three v0.2.0 sync
reads. Revisit: when a native x86_64 Linux host is available, run
`make test` and `make test-qualify` with the exact catalog-pinned
v0.1.8 and v0.2.0 binaries, including real absent/loaded/drifted
service inspection, then record the result before claiming Linux amd64
v0.2.0 support. Roadmap identity: EPIC-009/TASK-033; this entry is a
re-entry pointer, while the roadmap owns lifecycle and acceptance.

### Linux and multi-platform support

Source: `REQ-PLUGIN-WIKI-SYNC/v1` plugin intake (EPIC-006). Disposition:
adopted as EPIC-006; living catalog and PRD now admit linux/amd64 and
linux/arm64 with host-selected launchd/systemd. Rationale: Darwin arm64
is still the release host. A native linux/arm64 host has now recorded
real Hermes qualification against Agent Dispatch v0.1.7; native
linux/amd64 and Agent Dispatch v0.1.6 linux-arm64 remain missing. Revisit:
TASK-021 for those remaining advertised combinations; do not treat
translated amd64 containers as that evidence.
Roadmap identity: EPIC-006 (TASK-018 through TASK-022).

### Protected-path redaction vocabulary

Source: EPIC-004 whole-epic validation review, round one. Disposition:
deferred feedback. Rationale: the frozen redaction rules as written are
satisfied by the current display policy, which suppresses the full path but
keeps the final component for operability; a filename that merely carries a
secret-looking stem (for example `agent-dispatch-secret.conf`) therefore
survives as `[redacted-path:<basename>]`. Extending the fully-redacted
vocabulary to such stems is a deliberate security-hardening amendment with
its own fixture updates, not a current-contract defect, and the frozen
fixtures pin the present behavior. Revisit: when the security contracts are
re-opened for any amendment, extend the fully-redacted path vocabulary to
secret-stemmed final components and update the frozen fixtures with it.
Roadmap identity: none.

### Qualification seeding template assertions

Source: EPIC-004 whole-epic validation review, round one. Disposition:
adopted when the release matrix expanded to v0.1.6 and v0.1.7. Each of the
four generated-config fragments must occur exactly once before replacement,
and its replacement must be present afterward. This makes template drift
fail at the specific edit rather than a downstream fixture assertion.
Keep these checks when adding future compatible artifacts. Roadmap identity:
none.

### Shared wrapper-validator construction across test modules

Source: EPIC-004 whole-epic validation review, round one (verified at five
modules, not the initially reported seven). Disposition: deferred feedback.
Rationale: the frozen-schema registry helper that builds the wrapper
validator is duplicated across five test modules spanning three delivered
epics while `tests/conftest.py` is the natural shared home; consolidating it
is a mechanical refactor of passing suites and is deliberately outside a
validation remediation. Revisit: the next change to frozen-schema loading
(for example a new schema file location) should first move the helper into
`tests/conftest.py` and derive every module from that one construction.
Roadmap identity: none.
