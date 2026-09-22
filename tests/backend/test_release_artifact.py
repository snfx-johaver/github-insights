"""Release artifact validation tests."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts import validate_release_artifact


def _write_archive(
    archive_path: Path,
    *,
    extra_files: dict[str, bytes] | None = None,
    manifest_root: str = "custom_components/github_insights",
) -> None:
    files = {
        "__init__.py": b"",
        "frontend/github-insights-cards.js": b"export {};",
        "manifest.json": b'{"domain":"github_insights"}',
    }
    manifest_files = [
        {
            "path": name,
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for name, content in sorted(files.items())
    ]
    manifest = {
        "format": 1,
        "root": manifest_root,
        "files": manifest_files,
    }
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, content in files.items():
            archive.writestr(f"github_insights/{name}", content)
        for name, content in (extra_files or {}).items():
            archive.writestr(name, content)
        archive.writestr(
            "github_insights/deployment-manifest.json",
            json.dumps(manifest).encode(),
        )


def test_accepts_exact_manifest_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_path = tmp_path / "github_insights.zip"
    _write_archive(archive_path)
    monkeypatch.setattr(validate_release_artifact, "ARCHIVE", archive_path)

    validate_release_artifact.main()


def test_rejects_unlisted_payload_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_path = tmp_path / "github_insights.zip"
    _write_archive(
        archive_path,
        extra_files={"github_insights/unlisted.json": b"{}"},
    )
    monkeypatch.setattr(validate_release_artifact, "ARCHIVE", archive_path)

    with pytest.raises(SystemExit, match="coverage mismatch"):
        validate_release_artifact.main()


def test_rejects_development_documentation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_path = tmp_path / "github_insights.zip"
    _write_archive(
        archive_path,
        extra_files={"github_insights/frontend/README.md": b"development notes"},
    )
    monkeypatch.setattr(validate_release_artifact, "ARCHIVE", archive_path)

    with pytest.raises(SystemExit, match="Development-only file"):
        validate_release_artifact.main()


def test_rejects_incorrect_install_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_path = tmp_path / "github_insights.zip"
    _write_archive(archive_path, manifest_root="custom_components/other")
    monkeypatch.setattr(validate_release_artifact, "ARCHIVE", archive_path)

    with pytest.raises(SystemExit, match="root is invalid"):
        validate_release_artifact.main()
