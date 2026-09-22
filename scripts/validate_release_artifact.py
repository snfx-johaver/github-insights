"""Validate the single-installation release archive."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
ARCHIVE = ROOT / "dist" / "github_insights.zip"
PREFIX = "github_insights/"
FORBIDDEN_PARTS = {
    "__pycache__",
    "node_modules",
    "tests",
    "fixtures",
    "src",
}
FORBIDDEN_SUFFIXES = {".map", ".pyc", ".pyo", ".ts"}


def main() -> None:
    """Reject archives that violate HACS or payload invariants."""
    if not ARCHIVE.is_file():
        raise SystemExit("Release archive is missing.")

    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        if not names or any(not name.startswith(PREFIX) for name in names):
            raise SystemExit("Archive must contain one github_insights root.")
        if len(names) != len(set(names)):
            raise SystemExit("Archive contains duplicate paths.")
        for name in names:
            path = Path(name)
            if FORBIDDEN_PARTS.intersection(path.parts):
                raise SystemExit(f"Development-only path in archive: {name}")
            if path.suffix in FORBIDDEN_SUFFIXES:
                raise SystemExit(f"Development-only file in archive: {name}")

        required = {
            f"{PREFIX}manifest.json",
            f"{PREFIX}__init__.py",
            f"{PREFIX}frontend/github-insights-cards.js",
            f"{PREFIX}deployment-manifest.json",
        }
        missing = required.difference(names)
        if missing:
            raise SystemExit(f"Archive is missing: {sorted(missing)}")

        manifest = json.loads(archive.read(f"{PREFIX}deployment-manifest.json"))
        for item in manifest["files"]:
            name = f"{PREFIX}{item['path']}"
            digest = hashlib.sha256(archive.read(name)).hexdigest()
            if digest != item["sha256"]:
                raise SystemExit(f"Hash mismatch for {name}")


if __name__ == "__main__":
    main()
