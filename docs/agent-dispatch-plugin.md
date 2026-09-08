---
title: Agent Dispatch Plugin
created: 2026-09-03
updated: 2026-09-03
type: concept
tags: [workflow, multi-agent, artifact-management, wiki-governance]
owner: ai
authorship: ai
review_status: ai-reviewed
authority: working
sources:
  - raw/web/agent-dispatch-v0-1-6-release-2026.md
  - raw/web/agent-dispatch-v0-1-6-plugin-contracts-2026.md
  - raw/web/hermes-native-plugin-system-2026.md
aliases: [agent-dispatch-plugin]
confidence: medium
review_by: 2026-10-03
contested: false
---

# Agent Dispatch Plugin Development Brief

> Status: development-ready proposal, not approved implementation
> Target repository: `github.com/<owner>/agent-dispatch-plugin`
> Baseline: Agent Dispatch v0.1.6, Hermes Agent v0.20.5 or newer, macOS darwin/arm64
> Primary audience: engineering lead, plugin developer, security reviewer, release owner

## 1. Executive decision

Build `agent-dispatch-plugin` as a separate GitHub repository containing a Hermes `standalone` native runtime plugin. The plugin is a thin management and inspection adapter over the Agent Dispatch public CLI. It must not own sensing, route policy, SQLite state, retry decisions, serialization, notification identity, or dispatch correctness. ^[raw/web/agent-dispatch-v0-1-6-plugin-contracts-2026.md]

The first release should contain inspection tools only. Worker receipt tools follow after a separate security gate. Operator mutations and Desktop UI are later options, not v0.1.0 requirements.

This document is the implementation brief. A development team should be able to derive issues, estimates, code structure, tests, review gates, installation instructions, and release criteria from it without inventing product semantics.

## 2. Problem statement

Agent Dispatch already exposes operational truth through its CLI, but Hermes agents must currently invoke that CLI through a general terminal tool and remember command syntax, output contracts, side effects, and trust boundaries. This creates avoidable risks:

- models can choose the wrong command or flags;
- observational and mutating commands are easy to confuse;
- unbounded or malformed output may enter the model context;
- binary, config, route, and identity values can be selected from untrusted text;
- worker receipts can be attempted outside their dispatch lineage;
- installation and compatibility checks are manual and inconsistent.

The plugin solves those integration problems without replacing Agent Dispatch authority.

## 3. Product goal

Provide typed, discoverable, bounded Hermes tools that let an authorized Hermes agent inspect Agent Dispatch safely and consistently through the official Agent Dispatch CLI.

### Success outcomes

1. A user installs the plugin from GitHub with an immutable commit SHA.
2. Installation is disabled by default and requires explicit review and enablement.
3. Hermes exposes the `agent_dispatch` toolset only on selected platforms.
4. A normal Hermes session can inspect status, routes, dispatches, receipts, events, quarantine, notifications, schedule, and redacted config.
5. No v0.1.0 tool submits work, changes policy, delivers notifications, modifies Watchman or launchd, or edits SQLite.
6. Invalid binaries, unsupported versions, malformed envelopes, oversized output, and unexpected commands fail closed.
7. Removing the plugin leaves Agent Dispatch sensing, dispatch, state, and history intact.

### Measurable release targets

- 100% of declared tools have positive, negative, timeout, malformed-output, and command-injection tests.
- `hermes plugins doctor . --ci` passes from a clean clone.
- A disposable Hermes profile installs the GitHub commit, enables the plugin and toolset, runs every v0.1.0 tool, disables and removes the plugin, and has no plugin residue.
- No test or implementation reads Agent Dispatch SQLite directly.
- No subprocess call uses a shell.
- No secret, note body, frontmatter body, or unrestricted stderr appears in tool output.

## 4. Non-goals

The project must not:

- host or replace the Watchman trigger;
- implement Agent Dispatch route evaluation;
- read or write Agent Dispatch SQLite directly;
- recreate Agent Dispatch retry, reconciliation, or serialization logic;
- create, rename, or delete Hermes Kanban boards;
- access Hermes private task or profile databases;
- infer authority from note text, file names, manifest fields, or model output;
- install or modify Agent Dispatch itself;
- silently enable a production route;
- add a daemon, network listener, MCP server, or webhook endpoint in v0.1.0;
- expose a generic “run arbitrary Agent Dispatch command” tool;
- bundle copied official skills in v0.1.0;
- provide Desktop UI in v0.1.0;
- claim strict filesystem read-only behavior when opening an older Agent Dispatch store may migrate it.

## 5. Design principles

1. **Single authority:** Agent Dispatch remains authoritative for its state and decisions.
2. **Public interfaces only:** use documented Hermes plugin APIs and Agent Dispatch CLI surfaces.
3. **Contract first:** define JSON schemas and error semantics before handlers.
4. **Least privilege:** inspection first; worker and admin surfaces are separate.
5. **Fail closed:** uncertainty hides or rejects a capability rather than guessing.
6. **No shell:** executable plus argv array only.
7. **Bound everything:** time, output bytes, identifiers, list limits, diagnostics.
8. **Explicit activation:** install, plugin enablement, and toolset enablement are separate.
9. **Reproducible distribution:** immutable Git commit and release evidence.
10. **Honest observability:** distinguish domain result, CLI exit, plugin transport, and cache or migration side effects.

### Binding v0.1.0 decisions

The following are fixed for v0.1.0 and are not open to implementation-team reinterpretation:

- release scope is the ten inspection tools only;
- worker receipt, admin mutation, hooks, CLI/slash commands, gateway, ACP, Desktop, and plugin-bundled skills are excluded;
- toolset activation is supported only on the interactive Hermes CLI surface;
- inspection is migration-capable under Agent Dispatch's documented forward-migration and backup behavior; explicit plugin and CLI-toolset enablement constitutes operator consent to that bounded side effect;
- unattended worker, cron, gateway, and messaging use is prohibited in v0.1.0;
- production configuration requires absolute, non-symlink binary and config paths plus an expected binary SHA-256;
- supported host is exactly `darwin/arm64`;
- supported Agent Dispatch range is `>=0.1.6,<0.2.0` with exact `agent-dispatch.cli/v1` compatibility;
- supported Hermes range for v0.1.0 is `>=0.20.5`, with v0.20.5 as the tested reference build;
- the GitHub repository is source-only; no wheel, daemon, service, or bundled executable is distributed.

## 6. Supported compatibility

### Required baseline

| Component | Required |
|---|---|
| Agent Dispatch | `>=0.1.6,<0.2.0`, plus exact machine API v1 |
| Hermes Agent | `>=0.20.5`; v0.20.5 is the tested reference build for plugin v0.1.0 |
| OS/architecture | exactly Darwin arm64 |
| Plugin format | native directory plugin |
| Manifest | v2 |
| Plugin API | v1 |
| Agent Dispatch machine API | `agent-dispatch.cli/v1` |

Do not use an unbounded “latest works” claim. Each plugin release must publish a tested matrix. A new Agent Dispatch or Hermes release is unsupported until contract tests pass and the matrix changes in a reviewed plugin release.

### Version detection

- Resolve the binary from operator-controlled plugin config.
- Require an absolute regular executable that is not a symlink in production mode.
- Verify its SHA-256 against the configured expected digest before every invocation; refuse a mismatch.
- Require `platform.system() == "Darwin"` and `platform.machine() == "arm64"`.
- Run `<binary> version --json` without `--output`.
- Require `name == "agent-dispatch"`.
- Require a parseable version in `>=0.1.6,<0.2.0` and reject an unknown machine API.
- Cache only successful detection for the current process.
- Clear the cache when plugin settings reload.
- Hide tools when detection fails.

## 7. Repository and ownership

### Recommended repository

`github.com/irootkernel/agent-dispatch-plugin` is preferred if the Agent Dispatch maintainer owns the integration. If another organization owns it, the README must state that it is an independent integration and not part of Agent Dispatch.

### Roles

| Role | Responsibility |
|---|---|
| Product owner | approves goals, scope, naming, public release |
| Engineering lead | owns architecture, issue breakdown, merge decisions |
| Plugin developer | implements manifest, schemas, runner, handlers, tests |
| Security reviewer | reviews process execution, context gates, redaction, mutations |
| Agent Dispatch maintainer | confirms CLI and receipt contract interpretation |
| Release owner | pins commits, verifies clean install, publishes release evidence |

One person may hold several roles, but security approval and release approval should not rely solely on the implementation author for v0.1.0.

## 8. Required repository layout

```text
agent-dispatch-plugin/
├── plugin.yaml
├── __init__.py
├── schemas.py
├── runner.py
├── tools/
│   ├── __init__.py
│   ├── status.py
│   ├── routes.py
│   ├── dispatches.py
│   ├── receipts.py
│   ├── events.py
│   ├── quarantine.py
│   ├── notifications.py
│   ├── schedule.py
│   └── config.py
├── tests/
│   ├── fixtures/
│   ├── test_manifest.py
│   ├── test_runner.py
│   ├── test_schemas.py
│   ├── test_inspection_tools.py
│   ├── test_security.py
│   ├── test_installation.py
│   └── test_contract_compatibility.py
├── docs/
│   ├── architecture.md
│   ├── security.md
│   ├── compatibility.md
│   ├── installation.md
│   ├── operations.md
│   └── release-checklist.md
├── AGENTS.md
├── CHANGELOG.md
├── README.md
├── LICENSE
└── pyproject.toml
```

`runner.py` is the sole subprocess boundary. Tool modules may build typed requests but must not call `subprocess` directly.

## 9. Hermes plugin manifest contract

Minimum intended manifest:

```yaml
name: agent-dispatch-plugin
version: 0.1.0
kind: standalone
manifest_version: 2
api_version: 1
platforms: [macos]
description: Inspect Agent Dispatch through its public CLI.
author: <owner>
license: MIT
homepage: https://github.com/<owner>/agent-dispatch-plugin
tags: [agent-dispatch, hermes, kanban, operations]
provides_tools:
  - agent_dispatch_status
  - agent_dispatch_doctor
  - agent_dispatch_routes
  - agent_dispatch_dispatches
  - agent_dispatch_receipts
  - agent_dispatch_event_show
  - agent_dispatch_quarantine
  - agent_dispatch_notifications
  - agent_dispatch_schedule_inspect
  - agent_dispatch_config
config_schema:
  binary_path:
    type: str
    required: true
    description: Absolute non-symlink Agent Dispatch executable path.
  binary_sha256:
    type: str
    required: true
    description: Expected lowercase SHA-256 of the Agent Dispatch executable.
  config_path:
    type: str
    required: true
    description: Absolute non-symlink trusted Agent Dispatch config path.
  timeout_seconds:
    type: int
    default: 30
    description: Per-command timeout from 1 through 300 seconds.
  max_output_bytes:
    type: int
    default: 1048576
    description: Combined bounded output ceiling.
```

### Manifest rules

Do:

- declare every registered tool exactly once;
- declare `standalone`, manifest v2, API v1, and macOS explicitly;
- keep the description concise and operational;
- use plugin-scoped settings through `ctx.get_config()`;
- request no privileged capabilities in v0.1.0.

Do not:

- use `override=True`;
- request `tools.override` or LLM override capabilities;
- declare Agent Dispatch as a Python dependency;
- include secrets in plugin settings defaults;
- copy configuration from event or model data;
- register undeclared tools or hooks.

## 10. Runtime architecture

```text
Hermes model
  → typed plugin schema
  → tool handler
  → request validation
  → shared runner
  → agent-dispatch executable
  → agent-dispatch.cli/v1 envelope
  → envelope and command verification
  → bounded plugin result
  → Hermes model
```

### Component responsibilities

#### `__init__.py`

- read plugin-scoped settings;
- construct immutable runtime configuration;
- register schemas and handlers using `ctx.register_tool()`;
- attach `check_fn` for binary and version availability;
- perform no network, database, migration, or Agent Dispatch state operation during registration.

#### `schemas.py`

- contain model-facing tool descriptions and JSON parameter schemas;
- make required fields explicit;
- use enums for actions and states;
- reject additional properties unless forward compatibility requires them;
- explain side effects honestly in descriptions.

#### `runner.py`

- resolve only the configured executable;
- append only fixed command tokens selected by code;
- append trusted `--config` when configured;
- use `--output json` for all commands except `version --json`;
- set `shell=False`;
- use a neutral trusted working directory;
- provide a minimal environment allowlist;
- close unexpected file descriptors;
- enforce timeout and process-group termination;
- cap stdout and stderr independently;
- parse and validate the returned envelope;
- redact diagnostics;
- return structured errors, never raise into the Hermes loop.

#### Tool handlers

- validate model arguments;
- map one tool action to one fixed CLI command;
- call only `runner.py`;
- normalize lists and limits;
- preserve identifiers exactly;
- never interpret note content or invent remediation.

## 11. External interface A — Hermes plugin API

Use only these required surfaces for v0.1.0:

| Hermes surface | Use |
|---|---|
| `register(ctx)` | plugin entrypoint called at startup |
| `ctx.register_tool()` | register each typed tool under `agent_dispatch` |
| `ctx.get_config()` | read plugin-scoped operator settings |
| `check_fn` | hide tools when binary or version is unavailable |
| `hermes plugins doctor` | validate discovery, manifest, import, registration |
| `hermes plugins install` | install the GitHub repository |
| `hermes plugins enable/disable/remove` | lifecycle management |
| `hermes tools enable/disable` | platform-specific toolset activation |

Do not use in v0.1.0:

- `ctx.register_hook()`;
- `ctx.register_cli_command()`;
- `ctx.register_command()`;
- `ctx.dispatch_tool()`;
- `ctx.state`;
- `ctx.set_config()`;
- built-in tool override;
- Desktop plugin APIs.

Those surfaces require a separate requirement and review. ^[raw/web/hermes-native-plugin-system-2026.md]

## 12. External interface B — Agent Dispatch CLI

### General invocation

```text
<binary> <command> [fixed subcommand] [validated arguments]
  [--config <trusted-config-path>]
  --output json
```

Exception:

```text
<binary> version --json
```

### Machine output

The runner requires one JSON object. For command invocations it must verify:

- `api_version == "agent-dispatch.cli/v1"`;
- `command` equals the requested command surface;
- `ok` is boolean;
- success and error members match the exit status;
- output stays within configured bounds.

The plugin returns a wrapper:

```json
{
  "schema_version": "agent-dispatch-plugin.result/v1",
  "ok": true,
  "operation": "agent_dispatch_status",
  "exit_code": 0,
  "agent_dispatch": {
    "api_version": "agent-dispatch.cli/v1",
    "command": "status",
    "ok": true,
    "result": {},
    "warnings": [],
    "trace_id": ""
  },
  "diagnostics": []
}
```

Do not flatten or reinterpret Agent Dispatch domain data in v0.1.0. Preserve the validated envelope so the plugin does not become a second semantic authority.

### Exit-code treatment

| Exit | Class | Plugin behavior |
|---:|---|---|
| 0 | success | return validated success envelope |
| 2 | usage | plugin bug or invalid mapping; return `adapter_usage_error` |
| 3 | configuration | return redacted configuration error |
| 4 | rejected/not found | return bounded domain rejection |
| 10 | transient | return retryable transport/runtime error without auto-retry |
| 11 | target unavailable | return target-unavailable evidence |
| 12 | target rejected | return target rejection; do not retry |
| 13 | acceptance unknown | preserve uncertainty; never infer failure or retry |
| 14 | conflict | return conflict and required operator inspection |
| 20 | storage | return storage failure; never inspect SQLite directly |
| 21 | migration | return migration failure and stop |
| 30 | security | return security refusal and stop |
| 40 | internal | return bounded internal error and stop |

The plugin must not automatically retry any Agent Dispatch command in v0.1.0.

## 13. External interface C — process environment

### Allowed inputs

- plugin setting `binary_path`;
- plugin setting `config_path`;
- plugin setting `timeout_seconds`;
- plugin setting `max_output_bytes`;
- a minimal environment needed by the configured executable, documented and tested.

### Forbidden inputs

Model arguments, note contents, manifest values, URLs, or file names must not select:

- executable path;
- config path;
- state directory;
- Hermes profile;
- Hermes board;
- notification sink;
- route not explicitly supplied to a route-scoped inspection tool;
- environment variables;
- working directory.

The runner must never inherit arbitrary environment variables merely for convenience. If `HOME` and `PATH` are needed, document why and test the exact allowlist.

## 14. External interface D — GitHub distribution

### Install

```bash
hermes plugins install <owner>/agent-dispatch-plugin \
  --no-enable \
  --ref <40-character-immutable-commit-sha>
```

### Review and activate

```bash
hermes plugins doctor agent-dispatch-plugin --ci
hermes plugins show agent-dispatch-plugin
hermes plugins capabilities agent-dispatch-plugin
hermes plugins enable agent-dispatch-plugin --no-allow-tool-override
hermes tools enable agent_dispatch --platform cli
```

### Disable and remove

```bash
hermes tools disable agent_dispatch --platform cli
hermes plugins disable agent-dispatch-plugin
hermes plugins remove agent-dispatch-plugin
```

Installation documentation must distinguish repository source, release tag, exact commit, plugin enablement, and toolset enablement.

## 15. v0.1.0 tool contract

All tools belong to `agent_dispatch`. All are inspection surfaces; none accepts arbitrary flags.

### `agent_dispatch_status`

- CLI: `status --output json`
- Input: empty object
- Output: complete status envelope
- Side effects: may open and migrate an older store under Agent Dispatch rules
- Must not: auto-fix drift, retry work, drain notifications

### `agent_dispatch_doctor`

- CLI: `doctor [--probe-targets] --output json`
- Input: `probe_targets: boolean = false`
- Output: findings and remediations
- Side effects: target probing can refresh capability evidence
- Must not: execute remediation

### `agent_dispatch_routes`

- CLI: `route list` or `route show --route <id>` or `route preflight --route <id>`
- Input: action enum; route ID required for show/preflight
- Output: route projection or preflight checks
- Must validate: route identifier grammar and length
- Must not: enable, disable, stale, set profile, or set skills

### `agent_dispatch_dispatches`

- CLI: `dispatches list` or `dispatches show <id>`
- Input: action enum, optional route/state/limit/offset, required dispatch ID for show
- Output: redacted list or lineage
- Must bound: limit and offset
- Must not: retry, drain, discard, rerun, reprocess, refresh

### `agent_dispatch_receipts`

- CLI: `receipts list` or `receipts show <id>`
- Input: action enum, optional route/dispatch/kind/limit/offset
- Output: redacted receipt evidence
- Must not: treat receipt existence as work success

### `agent_dispatch_event_show`

- CLI: `events show <aggregate-id>`
- Input: aggregate event ID
- Output: aggregate and child evidence
- Must not: trigger follow-up work

### `agent_dispatch_quarantine`

- CLI: `quarantine list` or `quarantine show <id>`
- Input: action enum, optional route/state/limit, required ID for show
- Output: held or resolved structural cases
- Must not: release or discard

### `agent_dispatch_notifications`

- CLI: `notifications list`
- Input: optional route/state/sink/limit
- Output: notification delivery evidence
- Must not: test, retry, or drain a sink

### `agent_dispatch_schedule_inspect`

- CLI: `schedule inspect --route <id> --platform launchd`
- Input: route ID
- Output: present, loaded, definition match, digests, health
- Must not: render, install, disable, uninstall, or run

### `agent_dispatch_config`

- CLI: `config show` or `config validate [--probe-targets]`
- Input: action enum, `probe_targets` for validate
- Output: redacted normalized config, computed revisions, validation findings
- Must not: return secret values or rewrite configuration

## 16. Exact parameter contract

All string identifiers must be preserved literally after validation; handlers must not lowercase, trim internal characters, repair, or reinterpret them. Reject invalid values before invoking the CLI.

| Tool | Parameter | Type | Required | Constraint |
|---|---|---|---:|---|
| status | none | object | yes | no additional properties |
| doctor | `probe_targets` | boolean | no | default false |
| routes | `action` | enum | yes | `list`, `show`, `preflight` |
| routes | `route_id` | string | conditional | required for show/preflight; Agent Dispatch identifier grammar |
| dispatches | `action` | enum | yes | `list`, `show` |
| dispatches | `dispatch_id` | string | conditional | required for show |
| dispatches | `route`, `state` | string | no | passed only to documented filters |
| dispatches | `limit` | integer | no | 1–100, default 25 |
| dispatches | `offset` | integer | no | 0 or greater; bounded upper limit documented by implementation |
| receipts | `action` | enum | yes | `list`, `show` |
| receipts | `receipt_id` | string | conditional | required for show |
| receipts | `route`, `dispatch`, `kind` | string/enum | no | kind from documented closed set |
| receipts | `limit`, `offset` | integer | no | same pagination bounds |
| event show | `aggregate_id` | string | yes | bounded identifier |
| quarantine | `action` | enum | yes | `list`, `show` |
| quarantine | `quarantine_id` | string | conditional | required for show |
| quarantine | `route`, `state`, `limit` | string/enum/integer | no | documented filters only |
| notifications | `route`, `state`, `sink` | string/enum/string | no | documented list filters only |
| notifications | `limit` | integer | no | 1–100, default 25 |
| schedule inspect | `route_id` | string | yes | bounded route identifier |
| config | `action` | enum | yes | `show`, `validate` |
| config | `probe_targets` | boolean | no | valid only for validate |

Schema rules:

- set `additionalProperties: false` for v0.1.0 tools;
- use conditional validation in handlers even when JSON Schema expresses it;
- return `invalid_argument` without spawning a process on any violation;
- never accept `flags`, `command`, `args`, `environment`, `cwd`, `binary`, `config`, or `state_dir` from the model;
- cap every list result through the documented CLI limit;
- treat unknown future enum values as unsupported until the plugin contract is updated.

## 17. Requirement traceability

| ID | Requirement | Verification |
|---|---|---|
| ARCH-001 | separate GitHub repository | repository URL and clean-clone test |
| ARCH-002 | management-only thin adapter | architecture review; no core state implementation |
| ARCH-003 | one shared subprocess runner | static search and code review |
| HERMES-001 | native standalone manifest v2/API v1 | Plugin Doctor |
| HERMES-002 | dynamic `agent_dispatch` toolset | fresh-session inventory |
| HERMES-003 | no override capabilities | manifest and capabilities output |
| AD-001 | Agent Dispatch v0.1.6 minimum | version positive/negative tests |
| AD-002 | `agent-dispatch.cli/v1` envelope | contract fixture tests |
| AD-003 | requested command matches envelope | mismatch negative test |
| AD-004 | public CLI only | static review; no SQLite imports or paths |
| SEC-001 | no shell execution | static search and subprocess mock assertions |
| SEC-002 | fixed command allowlist | command descriptor tests |
| SEC-003 | bounded timeout and outputs | timeout/oversize tests |
| SEC-004 | trusted binary/config only | schema negative tests |
| SEC-005 | redacted diagnostics | seeded-secret tests |
| SEC-006 | no automatic retry | call-count assertions |
| TOOL-001 | ten inspection tools only in v0.1.0 | manifest-to-registry parity test |
| TOOL-002 | no mutation command reachable | denylist/static command test |
| DIST-001 | disabled pinned GitHub install | disposable-profile transcript |
| DIST-002 | complete removal without residue | post-uninstall inspection |
| DOC-001 | install, security, compatibility, rollback docs | release checklist |
| WORK-001 | receipt tools absent in normal sessions | post-v0.1.0 negative test |
| WORK-002 | trusted worker identity only | worker extension security test |

Every PR must cite the requirement IDs it implements and the exact tests that verify them. A requirement may not be marked complete from prose review alone when a deterministic test is possible.

## 18. Plugin result and error contract

### Plugin errors

Use a closed plugin error set:

- `binary_unavailable`
- `unsupported_agent_dispatch_version`
- `invalid_argument`
- `timeout`
- `output_too_large`
- `malformed_json`
- `contract_mismatch`
- `adapter_usage_error`
- `execution_failed`
- `redaction_failure`

Each error includes:

```json
{
  "code": "contract_mismatch",
  "message": "bounded human-readable summary",
  "retryable": false
}
```

Do not expose Python tracebacks, unrestricted stderr, environment dumps, or file bodies to the model.

### Redaction

At minimum redact:

- authorization values;
- secret references when they reveal protected paths;
- token-like strings;
- full webhook URLs when Agent Dispatch output policy marks them sensitive;
- unexpected absolute paths outside the configured binary and config display policy.

Prefer returning Agent Dispatch's already-redacted JSON. Plugin redaction is defense in depth, not permission to call unredacted surfaces.

## 19. Worker receipt extension — post-v0.1.0

Do not include this in v0.1.0 unless the security review explicitly moves it into scope.

### Required context gate

Every receipt call must require all of the following:

1. `HERMES_KANBAN_TASK` exists.
2. Hermes reports dispatcher-owned worker context.
3. Execution is not a delegated child.
4. Execution is not an in-process cron context.
5. The current worker task equals the dispatch's stored external task ID through Agent Dispatch validation.
6. The plugin uses a fixed Agent Dispatch instance and config.

### Proposed tools

- `agent_dispatch_work_begin`
- `agent_dispatch_work_complete`
- `agent_dispatch_work_fail`

Do not combine them into a general work command. Tool visibility itself must be dynamic: ordinary sessions must not receive these schemas.

### Identity rules

- Do not accept `external_task_id` from the model.
- Derive it from trusted worker context.
- Generate run ID from trusted task and worker-run context plus sufficient uniqueness.
- Keep begin state scoped to the current process and worker.
- Require successful begin before complete or fail.
- Never synthesize a receipt from an assistant summary or a Kanban completion hook.

### Manifest rules

Prefer structured JSON arguments over arbitrary file paths. Validate before creating a temporary owner-only file:

- maximum 1,000 changes;
- vault-relative canonical paths only;
- reject absolute paths, `..`, NUL, duplicate paths, and non-normal form;
- digest format `sha256:<64 lowercase hex>`;
- no note bodies, frontmatter bodies, URLs, secrets, or hidden reasoning;
- partial completion requires non-empty completed and remaining scopes as defined by Agent Dispatch;
- blocked requires a bounded factual reason and no changes;
- failed requires one closed failure code.

Temporary receipt files must use an approved OS temporary location, mode 0600, deterministic cleanup, and no profile-directory scratch storage.

## 20. Operator mutation extension — later release

If needed, place mutation tools in a separate `agent_dispatch_admin` toolset disabled by default.

Candidate actions:

- route disable/enable;
- reconcile with or without submit;
- dispatch retry/drain/discard;
- quarantine release/discard;
- notification retry/drain.

Every mutation requires:

- exact target identifier;
- required operator reason;
- expected current state or revision;
- Hermes per-call human approval;
- Agent Dispatch's own confirmation and production gates;
- exact target read-back after success;
- no automatic chaining beyond the documented command.

Never protect mutation only with a model-provided `confirm: true`. Do not expose setup, Watchman lifecycle, schedule lifecycle, maintenance, raw dispatch, rerun, reprocess, or notification transport test as model-callable tools without a new threat model.

## 21. Threat model

| Threat | Required control |
|---|---|
| Shell injection | fixed argv, `shell=False`, identifier validation |
| Prompt injection | no note body; untrusted data cannot choose authority |
| Path traversal | no model-selected filesystem path in v0.1.0 |
| Binary substitution | operator config, version/name check, documented absolute-path option |
| Config substitution | plugin-scoped trusted setting only |
| Output poisoning | size cap, JSON parse, envelope and command verification |
| Secret leakage | redacted command surfaces and bounded diagnostics |
| Duplicate privileged work | no mutation in v0.1.0; preserve idempotency in later tools |
| Forged receipt | worker context and Agent Dispatch lineage validation |
| Split authority | no plugin DB and no reimplementation of policy/state machines |
| Lifecycle coupling | plugin removal cannot affect Agent Dispatch core |
| Cost amplification | no automatic retry, fan-out, or task creation |
| Migration surprise | document inspection as operational, not strict read-only |

## 22. Development methodology

Use contract-first TDD.

1. Freeze the supported external contracts and test fixtures.
2. Write tool JSON schemas and negative cases before handlers.
3. Build the shared runner before any domain tool.
4. Add one vertical slice: status from handler to real CLI fixture.
5. Add remaining inspection tools one domain at a time.
6. Run security review before worker or mutation work.
7. Validate from a clean GitHub clone and disposable Hermes profile.
8. Release only from the exact reviewed commit.

### Branch and review method

- one feature branch per milestone;
- small PRs with one contract or tool family;
- no drive-by Hermes or Agent Dispatch changes in this repository;
- Agent Dispatch incompatibility becomes an upstream issue, not a private workaround;
- at least one independent reviewer for runner, worker gate, and release PRs.

## 23. Development sequence

### Stage 0 — Decisions and contract freeze

Entry criteria:

- product owner confirms repository owner, public/private status, license, and v0.1.0 scope.

Do:

- pin Agent Dispatch v0.1.6 commit and Hermes v0.20.5-or-newer reference;
- copy representative redacted JSON fixtures into tests;
- document command classification and side effects;
- define plugin result and error schemas;
- open issues for every later feature.

Do not:

- write tool handlers;
- create a generic CLI passthrough;
- decide semantics from observed output alone when a contract exists.

Deliverables:

- architecture decision;
- compatibility matrix;
- tool catalog;
- threat model;
- issue breakdown.

Exit criteria:

- engineering lead, security reviewer, and Agent Dispatch maintainer approve the contracts.

### Stage 1 — Repository scaffold

Entry criteria: Stage 0 approved.

Do:

- create GitHub repository and default branch protections;
- add manifest, package skeleton, tests, docs, license, changelog, and AGENTS.md;
- add formatting, lint, type, unit-test, and Plugin Doctor commands;
- make the default plugin capability set empty.

Do not:

- publish a release;
- enable automatic mutation;
- add dependencies that are not required by the inspection MVP.

Deliverables:

- clean clone builds and validates;
- Plugin Doctor runs against the skeleton;
- contributor documentation names exact commands.

Exit criteria:

- repository bootstrap CI or reproducible local verification is green.

### Stage 2 — Shared runner

Entry criteria: scaffold green.

Do:

- implement immutable runtime config;
- resolve binary and version;
- implement fixed argv command descriptors;
- implement timeout, process termination, output caps, JSON parsing, envelope verification, redaction, and error mapping;
- add fake executable fixtures for every exit and malformed result.

Do not:

- implement tools with direct subprocess calls;
- auto-retry;
- inherit unrestricted environment;
- parse human output.

Deliverables:

- tested `runner.py`;
- command descriptor table;
- plugin result schema.

Exit criteria:

- all runner branches and security negatives pass.

### Stage 3 — Inspection tools

Entry criteria: runner accepted.

Do:

- implement each v0.1.0 tool against fixed mappings;
- validate required identifiers, enums, limits, and pagination;
- ensure every handler catches errors and returns JSON;
- compare declared and registered tools.

Do not:

- expose undocumented flags;
- execute remediations returned by doctor;
- turn warnings into success or failure decisions;
- flatten Agent Dispatch domain semantics.

Deliverables:

- ten inspection tools;
- model-facing schemas;
- handler tests and snapshot fixtures.

Exit criteria:

- all tools pass positive and negative fixtures and actual v0.1.6 smoke tests.

### Stage 4 — Security and compatibility validation

Entry criteria: inspection tools complete.

Do:

- test malicious identifiers, oversized output, malformed JSON, command mismatch, timeouts, broken pipes, missing binaries, wrong versions, and redaction failures;
- verify no direct SQLite access and no shell invocation;
- test older/newer store behavior in disposable state;
- document any migration side effect.

Do not:

- test against production Agent Dispatch state;
- suppress failing cases as expected without an issue and rationale;
- broaden compatibility claims beyond tested versions.

Deliverables:

- security review report;
- compatibility evidence;
- resolved or accepted risk list.

Exit criteria:

- no open P0/P1 security issue; accepted P2 risks documented.

### Stage 5 — GitHub installation validation

Entry criteria: security gate passed.

Do:

- install exact commit into a disposable Hermes profile with `--no-enable`;
- run Plugin Doctor and capability inspection;
- enable without tool override;
- enable `agent_dispatch` only on CLI;
- run every tool against disposable Agent Dispatch state;
- disable and remove the plugin;
- verify no plugin config, toolset, file, or task residue.

Do not:

- use a mutable branch as release evidence;
- test against the user's production vault;
- claim installation success from `git clone` alone.

Deliverables:

- sanitized install transcript;
- exact commit SHA;
- uninstall residue report.

Exit criteria:

- clean install→inspect→remove round trip passes.

### Stage 6 — v0.1.0 release

Entry criteria: all previous stages pass.

Do:

- update changelog and compatibility matrix;
- tag the exact reviewed commit;
- publish install, upgrade, rollback, and removal instructions;
- record checksums or commit identity;
- re-run final artifact verification.

Do not:

- release from an uncommitted tree;
- alter code after final verification without restarting the gate;
- call the plugin “official” unless the repository owner authorizes that designation.

Deliverables:

- GitHub release;
- immutable install command;
- release evidence and known limitations.

Exit criteria:

- release artifact and documented commit are identical and installable.

### Stage 7 — Worker receipt research

Entry criteria: v0.1.0 stable and receipt requirement approved.

Do:

- validate public Hermes worker-context APIs;
- design three separate receipt tools;
- implement negative context tests before happy paths;
- run disposable Kanban begin→complete, partial, blocked, and fail flows.

Do not:

- read Hermes private storage;
- expose receipt tools in ordinary sessions;
- accept task identity from the model;
- infer changed files from assistant prose.

Exit criteria:

- independent security review and actual disposable task round trip pass.

## 24. Test matrix

### Unit tests

- manifest fields and declared tools;
- argument schemas and additional-property rejection;
- identifier grammar and literal preservation;
- version parser and compatibility range;
- command descriptors;
- output and diagnostic caps;
- timeout and process termination;
- exit-code mapping;
- JSON and envelope validation;
- redaction;
- handler exception containment.

### Negative security tests

- route ID containing spaces or option prefixes;
- shell metacharacters;
- absolute or traversal paths;
- model-selected executable/config/state directory;
- malicious stderr containing token-like values;
- success exit with wrong command envelope;
- success exit with wrong API version;
- acceptance-unknown response;
- migration failure;
- output larger than limit;
- unexpected inherited environment.

### Integration tests

- real v0.1.6 binary identity;
- config show and validate on disposable config;
- status and doctor on disposable state;
- route and schedule inspection;
- dispatch, receipt, event, quarantine, notification readback fixtures;
- plugin disabled state;
- toolset disabled state;
- fresh session discovery;
- GitHub commit installation and complete removal.

### Worker extension tests

- normal session: receipt tools absent;
- delegated child: absent;
- nested cron: absent;
- dispatcher worker: present;
- task mismatch: rejected;
- complete without begin: rejected;
- second complete: rejected;
- partial without remaining scope: rejected;
- blocked with changes: rejected;
- failed with unknown failure code: rejected.

## 25. Documentation requirements

README must contain:

- what the plugin is and is not;
- supported versions and platform;
- immutable GitHub installation;
- enablement and toolset activation;
- configuration keys;
- tool catalog and side effects;
- security boundary;
- troubleshooting;
- disable/remove/rollback;
- current known limitations.

`docs/architecture.md` must contain component and sequence diagrams. `docs/security.md` must map every threat to code and tests. `docs/compatibility.md` must name exact tested commits and versions. `docs/release-checklist.md` must be executable as a checklist, not prose only.

## 26. Release, upgrade, rollback, and uninstall

### Upgrade

1. inspect current plugin version and Agent Dispatch compatibility;
2. review changelog and newly requested capabilities;
3. install or update to an exact commit;
4. run Plugin Doctor;
5. run inspection smoke tests before re-enabling all platforms;
6. retain the previous known-good commit for rollback.

### Rollback

1. disable the `agent_dispatch` toolset;
2. disable the plugin;
3. install the previous pinned commit;
4. run Plugin Doctor;
5. re-enable plugin and selected platforms;
6. verify Agent Dispatch itself was unaffected.

### Uninstall

1. disable the toolset on every enabled platform;
2. disable the plugin;
3. remove the plugin;
4. remove plugin-only settings if Hermes does not remove them;
5. verify no plugin files, config entries, toolsets, hooks, or background tasks remain;
6. do not delete Agent Dispatch config, state, schedule, trigger, or history.

## 27. Observability and support

Every plugin invocation should record only bounded operational metadata:

- plugin version;
- operation name;
- duration;
- Agent Dispatch exit class;
- trace ID when present;
- contract mismatch code;
- whether output was truncated or redacted.

Do not log model arguments wholesale. Do not log secrets, note content, manifest bodies, or unrestricted CLI output.

Support bundles may include:

- plugin and Hermes versions;
- Agent Dispatch compact version;
- redacted plugin config;
- Plugin Doctor output;
- bounded error envelope;
- exact installed commit.

## 28. Open decisions with recommendations

| Decision | Recommendation |
|---|---|
| Repository owner | `irootkernel` if maintainer-controlled |
| Visibility | public, unless product policy requires private development first |
| License | MIT to align with Agent Dispatch and Hermes plugin examples |
| v0.1.0 scope | inspection only |
| Worker receipts | v0.2.0 after public-context and security validation |
| Admin mutations | defer beyond v0.2.0 |
| Bundled skills | none in v0.1.0 |
| Desktop UI | defer until operational need is measured |
| CI | deterministic unit/security tests plus clean-clone Plugin Doctor |
| Release pin | 40-character Git commit SHA |

These decisions require owner approval before Stage 1. Until then this page remains `working`, not canonical.

## 29. Definition of Ready

Development may begin when:

- repository owner and visibility are decided;
- license is approved;
- v0.1.0 inspection-only scope is approved;
- exact compatibility baselines are pinned;
- tool catalog and result schema are accepted;
- security reviewer is assigned;
- disposable Hermes and Agent Dispatch test environments are available;
- upstream ambiguity has an owner or issue.

## 30. Definition of Done for v0.1.0

The release is done only when:

- all ten inspection tools are implemented and declared;
- no mutation, worker receipt, hook, daemon, or Desktop code is included;
- every tool has positive and negative tests;
- runner security tests pass;
- actual v0.1.6 smoke tests pass on disposable state;
- Plugin Doctor passes from clean clone and installed copy;
- GitHub SHA installation succeeds while disabled;
- explicit enablement and CLI toolset activation succeed;
- fresh Hermes session calls all tools successfully;
- uninstall leaves no plugin residue;
- Agent Dispatch state remains intact;
- compatibility, security, install, rollback, and known-limit documentation is complete;
- independent reviewer signs off;
- release tag points to the exact verified commit.

## 31. Development-team handoff checklist

Before accepting this brief, the engineering lead should confirm:

- [ ] We understand Agent Dispatch remains the sole state and policy authority.
- [ ] We will not read either product's private databases.
- [ ] We accept inspection-only v0.1.0.
- [ ] We have exact Agent Dispatch and Hermes reference versions.
- [ ] We agree on repository owner, license, and visibility.
- [ ] We can create disposable integration environments.
- [ ] We will use fixed argv and no shell.
- [ ] We will validate the CLI envelope and requested command.
- [ ] We will not auto-retry unknown or transient work.
- [ ] We will test GitHub installation, activation, rollback, and removal.
- [ ] We will open upstream issues rather than shipping private semantic workarounds.
- [ ] We will request a new review before adding worker or admin capabilities.

## 32. Source-of-truth references

- Agent Dispatch v0.1.6 release: `raw/web/agent-dispatch-v0-1-6-release-2026.md`
- Agent Dispatch plugin-facing contracts: `raw/web/agent-dispatch-v0-1-6-plugin-contracts-2026.md`
- Hermes native plugin system: `raw/web/hermes-native-plugin-system-2026.md`
- Related system role: [[agent-dispatch]]
- Event-to-agent architecture: [[jjukkumi-event-to-agent-bridge]]
- Artifact and receipt governance: [[multi-agent-artifact-governance]]
- Knowledge publish lifecycle: [[knowledge-lifecycle]]

## 33. Current status

- Brief maturity: development-ready draft
- GitHub repository: not created
- Plugin source: not created
- Hermes plugin installation: none
- Approved release: none
- Next action: product owner resolves the decisions in section 28 and authorizes Stage 1
