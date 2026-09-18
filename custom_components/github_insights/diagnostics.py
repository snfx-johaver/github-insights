"""Diagnostics for GitHub Insights."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN
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
    return {
        "entry": async_redact_data(
            {
                "data": dict(entry.data),
                "options": dict(entry.options),
                "version": entry.version,
                "minor_version": entry.minor_version,
            },
            TO_REDACT,
        ),
        "runtime": {
            "account_id": snapshot.account.id,
            "server": entry.runtime_data.client.server.web_url,
            "organization_count": len(snapshot.organizations),
            "repository_count": len(snapshot.repositories),
            "capabilities": {
                key: {
                    "status": capability.status,
                    "reason": capability.reason,
                }
                for key, capability in snapshot.capabilities.items()
            },
            "errors": dict(snapshot.errors),
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
        },
    }
