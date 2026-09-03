"""Integration tests: the contract oracle's failure paths stay bounded.

Every corruption that the gate must catch is exercised in a disposable copy
of the repository: the gate must exit non-zero, print its bounded failure
report, and never emit a traceback. These tests guard the gate fixes made
during the EPIC-001 audit against regression.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
IGNORE = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".mulgae", ".zcode", ".podway")


def _set_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def corrupt_dead_enum(work: Path) -> None:
    _set_json(
        work / "contracts/v0.1.0/catalog.json",
        lambda d: d["closed_enums"].__setitem__("routes.deprecated", ["x"]),
    )


def corrupt_diverged_enum(work: Path) -> None:
    _set_json(
        work / "contracts/v0.1.0/catalog.json",
        lambda d: d["closed_enums"].__setitem__("receipts.kind", ["acceptance", "work"]),
    )


def corrupt_unreadable_error_fixtures(work: Path) -> None:
    (work / "contracts/v0.1.0/fixtures/error.cases.json").write_text("{broken", encoding="utf-8")


def corrupt_unreadable_tool_schema(work: Path) -> None:
    (work / "contracts/v0.1.0/schemas/tools/agent_dispatch_routes.input.json").write_text(
        "{broken", encoding="utf-8"
    )


def corrupt_unreadable_catalog(work: Path) -> None:
    (work / "contracts/v0.1.0/catalog.json").write_text("{ not json", encoding="utf-8")


def corrupt_missing_catalog_section(work: Path) -> None:
    _set_json(
        work / "contracts/v0.1.0/catalog.json",
        lambda d: d.pop("pagination"),
    )


def corrupt_missing_tools_section(work: Path) -> None:
    _set_json(
        work / "contracts/v0.1.0/catalog.json",
        lambda d: d.pop("tools"),
    )


def corrupt_action_without_bindings(work: Path) -> None:
    def drop_bindings(catalog):
        for tool in catalog["tools"]:
            if tool["name"] == "agent_dispatch_dispatches":
                for action in tool["actions"]:
                    if action["id"] == "list":
                        action.pop("value_bindings", None)

    _set_json(work / "contracts/v0.1.0/catalog.json", drop_bindings)


def corrupt_fixture_without_cases(work: Path) -> None:
    (work / "contracts/v0.1.0/fixtures/error.cases.json").write_text(
        '{"schema_version": "agent-dispatch-plugin.fixtures/v1"}', encoding="utf-8"
    )


def corrupt_stale_anchor(work: Path) -> None:
    schema = work / "contracts/v0.1.0/schemas/tools/agent_dispatch_routes.input.json"
    schema.write_text(
        schema.read_text(encoding="utf-8").replace("(?![\\\\s\\\\S])", "$"), encoding="utf-8"
    )


def corrupt_unregistered_enum(work: Path) -> None:
    _set_json(
        work / "contracts/v0.1.0/schemas/tools/agent_dispatch_status.input.json",
        lambda d: d["properties"].__setitem__("mode", {"enum": ["a", "b"]}),
    )


@pytest.mark.parametrize(
    ("corruption", "label"),
    [
        (corrupt_dead_enum, "dead closed_enums entry"),
        (corrupt_diverged_enum, "diverged closed_enums entry"),
        (corrupt_unreadable_error_fixtures, "unreadable error fixtures"),
        (corrupt_unreadable_tool_schema, "unreadable tool schema"),
        (corrupt_unreadable_catalog, "unreadable catalog"),
        (corrupt_missing_catalog_section, "missing catalog section"),
        (corrupt_missing_tools_section, "missing tools section"),
        (corrupt_action_without_bindings, "action without value bindings"),
        (corrupt_fixture_without_cases, "fixture document without cases"),
        (corrupt_stale_anchor, "stale grammar anchor"),
        (corrupt_unregistered_enum, "unregistered schema enum"),
    ],
)
def test_gate_reports_corruptions_boundedly(corruption, label):
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "repo"
        shutil.copytree(ROOT, work, ignore=IGNORE)
        corruption(work)
        result = subprocess.run(
            ["uv", "run", "--project", str(work), "contracts/validate.py"],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode != 0, label
        assert "contracts validation FAILED" in result.stdout, label
        assert "Traceback" not in result.stderr, label


def corrupt_parity_unparseable_manifest(work: Path) -> None:
    (work / "plugin.yaml").write_text("name: [unclosed", encoding="utf-8")


def corrupt_parity_drifted_manifest(work: Path) -> None:
    manifest = work / "plugin.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("version: 0.1.0", "version: 9.9.9"),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("corruption", "label"),
    [
        (corrupt_parity_unparseable_manifest, "unparseable plugin.yaml"),
        (corrupt_parity_drifted_manifest, "drifted plugin.yaml"),
    ],
)
def test_parity_gate_reports_corruptions_boundedly(corruption, label):
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "repo"
        shutil.copytree(ROOT, work, ignore=IGNORE)
        corruption(work)
        result = subprocess.run(
            ["uv", "run", "--project", str(work), "scripts/manifest_parity.py"],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode != 0, label
        assert "parity" in result.stdout.lower(), label
        assert "Traceback" not in result.stderr, label
