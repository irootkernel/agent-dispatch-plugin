# Operations

Operational evidence for v0.1.0 is reproducible from a clean clone and
an immutable review target. The required operational coverage maps to
runbooks as follows:

- exact Agent Dispatch and Hermes artifact identity — the qualification
  runbook;
- disposable Darwin arm64 qualification — the qualification runbook;
- Plugin Doctor and fresh-session tool inventory — the clean-clone
  runbook;
- disabled-by-default installation and explicit toolset activation —
  the installation lifecycle runbook;
- complete disablement and removal — the installation lifecycle runbook;
- upgrade and rollback between pinned revisions — the upgrade/rollback
  runbook;
- redaction-safe evidence capture — the security evidence-capture guide;
- maintainer procedure and documentation review — the maintainer guide;
- symptom-driven diagnosis — the troubleshooting runbook.

Repository source, exact commit, release tag, plugin enablement, and
toolset enablement are separate states (the maintainer guide records
their owners and commands). No installation, activation, publication,
or release has been authorized by the current project-design work.

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
- [Installation Lifecycle Runbook](install-lifecycle-darwin-arm64.md) —
  the disposable-profile proof that pinned installation starts disabled,
  explicit plugin and toolset enablement and disablement are separate
  states, complete removal leaves no registration or inventory residue,
  and the installer manifest-version boundary (TASK-015).
- [Upgrade and Rollback Runbook](upgrade-rollback-darwin-arm64.md) —
  the pinned-revision swap model, the recorded rollback and upgrade
  reproduction between the first two documented pinned revisions, and
  the frozen-settings invariance that makes swaps safe (TASK-016).
- [Maintainer Guide](maintainer-guide.md) — the frozen surface and
  change control, the distinct-state model, the every-change gates, the
  documentation map, and the documentation review checklist (TASK-016).
- [Security Evidence Capture Guide](security-evidence-capture.md) —
  what the closed output boundary already guarantees and the
  operator-side capture discipline for transcripts and evidence
  packages (TASK-016).
- [Troubleshooting Runbook](troubleshooting.md) — symptom-driven
  diagnosis for enablement, trust-gate, doctor-boundary, installer,
  clean-clone, and rollback failures (TASK-016).
