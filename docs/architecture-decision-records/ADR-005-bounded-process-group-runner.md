# ADR-005: Bounded Process-Group Runner — Execution Environment, Concurrent Capture, and Termination

Status: Accepted

## Context

The PRD requires runner.py to construct fixed argv with shell disabled, run
it in a neutral trusted working directory with a minimal environment
allowlist and closed unexpected file descriptors, drain stdout and stderr
concurrently with bounded buffers, terminate the entire process group on
deadline or output overflow (TERM, a fixed two-second grace, then
force-kill), never retry, and discard captured output on deadline or
overflow. The catalog freezes the byte ceilings (stdout 1,048,576; stderr
65,536; combined 1,048,576; configuration tightens but never raises the
combined ceiling) and the grace ladder. The dossier names the neutral cwd,
the environment allowlist, the concurrent capture mechanism, and the
process-group termination implementation as decisions to record. The
upstream global `--config <path>` flag position was verified against the
installed Agent Dispatch v0.1.6: it is rejected before the subcommand and
accepted anywhere after it, so the runner appends it after the action's
frozen argv template.

## Decision

- **Fixed argv, appended trusted config.** One execution is exactly
  `argv = (trusted binary,) + ActionSpec.resolve_argv(params) +
  ("--config", trusted config path)`. Command construction lives only in
  the registry derivation (ADR-001); the runner adds nothing model
  reachable, `shell` is false at the single `Popen` site, and stdin is
  `DEVNULL` with `close_fds` true, so no unexpected descriptor survives
  into the child.
- **Neutral cwd is the plugin root.** The working directory is the frozen
  plugin package directory (`registry.PLUGIN_ROOT`): operator-installed,
  never model-controlled, and never a temporary or state directory the
  child could pollute. The trusted config's parent was rejected because a
  state-adjacent directory invites write side effects.
- **Minimal environment allowlist.** The child environment is exactly
  `PATH=/usr/bin:/bin:/usr/sbin:/sbin` and `TMPDIR=/tmp`, fixed in code.
  Nothing inherited — no `HOME`, no Hermes or agent variables, no proxy or
  credential variables — so the inspection cannot observe or depend on the
  host session. The same environment and cwd back the trust gate's
  `version` probe, verified against the real binary under `env -i`.
- **Concurrent capture with immediate ceiling checks.** Two daemon reader
  threads drain the pipes with unbuffered `os.read` partial reads (64 KiB
  slices): buffered `read(n)` was rejected because it blocks until a full
  buffer or EOF and would defer — or under partial backlog never reach —
  the ceiling decision. Every partial chunk is checked against its own
  stream cap (`min(stream cap, configured ceiling)` for stdout, the frozen
  stderr cap) and the shared combined counter before it is stored; the
  first chunk that would cross any ceiling sets one shared overflow flag
  and empties that stream's sink. The overflow flag is authoritative even
  when the process exits in the same instant, because a backlog can cross
  the ceiling after the waiter observed a clean exit.
- **TERM-then-force-kill over the whole group.** The child starts with
  `start_new_session=True`, so it leads a fresh process group. On deadline
  or overflow the runner sends SIGTERM to the group (`os.killpg`), waits
  the frozen two-second grace, then SIGKILLs the group; readers then see
  EOF and exit. Deadline and overflow share the same ladder.
- **No retry, ever.** One `run_inspection` call performs exactly one
  `Popen`; every failure mode — trust, spawn, timeout, overflow, malformed
  output — returns one closed wrapper result. On timeout or overflow every
  captured byte is discarded and only bounded, output-free diagnostics are
  returned.

## Consequences

- A command that ignores TERM still dies within deadline plus grace, and
  its children die with it; nothing survives the ladder.
- Output that crosses a ceiling kills the producer immediately instead of
  buffering megabytes; the JSON envelope of a well-behaved command never
  approaches the ceilings.
- The exit status of a terminated or overflowed process is not trusted as
  evidence; those results carry `exit_code` -1.
- A hostile producer can force at most one bounded execution per call.
- Accepted residual: a descendant that escapes the process group with its
  own session can hold the pipe write end open past the ladder, leaving a
  daemon reader blocked past its bounded join. The sinks are already capped
  so nothing grows, the result is built from the bounded sink, and a
  same-user process escaping the group is outside the threat model — the
  same boundary ADR-004 draws for the time-of-check window.

## Alternatives

- `subprocess.communicate(timeout=...)`: rejected — it cannot bound the
  two streams independently, cannot stop reading at a ceiling, and its
  kill path handles only the direct child.
- `selectors`-based single-thread draining: rejected — equivalent bounds
  with more state machine complexity for two streams.
- Killing only the child PID: rejected — grandchildren would survive
  (inspection commands may spawn helpers), violating the group guarantee.
- Buffered stream reads: rejected after testing — they deadlock the
  ceiling decision on partial backlogs (a stderr-only producer blocks the
  reader that must flag the overflow).

## Verification

`tests/unit/test_execution.py` proves fixed argv as an array with the
appended trusted `--config` flag, no shell, the exact minimal environment
(allowing only the macOS python3 shim's documented exec additions in the
fake), the neutral cwd, forbidden model inputs never reaching execution,
deadline `timeout` with partial-output disposal, per-stream and combined
and configured-ceiling `output_too_large`, the TERM-ignoring group killed
after grace with its child reaped, exactly one invocation per call under
every failure mode, domain rejection carrying the envelope and exit
status, malformed stdout failing closed, and spawn failure failing closed.
