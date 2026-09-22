"""Local estimate inputs for GitHub Insights."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_ESTIMATED_MINUTES,
    DEFAULT_ESTIMATED_MINUTES,
)
from .coordinator import GitHubInsightsConfigEntry
from .entity import GitHubInsightsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GitHubInsightsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the non-financial desired-minute estimate input."""
    async_add_entities(
        [GitHubInsightsEstimatedMinutesNumber(entry.runtime_data.coordinator, entry)]
    )


class GitHubInsightsEstimatedMinutesNumber(GitHubInsightsEntity, NumberEntity):
    """Store a desired minute target used only for local estimation."""

    _attr_translation_key = "actions_estimated_minutes_target"
    _attr_native_min_value = 0
    _attr_native_max_value = 1_000_000
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: object, entry: GitHubInsightsConfigEntry) -> None:
        """Initialize the estimate input."""
        super().__init__(coordinator, "actions_estimated_minutes_target")  # type: ignore[arg-type]
        self._entry = entry

    @property
    def native_value(self) -> float:
        """Return the configured estimate target."""
        return float(
            self._entry.options.get(CONF_ESTIMATED_MINUTES, DEFAULT_ESTIMATED_MINUTES)
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update a local estimate input without mutating GitHub."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_ESTIMATED_MINUTES: int(value)},
        )
