"""Verified release artifacts shared by every real-runtime qualification case."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ARTIFACTS = [
    (
        "v0.1.6",
        "ee1de77d3d4aa67cc1dcc6d7d1510024e4ce793c440b3f3d5c14debc1f424479",
        "AGENT_DISPATCH_QUALIFY_BINARY",
    ),
    (
        "v0.1.7",
        "c949e5c56929332cc102c228bfd9415fee0dbdd0b21c296ac136b9d114efbccf",
        "AGENT_DISPATCH_QUALIFY_BINARY_V017",
    ),
]


@pytest.fixture(params=ARTIFACTS, ids=[entry[0] for entry in ARTIFACTS])
def qualified_binary(request, tmp_path):
    version, expected_digest, variable = request.param
    source = os.environ.get(variable) or shutil.which("agent-dispatch")
    assert source, f"missing prerequisite: set {variable} to the {version} release executable"
    binary = tmp_path / "agent-dispatch"
    shutil.copy2(source, binary)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert digest == expected_digest, f"{version} release digest mismatch: {digest}"
    binary.chmod(0o755)
    probe = subprocess.run(
        [str(binary), "version", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TMPDIR": str(tmp_path)},
        cwd=tmp_path,
    )
    assert probe.returncode == 0
    assert json.loads(probe.stdout) == {"name": "agent-dispatch", "version": version}
    return Path(binary)
