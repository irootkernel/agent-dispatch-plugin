# Developer and Maintainer Documentation

This is the English, `single-scope` documentation system for
agent-dispatch-plugin. The single delivery scope is the plugin; its maintainers
own implementation, compatibility, and release engineering. The public
[README](../README.md) owns product introduction and end-user instructions.

## Start here

| Your task | Read |
|---|---|
| Make a first contribution | [Development workflow](implementation-tips/README.md), then [maintainer guide](implementation-tips/maintainer-guide.md) |
| Understand the code | [Architecture](architecture/README.md) and [decisions](architecture-decision-records/README.md) |
| Change a tool or result | [Specifications](specs/README.md), [contract reference](specs/contracts.md), and [executable contracts](../contracts/README.md) |
| Test a change | [Testing contract](../TESTING.md) and [clean-clone verification](implementation-tips/clean-clone-verification.md) |
| Prepare a release | [Release handoff](implementation-tips/release-handoff.md) |
| Diagnose an installation | [Operations](ops/README.md) |
| Find delivery history or postponed work | [Roadmap](roadmap/README.md), [TODO](todo/README.md), and [deferred feedback](deferred-feedback/README.md) |

## Ownership and precedence

| Role | Canonical owner | Responsibility |
|---|---|---|
| Specifications | [specs/](specs/README.md) | Product requirements and normative contracts |
| Architecture | [architecture/](architecture/README.md) | Current components, boundaries, and data flow |
| Decisions | [architecture-decision-records/](architecture-decision-records/README.md) | Accepted and superseded technical decisions |
| Implementation tips | [implementation-tips/](implementation-tips/README.md) | Development, review, testing guidance, and release engineering |
| Operations | [ops/](ops/README.md) | Profile lifecycle, diagnosis, and recovery |
| Roadmap | [roadmap/README.md](roadmap/README.md) | Epic and task identity, ordering, dependencies, and lifecycle |
| TODO dossiers | [todo/](todo/README.md) | Future epic proposals and any adopted temporary dossiers |
| Deferred feedback | [deferred-feedback/](deferred-feedback/README.md) | Small reviewed findings postponed from current work |

The [PRD](specs/PRD.md) defines product scope and acceptance. Accepted ADRs
explain technical decisions within that scope. The
[contract reference](specs/contracts.md) binds the PRD to the executable
artifacts in `contracts/v0.1.0/`; derived manifest and runtime views must agree
with them. The roadmap alone owns delivery status. An adopted dossier refines
its epic without overriding these owners. Operational and implementation
guidance explains how to execute accepted work.

[TESTING.md](../TESTING.md) retains the testing contract; [Makefile](../Makefile)
owns executable test orchestration. Neither is moved by this reorganization.
Resolve disagreements with the owning authority before changing behavior.
Do not treat old test transcripts as evidence for a new candidate revision.

Tracked evidence supports historical delivery; runtime logs and temporary
workflow evidence do not become canonical documentation.

## Identity and lifecycle

The namespace is `docs/roadmap/README.md`. Existing `EPIC-NNN` and `TASK-NNN`
identities are preserved. Their independent sequences are monotonic; task
numbering does not restart per epic and numbers are never reused. New numbers
follow the greatest number ever allocated in that namespace, including history.
Identity does not encode order; the roadmap records dependencies. ADRs use
`ADR-NNN` in their own index.

Lifecycle values remain Planned, In Progress, In Review, Completed, Deferred,
and Blocked. Every active epic links one Detailed SOT dossier under the existing
repository convention. All initial dossiers were promoted to the canonical
outcomes in their roadmap rows and retired. This migration creates no dossiers
or work units and changes no lifecycle state. Child task completion alone does
not establish epic acceptance.

## Documentation checks

Review links and relative anchors inside the repository, and compare examples
with the frozen schemas and implementation. Run these non-writing checks:

```bash
uv run contracts/validate.py
uv run scripts/manifest_parity.py
git --no-pager diff --check
```

There is no repository-native Markdown link checker. Check changed links
explicitly. Aquarium's optional documentation inspector is structural tooling,
not repository CI or runtime proof; its v2 parser does not recognize the
existing epic register/work-unit table layout, so audit those rows separately.
The full test and release gates remain in the testing contract and release
handoff. `make test` includes a formatter that can modify Python sources.
