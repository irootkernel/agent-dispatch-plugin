"""Independent exact-provider oracle and compatibility corruption checks."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _oracle(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / "contracts/validate_v030.py")],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_v030_oracle_accepts_the_exact_contract():
    result = _oracle(ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "v0.3.0 contract validation passed" in result.stdout


@pytest.mark.parametrize(
    "mutation", ["digest", "source", "artifact", "group", "versions", "admission", "schema"]
)
def test_v030_oracle_rejects_contract_drift(tmp_path, mutation):
    shutil.copytree(ROOT / "contracts", tmp_path / "contracts")
    path = tmp_path / "contracts/v0.3.0/catalog.json"
    catalog = json.loads(path.read_text())
    if mutation == "digest":
        catalog["sync_provider"]["contract_digest"] = "sha256:" + "0" * 64
    elif mutation == "source":
        catalog["sync_providers"]["0.3.0"]["source_commit"] = "0" * 40
    elif mutation == "artifact":
        catalog["sync_providers"]["0.3.0"]["artifact_sha256"]["linux/amd64"] = "0" * 64
    elif mutation == "group":
        catalog["sync_provider"]["trusted_group_pattern"] = ".*"
    elif mutation == "versions":
        catalog["compatibility"]["sync_agent_dispatch"]["versions"].append("0.3.1")
    elif mutation == "admission":
        path = path.parent / "fixtures/admission.cases.json"
        catalog = json.loads(path.read_text())
        catalog["cases"][-1]["instance"]["expected_available"] = 13
    else:
        path = path.parent / "schemas/results/agent_dispatch_sync_status.result.json"
        catalog = json.loads(path.read_text())
        catalog["additionalProperties"] = True
    path.write_text(json.dumps(catalog))
    result = _oracle(tmp_path)
    assert result.returncode != 0, mutation
    assert "v0.3.0 contract validation FAILED" in result.stdout
    assert "Traceback" not in result.stderr
