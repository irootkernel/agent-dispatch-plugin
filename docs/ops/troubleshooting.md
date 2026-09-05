# Troubleshooting Runbook

Target: `agent-dispatch-plugin` v0.1.0 installations in a Hermes v0.20.5
profile. Symptom → diagnosis → resolution, each verifiable without
touching live state. All commands run against the profile under
diagnosis (`HERMES_HOME=<profile>` for CLI commands).

## The plugin registers no tools

Diagnosis: `hermes plugins show agent-dispatch-plugin` — if the status
is `not enabled`, installation is fine and enablement is the gap.
Resolution: `hermes plugins enable agent-dispatch-plugin
--no-allow-tool-override` (the lifecycle runbook records the full state
model). If the plugin is absent from `hermes plugins list`, the plugin
directory is missing from `<profile>/plugins/agent-dispatch-plugin`.

## Tools register but the toolset is unavailable

Diagnosis: the trust gate closed. The five settings under
`plugins.entries.agent-dispatch-plugin.settings` must be present and
consistent: `binary_path` and `config_path` must exist as regular files
with no symlinked path segment, `binary_sha256` must match the
installed executable's digest exactly, and the executable's
`version --json` probe must report v0.1.6 (the supported range is
`>=0.1.6,<0.2.0`).
Resolution: restore the documented settings — never loosen the gate.
A swapped executable with a changed digest is rejected by design;
update `binary_sha256` only after verifying the new artifact's identity.

## A dispatch returns `contract_mismatch` for doctor

This is the recorded watchman boundary: upstream `doctor` probes the
watchman daemon under the plugin's frozen PATH allowlist and reports it
unreachable on hosts where watchman lives outside
`/usr/bin:/bin:/usr/sbin:/sbin`; the plugin closes this as the frozen
`contract_mismatch` error deterministically. The success mapping is
proven by the unit suite's deterministic fake. A canonical amendment
could make the allowlist operator-extensible; until then this response
is expected on such hosts.

## `hermes plugins install` rejects the repository

The v0.20.5 installer supports `manifest_version` 1 only and rejects
this plugin's frozen manifest 2 (the recorded installer boundary in the
installation lifecycle runbook). Install the documented way: the
source-only plugin directory at an exact pinned revision.

## The deterministic gates fail only in a fresh clone

The recorded directory-name defect: before the pytest `pythonpath` pin,
an identifier-named clone failed all unit tests with
`ModuleNotFoundError: No module named 'registry'` while the hyphen-named
working checkout passed. The pin in `pyproject.toml` makes every clone
location import identically; if the symptom reappears, the pin was
removed. Reproduce with the clean-clone runbook.

## A rollback leaves the toolset unavailable

The five settings are frozen across v0.1.x revisions and survive a
directory swap; an unavailable toolset after a rollback means the
settings no longer match the swapped revision's frozen contract.
Resolution: restore the documented settings (upgrade/rollback runbook)
and verify with one smoke inspection in a fresh session.

## Escalation

Anything not resolved above is a contract question: check
`docs/specs/contracts.md` first, then the frozen catalog
(`contracts/v0.1.0/catalog.json`), then the roadmap for the owning work
unit. A confirmed contract violation is a blocking defect — it goes to
the maintainers with the transcript captured under the security
evidence-capture guide.
