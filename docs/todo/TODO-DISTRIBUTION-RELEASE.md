# EPIC-005 Distribution and Release

Status: Adopted
Roadmap: EPIC-005 in docs/roadmap/README.md
Tasks: TASK-014, TASK-015, TASK-016, TASK-017
Depends on: EPIC-004

## Outcome

Hand maintainers a reproducible, immutable, clean-clone release candidate with
complete installation, removal, upgrade, rollback, and support evidence.

## Delivery

- Run clean-clone checks, Plugin Doctor, registration, and fresh-session
  inventory from the candidate revision.
- In a disposable Hermes profile, prove pinned installation starts disabled,
  explicit plugin and toolset enablement, disablement, and complete removal.
- Document repository source, exact commit, release tag, plugin enablement, and
  toolset enablement as distinct states.
- Complete security, compatibility, upgrade, rollback, and troubleshooting
  runbooks.
- Prepare an exact-commit handoff and release checklist.

## Acceptance

- Evidence is tied to one immutable candidate and includes all EPIC-004 gates.
- Removal leaves no plugin registration or tool inventory residue.
- Rollback between documented pinned revisions is reproducible.
- Documentation contains no secret or machine-specific trust assumption.
- The handoff clearly states that commit, push, tag, publication, installation,
  and activation each require separate authorization.

## Non-goals

Creating a commit, pushing, tagging, publishing, installing, activating, or
releasing as part of this dossier's planning work.
