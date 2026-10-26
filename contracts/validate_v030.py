#!/usr/bin/env python3
"""Offline oracle for the approved v0.3.0 multi-provider inspection contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent
V030 = ROOT / "v0.3.0"
V010 = ROOT / "v0.1.0"
NEW_TOOLS = (
    "agent_dispatch_sync_capabilities",
    "agent_dispatch_sync_status",
    "agent_dispatch_sync_service_inspect",
)
COMMANDS = (
    ("sync", "capabilities"),
    ("sync", "status"),
    ("sync", "service", "inspect"),
)
DIGEST = "sha256:30cf47b1bd854a0271aa9df3e7b37f0cc14cdd86d3f06a65a2cb787c6741131b"
LEGACY_ARTIFACTS = {
    "darwin/arm64": "7f9e68f7033ed7750f1d6912d510f617d2a06fd58f5f18400b73d68280604508",
    "linux/amd64": "a749ad083c2028af3b0d500c95d448f5a90af80c5c6e9a70fe950b011393efb2",
    "linux/arm64": "9ca8f030b7763f05c229c5792836ea86ad3f2a8cc97912e47dda8f8a687d2cec",
}
ARTIFACTS = {
    "darwin/arm64": "9b359d715f6a039199d0046755f6b27f3c195c8b024262a085f8df3697a6ab9c",
    "linux/arm64": "779b887596428a2d35ca040b7fcbf33fb7733b55902c0e210c9bd9713bb29804",
}
EXPECTED_PLUGIN_VERSION = "0.3.0"
IDENTITY_PATHS = [
    "sync capabilities.result.contract_digest",
    "sync status.result.config_revision",
    "sync status.result.latest_publication.target_commit",
    "sync status.result.latest_delivery.target_commit",
    "sync status.result.latest_import.target_commit",
    "sync status.result.latest_verification.target_commit",
]


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> None:
    catalog = read(V030 / "catalog.json")
    old = read(V010 / "catalog.json")
    old_names = [tool["name"] for tool in old["tools"]]
    tools = catalog["tools"]
    require(catalog["product_version"] == "0.3.0", "product_version")
    require(catalog["plugin"]["version"] == EXPECTED_PLUGIN_VERSION, "plugin.version")
    require([tool["name"] for tool in tools] == old_names + list(NEW_TOOLS), "tool roster")
    require(
        tools[: len(old_names)] == old["tools"], "frozen ten-tool descriptions or mappings changed"
    )
    require(
        catalog["compatibility"]["agent_dispatch"] == old["compatibility"]["agent_dispatch"],
        "legacy version range",
    )
    require(
        catalog["compatibility"]["sync_agent_dispatch"]
        == {
            "versions": ["0.2.0", "0.3.0"],
            "operator_digest_required": True,
            "platform_sha_allowlist_required": True,
            "scope": "exact reviewed version/platform artifacts only; no later build is admitted automatically",
        },
        "sync provider version pin",
    )
    provider = catalog["sync_provider"]
    require(provider["contract_digest"] == DIGEST, "provider digest")
    providers = catalog["sync_providers"]
    legacy = read(ROOT / "v0.2.0/catalog.json")["sync_provider"]
    require(set(providers) == {"0.2.0", "0.3.0"}, "exact provider versions")
    identity_keys = (
        "source_commit",
        "provider_bundle_commit",
        "bundle_path",
        "release_checksum_file_sha256",
        "artifact_sha256",
    )
    require(
        providers["0.2.0"] == {key: legacy[key] for key in identity_keys},
        "legacy provider identity",
    )
    require(providers["0.2.0"]["artifact_sha256"] == LEGACY_ARTIFACTS, "legacy platform pins")
    require(
        providers["0.3.0"]
        == {
            "source_commit": "4b1e5dcaa9c2c6bb4b043448c9ee0d9d2ed00b4f",
            "provider_bundle_commit": "4b1e5dcaa9c2c6bb4b043448c9ee0d9d2ed00b4f",
            "bundle_path": "docs/contracts/sync-provider-v1/",
            "release_checksum_file_sha256": "sha256:161846e74de9bc2aedc07674477ab306e794f00bcade26f3539647061e6f29c8",
            "artifact_sha256": ARTIFACTS,
        },
        "published v0.3.0 provider identity",
    )
    old_sync = read(ROOT / "v0.2.0/catalog.json")
    require(tools == old_sync["tools"], "thirteen fixed tools changed")
    for path in (ROOT / "v0.2.0/schemas").rglob("*.json"):
        relative = path.relative_to(ROOT / "v0.2.0")
        expected = path.read_text(encoding="utf-8").replace(
            "contracts:v0.2.0:", "contracts:v0.3.0:"
        )
        require(read(V030 / relative) == json.loads(expected), f"schema changed: {relative}")
    require(provider["trusted_group_pattern"] == "^[a-z][a-z0-9-]{0,62}$", "group grammar")
    require(
        provider["required_capabilities"] == ["contract_read", "status_read", "service_inspect"],
        "required capabilities",
    )
    require(provider["public_identity_paths"] == IDENTITY_PATHS, "public identity paths")
    require(
        catalog["plugin"]["config_schema"]["sync_group_id"]["required"] is False,
        "trusted group setting",
    )
    require(
        catalog["wrapper"]["schema_version"] == old["wrapper"]["schema_version"], "wrapper version"
    )
    require(catalog["errors"] == old["errors"], "closed errors changed")
    require(catalog["limits"] == old["limits"], "resource limits changed")
    require(catalog["diagnostics_bounds"] == old["diagnostics_bounds"], "diagnostics changed")
    allowed = dict(old["command_vocabulary"]["allowed"])
    allowed["sync"] = ["capabilities", "status", "service inspect"]
    require(catalog["command_vocabulary"]["allowed"] == allowed, "command vocabulary")
    denied = [
        token
        for token in old["command_vocabulary"]["denied_subcommands"]
        if token != "capabilities"
    ]
    require(
        catalog["command_vocabulary"]["denied_subcommands"] == denied,
        "denied subcommands",
    )
    wrapper_schema = read(V030 / catalog["wrapper"]["schema"])
    require(
        wrapper_schema["properties"]["operation"]["enum"] == old_names + list(NEW_TOOLS),
        "wrapper operation roster",
    )
    require(wrapper_schema["additionalProperties"] is False, "wrapper open boundary")
    require(catalog["wrapper"]["members"] == old["wrapper"]["members"], "wrapper members")
    cap_schema = read(V030 / tools[-3]["result_schema"])
    status_schema = read(V030 / tools[-2]["result_schema"])
    require(
        cap_schema["properties"]["contract_digest"] == {"const": DIGEST},
        "public contract digest format",
    )
    require(
        status_schema["properties"]["config_revision"]["anyOf"]
        == [
            {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            {"const": ""},
        ],
        "public config revision format",
    )
    for key in ("latest_publication", "latest_delivery", "latest_import", "latest_verification"):
        require(
            status_schema["properties"][key]["properties"]["target_commit"]
            == {"type": "string", "pattern": "^(?:[0-9a-f]{40}|[0-9a-f]{64})$"},
            f"public {key} target format",
        )

    for tool, command in zip(tools[-3:], COMMANDS, strict=True):
        name = tool["name"]
        input_schema = read(V030 / tool["input_schema"])
        require(
            input_schema["type"] == "object" and input_schema["properties"] == {},
            f"{name}: nonempty input",
        )
        require(input_schema["additionalProperties"] is False, f"{name}: open input")
        require(len(tool["actions"]) == 1, f"{name}: action count")
        action = tool["actions"][0]
        require(tuple(action["argv_prefix"]) == command, f"{name}: command")
        require(action["expected_command"] == " ".join(command), f"{name}: command identity")
        require(action["argv_suffix"] == ["--output", "json"], f"{name}: suffix")
        require(
            not action["value_bindings"] and not action["optional_flags"], f"{name}: model bindings"
        )
        if name.endswith("capabilities"):
            require(action["trusted_value_bindings"] == [], "capabilities trusted binding")
            require(action["append_trusted_config"] is False, "capabilities config flag")
        else:
            require(
                action["trusted_value_bindings"]
                == [{"setting": "sync_group_id", "flag": "--group"}],
                f"{name}: group binding",
            )
            require(action["append_trusted_config"] is True, f"{name}: config flag")
        schema = read(V030 / tool["result_schema"])
        require(schema["additionalProperties"] is False, f"{name}: open result")
        require(
            schema["properties"]["side_effects"] == {"type": "array", "maxItems": 0},
            f"{name}: effects",
        )

    registry = Registry()
    for path in (V030 / "schemas").rglob("*.json"):
        schema = read(path)
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    index = read(V030 / "fixtures/catalog.json")
    listed = set()
    for subject in index["subjects"]:
        schema_path = V030 / subject["schema"]
        fixture_path = V030 / subject["cases"]
        listed.add(fixture_path)
        schema = read(schema_path)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, registry=registry)
        cases = read(fixture_path)["cases"]
        require(any(c["expect"] == "valid" for c in cases), f"{fixture_path}: no valid case")
        require(any(c["expect"] == "invalid" for c in cases), f"{fixture_path}: no invalid case")
        for case in cases:
            errors = list(validator.iter_errors(case["instance"]))
            require(
                bool(errors) == (case["expect"] == "invalid"),
                f"{fixture_path}:{case['id']} expectation",
            )
    actual = set((V030 / "fixtures").rglob("*.json")) - {
        V030 / "fixtures/catalog.json",
        V030 / "fixtures/admission.cases.json",
        V030 / "fixtures/command.cases.json",
    }
    require(actual == listed, "orphan or missing fixture")

    capability_schema = read(V030 / tools[-3]["result_schema"])
    for case in read(V030 / "fixtures/admission.cases.json")["cases"]:
        item = case["instance"]
        version = item["version"]
        host = item["platform"]
        trusted = item["operator_sha256"] == item["binary_sha256"]
        if not trusted or host not in LEGACY_ARTIFACTS:
            count = 0
        elif re.fullmatch(r"0\.1\.(?:[6-9]|[1-9][0-9]+)", version):
            count = 10
        elif version in providers and item["binary_sha256"] == providers[version][
            "artifact_sha256"
        ].get(host):
            probe = item["capability_result"]
            group = item["sync_group_id"]
            capable = not list(Draft202012Validator(capability_schema).iter_errors(probe))
            if capable:
                capable = all(
                    probe["capabilities"][key] is True for key in provider["required_capabilities"]
                )
            count = 13 if re.fullmatch(provider["trusted_group_pattern"], group) and capable else 10
        else:
            count = 0
        require(count == item["expected_available"], f"admission:{case['id']}")

    declared_commands = {action["expected_command"] for tool in tools for action in tool["actions"]}
    for case in read(V030 / "fixtures/command.cases.json")["cases"]:
        item = case["instance"]
        same = (
            item["expected_command"] in declared_commands
            and item["envelope_command"] == item["expected_command"]
        )
        require(same is item["expected_match"], f"command:{case['id']}")


if __name__ == "__main__":
    try:
        validate()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"v0.3.0 contract validation FAILED: {exc}")
        raise SystemExit(1) from None
    print("v0.3.0 contract validation passed")
