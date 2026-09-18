"""Metadata checks for the Phase 2 integration."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
INTEGRATION = ROOT / "custom_components" / "github_insights"


def test_manifest_declares_phase_two_config_flow() -> None:
    """The manifest exposes one config-entry integration."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())

    assert manifest["domain"] == "github_insights"
    assert manifest["version"] == "0.1.0-beta.1"
    assert manifest["config_flow"] is True
    assert manifest["single_config_entry"] is True


def test_backend_and_frontend_versions_match() -> None:
    """The single installation artifact uses one version."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    frontend = json.loads((ROOT / "frontend" / "package.json").read_text())

    assert frontend["version"] == manifest["version"]
