"""Base entities for GitHub Insights."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import GitHubInsightsBillingCoordinator, GitHubInsightsCoordinator
from .models import BillingScopeData


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


class GitHubInsightsBillingEntity(CoordinatorEntity[GitHubInsightsBillingCoordinator]):
    """Base entity tied to one billing scope device."""

    _attr_has_entity_name = True
    _attr_attribution = "Billing data provided by the GitHub API"

    def __init__(
        self,
        coordinator: GitHubInsightsBillingCoordinator,
        scope_data: BillingScopeData,
        key: str,
    ) -> None:
        """Initialize the billing entity."""
        super().__init__(coordinator)
        account = coordinator.config_entry.data["account_id"]
        scope = scope_data.scope
        self.scope_key = scope.key
        self._attr_unique_id = f"{account}_billing_{scope.key}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{account}:billing:{scope.key}")},
            name=f"{NAME} Billing ({scope.scope_type.value}: {scope.name})",
            manufacturer="GitHub",
            model="Enhanced billing",
            via_device=(DOMAIN, str(account)),
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def scope_data(self) -> BillingScopeData:
        """Return current data for this entity's scope."""
        return self.coordinator.data.scopes[self.scope_key]
