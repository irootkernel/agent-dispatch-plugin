# Maintainer Documentation

This directory is the single-scope documentation system for
agent-dispatch-plugin. Canonical documentation is written in English.

## Authority and precedence

When documents disagree, use this order:

1. docs/specs/PRD.md defines product scope and acceptance.
2. Accepted architecture decision records define durable technical decisions.
3. docs/roadmap/README.md defines planned work and lifecycle state.
4. Adopted TODO dossiers are the detailed source of truth for their epic.
5. Operational and implementation notes explain how to execute accepted work.
6. docs/agent-dispatch-plugin.md is non-canonical working input. Its frozen
   source digest is
   684afa0f2eb3d2f66ef2c766fd34117446f3bbfa7fa6b9b7020e01d2eac06673.

Unresolved conflicts stop work until the higher-authority document is amended.

## Documentation roles

| Role | Index | Purpose |
|---|---|---|
| Specifications | docs/specs/README.md | Product requirements and normative contracts |
| Architecture | docs/architecture/README.md | System shape and component boundaries |
| Decisions | docs/architecture-decision-records/README.md | Accepted and superseded ADRs |
| Implementation tips | docs/implementation-tips/README.md | Non-normative implementation guidance |
| Operations | docs/ops/README.md | Qualification, installation, rollback, and support evidence |
| Roadmap | docs/roadmap/README.md | Epic and task lifecycle |
| TODO dossiers | docs/todo/README.md | Adopted detailed sources of truth |
| Deferred feedback | docs/deferred-feedback/README.md | Reviewed feedback not accepted into current scope |

## Identity and lifecycle

- Epics use EPIC-NNN.
- Work units use TASK-NNN and belong to exactly one epic.
- ADRs use ADR-NNN.
- Lifecycle values are Planned, In Progress, In Review, Completed, Deferred,
  and Blocked.
- Every active epic links one Detailed SOT dossier.
- A roadmap item is not complete until its deterministic evidence exists.
