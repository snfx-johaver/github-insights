"""Repairs support for GitHub Insights."""

from __future__ import annotations

from collections.abc import Mapping

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN

_CAPABILITY_ISSUES = {
    "organizations": "organizations_unavailable",
    "repositories": "repositories_unavailable",
    "rate_limit": "rate_limit_unavailable",
}


def async_update_capability_issues(
    hass: HomeAssistant,
    entry_id: str,
    errors: Mapping[str, str],
) -> None:
    """Create or clear non-fixable capability issues."""
    for capability, issue_key in _CAPABILITY_ISSUES.items():
        issue_id = f"{entry_id}_{issue_key}"
        if capability not in errors:
            ir.async_delete_issue(hass, DOMAIN, issue_id)
            continue
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="capability_unavailable",
            translation_placeholders={
                "capability": capability,
                "reason": errors[capability],
            },
        )
