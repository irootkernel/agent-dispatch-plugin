# ADR-010: Trusted OS User Environment for Native Service Inspection

Status: Accepted

## Context

ADR-005 fixed the child environment to `PATH` and `TMPDIR`. The v0.2.0
`sync service inspect` command resolves its managed definition through the
OS user home. Under the old environment, a real Darwin command resolves
`.LaunchAgents` relative to the plugin working directory instead of the
user's LaunchAgents directory. Linux `systemctl --user` additionally needs
the user's canonical runtime bus directory when a native user manager exists.
An absent-service result from the wrong path would be misleading.

## Decision

Keep the exact replacement environment of ADR-005 for the version probe,
capability probe, and original ten actions. Only `sync status` and
`sync service inspect` add `HOME` from the current UID's OS account record,
never from the parent process. On Linux, those two reads also add
`XDG_RUNTIME_DIR=/run/user/<uid>` only when that directory exists, is not a
symlink, and belongs to the current UID.
Resolve these values for each service-aware execution. If the UID has no
account record, return the closed `execution_failed` result for that read;
the original ten actions still load and use the unchanged environment.
No Hermes, agent, credential, proxy, arbitrary XDG, or D-Bus variables are
inherited. This adds a narrow exception to ADR-005's two-variable environment
decision; its other decisions remain.

## Consequences

The core resolves the real native user service definition path and can ask
the native user manager for load state. The original inspection actions keep
their prior environment and cannot access user-home state through this change.
The new values identify only the current OS user and standard user bus; they
are not model inputs. A user
without a native manager cannot supply loaded-service qualification.

## Verification

Unit tests poison parent `HOME` and `XDG_RUNTIME_DIR` and assert the two
service-aware reads use only the OS-derived values while ordinary status and
the capability probe retain the two-variable environment. They also cover
missing account records, refreshed runtime-directory state, and rejection
of symlinked, non-directory, or wrong-owner runtime paths. The v0.2.0
qualification stage checks
absent, loaded, and drifted definitions through fresh Hermes sessions and
the native user manager on each supported platform, with a unique group
and cleanup after the check.
