"""Base entities for GitHub Insights."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import GitHubInsightsCoordinator


class GitHubInsightsEntity(CoordinatorEntity[GitHubInsightsCoordinator]):
    """Base entity tied to the GitHub account device."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by the GitHub API"

    def __init__(
        self,
        coordinator: GitHubInsightsCoordinator,
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        account = coordinator.data.account
        self._attr_unique_id = f"{account.id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(account.id))},
            name=f"{NAME} ({account.login})",
            manufacturer="GitHub",
            configuration_url=account.html_url,
            entry_type=DeviceEntryType.SERVICE,
        )
