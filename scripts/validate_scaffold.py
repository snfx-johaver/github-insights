"""Validate repository structure and single-artifact invariants."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOMAIN = "github_insights"
INTEGRATION = ROOT / "custom_components" / DOMAIN
REQUIRED_DOCS = {
    "api-matrix.md",
    "architecture.md",
    "card-specifications.md",
    "data-availability.md",
    "deployment.md",
    "design-research.md",
    "hacs-publication.md",
    "implementation-plan.md",
    "permissions.md",
    "release-process.md",
}
REQUIRED_MODULES = {
    "__init__.py",
    "api.py",
    "binary_sensor.py",
    "button.py",
    "config_flow.py",
    "const.py",
    "coordinator.py",
    "diagnostics.py",
    "entity.py",
    "models.py",
    "number.py",
    "repairs.py",
    "select.py",
    "sensor.py",
    "switch.py",
}
REQUIRED_CARDS = {
    "github-insights-overview",
    "github-insights-usage",
    "github-insights-repositories",
    "github-insights-repository",
    "github-insights-actions",
    "github-insights-copilot",
    "github-insights-activity",
    "github-insights-contributions",
    "github-insights-security",
    "github-insights-compact",
    "github-insights-dashboard",
}
BUNDLED_CARD_PATTERN = re.compile(r"type:\s*custom:github-insights-[\w-]+")
BUNDLED_RESOURCE_URL = "/github_insights/frontend/github-insights-cards.js"
DASHBOARD = ROOT / "docs" / "release-candidate-dashboard.yaml"
DASHBOARD_SHA256 = "97fc8f3208cfbfa29731c656333afdb2237fadafb67c896eb61eec867be690d5"
RESOURCE_CONFIG = ROOT / "docs" / "release-candidate-lovelace-resources.yaml"
RESOURCE_EVIDENCE = ROOT / "release-ready.json"
DYNAMIC_DASHBOARD_FILTERS = {
    f"{domain}.github_insights_*"
    for domain in ("sensor", "binary_sensor", "number", "select", "switch", "button")
}


def load_json(path: Path) -> dict[str, object]:
    """Load a JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def pep440_version(version: str) -> str:
    """Convert the supported semantic prerelease spelling to PEP 440."""
    markers = {"alpha": "a", "beta": "b", "rc": "rc"}
    return re.sub(
        r"-(alpha|beta|rc)\.",
        lambda match: markers[match.group(1)],
        version,
    )


def canonical_text_sha256(path: Path) -> str:
    """Hash text consistently across LF and CRLF checkouts."""
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def has_bundled_resource_registration() -> bool:
    """Return whether supported resource configuration or evidence is present."""
    if RESOURCE_CONFIG.is_file():
        config = RESOURCE_CONFIG.read_text(encoding="utf-8")
        if BUNDLED_RESOURCE_URL in config and re.search(r"type:\s*module", config):
            return True
    if RESOURCE_EVIDENCE.is_file():
        evidence = load_json(RESOURCE_EVIDENCE)
        return (
            evidence.get("lovelace_resource_registration") is True
            and evidence.get("lovelace_resource_url") == BUNDLED_RESOURCE_URL
        )
    return False


def main() -> None:
    """Check structural and release-safety invariants."""
    manifest = load_json(INTEGRATION / "manifest.json")
    hacs = load_json(ROOT / "hacs.json")

    assert manifest["domain"] == DOMAIN
    assert manifest["version"] == "0.2.0-beta.1"
    assert manifest["config_flow"] is True
    assert manifest["single_config_entry"] is True
    assert hacs["zip_release"] is True
    assert hacs["filename"] == "github_insights.zip"
    assert hacs["hide_default_branch"] is True
    assert REQUIRED_DOCS <= {path.name for path in (ROOT / "docs").glob("*.md")}
    assert REQUIRED_MODULES <= {path.name for path in INTEGRATION.glob("*.py")}
    assert (INTEGRATION / "frontend" / "README.md").is_file()
    bundle = INTEGRATION / "frontend" / "github-insights-cards.js"
    assert bundle.is_file()
    bundle_text = bundle.read_text(encoding="utf-8")
    assert all(card in bundle_text for card in REQUIRED_CARDS)
    frontend = load_json(ROOT / "frontend" / "package.json")
    frontend_lock = load_json(ROOT / "frontend" / "package-lock.json")
    assert frontend["version"] == manifest["version"]
    assert frontend_lock["version"] == manifest["version"]
    packages = frontend_lock["packages"]
    assert isinstance(packages, dict)
    assert packages[""]["version"] == manifest["version"]
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == pep440_version(str(manifest["version"]))
    assert (ROOT / "frontend" / "package-lock.json").is_file()
    assert canonical_text_sha256(DASHBOARD) == DASHBOARD_SHA256, (
        "release-candidate-dashboard.yaml is the exact storage-dashboard import "
        "template and must not change without an intentional template revision"
    )
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    bundled_card_references = BUNDLED_CARD_PATTERN.findall(dashboard)
    assert not bundled_card_references or has_bundled_resource_registration(), (
        "release candidate dashboard references bundled cards without supported "
        "Lovelace resource registration configuration or evidence"
    )
    if not has_bundled_resource_registration():
        assert "type: custom:auto-entities" in dashboard
        assert "entity_id: sensor.github_insights_*" in dashboard
        assert not re.search(r"^\s+entity:\s+\S+", dashboard, re.MULTILINE), (
            "safe fallback dashboard must discover entities dynamically instead of "
            "hardcoding deployment-specific entity IDs"
        )
    assert re.findall(r"^  - title: (.+)$", dashboard, re.MULTILINE) == [
        "Overview",
        "All entities",
    ]
    assert not re.search(
        r"^\s+-?\s*(?:entity|entity_id): "
        r"(?:sensor|binary_sensor|number|select|switch|button)"
        r"\.github_insights_[a-z0-9_]+$",
        dashboard,
        re.MULTILINE,
    )
    assert all(
        f"entity_id: {entity_filter}" in dashboard
        for entity_filter in DYNAMIC_DASHBOARD_FILTERS
    )
    deployment_docs = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    assert "storage dashboard" in deployment_docs
    assert "mode: yaml" in deployment_docs
    assert "non-editable in the UI" in deployment_docs
    assert "Never edit `.storage` directly" in deployment_docs


if __name__ == "__main__":
    main()
