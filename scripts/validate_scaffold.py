"""Validate Phase 0 and Phase 1 repository invariants."""

from __future__ import annotations

import json
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


def load_json(path: Path) -> dict[str, object]:
    """Load a JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> None:
    """Check structural and release-safety invariants."""
    manifest = load_json(INTEGRATION / "manifest.json")
    hacs = load_json(ROOT / "hacs.json")

    assert manifest["domain"] == DOMAIN
    assert manifest["version"] == "0.0.0"
    assert "config_flow" not in manifest
    assert hacs["zip_release"] is True
    assert hacs["filename"] == "github_insights.zip"
    assert hacs["hide_default_branch"] is True
    assert REQUIRED_DOCS <= {path.name for path in (ROOT / "docs").glob("*.md")}
    assert REQUIRED_MODULES <= {path.name for path in INTEGRATION.glob("*.py")}
    assert (INTEGRATION / "frontend" / "README.md").is_file()


if __name__ == "__main__":
    main()
