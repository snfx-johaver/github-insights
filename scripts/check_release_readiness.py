"""Block releases until a functional implementation replaces Phase 1."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
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

if manifest["version"] != frontend["version"]:
    raise SystemExit("Release blocked: backend and frontend versions differ.")

