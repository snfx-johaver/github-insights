"""Tests for GitHub Insights config and options flows."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.github_insights.config_flow import ValidatedSetup
from custom_components.github_insights.const import (
    CONF_ACCOUNT_ID,
    CONF_ACCOUNT_LOGIN,
    CONF_AUTO_DISCOVER,
    CONF_ORGANIZATIONS,
    CONF_REPOSITORIES,
    CONF_SERVER,
    CONF_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_SERVER,
    DOMAIN,
)

from .helpers import snapshot


async def test_user_flow(hass: HomeAssistant) -> None:
    """A valid token creates one scoped entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    validated = ValidatedSetup(DEFAULT_SERVER, "secret-token", snapshot())
    with patch(
        "custom_components.github_insights.config_flow.async_validate_input",
        return_value=validated,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SERVER: DEFAULT_SERVER, CONF_TOKEN: "secret-token"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "scope"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_AUTO_DISCOVER: True,
            CONF_ORGANIZATIONS: ["example-org"],
            CONF_REPOSITORIES: ["octocat/example"],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "octocat"
    assert result["data"][CONF_ACCOUNT_ID] == 42
    assert result["data"][CONF_TOKEN] == "secret-token"


async def test_single_entry_only(hass: HomeAssistant) -> None:
    """A second config entry is rejected."""
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

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_reauthentication_rejects_different_account(
    hass: HomeAssistant,
) -> None:
    """A replacement token must represent the original account."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="https://github.com:42",
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "expired",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
    )
    entry.add_to_hass(hass)
    validated = ValidatedSetup(DEFAULT_SERVER, "replacement", snapshot(account_id=99))

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=dict(entry.data),
    )
    with patch(
        "custom_components.github_insights.config_flow.async_validate_input",
        return_value=validated,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_TOKEN: "replacement"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "wrong_account"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Options update repository selection and safe polling interval."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "token",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
        options={
            CONF_AUTO_DISCOVER: True,
            CONF_ORGANIZATIONS: [],
            CONF_REPOSITORIES: [],
            CONF_UPDATE_INTERVAL: 15,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_AUTO_DISCOVER: False,
            CONF_ORGANIZATIONS: [],
            CONF_REPOSITORIES: [],
            CONF_UPDATE_INTERVAL: 30,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_UPDATE_INTERVAL] == 30
