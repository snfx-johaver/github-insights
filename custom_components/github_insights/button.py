"""Buttons for GitHub Insights."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GitHubInsightsConfigEntry
from .entity import GitHubInsightsBillingEntity
from .models import BillingScopeData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GitHubInsightsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up manual billing refresh buttons."""
    coordinator = entry.runtime_data.billing_coordinator
    async_add_entities(
        GitHubInsightsBillingRefreshButton(coordinator, scope_data)
        for scope_data in coordinator.data.scopes.values()
    )


class GitHubInsightsBillingRefreshButton(GitHubInsightsBillingEntity, ButtonEntity):
    """Request a throttled coordinator refresh."""

    _attr_translation_key = "actions_refresh"

    def __init__(self, coordinator: object, scope_data: BillingScopeData) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator, scope_data, "actions_refresh")  # type: ignore[arg-type]

    async def async_press(self) -> None:
        """Refresh authoritative billing data."""
        await self.coordinator.async_request_refresh()
