"""Validate the intentionally nonfunctional Phase 1 scaffold."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
INTEGRATION = ROOT / "custom_components" / "github_insights"


def test_manifest_is_explicitly_unreleased() -> None:
    """The placeholder must not be mistaken for a functional release."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())

    assert manifest["domain"] == "github_insights"
    assert manifest["version"] == "0.0.0"
    assert "config_flow" not in manifest


def test_hacs_uses_one_integration_zip() -> None:
    """HACS must install one integration artifact, never a second plugin."""
    hacs = json.loads((ROOT / "hacs.json").read_text())

    assert hacs["zip_release"] is True
    assert hacs["filename"] == "github_insights.zip"
    assert hacs["hide_default_branch"] is True
