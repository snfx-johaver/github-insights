"""Metadata checks for the Phase 2 integration."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from scripts.validate_scaffold import canonical_text_sha256

ROOT = Path(__file__).parents[2]
INTEGRATION = ROOT / "custom_components" / "github_insights"


def test_manifest_declares_phase_two_config_flow() -> None:
    """The manifest exposes one config-entry integration."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())

    assert manifest["domain"] == "github_insights"
    assert manifest["version"] == "0.2.0-beta.1"
    assert manifest["config_flow"] is True
    assert manifest["single_config_entry"] is True


def test_backend_and_frontend_versions_match() -> None:
    """The single installation artifact uses one version."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    frontend = json.loads((ROOT / "frontend" / "package.json").read_text())
    frontend_lock = json.loads((ROOT / "frontend" / "package-lock.json").read_text())
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert frontend["version"] == manifest["version"]
    assert frontend_lock["version"] == manifest["version"]
    assert frontend_lock["packages"][""]["version"] == manifest["version"]
    assert pyproject["project"]["version"] == "0.2.0b1"


def test_dashboard_template_hash_is_line_ending_independent(tmp_path: Path) -> None:
    """The exact template check works in Linux and Windows checkouts."""
    lf_template = tmp_path / "lf.yaml"
    crlf_template = tmp_path / "crlf.yaml"
    lf_template.write_bytes(b"title: GitHub Insights\nviews: []\n")
    crlf_template.write_bytes(b"title: GitHub Insights\r\nviews: []\r\n")

    assert canonical_text_sha256(lf_template) == canonical_text_sha256(crlf_template)
