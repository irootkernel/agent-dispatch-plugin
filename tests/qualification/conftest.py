"""Verified release artifacts shared by every real-runtime qualification case.

The fixture is host-selected and fail-closed: Darwin arm64 runs both pinned
Darwin artifacts; linux/arm64 runs the pinned v0.1.7 linux-arm64 artifact.
Any other host, a missing binary, or a digest mismatch fails the stage.
There is no skip path.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

import runner

MINIMUM_HERMES_VERSION = (0, 20, 5)

DARWIN_ARM64_ARTIFACTS = [
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

LINUX_ARM64_ARTIFACTS = [
    (
        "v0.1.7",
        "5493b1a13d28fa28eee850617be7c745d47898b87a7c3c4ea114f5c1cf2481c0",
        "AGENT_DISPATCH_QUALIFY_BINARY_V017",
    ),
]


def qualification_host() -> str:
    """Return the catalog platform key; identical to the runner trust gate."""
    return runner._host_platform()


def artifacts_for_this_host() -> list[tuple[str, str, str]]:
    host = qualification_host()
    if host == "darwin/arm64":
        return DARWIN_ARM64_ARTIFACTS
    if host == "linux/arm64":
        return LINUX_ARM64_ARTIFACTS
    raise AssertionError(
        "missing prerequisite: the qualification matrix targets darwin/arm64 or "
        f"linux/arm64 hosts, got {host}"
    )


ARTIFACTS = artifacts_for_this_host()


def require_qualification_prerequisites() -> tuple[str, Path]:
    """Fail with the exact missing prerequisite; this stage never skips."""
    host = qualification_host()
    assert host in ("darwin/arm64", "linux/arm64"), (
        "missing prerequisite: the qualification matrix targets darwin/arm64 or "
        f"linux/arm64 hosts, got {host}"
    )
    hermes = shutil.which("hermes")
    assert hermes is not None, (
        "missing prerequisite: the Hermes Agent CLI (v0.20.5 or newer) must be on PATH "
        "for qualification"
    )
    version_output = subprocess.run(
        [hermes, "--version"], capture_output=True, text=True, timeout=30
    ).stdout
    first_line = version_output.splitlines()[0].strip() if version_output else ""
    # v0.21.0+ appends upstream/local commit trailers after the build date,
    # so the identity check anchors the prefix rather than the whole line.
    version_match = re.match(r"Hermes Agent v(\d+)\.(\d+)\.(\d+) \(\d{4}\.\d+\.\d+\)", first_line)
    assert version_match, (
        f"missing prerequisite: unrecognized hermes --version line, got "
        f"{version_output.splitlines()[:1]}"
    )
    hermes_version = tuple(int(part) for part in version_match.groups())
    assert hermes_version >= MINIMUM_HERMES_VERSION, (
        f"missing prerequisite: Hermes must be v0.20.5 or newer, got "
        f"v{'.'.join(str(part) for part in hermes_version)}"
    )
    install_dir = None
    for line in version_output.splitlines():
        if line.startswith("Install directory:"):
            install_dir = line.split(":", 1)[1].strip()
    assert install_dir, "missing prerequisite: hermes --version names no install directory"
    venv_python = Path(install_dir) / "venv" / "bin" / "python"
    assert venv_python.is_file(), (
        f"missing prerequisite: the Hermes venv interpreter is expected at {venv_python}"
    )
    return hermes, venv_python


@pytest.fixture
def qualification_runtime():
    return require_qualification_prerequisites()


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
