"""Build the single HACS installation archive after release readiness passes."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "custom_components" / "github_insights"
DIST = ROOT / "dist"
STAGING = DIST / "github_insights"
FRONTEND_BUILD = SOURCE / "frontend" / "github-insights-cards.js"
ARCHIVE = DIST / "github_insights.zip"
FIXED_TIMESTAMP = (2024, 1, 1, 0, 0, 0)
IGNORED_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

if not FRONTEND_BUILD.is_file():
    raise SystemExit("Frontend production bundle is missing.")

if DIST.exists():
    shutil.rmtree(DIST)
shutil.copytree(
    SOURCE,
    STAGING,
    ignore=shutil.ignore_patterns(
        *IGNORED_NAMES,
        "*.pyc",
        "*.pyo",
        "*.map",
        "*.md",
    ),
)

runtime_files = sorted(path for path in STAGING.rglob("*") if path.is_file())
deployment_manifest = {
    "format": 1,
    "root": "custom_components/github_insights",
    "files": [
        {
            "path": path.relative_to(STAGING).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in runtime_files
    ],
}
(STAGING / "deployment-manifest.json").write_text(
    json.dumps(deployment_manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(STAGING.rglob("*")):
        if not path.is_file():
            continue
        relative = Path("github_insights") / path.relative_to(STAGING)
        info = zipfile.ZipInfo(relative.as_posix(), FIXED_TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, path.read_bytes())
