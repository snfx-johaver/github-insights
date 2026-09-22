"""Tests for two-stage release readiness evidence."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts import check_release_readiness

SHA256 = "a" * 64


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _configure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    version: str = "0.2.0-beta.1",
    evidence: dict[str, object] | None = None,
) -> None:
    manifest = tmp_path / "manifest.json"
    frontend = tmp_path / "package.json"
    lockfile = tmp_path / "package-lock.json"
    pyproject = tmp_path / "pyproject.toml"
    marker = tmp_path / "release-ready.json"
    post_marker = tmp_path / "post-release-validation.json"
    archive = tmp_path / "github_insights.zip"
    _write_json(manifest, {"version": version})
    _write_json(frontend, {"version": version})
    _write_json(lockfile, {"version": version, "packages": {"": {"version": version}}})
    pyproject.write_text(
        f'[project]\nversion = "{check_release_readiness._pep440_version(version)}"\n',
        encoding="utf-8",
    )
    with zipfile.ZipFile(archive, "w") as release_archive:
        release_archive.writestr("github_insights/manifest.json", "{}")
        release_archive.writestr("github_insights/deployment-manifest.json", "{}")
    archive_bytes = archive.read_bytes()
    artifact = {
        "artifact_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "artifact_size_bytes": len(archive_bytes),
        "artifact_file_count": 2,
    }
    _write_json(
        marker,
        evidence
        or {
            "version": version,
            **check_release_readiness.PRE_RELEASE_GATES,
            **artifact,
            "custom_repository_install_test": False,
        },
    )
    monkeypatch.setattr(check_release_readiness, "MANIFEST", manifest)
    monkeypatch.setattr(check_release_readiness, "FRONTEND_PACKAGE", frontend)
    monkeypatch.setattr(check_release_readiness, "LOCKFILE", lockfile)
    monkeypatch.setattr(check_release_readiness, "PYPROJECT", pyproject)
    monkeypatch.setattr(check_release_readiness, "ARCHIVE", archive)
    monkeypatch.setattr(check_release_readiness, "RELEASE_MARKER", marker)
    monkeypatch.setattr(check_release_readiness, "POST_RELEASE_MARKER", post_marker)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)


def test_prerelease_accepts_truthful_pre_release_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(tmp_path, monkeypatch)

    check_release_readiness.main()


def test_prerelease_rejects_false_custom_install_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(tmp_path, monkeypatch)
    evidence = json.loads(check_release_readiness.RELEASE_MARKER.read_text())
    evidence["custom_repository_install_test"] = True
    _write_json(check_release_readiness.RELEASE_MARKER, evidence)

    with pytest.raises(SystemExit, match="must not claim"):
        check_release_readiness.main()


def test_prerelease_rejects_missing_live_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(tmp_path, monkeypatch)
    evidence = json.loads(check_release_readiness.RELEASE_MARKER.read_text())
    evidence["live_home_assistant_validation"] = False
    _write_json(check_release_readiness.RELEASE_MARKER, evidence)

    with pytest.raises(SystemExit, match="live_home_assistant_validation"):
        check_release_readiness.main()


def test_stable_release_requires_post_release_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(tmp_path, monkeypatch, version="0.2.0")

    with pytest.raises(SystemExit, match="post-release-validation.json"):
        check_release_readiness.main()


def test_stable_release_accepts_validated_prerelease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(tmp_path, monkeypatch, version="0.2.0")
    _write_json(
        check_release_readiness.POST_RELEASE_MARKER,
        {
            "validated_prerelease_version": "0.2.0-beta.1",
            "artifact_sha256": SHA256,
            **check_release_readiness.POST_RELEASE_GATES,
        },
    )

    check_release_readiness.main()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("artifact_sha256", SHA256, "SHA-256 differs"),
        ("artifact_size_bytes", 1, "size differs"),
        ("artifact_file_count", 1, "file count differs"),
    ],
)
def test_release_rejects_artifact_evidence_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    _configure(tmp_path, monkeypatch)
    evidence = json.loads(check_release_readiness.RELEASE_MARKER.read_text())
    evidence[field] = value
    _write_json(check_release_readiness.RELEASE_MARKER, evidence)

    with pytest.raises(SystemExit, match=message):
        check_release_readiness.main()
