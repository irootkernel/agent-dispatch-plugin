# EPIC-004 Security and Compatibility

Status: Adopted
Roadmap: EPIC-004 in docs/roadmap/README.md
Tasks: TASK-011, TASK-012, TASK-013
Depends on: EPIC-001, EPIC-002, EPIC-003

## Outcome

Produce release-blocking evidence that the complete public surface is secure
and compatible with the exact v0.1.0 matrix.

## Delivery

- Exercise injection, traversal, symlink, digest, environment, secret,
  malformed-envelope, command-mismatch, output-limit, timeout, termination,
  and no-retry negatives.
- In a disposable profile, run every public action through Hermes exactly
  v0.20.5 into real pinned Agent Dispatch artifacts on Darwin arm64.
- Cover Agent Dispatch v0.1.6 and the selected highest compatible release below
  v0.2.0 and record exact commit, tag, version, and digest identities.
- Obtain an independent security and compatibility review and adjudicate every
  finding.

## Evidence policy

Real end-to-end success is mandatory for every advertised action. Synthetic
Agent Dispatch state and controlled fake targets keep the environment safe.
Fixtures supplement unsafe or nondeterministic failure branches but never
replace successful real action evidence.

Any disproved compatibility assumption blocks release. Triage plugin defects
separately from upstream incompatibility. A changed baseline requires a
separately approved canonical amendment.

## Non-goals

Silent compatibility adaptation, waiver of a failed gate, production-state
testing, external mutation, or release publication.
