"""Reference runner selection for local budget estimates."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_REFERENCE_RUNNER,
    DEFAULT_REFERENCE_RUNNER,
    REFERENCE_RUNNER_PRICES,
)
from .coordinator import GitHubInsightsConfigEntry
from .entity import GitHubInsightsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GitHubInsightsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the local reference-runner selector."""
    async_add_entities(
        [GitHubInsightsReferenceRunnerSelect(entry.runtime_data.coordinator, entry)]
    )


class GitHubInsightsReferenceRunnerSelect(GitHubInsightsEntity, SelectEntity):
    """Choose the runner price used by explicitly estimated values."""

    _attr_translation_key = "actions_reference_runner"
    _attr_options = list(REFERENCE_RUNNER_PRICES)

    def __init__(self, coordinator: object, entry: GitHubInsightsConfigEntry) -> None:
        """Initialize the selector."""
        super().__init__(coordinator, "actions_reference_runner")  # type: ignore[arg-type]
        self._entry = entry

    @property
    def current_option(self) -> str:
        """Return the configured runner."""
        return str(
            self._entry.options.get(CONF_REFERENCE_RUNNER, DEFAULT_REFERENCE_RUNNER)
        )

    async def async_select_option(self, option: str) -> None:
        """Update the local estimate source without mutating GitHub."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_REFERENCE_RUNNER: option},
        )
