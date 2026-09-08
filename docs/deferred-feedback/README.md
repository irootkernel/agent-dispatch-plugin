# Deferred Feedback

This role records reviewed suggestions that are not accepted into the current
scope. Each entry must identify its source, disposition, rationale, revisit
condition, and any later roadmap identity.

Initial candidate topics:

- worker receipt submission, completion, and failure mutations;
- administrative mutation tools.

These candidates are not v0.1.0 requirements and have no initial epic or task.
All other excluded surfaces remain durable non-goals unless the PRD is amended.

## Entries

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
