"""Sensor platform for GitHub Insights."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_DATA_CLASS,
    ATTR_FRESHNESS,
    ATTR_SOURCE,
    CONF_ESTIMATED_MINUTES,
    CONF_REFERENCE_RUNNER,
    DEFAULT_ESTIMATED_MINUTES,
    DEFAULT_REFERENCE_RUNNER,
    REFERENCE_RUNNER_PRICES,
)
from .coordinator import (
    GitHubInsightsBillingCoordinator,
    GitHubInsightsConfigEntry,
    GitHubInsightsCoordinator,
)
from .entity import GitHubInsightsBillingEntity, GitHubInsightsEntity
from .models import (
    BillingBudget,
    BillingScopeData,
    BillingUsageItem,
    DataClass,
    GitHubSnapshot,
)

type SensorValue = StateType | date | datetime | Decimal


@dataclass(frozen=True, kw_only=True)
class GitHubInsightsSensorDescription(SensorEntityDescription):
    """Describe a GitHub Insights sensor."""

    value_fn: Callable[[GitHubSnapshot], SensorValue]
    available_fn: Callable[[GitHubSnapshot], bool] = lambda snapshot: True
    attributes_fn: Callable[[GitHubSnapshot], Mapping[str, Any] | None] = (
        lambda snapshot: None
    )


SENSORS: tuple[GitHubInsightsSensorDescription, ...] = (
    GitHubInsightsSensorDescription(
        key="account",
        translation_key="account",
        value_fn=lambda snapshot: snapshot.account.login,
        attributes_fn=lambda snapshot: {
            "display_name": snapshot.account.name,
            "avatar_url": snapshot.account.avatar_url,
            "url": snapshot.account.html_url,
            "organizations": len(snapshot.organizations),
            "discovered_repositories": len(snapshot.repositories),
        },
    ),
    GitHubInsightsSensorDescription(
        key="public_repositories",
        translation_key="public_repositories",
        native_unit_of_measurement="repositories",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.account.public_repos,
    ),
    GitHubInsightsSensorDescription(
        key="private_repositories",
        translation_key="private_repositories",
        native_unit_of_measurement="repositories",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        available_fn=lambda snapshot: snapshot.account.total_private_repos is not None,
        value_fn=lambda snapshot: snapshot.account.total_private_repos,
    ),
    GitHubInsightsSensorDescription(
        key="followers",
        translation_key="followers",
        native_unit_of_measurement="followers",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: snapshot.account.followers,
    ),
    GitHubInsightsSensorDescription(
        key="following",
        translation_key="following",
        native_unit_of_measurement="users",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda snapshot: snapshot.account.following,
    ),
    GitHubInsightsSensorDescription(
        key="organizations",
        translation_key="organizations",
        native_unit_of_measurement="organizations",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda snapshot: len(snapshot.organizations),
    ),
    GitHubInsightsSensorDescription(
        key="api_rate_limit_remaining",
        translation_key="api_rate_limit_remaining",
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        available_fn=lambda snapshot: snapshot.rate_limit is not None,
        value_fn=lambda snapshot: (
            snapshot.rate_limit.remaining if snapshot.rate_limit else None
        ),
        attributes_fn=lambda snapshot: (
            {
                "limit": snapshot.rate_limit.limit,
                "used": snapshot.rate_limit.used,
            }
            if snapshot.rate_limit
            else None
        ),
    ),
    GitHubInsightsSensorDescription(
        key="api_rate_limit_reset",
        translation_key="api_rate_limit_reset",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        available_fn=lambda snapshot: snapshot.rate_limit is not None,
        value_fn=lambda snapshot: (
            snapshot.rate_limit.reset_at if snapshot.rate_limit else None
        ),
    ),
    GitHubInsightsSensorDescription(
        key="last_successful_sync",
        translation_key="last_successful_sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda snapshot: snapshot.fetched_at,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GitHubInsightsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up GitHub Insights sensors."""
    coordinator = entry.runtime_data.coordinator
    billing_coordinator = entry.runtime_data.billing_coordinator
    async_add_entities(
        GitHubInsightsSensor(coordinator, description) for description in SENSORS
    )
    async_add_entities(
        GitHubInsightsBillingSensor(billing_coordinator, scope_data, key)
        for scope_data in billing_coordinator.data.scopes.values()
        for key in BILLING_SENSOR_KEYS
    )


class GitHubInsightsSensor(GitHubInsightsEntity, SensorEntity):
    """A coordinator-backed GitHub Insights sensor."""

    entity_description: GitHubInsightsSensorDescription

    def __init__(
        self,
        coordinator: GitHubInsightsCoordinator,
        description: GitHubInsightsSensorDescription,
    ) -> None:
        """Initialize a sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return whether this metric is currently available."""
        return super().available and self.entity_description.available_fn(
            self.coordinator.data
        )

    @property
    def native_value(self) -> SensorValue:
        """Return the current native value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return bounded metadata and provenance."""
        attributes = dict(
            self.entity_description.attributes_fn(self.coordinator.data) or {}
        )
        attributes.update(
            {
                ATTR_DATA_CLASS: DataClass.AUTHORITATIVE,
                ATTR_FRESHNESS: self.coordinator.data.fetched_at.isoformat(),
                ATTR_SOURCE: "GitHub API",
            }
        )
        return attributes


BILLING_SENSOR_KEYS = (
    "billing_period",
    "actions_billable_usage",
    "actions_discounted_usage",
    "actions_gross_cost",
    "actions_discount",
    "actions_cost",
    "actions_budget_count",
    "actions_budget",
    "actions_budget_remaining",
    "actions_budget_percent",
    "actions_estimated_minutes_remaining",
    "actions_estimated_budget",
)


class GitHubInsightsBillingSensor(GitHubInsightsBillingEntity, SensorEntity):
    """A safe scope-level billing and budget sensor."""

    def __init__(
        self,
        coordinator: GitHubInsightsBillingCoordinator,
        scope_data: BillingScopeData,
        key: str,
    ) -> None:
        """Initialize a billing sensor."""
        super().__init__(coordinator, scope_data, key)
        self._key = key
        self._attr_translation_key = key
        if key in {
            "actions_gross_cost",
            "actions_discount",
            "actions_cost",
            "actions_budget",
            "actions_budget_remaining",
            "actions_estimated_budget",
        }:
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_native_unit_of_measurement = "USD"
            self._attr_suggested_display_precision = 2
        elif key == "actions_budget_percent":
            self._attr_native_unit_of_measurement = "%"
            self._attr_suggested_display_precision = 1
        elif key == "actions_estimated_minutes_remaining":
            self._attr_native_unit_of_measurement = "min"
            self._attr_suggested_display_precision = 0
        elif key in {"actions_billable_usage", "actions_discounted_usage"}:
            self._attr_suggested_display_precision = 2

    @property
    def available(self) -> bool:
        """Return whether this metric has an unambiguous source value."""
        if not super().available:
            return False
        data = self.scope_data
        if self._key == "billing_period":
            return data.usage is not None
        if self._key.startswith("actions_budget") or self._key == (
            "actions_estimated_minutes_remaining"
        ):
            if self._key == "actions_budget_count":
                return data.budget_capability.status.value == "available"
            return _single_actions_budget(data) is not None
        if self._key == "actions_estimated_budget":
            return True
        return data.usage is not None and bool(data.usage.actions_items)

    @property
    def native_value(self) -> SensorValue:
        """Return a non-conflated billing value."""
        data = self.scope_data
        usage = data.usage
        budget = _single_actions_budget(data)
        if self._key == "billing_period":
            return usage.period.label if usage else None
        if self._key == "actions_billable_usage":
            return _common_quantity(
                usage.actions_items if usage else (), "net_quantity"
            )
        if self._key == "actions_discounted_usage":
            return _common_quantity(
                usage.actions_items if usage else (), "discount_quantity"
            )
        if self._key == "actions_gross_cost":
            return (
                _sum_decimal(item.gross_amount for item in usage.actions_items)
                if usage
                else None
            )
        if self._key == "actions_discount":
            return (
                _sum_decimal(item.discount_amount for item in usage.actions_items)
                if usage
                else None
            )
        if self._key == "actions_cost":
            return (
                _sum_decimal(item.net_amount for item in usage.actions_items)
                if usage
                else None
            )
        if self._key == "actions_budget_count":
            return len(_actions_budgets(data))
        if self._key == "actions_budget":
            return budget.amount if budget else None
        if self._key == "actions_budget_remaining":
            return budget.remaining_amount if budget else None
        if self._key == "actions_budget_percent":
            return budget.used_percent if budget else None
        runner = str(
            self.coordinator.config_entry.options.get(
                CONF_REFERENCE_RUNNER, DEFAULT_REFERENCE_RUNNER
            )
        )
        price = Decimal(REFERENCE_RUNNER_PRICES[runner])
        if self._key == "actions_estimated_minutes_remaining":
            return (
                (budget.remaining_amount / price).quantize(Decimal("1"))
                if budget
                else None
            )
        if self._key == "actions_estimated_budget":
            minutes = int(
                self.coordinator.config_entry.options.get(
                    CONF_ESTIMATED_MINUTES, DEFAULT_ESTIMATED_MINUTES
                )
            )
            return (Decimal(minutes) * price).quantize(Decimal("0.01"))
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return bounded provenance and breakdown metadata."""
        data = self.scope_data
        usage = data.usage
        attributes: dict[str, Any] = {
            ATTR_FRESHNESS: self.coordinator.data.fetched_at.isoformat(),
            ATTR_SOURCE: "GitHub enhanced billing API",
            "scope": data.scope.scope_type.value,
            "scope_name": data.scope.name,
            "currency": "USD",
        }
        if self._key.startswith("actions_estimated"):
            runner = str(
                self.coordinator.config_entry.options.get(
                    CONF_REFERENCE_RUNNER, DEFAULT_REFERENCE_RUNNER
                )
            )
            attributes.update(
                {
                    ATTR_DATA_CLASS: DataClass.ESTIMATED,
                    "reference_runner": runner,
                    "price_per_minute": REFERENCE_RUNNER_PRICES[runner],
                    "estimate_warning": (
                        "Estimate only; runner mix, included usage, discounts, "
                        "taxes, and price changes can alter billed consumption."
                    ),
                }
            )
        else:
            attributes[ATTR_DATA_CLASS] = DataClass.AUTHORITATIVE
        if usage and self._key in {
            "actions_billable_usage",
            "actions_discounted_usage",
            "actions_gross_cost",
            "actions_discount",
            "actions_cost",
        }:
            attributes["sku_breakdown"] = [
                _usage_item_attributes(item) for item in usage.actions_items
            ]
            attributes["repository_breakdown"] = _repository_breakdown(
                usage.detail_items
            )
            attributes["unavailable_sections"] = usage.unavailable_sections
        if self._key.startswith("actions_budget"):
            attributes["budgets"] = [
                {
                    "id": budget.id,
                    "scope": budget.budget_scope,
                    "entity_name": budget.entity_name,
                    "product_sku": budget.product_sku,
                    "amount": str(budget.amount),
                    "consumed_amount": str(budget.consumed_amount),
                    "prevent_further_usage": budget.prevent_further_usage,
                }
                for budget in _actions_budgets(data)
            ]
            if len(_actions_budgets(data)) > 1:
                attributes["availability_note"] = (
                    "Amount sensors are unavailable because overlapping Actions "
                    "budgets cannot be safely aggregated."
                )
        return attributes

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the authoritative quantity unit when it is unambiguous."""
        if self._key in {"actions_billable_usage", "actions_discounted_usage"}:
            usage = self.scope_data.usage
            if usage:
                units = {item.unit_type for item in usage.actions_items}
                if len(units) == 1:
                    return next(iter(units))
            return None
        return self._attr_native_unit_of_measurement


def _actions_budgets(data: BillingScopeData) -> tuple[BillingBudget, ...]:
    return tuple(budget for budget in data.budgets if budget.is_actions)


def _single_actions_budget(data: BillingScopeData) -> BillingBudget | None:
    budgets = _actions_budgets(data)
    return budgets[0] if len(budgets) == 1 else None


def _sum_decimal(values: Any) -> Decimal:
    return sum(values, start=Decimal())


def _common_quantity(
    items: tuple[BillingUsageItem, ...],
    attribute: str,
) -> Decimal | None:
    if not items or len({item.unit_type for item in items}) != 1:
        return None
    values = (getattr(item, attribute) for item in items)
    return _sum_decimal(value for value in values if value is not None)


def _usage_item_attributes(item: BillingUsageItem) -> dict[str, str]:
    return {
        "sku": item.sku,
        "unit_type": item.unit_type,
        "price_per_unit": str(item.price_per_unit),
        "gross_quantity": str(item.gross_quantity),
        "discount_quantity": str(item.discount_quantity),
        "net_quantity": str(item.net_quantity),
        "gross_amount": str(item.gross_amount),
        "discount_amount": str(item.discount_amount),
        "net_amount": str(item.net_amount),
    }


def _repository_breakdown(
    items: tuple[BillingUsageItem, ...],
) -> list[dict[str, str]]:
    totals: dict[str, Decimal] = {}
    for item in items:
        if item.product.casefold() not in {"actions", "github actions"}:
            continue
        repository = item.repository_name or "unattributed"
        totals[repository] = totals.get(repository, Decimal()) + item.net_amount
    return [
        {"repository": repository, "net_amount": str(amount)}
        for repository, amount in sorted(totals.items())
    ]
