# Architecture

The v0.1.0 architecture is a thin, management-only adapter:

Hermes model -> typed plugin schema -> validated tool handler -> shared runner
-> Agent Dispatch CLI -> validated agent-dispatch.cli/v1 envelope -> bounded
plugin result.

The plugin owns input validation, fixed command selection, process isolation,
envelope validation, and diagnostic redaction. Agent Dispatch remains the
authority for domain state and semantics. runner.py is the sole process
boundary, and handlers cannot open the Agent Dispatch database.

Durable implementation choices must be recorded in
docs/architecture-decision-records/README.md. Normative behavior remains in
docs/specs/PRD.md.
