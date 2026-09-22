"""Binary sensors for GitHub Actions budget state."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_BUDGET_WARNING_THRESHOLD,
    DEFAULT_BUDGET_WARNING_THRESHOLD,
)
from .coordinator import GitHubInsightsConfigEntry
from .entity import GitHubInsightsBillingEntity
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
    """Set up budget state sensors."""
    coordinator = entry.runtime_data.billing_coordinator
    async_add_entities(
        GitHubInsightsBudgetBinarySensor(coordinator, scope_data, key)
        for scope_data in coordinator.data.scopes.values()
        for key in BINARY_SENSOR_KEYS
    )


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
