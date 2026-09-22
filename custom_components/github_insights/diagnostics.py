"""Diagnostics for GitHub Insights."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENABLED_CATEGORIES,
    CONF_INCLUDE_ARCHIVED,
    CONF_INCLUDE_FORKS,
    CONF_MAX_REPOSITORIES,
    CONF_ORGANIZATIONS,
    CONF_REPOSITORIES,
    CONF_SERVER,
    CONF_TOKEN,
)
from .coordinator import GitHubInsightsConfigEntry

TO_REDACT = {
    CONF_TOKEN,
    "authorization",
    "cookie",
    "download_links",
    "email",
    "secret",
    "signed_url",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: GitHubInsightsConfigEntry,
) -> dict[str, Any]:
    """Return sanitized diagnostics for one config entry."""
    snapshot = entry.runtime_data.coordinator.data
    billing = entry.runtime_data.billing_coordinator.data
    return {
        "entry": async_redact_data(
            {
                "data": {
                    CONF_SERVER: (
                        "github.com"
                        if entry.runtime_data.client.server.is_dotcom
                        else "github_enterprise_server"
                    ),
                    CONF_TOKEN: entry.data[CONF_TOKEN],
                },
                "options": {
                    "organization_selection_count": len(
                        entry.options.get(CONF_ORGANIZATIONS, [])
                    ),
                    "repository_selection_count": len(
                        entry.options.get(CONF_REPOSITORIES, [])
                    ),
                    "enabled_categories": sorted(
                        entry.options.get(CONF_ENABLED_CATEGORIES, [])
                    ),
                    "include_archived": entry.options.get(CONF_INCLUDE_ARCHIVED, False),
                    "include_forks": entry.options.get(CONF_INCLUDE_FORKS, True),
                    "repository_limit": entry.options.get(CONF_MAX_REPOSITORIES, 10),
                },
                "version": entry.version,
                "minor_version": entry.minor_version,
            },
            TO_REDACT,
        ),
        "runtime": {
            "server_type": (
                "github.com"
                if entry.runtime_data.client.server.is_dotcom
                else "github_enterprise_server"
            ),
            "token_type": entry.runtime_data.client.token_type,
            "organization_count": len(snapshot.organizations),
            "repository_count": len(snapshot.repositories),
            "selected_repository_count": len(snapshot.repository_insights),
            "copilot_scope_count": len(snapshot.copilot),
            "capability_status_counts": _value_counts(
                capability.status for capability in snapshot.capabilities.values()
            ),
            "capability_reason_counts": _value_counts(
                capability.reason
                for capability in snapshot.capabilities.values()
                if capability.reason
            ),
            "error_reason_counts": _value_counts(snapshot.errors.values()),
            "token_scopes": snapshot.token_scopes,
            "fetched_at": snapshot.fetched_at,
            "rate_limit": (
                {
                    "limit": snapshot.rate_limit.limit,
                    "remaining": snapshot.rate_limit.remaining,
                    "used": snapshot.rate_limit.used,
                    "reset_at": snapshot.rate_limit.reset_at,
                }
                if snapshot.rate_limit
                else None
            ),
            "billing": {
                "scope_count": len(billing.scopes),
                "scopes": [
                    {
                        "scope_type": scope_data.scope.scope_type,
                        "usage_status": scope_data.usage_capability.status,
                        "usage_reason": scope_data.usage_capability.reason,
                        "budget_status": scope_data.budget_capability.status,
                        "budget_reason": scope_data.budget_capability.reason,
                        "usage_item_count": (
                            len(scope_data.usage.summary_items)
                            if scope_data.usage
                            else 0
                        ),
                        "budget_count": len(scope_data.budgets),
                    }
                    for scope_data in billing.scopes.values()
                ],
                "fetched_at": billing.fetched_at,
                "last_mutation": (
                    {
                        "action": billing.last_mutation.action,
                        "scope_type": billing.last_mutation.scope_key.split(":", 1)[0],
                        "completed_at": billing.last_mutation.completed_at,
                    }
                    if billing.last_mutation
                    else None
                ),
            },
        },
    }


def _value_counts(values: Iterable[object]) -> dict[str, int]:
    """Return non-identifying counts for diagnostic capability values."""
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts
