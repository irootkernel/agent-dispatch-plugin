"""Verified release artifacts shared by real-runtime qualification cases.

The fixture is host-selected and fail-closed: Darwin arm64 runs v0.1.6 and
v0.1.7; Linux arm64 and amd64 run v0.1.8. Every host also runs v0.2.0.
An unsupported host, missing binary, or digest mismatch fails the stage.
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
        "v0.1.8",
        "3d06d4d35493ce51581bb8c61f4ffc3dfd700499863a492a337ab7fb762ddf8e",
        "AGENT_DISPATCH_QUALIFY_BINARY_V018",
    ),
]

LINUX_AMD64_ARTIFACTS = [
    (
        "v0.1.8",
        "ac844117af9cb10d5e7a18b5294336283e03e44bd8ab3c59aa500d0ad4b6ce7d",
        "AGENT_DISPATCH_QUALIFY_BINARY_V018",
    ),
]

V020_SHA256 = {
    "darwin/arm64": "aa7ebe7af91a68f7a5a3137de9cd5ab5bbdcff4e8aa4502fc03f13f0d4636889",
    "linux/amd64": "59216c7ec8aee4abb9e00377a81686156b08a3235275afcde5b6ec28363bb8d6",
    "linux/arm64": "d760586c7db77023b462c940cc8f4904caff5d54b0e767ef29a2e1cf83f85ac8",
}
V020_SOURCE_COMMIT = "6b1c78b19f4cdb69dfd070ea016430f03075b73d"


def _check_v020_catalog_pins() -> None:
    catalog = json.loads(
        (Path(__file__).resolve().parents[2] / "contracts/v0.2.0/catalog.json").read_text(
            encoding="utf-8"
        )
    )
    provider = catalog["sync_provider"]
    assert provider["source_commit"] == V020_SOURCE_COMMIT
    assert provider["artifact_sha256"] == V020_SHA256


def qualification_host() -> str:
    """Return the catalog platform key; identical to the runner trust gate."""
    return runner._host_platform()


def artifacts_for_this_host() -> list[tuple[str, str, str]]:
    host = qualification_host()
    if host == "darwin/arm64":
        return DARWIN_ARM64_ARTIFACTS
    if host == "linux/arm64":
        return LINUX_ARM64_ARTIFACTS
    if host == "linux/amd64":
        return LINUX_AMD64_ARTIFACTS
    raise AssertionError(
        "missing prerequisite: the qualification matrix targets darwin/arm64, "
        f"linux/amd64, or linux/arm64 hosts, got {host}"
    )


ARTIFACTS = artifacts_for_this_host() + [
    ("v0.2.0", V020_SHA256[qualification_host()], "AGENT_DISPATCH_QUALIFY_BINARY_V020")
]


def require_qualification_prerequisites() -> tuple[str, Path]:
    """Fail with the exact missing prerequisite; this stage never skips."""
    host = qualification_host()
    assert host in ("darwin/arm64", "linux/amd64", "linux/arm64"), (
        "missing prerequisite: the qualification matrix targets darwin/arm64, "
        f"linux/amd64, or linux/arm64 hosts, got {host}"
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


def _copy_verified_binary(tmp_path, version, expected_digest, variable):
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


@pytest.fixture(params=ARTIFACTS, ids=[entry[0] for entry in ARTIFACTS])
def qualified_binary(request, tmp_path):
    if request.param[0] == "v0.2.0":
        _check_v020_catalog_pins()
    return _copy_verified_binary(tmp_path, *request.param)


@pytest.fixture
def v020_binary(tmp_path):
    _check_v020_catalog_pins()
    return _copy_verified_binary(
        tmp_path,
        "v0.2.0",
        V020_SHA256[qualification_host()],
        "AGENT_DISPATCH_QUALIFY_BINARY_V020",
    )
