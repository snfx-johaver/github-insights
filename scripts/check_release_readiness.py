"""Validate fail-closed pre-release and stable release evidence."""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
LOCKFILE = ROOT / "frontend" / "package-lock.json"
RELEASE_MARKER = ROOT / "release-ready.json"
POST_RELEASE_MARKER = ROOT / "post-release-validation.json"
MANIFEST = ROOT / "custom_components" / "github_insights" / "manifest.json"
FRONTEND_PACKAGE = ROOT / "frontend" / "package.json"
PYPROJECT = ROOT / "pyproject.toml"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

PRE_RELEASE_GATES = {
    "source_validation": True,
    "hacs_validation": True,
    "hassfest_validation": True,
    "artifact_validation": True,
    "secret_scan": True,
    "live_home_assistant_validation": True,
}
POST_RELEASE_GATES = {
    "custom_repository_install_test": True,
    "upgrade_test": True,
}


def _load_json(path: Path, description: str) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Release blocked: {description} is missing.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise SystemExit(f"Release blocked: {description} is invalid.") from err
    if not isinstance(value, dict):
        raise SystemExit(f"Release blocked: {description} must be an object.")
    return value


def _require_gates(evidence: dict[str, Any], gates: dict[str, bool]) -> None:
    for gate, required_value in gates.items():
        if evidence.get(gate) is not required_value:
            raise SystemExit(f"Release blocked: {gate} has not been confirmed.")


def _is_prerelease(version: str) -> bool:
    return "-" in version


def _pep440_version(version: str) -> str:
    markers = {"alpha": "a", "beta": "b", "rc": "rc"}
    return re.sub(
        r"-(alpha|beta|rc)\.",
        lambda match: markers[match.group(1)],
        version,
    )


def main() -> None:
    """Validate evidence appropriate for the version being published."""
    manifest = _load_json(MANIFEST, "integration manifest")
    frontend = _load_json(FRONTEND_PACKAGE, "frontend package")
    frontend_lock = _load_json(LOCKFILE, "frontend lockfile")
    if not PYPROJECT.is_file():
        raise SystemExit("Release blocked: pyproject.toml is missing.")
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = manifest.get("version")

    if not isinstance(version, str) or not version or version == "0.0.0":
        raise SystemExit("Release blocked: integration version is not releasable.")
    if frontend.get("version") != version:
        raise SystemExit("Release blocked: backend and frontend versions differ.")
    packages = frontend_lock.get("packages")
    lock_root = packages.get("") if isinstance(packages, dict) else None
    if (
        frontend_lock.get("version") != version
        or not isinstance(lock_root, dict)
        or lock_root.get("version") != version
    ):
        raise SystemExit("Release blocked: frontend lockfile version differs.")
    if pyproject.get("project", {}).get("version") != _pep440_version(version):
        raise SystemExit("Release blocked: Python project version differs.")

    release_ready = _load_json(RELEASE_MARKER, "release-ready.json")
    if release_ready.get("version") != version:
        raise SystemExit("Release blocked: release-ready version does not match.")
    _require_gates(release_ready, PRE_RELEASE_GATES)

    digest = release_ready.get("artifact_sha256")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise SystemExit("Release blocked: artifact SHA-256 evidence is invalid.")
    if not isinstance(release_ready.get("artifact_size_bytes"), int) or (
        release_ready["artifact_size_bytes"] <= 0
    ):
        raise SystemExit("Release blocked: artifact size evidence is invalid.")
    if not isinstance(release_ready.get("artifact_file_count"), int) or (
        release_ready["artifact_file_count"] <= 0
    ):
        raise SystemExit("Release blocked: artifact file-count evidence is invalid.")

    ref_name = os.environ.get("GITHUB_REF_NAME", "")
    if ref_name.startswith("v") and ref_name[1:] != version:
        raise SystemExit("Release blocked: Git tag and manifest version differ.")

    if _is_prerelease(version):
        if release_ready.get("custom_repository_install_test") is True:
            raise SystemExit(
                "Release blocked: pre-release evidence must not claim the "
                "post-release custom-repository install gate."
            )
        return

    post_release = _load_json(
        POST_RELEASE_MARKER,
        "post-release-validation.json required for stable publication",
    )
    _require_gates(post_release, POST_RELEASE_GATES)
    validated_version = post_release.get("validated_prerelease_version")
    if not isinstance(validated_version, str) or not _is_prerelease(validated_version):
        raise SystemExit(
            "Release blocked: stable publication requires a validated prerelease."
        )
    validated_digest = post_release.get("artifact_sha256")
    if not isinstance(validated_digest, str) or not SHA256_PATTERN.fullmatch(
        validated_digest
    ):
        raise SystemExit(
            "Release blocked: post-release artifact SHA-256 evidence is invalid."
        )


if __name__ == "__main__":
    main()
