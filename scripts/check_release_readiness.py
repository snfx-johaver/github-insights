"""Block releases until a functional implementation replaces Phase 1."""

from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).parents[1]
LOCKFILE = ROOT / "frontend" / "package-lock.json"
manifest = json.loads(
    (ROOT / "custom_components/github_insights/manifest.json").read_text(
        encoding="utf-8"
    )
)
frontend = json.loads(
    (ROOT / "frontend/package.json").read_text(encoding="utf-8")
)

if manifest["version"] == "0.0.0" or frontend["version"] == "0.0.0":
    raise SystemExit(
        "Release blocked: Phase 1 version 0.0.0 is documentation-only."
    )

if not LOCKFILE.is_file():
    raise SystemExit("Release blocked: frontend/package-lock.json is missing.")

if manifest["version"] != frontend["version"]:
    raise SystemExit("Release blocked: backend and frontend versions differ.")
