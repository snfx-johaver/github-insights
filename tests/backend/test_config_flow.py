"""Tests for GitHub Insights config and options flows."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.github_insights.config_flow import (
    ACTIONS_ALLOWANCE_URL,
    BILLING_USAGE_URL,
    CLASSIC_PAT_URL,
    COPILOT_ORGANIZATION_URL,
    COPILOT_SETTINGS_URL,
    ENTERPRISE_SLUG_URL,
    ENTERPRISE_URL_EXAMPLE,
    FINE_GRAINED_PAT_URL,
    ValidatedSetup,
)
from custom_components.github_insights.const import (
    CONF_ACCOUNT_ID,
    CONF_ACCOUNT_LOGIN,
    CONF_ACTIONS_INCLUDED_MINUTES,
    CONF_AUTO_DISCOVER,
    CONF_BILLING_ENTERPRISE,
    CONF_BILLING_INTERVAL,
    CONF_BILLING_ORGANIZATIONS,
    CONF_BILLING_TOKEN,
    CONF_BUDGET_CRITICAL_THRESHOLD,
    CONF_BUDGET_MANAGEMENT,
    CONF_BUDGET_WARNING_THRESHOLD,
    CONF_ESTIMATED_MINUTES,
    CONF_MAX_REPOSITORIES,
    CONF_ORGANIZATIONS,
    CONF_PERSONAL_BILLING,
    CONF_REFERENCE_RUNNER,
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
    assert result["description_placeholders"] == {
        "fine_grained_pat_url": FINE_GRAINED_PAT_URL,
        "classic_pat_url": CLASSIC_PAT_URL,
    }
    assert "secret-token" not in str(result["description_placeholders"])
    assert "classic-billing-token" not in str(result["description_placeholders"])

    validated = ValidatedSetup(DEFAULT_SERVER, "secret-token", snapshot())
    with patch(
        "custom_components.github_insights.config_flow.async_validate_input",
        return_value=validated,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERVER: DEFAULT_SERVER,
                CONF_TOKEN: "secret-token",
                CONF_BILLING_TOKEN: "classic-billing-token",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "scope"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_AUTO_DISCOVER: True,
            CONF_ORGANIZATIONS: ["example-org"],
            CONF_REPOSITORIES: ["octocat/example"],
            CONF_MAX_REPOSITORIES: 10.0,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "octocat"
    assert result["data"][CONF_ACCOUNT_ID] == 42
    assert result["data"][CONF_TOKEN] == "secret-token"
    assert result["options"][CONF_BILLING_TOKEN] == "classic-billing-token"
    assert result["options"][CONF_MAX_REPOSITORIES] == 10
    assert isinstance(result["options"][CONF_MAX_REPOSITORIES], int)


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
    assert result["errors"] is not None
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
    assert result["description_placeholders"] == {
        "classic_pat_url": CLASSIC_PAT_URL,
        "billing_usage_url": BILLING_USAGE_URL,
        "enterprise_slug_url": ENTERPRISE_SLUG_URL,
        "enterprise_url_example": ENTERPRISE_URL_EXAMPLE,
        "actions_allowance_url": ACTIONS_ALLOWANCE_URL,
        "copilot_settings_url": COPILOT_SETTINGS_URL,
        "copilot_organization_url": COPILOT_ORGANIZATION_URL,
    }
    assert "classic-billing-token" not in str(result["description_placeholders"])

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_AUTO_DISCOVER: False,
            CONF_ORGANIZATIONS: [],
            CONF_REPOSITORIES: [],
            CONF_UPDATE_INTERVAL: 30.0,
            CONF_BILLING_INTERVAL: 60.0,
            CONF_BILLING_TOKEN: "classic-billing-token",
            CONF_PERSONAL_BILLING: True,
            CONF_BILLING_ORGANIZATIONS: [],
            CONF_BILLING_ENTERPRISE: "",
            CONF_BUDGET_MANAGEMENT: False,
            CONF_REFERENCE_RUNNER: "linux_standard",
            CONF_ESTIMATED_MINUTES: 1000.0,
            CONF_ACTIONS_INCLUDED_MINUTES: 3000.0,
            CONF_BUDGET_WARNING_THRESHOLD: 75.0,
            CONF_BUDGET_CRITICAL_THRESHOLD: 90.0,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_UPDATE_INTERVAL] == 30
    assert result["data"][CONF_ACTIONS_INCLUDED_MINUTES] == 3000
    assert result["data"][CONF_BILLING_TOKEN] == "classic-billing-token"
    for key in (
        CONF_UPDATE_INTERVAL,
        CONF_BILLING_INTERVAL,
        CONF_ESTIMATED_MINUTES,
        CONF_ACTIONS_INCLUDED_MINUTES,
        CONF_BUDGET_WARNING_THRESHOLD,
        CONF_BUDGET_CRITICAL_THRESHOLD,
    ):
        assert isinstance(result["data"][key], int)


async def test_options_flow_preserves_updates_and_clears_billing_token(
    hass: HomeAssistant,
) -> None:
    """The optional credential is masked, replaceable, and explicitly clearable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "primary-token",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
        options={
            CONF_AUTO_DISCOVER: True,
            CONF_BILLING_TOKEN: "saved-classic-token",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["data_schema"] is not None
    values = {
        key.schema: key.default()
        for key in result["data_schema"].schema
        if hasattr(key, "default")
    }
    assert values[CONF_BILLING_TOKEN] == "********"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], values
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BILLING_TOKEN] == "saved-classic-token"
    assert "********" not in str(result["data"])

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["data_schema"] is not None
    values = {
        key.schema: key.default()
        for key in result["data_schema"].schema
        if hasattr(key, "default")
    }
    values[CONF_BILLING_TOKEN] = "replacement-classic-token"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], values
    )
    assert result["data"][CONF_BILLING_TOKEN] == "replacement-classic-token"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["data_schema"] is not None
    values = {
        key.schema: key.default()
        for key in result["data_schema"].schema
        if hasattr(key, "default")
    }
    values[CONF_BILLING_TOKEN] = ""
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], values
    )
    assert CONF_BILLING_TOKEN not in result["data"]


async def test_options_reject_fractional_actions_allowance(
    hass: HomeAssistant,
) -> None:
    """The configured Actions allowance must be a bounded integer."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "token",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
        options={CONF_AUTO_DISCOVER: True},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["data_schema"] is not None
    values = {
        key.schema: key.default()
        for key in result["data_schema"].schema
        if hasattr(key, "default")
    }
    values[CONF_ACTIONS_INCLUDED_MINUTES] = 12.5

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], values
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_ACTIONS_INCLUDED_MINUTES: "invalid_actions_allowance"
    }
