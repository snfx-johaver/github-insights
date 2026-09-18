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
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    LOGGER,
)
from .models import GitHubSnapshot
from .repairs import async_update_capability_issues


@dataclass(slots=True)
class GitHubInsightsRuntimeData:
    """Runtime objects for one GitHub Insights config entry."""

    client: GitHubClient
    coordinator: GitHubInsightsCoordinator


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
