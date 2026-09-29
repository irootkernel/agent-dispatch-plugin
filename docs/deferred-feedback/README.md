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

### EPIC-007 result-schema keyword shapes

Source: Mulgae EPIC-007 whole-Epic final composite review
`r_975f9f7e-56d9-789e-bdd3-8d5587ebbc55`, security F001 (Low).
Disposition: deferred feedback. Owner: Plugin maintainer. Rationale:
the three current closed result schemas use only
`additionalProperties: false` and object-valued recursive keywords,
which the runtime evaluator handles. Its schema guard checks keyword
names but does not reject other Draft 2020-12 value forms that the
evaluator does not implement. This is a future amendment risk, with no
current schema using those forms. Revisit: before the next result-schema
amendment, require exactly the supported keyword value shapes in
`_check_sync_schema` and add rejection cases for schema-valued or true
`additionalProperties` and non-object recursive keywords. Roadmap
identity: EPIC-007 hardening follow-up; no new task ID allocated.

### EPIC-007 result-pattern oracle semantics

Source: Mulgae EPIC-007 whole-Epic corrected-target review
`r_01a0ecdf-c92f-7961-9467-b3e0ab4b047e`, F001 (Low).
Disposition: deferred feedback. Owner: Plugin maintainer. Rationale:
the runtime uses whole-string matching and directly rejects trailing LF
for result identities, while Python `jsonschema` applies `$` through
`re.search` and would accept that value in the offline fixture oracle.
The current boundary fails closed; the discrepancy limits future oracle
fixture coverage rather than current runtime safety. Revisit: before the
next versioned result-contract amendment, replace bare `$` anchors with
the portable `(?![\\s\\S])` terminator and add invalid trailing-LF fixtures
so both validators enforce the same negative. Roadmap identity: EPIC-007
hardening follow-up; no new task ID allocated.

### EPIC-007 contract-oracle regression coverage

Source: Mulgae EPIC-007 whole-Epic review
`r_c02aca42-9d72-75ac-9509-494142e0e7cc`, testing Finding 1 (Low).
Disposition: deferred feedback. Owner: Plugin maintainer. Rationale:
`make test` already runs the v0.2.0 oracle before the test suites, while
registry and manifest parity corruption tests cover adjacent boundaries.
Independent pytest subprocess and corruption cases would improve detection
when only `test-int` is run or the oracle itself regresses, but are not
required for this Epic's verified contract behavior. Revisit: before the
next v0.2.0 contract amendment, add a green subprocess case and focused
corruption cases for the provider digest, platform allowlist, group grammar,
and admission expectations. Roadmap identity: EPIC-007 hardening follow-up;
no new task ID allocated.

### EPIC-007 requested sync read failure-path coverage

Source: Mulgae EPIC-007 whole-Epic review
`r_c02aca42-9d72-75ac-9509-494142e0e7cc`, testing Finding 2 (Low).
Disposition: deferred feedback. Owner: Plugin maintainer. Rationale:
the requested read uses the shared bounded executor already exercised by
legacy timeout and overflow tests; sync-specific tests cover failures of
the preceding capability probe and successful requested reads. A fake
that fails after a passing probe would detect future branch regressions,
but no current incorrect mapping was found. Revisit: before changing sync
dispatch or bounded execution, exercise requested-command timeout,
overflow, and nonzero exit after a passing probe, including the exact
probe invocation count. Roadmap identity: EPIC-007 hardening follow-up;
no new task ID allocated.

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
