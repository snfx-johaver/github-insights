"""Validate repository structure and single-artifact invariants."""

from __future__ import annotations

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
RESOURCE_CONFIG = ROOT / "docs" / "release-candidate-lovelace-resources.yaml"
RESOURCE_EVIDENCE = ROOT / "release-ready.json"


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
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    bundled_card_references = BUNDLED_CARD_PATTERN.findall(dashboard)
    assert not bundled_card_references or has_bundled_resource_registration(), (
        "release candidate dashboard references bundled cards without supported "
        "Lovelace resource registration configuration or evidence"
    )


if __name__ == "__main__":
    main()
