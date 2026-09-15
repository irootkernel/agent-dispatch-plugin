# Changelog

This file records concise shipped outcomes and pending changes.

## v0.1.1 - Unreleased

### Changed

- Admit Linux amd64 and Linux arm64 alongside Darwin arm64 in the living
  catalog, and select launchd or systemd for schedule inspection from the
  trusted host. Darwin arm64 remains the release host.
- Record real-machine linux/arm64 qualification of the existing ten tools
  against Agent Dispatch v0.1.7 (Hermes >=0.20.5, systemd absent-schedule
  inspect). Admit linux/amd64 into the qualification matrix against
  Agent Dispatch v0.1.8. GitHub v0.1.6/v0.1.7 linux artifacts were not
  published. Next program position after EPIC-006 is Dispatch E20 / E20-T1;
  v0.1.1 is not tagged by that close.

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
