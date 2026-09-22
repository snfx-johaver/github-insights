"""Block releases until a functional implementation replaces Phase 1."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
LOCKFILE = ROOT / "frontend" / "package-lock.json"
RELEASE_MARKER = ROOT / "release-ready.json"
manifest = json.loads(
    (ROOT / "custom_components/github_insights/manifest.json").read_text(
        encoding="utf-8"
    )
)
frontend = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))

if manifest["version"] == "0.0.0" or frontend["version"] == "0.0.0":
    raise SystemExit("Release blocked: Phase 1 version 0.0.0 is documentation-only.")

if not LOCKFILE.is_file():
    raise SystemExit("Release blocked: frontend/package-lock.json is missing.")

if not RELEASE_MARKER.is_file():
    raise SystemExit("Release blocked: release-ready.json is missing.")

if manifest["version"] != frontend["version"]:
    raise SystemExit("Release blocked: backend and frontend versions differ.")

release_ready = json.loads(RELEASE_MARKER.read_text(encoding="utf-8"))
required_gates = {
    "hacs_validation": True,
    "hassfest_validation": True,
    "custom_repository_install_test": True,
}
if release_ready.get("version") != manifest["version"]:
    raise SystemExit("Release blocked: release-ready version does not match.")
for gate, required_value in required_gates.items():
    if release_ready.get(gate) is not required_value:
        raise SystemExit(f"Release blocked: {gate} has not been confirmed.")

ref_name = __import__("os").environ.get("GITHUB_REF_NAME", "")
if ref_name.startswith("v") and ref_name[1:] != manifest["version"]:
    raise SystemExit("Release blocked: Git tag and manifest version differ.")
