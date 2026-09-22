"""Local safety switches for GitHub Insights."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_BUDGET_MANAGEMENT
from .coordinator import GitHubInsightsConfigEntry
from .entity import GitHubInsightsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GitHubInsightsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the local budget-management opt-in."""
    async_add_entities(
        [GitHubInsightsBudgetManagementSwitch(entry.runtime_data.coordinator, entry)]
    )


class GitHubInsightsBudgetManagementSwitch(GitHubInsightsEntity, SwitchEntity):
    """Enable service access without directly changing a GitHub budget."""

    _attr_translation_key = "budget_management"

    def __init__(self, coordinator: object, entry: GitHubInsightsConfigEntry) -> None:
        """Initialize the opt-in switch."""
        super().__init__(coordinator, "budget_management")  # type: ignore[arg-type]
        self._entry = entry

    @property
    def is_on(self) -> bool:
        """Return whether confirmed mutation services are enabled."""
        return bool(self._entry.options.get(CONF_BUDGET_MANAGEMENT, False))

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable confirmed mutation services."""
        self._set_enabled(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable confirmed mutation services."""
        self._set_enabled(False)

    def _set_enabled(self, enabled: bool) -> None:
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_BUDGET_MANAGEMENT: enabled},
        )
