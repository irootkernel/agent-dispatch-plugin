# Operations

Operational evidence for v0.1.0 must be reproducible from a clean clone and an
immutable review target. Required runbooks will cover:

- exact Agent Dispatch and Hermes artifact identity;
- disposable Darwin arm64 qualification;
- Plugin Doctor and fresh-session tool inventory;
- disabled-by-default installation and explicit toolset activation;
- complete disablement and removal;
- upgrade and rollback between pinned revisions;
- redaction-safe evidence capture.

Repository source, exact commit, release tag, plugin enablement, and toolset
enablement are separate states. No installation, activation, publication, or
release has been authorized by the current project-design work.

## Runbooks

- [Qualification Runbook: Darwin arm64 Compatibility Matrix](qualification-darwin-arm64.md) —
  the exact artifact identities, the disposable-profile reproduction
  procedure, the single-entry support-matrix rationale, and the adjudicated
  qualification boundaries (TASK-012).
- [Clean-Clone Verification Runbook](clean-clone-verification.md) — the
  clean-clone reproduction procedure for the complete deterministic gate
  set, the recorded directory-name import defect with its remediation, and
  the clean-environment transcript including Plugin Doctor and the
  fresh-session tool inventory (TASK-014).
