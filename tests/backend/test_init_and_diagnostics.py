"""Tests for setup, migration, entities, and diagnostics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.github_insights import (
    FRONTEND_PATH,
    FRONTEND_REGISTERED,
    FRONTEND_URL,
    async_migrate_entry,
    async_setup,
)
from custom_components.github_insights.const import (
    CONF_ACCOUNT_ID,
    CONF_ACCOUNT_LOGIN,
    CONF_ACTIONS_INCLUDED_MINUTES,
    CONF_BILLING_INTERVAL,
    CONF_BILLING_ORGANIZATIONS,
    CONF_BILLING_TOKEN,
    CONF_ENABLED_CATEGORIES,
    CONF_ESTIMATED_MINUTES,
    CONF_MAX_REPOSITORIES,
    CONF_PERSONAL_BILLING,
    CONF_SERVER,
    CONF_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_SERVER,
    DOMAIN,
)
from custom_components.github_insights.diagnostics import (
    _billing_auth_method,
    async_get_config_entry_diagnostics,
)
from custom_components.github_insights.models import BillingSnapshot

from .helpers import billing_snapshot, snapshot


async def test_setup_registers_bundled_frontend_once() -> None:
    """The integration exposes its bundled card asset idempotently."""
    register = AsyncMock()
    fake_hass = cast(
        HomeAssistant,
        SimpleNamespace(
            data={},
            http=SimpleNamespace(async_register_static_paths=register),
        ),
    )

    assert await async_setup(fake_hass, {})
    assert await async_setup(fake_hass, {})

    register.assert_awaited_once()
    awaited = register.await_args
    assert awaited is not None
    static_path = awaited.args[0][0]
    assert static_path.url_path == FRONTEND_URL
    assert static_path.path == str(FRONTEND_PATH)
    assert static_path.cache_headers is True
    assert fake_hass.data[FRONTEND_REGISTERED] is True


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

    with (
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
            new=AsyncMock(return_value=snapshot()),
        ),
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_billing_snapshot",
            new=AsyncMock(return_value=billing_snapshot()),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.github_insights_octocat_account") is not None
    rate_limit_state = hass.states.get(
        "sensor.github_insights_octocat_api_rate_limit_remaining"
    )
    assert rate_limit_state is not None
    assert rate_limit_state.state == "4990"


async def test_setup_keeps_primary_and_billing_clients_isolated(
    hass: HomeAssistant,
) -> None:
    """Normal API collection and billing collection receive different clients."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="https://github.com:42",
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "github_pat_primary_fake",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
        options={CONF_BILLING_TOKEN: "ghp_billing_fake"},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
            new=AsyncMock(return_value=snapshot()),
        ) as normal_fetch,
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_billing_snapshot",
            new=AsyncMock(return_value=billing_snapshot()),
        ) as billing_fetch,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    normal_fetch.assert_awaited_once()
    billing_fetch.assert_awaited_once()
    normal_client = entry.runtime_data.client
    billing_client = entry.runtime_data.billing_client
    assert billing_client is not None
    assert normal_client is not billing_client
    assert normal_client.token_type == "fine_grained_pat"
    assert billing_client.token_type == "classic_pat"


async def test_missing_billing_token_is_nonfatal_and_unavailable(
    hass: HomeAssistant,
) -> None:
    """A missing optional credential never blocks normal integration setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="https://github.com:42",
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "github_pat_primary",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
            new=AsyncMock(return_value=snapshot()),
        ),
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_billing_snapshot",
            new=AsyncMock(),
        ) as billing_fetch,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    billing_fetch.assert_not_awaited()
    scope = entry.runtime_data.billing_coordinator.data.scopes["user:octocat"]
    assert scope.usage is None
    assert scope.usage_capability.reason == "billing_token_not_configured"
    assert entry.runtime_data.coordinator.data.account.login == "octocat"


async def test_setup_normalizes_float_shaped_number_selector_options(
    hass: HomeAssistant,
) -> None:
    """Float-shaped selector values support setup and repository discovery."""
    captured: dict[str, object] = {}

    async def async_fetch_snapshot(
        client: object,
        *,
        repository_options: object,
        copilot_organizations: tuple[str, ...],
        copilot_billing_client: object | None,
    ) -> object:
        captured["repository_options"] = repository_options
        return snapshot()

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        minor_version=5,
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "primary-token",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
        options={
            CONF_MAX_REPOSITORIES: 10.0,
            CONF_UPDATE_INTERVAL: 15.0,
            CONF_BILLING_INTERVAL: 60.0,
            CONF_ESTIMATED_MINUTES: 1000.0,
            CONF_ACTIONS_INCLUDED_MINUTES: 3000.0,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
        new=async_fetch_snapshot,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    repository_options = cast(Any, captured["repository_options"])
    assert repository_options.repository_limit == 10
    assert isinstance(repository_options.repository_limit, int)
    assert entry.runtime_data.coordinator.update_interval == timedelta(minutes=15)
    assert entry.runtime_data.billing_coordinator.update_interval == timedelta(
        minutes=60
    )


async def test_configured_allowance_exists_without_billing_scopes(
    hass: HomeAssistant,
) -> None:
    """The configured allowance is an account sensor, not a billing-scope sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="https://github.com:42",
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "secret-token",
            CONF_ACCOUNT_ID: 42,
            CONF_ACCOUNT_LOGIN: "octocat",
        },
        options={
            CONF_ACTIONS_INCLUDED_MINUTES: 3000,
            CONF_PERSONAL_BILLING: False,
            CONF_BILLING_ORGANIZATIONS: [],
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
            new=AsyncMock(return_value=snapshot()),
        ),
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_billing_snapshot",
            new=AsyncMock(
                return_value=BillingSnapshot.create(
                    scopes={},
                    fetched_at=datetime(2026, 9, 22, tzinfo=UTC),
                )
            ),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    allowance = hass.states.get(
        "sensor.github_insights_octocat_configured_actions_included_minutes"
    )
    assert allowance is not None
    assert allowance.state == "3000"
    assert allowance.attributes["data_class"] == "configured"
    assert not any(
        state.entity_id.endswith("billing_configured_actions_included_minutes")
        for state in hass.states.async_all("sensor")
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
        options={
            CONF_ACTIONS_INCLUDED_MINUTES: 3000,
            CONF_BILLING_TOKEN: "secondary-classic-token",
            "organizations": ["private-org"],
            "repositories": ["private-org/private-repo"],
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_snapshot",
            new=AsyncMock(return_value=snapshot()),
        ),
        patch(
            "custom_components.github_insights.api.GitHubClient.async_fetch_billing_snapshot",
            new=AsyncMock(return_value=billing_snapshot()),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert "secret-token" not in str(diagnostics)
    assert "secondary-classic-token" not in str(diagnostics)
    assert "private-org" not in str(diagnostics)
    assert diagnostics["runtime"]["repository_count"] == 1
    assert "example-org" not in str(diagnostics)
    assert "budget-1" not in str(diagnostics)
    assert diagnostics["runtime"]["billing"]["scope_count"] == 1
    assert diagnostics["runtime"]["billing_auth_method"] == "classic_billing_token"
    assert (
        diagnostics["entry"]["options"]["configured_actions_included_minutes"] == 3000
    )


def test_diagnostics_billing_auth_method_values() -> None:
    """Diagnostics use only the documented non-secret auth method values."""

    def entry(token_type: str, billing_client: object | None) -> Any:
        return SimpleNamespace(
            runtime_data=SimpleNamespace(
                client=SimpleNamespace(token_type=token_type),
                billing_client=billing_client,
            )
        )

    assert _billing_auth_method(entry("fine_grained_pat", None)) == "fine_grained"
    assert _billing_auth_method(entry("classic_pat", None)) == "not_configured"
    assert _billing_auth_method(entry("fine_grained_pat", object())) == (
        "classic_billing_token"
    )


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
    assert entry.version == 3
    assert entry.minor_version == 5
    assert entry.data[CONF_SERVER] == "https://github.example.com"
    assert entry.data[CONF_ACCOUNT_LOGIN] == "octocat"
    assert "repositories" in entry.options[CONF_ENABLED_CATEGORIES]
    assert entry.options[CONF_MAX_REPOSITORIES] == 10
    assert entry.options[CONF_ACTIONS_INCLUDED_MINUTES] == 0


async def test_migrate_float_shaped_number_selector_options(
    hass: HomeAssistant,
) -> None:
    """Version 3.4 entries normalize every integer-valued numeric option."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        minor_version=4,
        data={
            CONF_SERVER: DEFAULT_SERVER,
            CONF_TOKEN: "token",
            CONF_ACCOUNT_LOGIN: "octocat",
        },
        options={
            CONF_MAX_REPOSITORIES: 10.0,
            CONF_UPDATE_INTERVAL: 15.0,
            CONF_BILLING_INTERVAL: 60.0,
            CONF_ESTIMATED_MINUTES: 1000.0,
            CONF_ACTIONS_INCLUDED_MINUTES: 3000.0,
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.minor_version == 5
    for key in (
        CONF_MAX_REPOSITORIES,
        CONF_UPDATE_INTERVAL,
        CONF_BILLING_INTERVAL,
        CONF_ESTIMATED_MINUTES,
        CONF_ACTIONS_INCLUDED_MINUTES,
    ):
        assert isinstance(entry.options[key], int)
