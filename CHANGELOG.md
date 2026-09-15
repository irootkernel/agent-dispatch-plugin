# Changelog

This file records concise shipped outcomes and pending changes.

## v0.1.2 - Unreleased

## v0.1.1 - 2026-09-16

### Added

- Add Linux source-directory install and rollback runbooks for native
  linux/amd64 and linux/arm64 hosts.

### Changed

- Admit native Linux amd64 and Linux arm64 alongside Darwin arm64, and
  select launchd or systemd for schedule inspection from the trusted host.
  Darwin arm64 remains the release host.
- Qualify linux/arm64 against Agent Dispatch v0.1.7 and linux/amd64 against
  v0.1.8. GitHub v0.1.6 and v0.1.7 published Darwin arm64 artifacts only.

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
