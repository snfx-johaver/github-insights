"""GitHub Insights integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GitHubClient
from .const import (
    CONF_ACCOUNT_ID,
    CONF_ACCOUNT_LOGIN,
    CONF_SERVER,
    CONF_TOKEN,
    DEFAULT_SERVER,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import (
    GitHubInsightsConfigEntry,
    GitHubInsightsCoordinator,
    GitHubInsightsRuntimeData,
)

FRONTEND_URL = "/github_insights/frontend"
FRONTEND_PATH = Path(__file__).parent / "frontend"
FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Register the bundled frontend asset directory."""
    if hass.data.get(FRONTEND_REGISTERED):
        return True
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_URL,
                str(FRONTEND_PATH),
                cache_headers=True,
            )
        ]
    )
    hass.data[FRONTEND_REGISTERED] = True
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: GitHubInsightsConfigEntry
) -> bool:
    """Set up GitHub Insights from a config entry."""
    client = GitHubClient(
        async_get_clientsession(hass),
        entry.data[CONF_TOKEN],
        entry.data[CONF_SERVER],
    )
    coordinator = GitHubInsightsCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    if CONF_ACCOUNT_ID not in entry.data:
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_ACCOUNT_ID: coordinator.data.account.id,
                CONF_ACCOUNT_LOGIN: coordinator.data.account.login,
            },
            unique_id=f"{client.server.web_url}:{coordinator.data.account.id}",
        )

    entry.runtime_data = GitHubInsightsRuntimeData(
        client=client,
        coordinator=coordinator,
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: GitHubInsightsConfigEntry
) -> bool:
    """Unload GitHub Insights."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant, entry: GitHubInsightsConfigEntry
) -> None:
    """Reload GitHub Insights after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy Phase 2 config-entry data."""
    if entry.version > 2:
        return False

    if entry.version == 1:
        data = dict(entry.data)
        data[CONF_SERVER] = data.pop("host", DEFAULT_SERVER)
        if CONF_ACCOUNT_LOGIN not in data and entry.title:
            data[CONF_ACCOUNT_LOGIN] = entry.title
        hass.config_entries.async_update_entry(
            entry,
            data=data,
            version=2,
            minor_version=1,
        )
    elif entry.minor_version < 1:
        hass.config_entries.async_update_entry(entry, minor_version=1)

    return True
