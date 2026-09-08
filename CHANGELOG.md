# Changelog

This file records concise shipped outcomes and pending changes.

## v0.1.0 - 2026-09-09

### Added

- Add ten inspection tools for interactive Hermes conversations covering status,
  diagnostics, routes, dispatches, receipts, events, quarantine, notifications, scheduling, and configuration.
- Support macOS Apple Silicon with Hermes 0.20.5 or newer and Agent Dispatch
  0.1.6 through versions below 0.2.0, distributed as a source-only plugin.
- Require trusted executable and configuration paths plus an executable SHA-256,
  with bounded execution, validated responses, and sensitive-output redaction.

- Preserve doctor findings when Agent Dispatch returns diagnostic exit code 3,
  so errors such as an unavailable Watchman remain inspectable in Hermes.
