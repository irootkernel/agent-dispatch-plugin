# Agent Dispatch Plugin

Agent Dispatch Plugin connects [Agent Dispatch](https://github.com/irootkernel/agent-dispatch) to your interactive Hermes conversations. Ask Hermes to inspect routes, follow a dispatch through its recorded history, look up receipts, or explain diagnostic findings without composing Agent Dispatch CLI commands yourself.

The plugin gives Hermes ten tools with defined inputs. Each tool invokes a specific Agent Dispatch inspection command, validates the response, and redacts sensitive information before returning it to the conversation. Agent Dispatch remains responsible for routing, execution, and stored state.

## What you can do

- **Check the current state:** ask for a status summary and inspect the configured routes.
- **Investigate a dispatch:** list recent dispatches for a route, open a particular dispatch, and inspect its receipts and related event evidence.
- **Understand a delivery problem:** inspect quarantine entries and notification records before deciding what to do next.
- **Check configuration and scheduling:** view redacted configuration, request validation or route preflight, and inspect a route's launchd schedule.

The plugin does not submit jobs, retry or discard dispatches, change routes, or send receipts. If the evidence points to a change being needed, you make that change separately through Agent Dispatch.

## Contents

- [Requirements](#requirements)
- [Install](#install)
- [Configure and enable](#configure-and-enable)
- [Your first conversation](#your-first-conversation)
- [Everyday examples](#everyday-examples)
- [Available tools](#available-tools)
- [Understand the results](#understand-the-results)
- [Troubleshooting](#troubleshooting)
- [Update or roll back](#update-or-roll-back)
- [Disable or remove](#disable-or-remove)
- [Release history](CHANGELOG.md)
- [Contribute](#contribute)

## Requirements

| Component | Requirement |
|---|---|
| Host | macOS on Apple Silicon (`darwin/arm64`) |
| Hermes | `>=0.20.5`; interactive CLI sessions only |
| Agent Dispatch | `>=0.1.6,<0.2.0`, with `agent-dispatch.cli/v1` |
| Distribution | Source directory; no wheel or bundled Agent Dispatch binary |

The v0.1.0 qualification targets Hermes v0.21.0 and both Agent Dispatch
v0.1.6 and v0.1.7 Darwin arm64 release artifacts. Version requirements do not mean
that every newer combination has been tested; see the
[qualification matrix](docs/implementation-tips/qualification-darwin-arm64.md).

The plugin offers inspection tools only: it cannot submit work, retry dispatches, or edit routes.
Inspection can still trigger Agent Dispatch's forward store migration and
backup behavior, and target probes can refresh capability caches. Enable it only for a configuration whose store you authorize
it to open. Unattended workers, cron, gateways, and messaging surfaces are
outside v0.1.0's supported use.

## Install

### 1. Prepare Agent Dispatch and your Hermes profile


Install [Agent Dispatch](https://github.com/irootkernel/agent-dispatch) separately
before installing this plugin; the plugin does not include the Agent Dispatch executable.

Have these values ready before proceeding:

| Value | Where it comes from |
|---|---|
| Hermes profile directory | The profile in which you want to use the plugin; it contains that profile's `config.yaml` |
| Agent Dispatch executable | Your separately installed Agent Dispatch binary |
| Agent Dispatch configuration | The existing configuration for the routes and state you want to inspect |
| Expected binary SHA-256 | The trusted identity of the Agent Dispatch artifact you installed |
| Plugin revision | The full commit ID selected for this installation |

The Hermes profile configuration and the Agent Dispatch configuration are different files. The plugin's settings go in the Hermes profile; `config_path` points to the Agent Dispatch configuration. Installing the plugin does not initialize Agent Dispatch or create routes for you.

### 2. Download the selected plugin revision

The [v0.1.0 release](https://github.com/irootkernel/agent-dispatch-plugin/releases/tag/v0.1.0)
provides a source archive and `SHA256SUMS`. Verify the checksum before
extracting it. The archive contains a top-level `agent-dispatch-plugin-v0.1.0/`
directory; copy that directory's contents into a new profile plugin directory,
then follow the configuration steps below. Install Agent Dispatch separately.
The release also records the exact source commit for the Git-based procedure:

Choose a full commit ID for the plugin revision you intend to install. Replace
the example values below, including the Hermes profile directory. Use the same
`HERMES_HOME` for configuration and every Hermes command.

```bash
export HERMES_HOME="/absolute/path/to/your/hermes-profile"
PLUGIN_REVISION="<full-40-character-commit-id>"

git clone https://github.com/irootkernel/agent-dispatch-plugin.git
cd agent-dispatch-plugin
git checkout --detach "$PLUGIN_REVISION"
git rev-parse HEAD
```

### 3. Place the plugin in the profile

Confirm the printed commit matches your selected revision before continuing. The commands below export the tracked source files into the profile's plugin directory; there is no plugin compilation or Python dependency installation step for users:

```bash
mkdir -p "$HERMES_HOME/plugins"
# Refuse an existing installation; only extract after mkdir succeeds.
mkdir "$HERMES_HOME/plugins/agent-dispatch-plugin" &&
  git archive HEAD | tar -x -C "$HERMES_HOME/plugins/agent-dispatch-plugin"
```

For an existing installation, use the
[upgrade and rollback procedure](docs/ops/upgrade-rollback-darwin-arm64.md).
Directory installation starts disabled. Hermes v0.20.5's `plugins install`
command rejects this plugin's manifest v2; its directory loader supports it.

## Configure and enable

### 1. Add the plugin settings

Merge this YAML into your profile's `config.yaml`, preserving its other
settings and plugin entries. Replace the three trust values with verified
paths and the binary digest.

```yaml
plugins:
  entries:
    agent-dispatch-plugin:
      settings:
        binary_path: "/absolute/path/to/agent-dispatch"
        binary_sha256: "<verified-lowercase-sha256>"
        config_path: "/absolute/path/to/agent-dispatch-config.yaml"
        timeout_seconds: 30
        max_output_bytes: 1048576
```

| Setting | Required / default | Meaning |
|---|---|---|
| `binary_path` | Required | Absolute regular executable path; no symlinked path segments |
| `binary_sha256` | Required | Expected 64-character lowercase SHA-256 of the trusted executable |
| `config_path` | Required | Absolute regular configuration file path; no symlinked path segments |
| `timeout_seconds` | Optional; `30` | Integer from 1 to 300 seconds per command |
| `max_output_bytes` | Optional; `1048576` | Integer from 1 to 1048576; tightens the combined output ceiling |

Use `shasum -a 256 /absolute/path/to/agent-dispatch` to calculate the local
digest and compare it with the trusted artifact identity before configuring
it. The local digest alone does not establish the artifact's origin.

### 2. Enable the plugin and its tools

These are installation and activation commands for your Hermes profile. They do not run the repository's developer test suite.

```bash
hermes plugins enable agent-dispatch-plugin --no-allow-tool-override
hermes tools enable agent_dispatch
hermes plugins show agent-dispatch-plugin
hermes tools list
```

Plugin enablement lets Hermes load the plugin. Toolset enablement makes `agent_dispatch` available on the interactive CLI surface. Both must be enabled in the same profile. `plugins show` and `tools list` help confirm those two states, but a successful inspection in a fresh conversation is the final check that the configured executable can be used.

## Your first conversation

Start a fresh interactive Hermes session using the profile you configured. Ask:

> Use agent_dispatch_status to inspect Agent Dispatch and summarize its current status.

Hermes should call `agent_dispatch_status` and explain the returned evidence. If the tool is unavailable, follow the troubleshooting section below before asking Hermes to diagnose domain state.

Next, discover the actual route IDs:

> Use the Agent Dispatch tools to list my configured routes. Show their IDs so I can choose one to inspect.

Pick an ID from that result and ask:

> Show the configuration for route ROUTE_ID and explain what the returned fields say about it.

Replace `ROUTE_ID` with the returned ID. You do not need to compose a JSON request: Hermes supplies the tool arguments from your request. If you have several similarly named routes, give the exact ID so the next inspection uses the intended one.

## Everyday examples

### Follow a dispatch

Start with the route and a small result set:

> List the 10 most recent dispatches returned for route ROUTE_ID. Show the dispatch IDs and their recorded states.

Then select a dispatch from the result:

> Inspect dispatch DISPATCH_ID and summarize its recorded lineage. List any receipts associated with it, and show which evidence supports your explanation.

Use IDs from the returned data. A receipt is something this plugin can inspect; asking it to inspect one does not acknowledge, complete, or fail a job. For another page of dispatches or receipts, ask for a list with the next offset. List requests default to 25 items and accept limits from 1 to 100.

### Investigate quarantine or notifications

> List the quarantine entries for route ROUTE_ID, then inspect the entry I select and explain its recorded details.

> Show the notification delivery records for route ROUTE_ID. Summarize the recorded states without attempting to resend anything.

These requests give you evidence for deciding what to do next. They do not release quarantined items or deliver notifications. When a returned record refers to an aggregate event, you can ask Hermes to inspect that aggregate ID for its child evidence.

### Check a route before taking action elsewhere

> Run preflight inspection for route ROUTE_ID and summarize its findings.

> Inspect the launchd schedule for route ROUTE_ID. Explain its reported presence, loaded state, and definition match.

Schedule inspection reports what Agent Dispatch observes; it does not install, load, or repair a schedule.

### Review configuration or diagnostics

> Show the redacted Agent Dispatch configuration and explain the fields relevant to my route.

> Validate the Agent Dispatch configuration without target probing and summarize any findings.

You can also ask for diagnostics with `agent_dispatch_doctor`. Target probing is optional for doctor and configuration validation; request it explicitly when you want it. Probes can refresh capability caches. The known Watchman lookup limitation described below can affect doctor results.

## Available tools

| Tool | What you can inspect |
|---|---|
| `agent_dispatch_status` | Overall status |
| `agent_dispatch_doctor` | Diagnostic findings; optional target probing |
| `agent_dispatch_routes` | Route list, one route, or route preflight |
| `agent_dispatch_dispatches` | Dispatch list or one dispatch's lineage |
| `agent_dispatch_receipts` | Receipt list or one receipt |
| `agent_dispatch_event_show` | An aggregate event and its child evidence |
| `agent_dispatch_quarantine` | Quarantined items and individual details |
| `agent_dispatch_notifications` | Notification delivery evidence |
| `agent_dispatch_schedule_inspect` | A route's launchd schedule |
| `agent_dispatch_config` | Redacted configuration or validation findings |

## Understand the results

Hermes receives validated Agent Dispatch evidence, not unrestricted terminal output. Configuration and diagnostics are redacted, so values may be intentionally hidden. Ask Hermes to distinguish the fields reported by a tool from its interpretation of them.

For doctor, a successful response can retain exit code 3: it means diagnostic
findings were retrieved, including error-severity findings. Read those findings
and their remediation guidance; the plugin does not execute remediation.
Watchman installed through Homebrew is outside the plugin's fixed PATH, so
an unavailable-Watchman finding can describe this inspection environment.

A successful tool call means the inspection completed through the plugin. It does not mean that a dispatch succeeded or that every diagnostic finding is healthy: those conclusions depend on the returned domain values. Likewise, an empty list means the request returned no matching records; check the route and filters before drawing a broader conclusion.

If the plugin cannot validate a response, reaches its time or output limit, or cannot trust the configured executable, it returns an error or keeps the tools unavailable. An inspection error does not establish the state of the dispatch you were investigating. The plugin does not automatically retry failed calls.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Hermes does not list the plugin | Confirm `HERMES_HOME` selects the profile where you installed it, and run `hermes plugins show agent-dispatch-plugin`. Check that the plugin directory is inside that profile's `plugins/` directory. |
| The plugin is installed but tools are missing | Enable both the plugin and `agent_dispatch` toolset, check `hermes tools list`, and start a fresh conversation in that profile. |
| Tools remain unavailable after enablement | Check the supported host and executable version, the three required settings, and whether either configured path contains a symlink. Compare the executable digest with the trusted artifact identity. |
| A binary replacement stops working | Confirm the replacement artifact's identity before updating `binary_sha256`; a different executable is rejected until its expected digest matches. |
| `hermes plugins install` rejects manifest v2 | Use the source-directory installation above. This is a recorded installer limitation in Hermes v0.20.5. |
| Doctor reports unavailable Watchman | Exit code 3 with a successful response preserves the diagnostic findings. Homebrew Watchman is outside the fixed PATH; read the findings and the detailed diagnosis below. |
| Doctor returns `contract_mismatch` | The response violated the expected contract. Verify the executable identity and version, then capture redacted evidence for the maintainer. |
| A request times out | Narrow the request. If appropriate, increase `timeout_seconds` within its 1–300 second range and start a fresh session before retrying. |
| A response exceeds the output limit | Request fewer items or inspect one record. `max_output_bytes` cannot exceed 1048576. |
| An identifier or argument is rejected | Use an exact ID returned by a previous inspection. Avoid adding shell flags or command text to an ID. |

If the problem persists, consult [diagnosis and recovery](docs/ops/troubleshooting.md). When asking the maintainers for help, include the plugin revision, Hermes and Agent Dispatch versions, tool name, and redacted error. Follow the [evidence capture guide](docs/ops/security-evidence-capture.md) before sharing output; do not attach your full profile configuration or raw secrets.

## Update or roll back

An installed plugin is a source directory at one selected revision. Updating replaces that directory; your settings and enablement belong to the Hermes profile. Keep a record of the previous revision so you can return to it if the update fails.

Use the [upgrade and rollback procedure](docs/ops/upgrade-rollback-darwin-arm64.md) instead of copying a new checkout over the old directory. After a replacement, open a fresh session and repeat the status inspection. If tools become unavailable, check the selected revision and trusted settings before proceeding.

## Disable or remove

Run these commands against the same profile used for installation:

```bash
hermes tools disable agent_dispatch
hermes plugins disable agent-dispatch-plugin
# Optional: delete the installed plugin directory through Hermes.
hermes plugins remove agent-dispatch-plugin
```

Start a fresh session and confirm the plugin's tools are absent. Removal leaves
Agent Dispatch's installation and domain state in place. For complete profile
bookkeeping cleanup, follow the
[installation lifecycle guide](docs/ops/install-lifecycle-darwin-arm64.md);
preserve other plugins' entries in shared configuration lists.

## Contribute

Start with the [developer documentation](docs/README.md) for the architecture,
development environment, contract ownership, testing, and release procedure.
