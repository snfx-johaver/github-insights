"""Data update coordinator for GitHub Insights."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    GitHubAuthenticationError,
    GitHubClient,
    GitHubConnectionError,
    GitHubInsightsError,
    GitHubRateLimitError,
)
from .const import (
    CONF_ACCOUNT_LOGIN,
    CONF_BILLING_ENTERPRISE,
    CONF_BILLING_INTERVAL,
    CONF_BILLING_ORGANIZATIONS,
    CONF_ORGANIZATIONS,
    CONF_PERSONAL_BILLING,
    CONF_UPDATE_INTERVAL,
    DEFAULT_BILLING_INTERVAL_MINUTES,
    DEFAULT_PERSONAL_BILLING,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    LOGGER,
)
from .models import (
    BillingMutation,
    BillingScope,
    BillingScopeData,
    BillingScopeType,
    BillingSnapshot,
    GitHubSnapshot,
)
from .repairs import async_update_billing_issues, async_update_capability_issues


@dataclass(slots=True)
class GitHubInsightsRuntimeData:
    """Runtime objects for one GitHub Insights config entry."""

    client: GitHubClient
    coordinator: GitHubInsightsCoordinator
    billing_coordinator: GitHubInsightsBillingCoordinator


type GitHubInsightsConfigEntry = ConfigEntry[GitHubInsightsRuntimeData]


class GitHubInsightsCoordinator(DataUpdateCoordinator[GitHubSnapshot]):
    """Coordinate account, repository discovery, and rate-limit data."""

    config_entry: GitHubInsightsConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GitHubInsightsConfigEntry,
        client: GitHubClient,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        interval = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES
        )
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
            always_update=False,
        )

    async def _async_update_data(self) -> GitHubSnapshot:
        """Fetch a normalized GitHub snapshot."""
        try:
            snapshot = await self.client.async_fetch_snapshot()
        except GitHubAuthenticationError as err:
            raise ConfigEntryAuthFailed("GitHub credentials were rejected") from err
        except GitHubRateLimitError as err:
            raise UpdateFailed(
                "GitHub rate limit reached", retry_after=err.retry_after
            ) from err
        except GitHubConnectionError as err:
            raise UpdateFailed("Unable to connect to GitHub") from err
        except GitHubInsightsError as err:
            raise UpdateFailed(f"GitHub API error: {err}") from err

        snapshot = _merge_last_known_good(self.data, snapshot)
        async_update_capability_issues(
            self.hass, self.config_entry.entry_id, snapshot.errors
        )
        return snapshot


class GitHubInsightsBillingCoordinator(DataUpdateCoordinator[BillingSnapshot]):
    """Coordinate enhanced-billing usage and budgets independently."""

    config_entry: GitHubInsightsConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GitHubInsightsConfigEntry,
        client: GitHubClient,
    ) -> None:
        """Initialize the billing coordinator."""
        self.client = client
        self._last_mutation: BillingMutation | None = None
        interval = entry.options.get(
            CONF_BILLING_INTERVAL, DEFAULT_BILLING_INTERVAL_MINUTES
        )
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_billing",
            update_interval=timedelta(minutes=interval),
            always_update=False,
        )

    @property
    def scopes(self) -> tuple[BillingScope, ...]:
        """Return configured official billing scopes."""
        options = self.config_entry.options
        scopes: list[BillingScope] = []
        if options.get(CONF_PERSONAL_BILLING, DEFAULT_PERSONAL_BILLING):
            scopes.append(
                BillingScope(
                    BillingScopeType.USER,
                    str(self.config_entry.data[CONF_ACCOUNT_LOGIN]),
                )
            )
        organizations = options.get(
            CONF_BILLING_ORGANIZATIONS,
            options.get(CONF_ORGANIZATIONS, []),
        )
        scopes.extend(
            BillingScope(BillingScopeType.ORGANIZATION, str(organization))
            for organization in organizations
        )
        enterprise = str(options.get(CONF_BILLING_ENTERPRISE, "")).strip()
        if enterprise:
            scopes.append(BillingScope(BillingScopeType.ENTERPRISE, enterprise))
        return tuple(scopes)

    async def _async_update_data(self) -> BillingSnapshot:
        """Fetch isolated billing scope snapshots."""
        try:
            snapshot = await self.client.async_fetch_billing_snapshot(self.scopes)
        except GitHubAuthenticationError as err:
            raise ConfigEntryAuthFailed("GitHub credentials were rejected") from err
        except GitHubRateLimitError as err:
            raise UpdateFailed(
                "GitHub billing rate limit reached", retry_after=err.retry_after
            ) from err
        except GitHubConnectionError as err:
            raise UpdateFailed("Unable to connect to GitHub billing") from err
        except GitHubInsightsError as err:
            raise UpdateFailed(f"GitHub billing API error: {err}") from err

        snapshot = _merge_billing_last_known_good(self.data, snapshot)
        if self._last_mutation is not None:
            snapshot = replace(snapshot, last_mutation=self._last_mutation)
        async_update_billing_issues(
            self.hass, self.config_entry.entry_id, snapshot.errors
        )
        return snapshot

    def record_mutation(self, mutation: BillingMutation) -> None:
        """Retain sanitized mutation metadata for diagnostics."""
        self._last_mutation = mutation


def _merge_last_known_good(
    previous: GitHubSnapshot | None,
    current: GitHubSnapshot,
) -> GitHubSnapshot:
    """Retain prior category values when an optional endpoint is stale."""
    if previous is None or not current.errors:
        return current

    return replace(
        current,
        organizations=(
            previous.organizations
            if "organizations" in current.errors
            else current.organizations
        ),
        repositories=(
            previous.repositories
            if "repositories" in current.errors
            else current.repositories
        ),
        rate_limit=(
            previous.rate_limit
            if "rate_limit" in current.errors
            else current.rate_limit
        ),
    )


def _merge_billing_last_known_good(
    previous: BillingSnapshot | None,
    current: BillingSnapshot,
) -> BillingSnapshot:
    """Retain prior billing categories when one endpoint is temporarily stale."""
    if previous is None or not current.errors:
        return current
    merged: dict[str, BillingScopeData] = {}
    for key, scope_data in current.scopes.items():
        old = previous.scopes.get(key)
        if old is None:
            merged[key] = scope_data
            continue
        merged[key] = replace(
            scope_data,
            usage=old.usage if "usage" in scope_data.errors else scope_data.usage,
            budgets=(
                old.budgets if "budgets" in scope_data.errors else scope_data.budgets
            ),
        )
    return BillingSnapshot.create(
        scopes=merged,
        fetched_at=current.fetched_at,
        errors=current.errors,
        last_mutation=current.last_mutation or previous.last_mutation,
    )
