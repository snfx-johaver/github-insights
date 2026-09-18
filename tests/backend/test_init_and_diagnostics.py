"""Tests for setup, migration, entities, and diagnostics."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.github_insights import async_migrate_entry
from custom_components.github_insights.const import (
    CONF_ACCOUNT_ID,
    CONF_ACCOUNT_LOGIN,
    CONF_SERVER,
    CONF_TOKEN,
    DEFAULT_SERVER,
    DOMAIN,
)
from custom_components.github_insights.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .helpers import snapshot


async def test_setup_creates_account_sensors(hass: HomeAssistant) -> None:
    """A successful first refresh creates account and rate-limit sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="https://github.com:42",
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "secret-token",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
        new=AsyncMock(return_value=snapshot()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.github_insights_octocat_account") is not None
    assert (
        hass.states.get("sensor.github_insights_octocat_api_rate_limit_remaining").state
        == "4990"
    )


async def test_diagnostics_redact_token(hass: HomeAssistant) -> None:
    """Diagnostics contain capability summaries but no credential."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "secret-token",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
        new=AsyncMock(return_value=snapshot()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert "secret-token" not in str(diagnostics)
    assert diagnostics["runtime"]["repository_count"] == 1


async def test_migrate_legacy_host_key(hass: HomeAssistant) -> None:
    """Version 1 entries migrate without network I/O."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={
            "host": "https://github.example.com",
            CONF_TOKEN: "token",
        },
        title="octocat",
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
    assert entry.data[CONF_SERVER] == "https://github.example.com"
    assert entry.data[CONF_ACCOUNT_LOGIN] == "octocat"
