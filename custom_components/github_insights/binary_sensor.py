"""Binary sensors for GitHub Actions budgets and repository health."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_BUDGET_WARNING_THRESHOLD,
    DEFAULT_BUDGET_WARNING_THRESHOLD,
)
from .coordinator import GitHubInsightsConfigEntry, GitHubInsightsCoordinator
from .entity import GitHubInsightsBillingEntity, GitHubRepositoryEntity
from .models import BillingBudget, BillingScopeData

BINARY_SENSOR_KEYS = (
    "actions_budget_warning",
    "actions_budget_exhausted",
    "actions_blocked",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GitHubInsightsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up budget state and repository health sensors."""
    billing_coordinator = entry.runtime_data.billing_coordinator
    async_add_entities(
        GitHubInsightsBudgetBinarySensor(billing_coordinator, scope_data, key)
        for scope_data in billing_coordinator.data.scopes.values()
        for key in BINARY_SENSOR_KEYS
    )
    coordinator = entry.runtime_data.coordinator
    known: set[str] = set()

    def add_discovered_entities() -> None:
        entities: list[BinarySensorEntity] = []
        for item in coordinator.data.repository_insights:
            if (
                "workflows" in item.capabilities
                and f"{item.repository.id}:workflow" not in known
            ):
                known.add(f"{item.repository.id}:workflow")
                entities.append(
                    GitHubRepositoryHealthBinarySensor(
                        coordinator,
                        item.repository.id,
                        BinarySensorEntityDescription(
                            key="workflow_failure",
                            translation_key="repository_workflow_failure",
                            device_class=BinarySensorDeviceClass.PROBLEM,
                        ),
                    )
                )
            if (
                item.security is not None
                and f"{item.repository.id}:security" not in known
            ):
                known.add(f"{item.repository.id}:security")
                entities.append(
                    GitHubRepositoryHealthBinarySensor(
                        coordinator,
                        item.repository.id,
                        BinarySensorEntityDescription(
                            key="security_alert",
                            translation_key="repository_security_alert",
                            device_class=BinarySensorDeviceClass.PROBLEM,
                        ),
                    ),
                )
        if entities:
            async_add_entities(entities)

    add_discovered_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_discovered_entities))


class GitHubInsightsBudgetBinarySensor(GitHubInsightsBillingEntity, BinarySensorEntity):
    """Expose warning, exhaustion, and GitHub enforcement state."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self, coordinator: Any, scope_data: BillingScopeData, key: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, scope_data, key)
        self._key = key
        self._attr_translation_key = key

    @property
    def available(self) -> bool:
        """Require one unambiguous Actions budget."""
        return super().available and _single_actions_budget(self.scope_data) is not None

    @property
    def is_on(self) -> bool | None:
        """Return the current budget condition."""
        budget = _single_actions_budget(self.scope_data)
        if budget is None:
            return None
        threshold = Decimal(
            str(
                self.coordinator.config_entry.options.get(
                    CONF_BUDGET_WARNING_THRESHOLD,
                    DEFAULT_BUDGET_WARNING_THRESHOLD,
                )
            )
        )
        warning, exhausted, blocked = _budget_flags(budget, threshold)
        if self._key == "actions_budget_warning":
            return warning
        if self._key == "actions_budget_exhausted":
            return exhausted
        return blocked


def _single_actions_budget(data: BillingScopeData) -> BillingBudget | None:
    budgets = tuple(budget for budget in data.budgets if budget.is_actions)
    return budgets[0] if len(budgets) == 1 else None


def _budget_flags(
    budget: BillingBudget, warning_threshold: Decimal
) -> tuple[bool, bool, bool]:
    """Return warning, exhausted, and GitHub-blocked states."""
    percent = budget.used_percent
    warning = percent is not None and percent >= warning_threshold
    exhausted = budget.remaining_amount <= 0
    return warning, exhausted, exhausted and budget.prevent_further_usage


class GitHubRepositoryHealthBinarySensor(GitHubRepositoryEntity, BinarySensorEntity):
    """Repository problem indicator."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: GitHubInsightsCoordinator,
        repository_id: int,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize a repository health sensor."""
        super().__init__(coordinator, repository_id, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return whether the source capability is available."""
        item = self.repository_data
        if item is None or not super().available:
            return False
        if self.entity_description.key == "workflow_failure":
            return item.workflow_status is not None
        return (
            item.security is not None
            and item.security.dependabot is not None
            and item.security.code_scanning is not None
            and item.security.secret_scanning is not None
        )

    @property
    def is_on(self) -> bool | None:
        """Return whether a repository has a current problem."""
        item = self.repository_data
        if item is None:
            return None
        if self.entity_description.key == "workflow_failure":
            return item.workflow_status == "failure"
        return bool(item.security and item.security.total)
