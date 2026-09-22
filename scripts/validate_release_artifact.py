"""Validate the single-installation release archive."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).parents[1]
ARCHIVE = ROOT / "dist" / "github_insights.zip"
PREFIX = "github_insights/"
DEPLOYMENT_MANIFEST = f"{PREFIX}deployment-manifest.json"
FORBIDDEN_PARTS = {
    "__pycache__",
    "node_modules",
    "tests",
    "fixtures",
    "src",
}
FORBIDDEN_SUFFIXES = {".map", ".md", ".pyc", ".pyo", ".ts"}


def _validated_member_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (
        "\\" in name
        or not name.startswith(PREFIX)
        or name != path.as_posix()
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise SystemExit(f"Unsafe archive path: {name}")
    return path


def _load_deployment_manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    try:
        manifest = json.loads(archive.read(DEPLOYMENT_MANIFEST))
    except (KeyError, json.JSONDecodeError) as err:
        raise SystemExit("Deployment manifest is missing or invalid.") from err
    if not isinstance(manifest, dict):
        raise SystemExit("Deployment manifest must be a JSON object.")
    if manifest.get("format") != 1:
        raise SystemExit("Deployment manifest format must be 1.")
    if manifest.get("root") != "custom_components/github_insights":
        raise SystemExit("Deployment manifest root is invalid.")
    if not isinstance(manifest.get("files"), list):
        raise SystemExit("Deployment manifest files must be a list.")
    return manifest


def main() -> None:
    """Reject archives that violate HACS or payload invariants."""
    if not ARCHIVE.is_file():
        raise SystemExit("Release archive is missing.")

    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        if not names:
            raise SystemExit("Archive must contain one github_insights root.")
        if len(names) != len(set(names)):
            raise SystemExit("Archive contains duplicate paths.")
        for name in names:
            path = _validated_member_path(name)
            lowered_parts = {part.lower() for part in path.parts}
            if FORBIDDEN_PARTS.intersection(lowered_parts):
                raise SystemExit(f"Development-only path in archive: {name}")
            if path.suffix.lower() in FORBIDDEN_SUFFIXES:
                raise SystemExit(f"Development-only file in archive: {name}")

        required = {
            f"{PREFIX}manifest.json",
            f"{PREFIX}__init__.py",
            f"{PREFIX}frontend/github-insights-cards.js",
            DEPLOYMENT_MANIFEST,
        }
        missing = required.difference(names)
        if missing:
            raise SystemExit(f"Archive is missing: {sorted(missing)}")

        manifest = _load_deployment_manifest(archive)
        listed_names: set[str] = set()
        for item in manifest["files"]:
            if not isinstance(item, dict):
                raise SystemExit("Deployment manifest file entries must be objects.")
            relative_name = item.get("path")
            expected_digest = item.get("sha256")
            if not isinstance(relative_name, str) or not isinstance(
                expected_digest, str
            ):
                raise SystemExit("Deployment manifest file entry is invalid.")
            relative_path = PurePosixPath(relative_name)
            if (
                "\\" in relative_name
                or relative_name != relative_path.as_posix()
                or relative_path.is_absolute()
                or any(part in {"", ".", ".."} for part in relative_path.parts)
            ):
                raise SystemExit(f"Unsafe deployment manifest path: {relative_name}")
            name = f"{PREFIX}{item['path']}"
            if name in listed_names:
                raise SystemExit(f"Duplicate deployment manifest path: {name}")
            listed_names.add(name)
            try:
                content = archive.read(name)
            except KeyError as err:
                raise SystemExit(f"Manifest-listed file is missing: {name}") from err
            digest = hashlib.sha256(content).hexdigest()
            if digest != expected_digest:
                raise SystemExit(f"Hash mismatch for {name}")

        archived_payload = set(names).difference({DEPLOYMENT_MANIFEST})
        if listed_names != archived_payload:
            missing_from_manifest = sorted(archived_payload.difference(listed_names))
            missing_from_archive = sorted(listed_names.difference(archived_payload))
            raise SystemExit(
                "Deployment manifest coverage mismatch: "
                f"unlisted={missing_from_manifest}, missing={missing_from_archive}"
            )


if __name__ == "__main__":
    main()
