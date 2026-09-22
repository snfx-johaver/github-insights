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
from .entity import (
    GitHubInsightsBillingEntity,
    GitHubInsightsEntity,
    GitHubRepositoryEntity,
)
from .models import (
    BillingBudget,
    BillingScopeData,
    BillingUsageItem,
    DataClass,
    GitHubCopilotUsage,
    GitHubRepositoryInsights,
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
        attributes_fn=lambda snapshot: _account_attributes(snapshot),
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


@dataclass(frozen=True, kw_only=True)
class GitHubRepositorySensorDescription(SensorEntityDescription):
    """Describe a repository sensor."""

    value_fn: Callable[[GitHubRepositoryInsights], SensorValue]
    available_fn: Callable[[GitHubRepositoryInsights], bool] = lambda item: True
    attributes_fn: Callable[[GitHubRepositoryInsights], Mapping[str, Any] | None] = (
        lambda item: None
    )


def _activity_available(
    attribute: str,
) -> Callable[[GitHubRepositoryInsights], bool]:
    """Return an availability predicate for one activity metric."""

    def available(item: GitHubRepositoryInsights) -> bool:
        activity = item.activity
        return activity is not None and getattr(activity, attribute) is not None

    return available


def _activity_value(
    attribute: str,
) -> Callable[[GitHubRepositoryInsights], SensorValue]:
    """Return a typed value getter for one activity metric."""

    def value(item: GitHubRepositoryInsights) -> SensorValue:
        activity = item.activity
        if activity is None:
            return None
        result = getattr(activity, attribute)
        return result if isinstance(result, int) else None

    return value


REPOSITORY_SENSORS: tuple[GitHubRepositorySensorDescription, ...] = (
    GitHubRepositorySensorDescription(
        key="stars",
        translation_key="stars",
        native_unit_of_measurement="stars",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda item: item.repository.stargazers_count,
    ),
    GitHubRepositorySensorDescription(
        key="forks",
        translation_key="forks",
        native_unit_of_measurement="forks",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda item: item.repository.forks_count,
    ),
    GitHubRepositorySensorDescription(
        key="open_issues",
        translation_key="open_issues",
        native_unit_of_measurement="issues",
        state_class=SensorStateClass.MEASUREMENT,
        available_fn=lambda item: item.open_issues is not None,
        value_fn=lambda item: item.open_issues,
        attributes_fn=lambda item: _repository_attributes(item),
    ),
    GitHubRepositorySensorDescription(
        key="open_pull_requests",
        translation_key="open_pull_requests",
        native_unit_of_measurement="pull requests",
        state_class=SensorStateClass.MEASUREMENT,
        available_fn=lambda item: item.open_pull_requests is not None,
        value_fn=lambda item: item.open_pull_requests,
    ),
    GitHubRepositorySensorDescription(
        key="workflow_health",
        translation_key="workflow_health",
        available_fn=lambda item: "workflows" in item.capabilities,
        value_fn=lambda item: item.workflow_status or "no_runs",
        attributes_fn=lambda item: {
            "recent_runs": [
                {
                    "name": run.name,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "url": run.html_url,
                    "runtime_seconds": run.runtime_seconds,
                    "job_runtime_seconds": run.job_runtime_seconds,
                    "jobs": run.jobs,
                }
                for run in item.workflow_runs[:10]
            ]
        },
    ),
    GitHubRepositorySensorDescription(
        key="deployment_status",
        translation_key="deployment_status",
        available_fn=lambda item: item.deployment is not None,
        value_fn=lambda item: (
            item.deployment.state or "unknown" if item.deployment else None
        ),
        attributes_fn=lambda item: (
            {
                "environment": item.deployment.environment,
                "created_at": item.deployment.created_at.isoformat(),
                "url": item.deployment.html_url,
                "environments": list(item.environments),
            }
            if item.deployment
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="latest_release",
        translation_key="latest_release",
        available_fn=lambda item: item.latest_release is not None,
        value_fn=lambda item: (
            item.latest_release.title if item.latest_release else None
        ),
        attributes_fn=lambda item: (
            {
                "url": item.latest_release.html_url,
                "published_at": item.latest_release.created_at.isoformat(),
            }
            if item.latest_release
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="latest_commit",
        translation_key="latest_commit",
        device_class=SensorDeviceClass.TIMESTAMP,
        available_fn=lambda item: item.latest_commit is not None,
        value_fn=lambda item: (
            item.latest_commit.committed_at if item.latest_commit else None
        ),
        attributes_fn=lambda item: (
            {
                "sha": item.latest_commit.sha,
                "message": item.latest_commit.message,
                "author": item.latest_commit.author,
                "url": item.latest_commit.html_url,
            }
            if item.latest_commit
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="latest_issue",
        translation_key="latest_issue",
        entity_registry_enabled_default=False,
        available_fn=lambda item: item.latest_issue is not None,
        value_fn=lambda item: item.latest_issue.title if item.latest_issue else None,
        attributes_fn=lambda item: (
            {
                "number": item.latest_issue.number,
                "author": item.latest_issue.author,
                "state": item.latest_issue.state,
                "url": item.latest_issue.html_url,
                "created_at": item.latest_issue.created_at.isoformat(),
            }
            if item.latest_issue
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="latest_pull_request",
        translation_key="latest_pull_request",
        entity_registry_enabled_default=False,
        available_fn=lambda item: item.latest_pull_request is not None,
        value_fn=lambda item: (
            item.latest_pull_request.title if item.latest_pull_request else None
        ),
        attributes_fn=lambda item: (
            {
                "number": item.latest_pull_request.number,
                "author": item.latest_pull_request.author,
                "state": item.latest_pull_request.state,
                "url": item.latest_pull_request.html_url,
                "created_at": item.latest_pull_request.created_at.isoformat(),
            }
            if item.latest_pull_request
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="activity_90d",
        translation_key="repository_activity_90d",
        native_unit_of_measurement="events",
        state_class=SensorStateClass.MEASUREMENT,
        available_fn=lambda item: item.activity is not None,
        value_fn=lambda item: (
            item.activity.commits
            + item.activity.pull_requests_opened
            + item.activity.issues_opened
            + item.activity.releases
            if item.activity
            else None
        ),
        attributes_fn=lambda item: (
            {
                "commits": item.activity.commits,
                "pull_requests_opened": item.activity.pull_requests_opened,
                "pull_requests_merged": item.activity.pull_requests_merged,
                "issues_opened": item.activity.issues_opened,
                "issues_closed": item.activity.issues_closed,
                "releases": item.activity.releases,
                "period_totals": dict(item.activity.period_totals),
                "weekday_distribution": dict(item.activity.weekday_distribution),
                "coverage_days": item.activity.coverage_days,
                "coverage_complete": item.activity.coverage_complete,
            }
            if item.activity
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="current_activity_streak",
        translation_key="repository_current_activity_streak",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        available_fn=lambda item: (
            item.activity is not None and item.activity.current_streak is not None
        ),
        value_fn=lambda item: item.activity.current_streak if item.activity else None,
    ),
    GitHubRepositorySensorDescription(
        key="traffic_views",
        translation_key="traffic_views",
        native_unit_of_measurement="views",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        available_fn=lambda item: item.traffic is not None,
        value_fn=lambda item: item.traffic.views if item.traffic else None,
        attributes_fn=lambda item: (
            {
                "unique_visitors": item.traffic.unique_visitors,
                "clones": item.traffic.clones,
                "unique_cloners": item.traffic.unique_cloners,
                "referrers": [referrer.title for referrer in item.traffic.referrers],
                "popular_content": [
                    content.title for content in item.traffic.popular_paths
                ],
            }
            if item.traffic
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="dependabot_alerts",
        translation_key="dependabot_alerts",
        native_unit_of_measurement="alerts",
        state_class=SensorStateClass.MEASUREMENT,
        available_fn=lambda item: (
            item.security is not None and item.security.dependabot is not None
        ),
        value_fn=lambda item: item.security.dependabot if item.security else None,
    ),
    GitHubRepositorySensorDescription(
        key="code_scanning_alerts",
        translation_key="code_scanning_alerts",
        native_unit_of_measurement="alerts",
        state_class=SensorStateClass.MEASUREMENT,
        available_fn=lambda item: (
            item.security is not None and item.security.code_scanning is not None
        ),
        value_fn=lambda item: item.security.code_scanning if item.security else None,
        attributes_fn=lambda item: (
            {
                "severity": dict(item.security.severity),
            }
            if item.security
            else None
        ),
    ),
    GitHubRepositorySensorDescription(
        key="secret_scanning_alerts",
        translation_key="secret_scanning_alerts",
        native_unit_of_measurement="alerts",
        state_class=SensorStateClass.MEASUREMENT,
        available_fn=lambda item: (
            item.security is not None and item.security.secret_scanning is not None
        ),
        value_fn=lambda item: item.security.secret_scanning if item.security else None,
    ),
    *tuple(
        GitHubRepositorySensorDescription(
            key=key,
            translation_key=key,
            native_unit_of_measurement=unit,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=enabled,
            available_fn=_activity_available(attribute),
            value_fn=_activity_value(attribute),
        )
        for key, attribute, unit, enabled in (
            ("commits", "commits", "commits", True),
            ("pull_requests_opened", "pull_requests_opened", "pull requests", True),
            ("pull_requests_merged", "pull_requests_merged", "pull requests", False),
            ("issues_opened", "issues_opened", "issues", True),
            ("reviews", "reviews", "reviews", False),
            ("releases", "releases", "releases", False),
            ("current_streak", "current_streak", "days", False),
            ("longest_streak", "longest_streak", "days", False),
        )
    ),
    GitHubRepositorySensorDescription(
        key="contributions",
        translation_key="contributions",
        native_unit_of_measurement="events",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        available_fn=lambda item: item.activity is not None,
        value_fn=lambda item: (
            item.activity.commits
            + item.activity.pull_requests_opened
            + item.activity.issues_opened
            + item.activity.releases
            if item.activity
            else None
        ),
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
    known: set[str] = set()

    def add_discovered_entities() -> None:
        entities: list[SensorEntity] = []
        for repository in coordinator.data.repository_insights:
            for description in REPOSITORY_SENSORS:
                unique_key = f"repository:{repository.repository.id}:{description.key}"
                if unique_key in known or not _repository_sensor_supported(
                    repository, description.key
                ):
                    continue
                known.add(unique_key)
                entities.append(
                    GitHubRepositorySensor(
                        coordinator,
                        repository.repository.id,
                        description,
                    )
                )
        for usage in coordinator.data.copilot:
            for key, attribute in (
                ("copilot_premium_requests_used", "premium_requests_used"),
                ("copilot_paid_usage", "premium_requests_paid"),
                ("copilot_ai_credits_used", "ai_credits_used"),
                ("copilot_cost", "cost"),
                ("copilot_active_users", "active_users"),
                ("copilot_engaged_users", "engaged_users"),
                ("copilot_coding_agent_pull_requests", "coding_agent_pull_requests"),
                (
                    "copilot_coding_agent_merged_pull_requests",
                    "coding_agent_merged_pull_requests",
                ),
                ("copilot_code_review_pull_requests", "code_review_pull_requests"),
            ):
                unique_key = f"copilot:{usage.scope_type}:{usage.scope_id}:{key}"
                if unique_key in known or getattr(usage, attribute) is None:
                    continue
                known.add(unique_key)
                entities.append(
                    GitHubCopilotSensor(
                        coordinator,
                        usage,
                        key,
                        attribute,
                    )
                )
        if entities:
            async_add_entities(entities)

    add_discovered_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_discovered_entities))


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


class GitHubRepositorySensor(GitHubRepositoryEntity, SensorEntity):
    """A coordinator-backed repository sensor."""

    entity_description: GitHubRepositorySensorDescription

    def __init__(
        self,
        coordinator: GitHubInsightsCoordinator,
        repository_id: int,
        description: GitHubRepositorySensorDescription,
    ) -> None:
        """Initialize a repository sensor."""
        super().__init__(coordinator, repository_id, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return whether the repository metric is available."""
        item = self.repository_data
        return (
            super().available
            and item is not None
            and self.entity_description.available_fn(item)
        )

    @property
    def native_value(self) -> SensorValue:
        """Return the current repository metric."""
        item = self.repository_data
        return self.entity_description.value_fn(item) if item else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return bounded repository metadata and provenance."""
        item = self.repository_data
        if item is None:
            return None
        attributes = dict(self.entity_description.attributes_fn(item) or {})
        attributes.update(
            {
                ATTR_DATA_CLASS: DataClass.AUTHORITATIVE,
                ATTR_FRESHNESS: self.coordinator.data.fetched_at.isoformat(),
                ATTR_SOURCE: "GitHub API",
            }
        )
        return attributes


def _repository_sensor_supported(item: GitHubRepositoryInsights, key: str) -> bool:
    """Avoid creating entities for structurally unavailable capabilities."""
    capability_by_key = {
        "workflow_health": "workflows",
        "deployment_status": "deployments",
        "latest_release": "releases",
        "latest_commit": "commits",
        "latest_issue": "issues",
        "latest_pull_request": "pull_requests",
        "activity_90d": "activity",
        "current_activity_streak": "activity",
        "traffic_views": "traffic",
        "dependabot_alerts": "security",
        "code_scanning_alerts": "security",
        "secret_scanning_alerts": "security",
        "commits": "activity",
        "pull_requests_opened": "activity",
        "pull_requests_merged": "activity",
        "issues_opened": "activity",
        "reviews": "activity",
        "releases": "activity",
        "current_streak": "activity",
        "longest_streak": "activity",
        "contributions": "activity",
    }
    capability = capability_by_key.get(key)
    if capability == "security":
        return item.security is not None
    if capability is None:
        return True
    return capability in item.capabilities


def _repository_attributes(item: GitHubRepositoryInsights) -> Mapping[str, Any]:
    """Return bounded repository summary attributes."""
    repository = item.repository
    return {
        "name": repository.name,
        "full_name": repository.full_name,
        "description": repository.description,
        "url": repository.html_url,
        "visibility": repository.visibility,
        "default_branch": repository.default_branch,
        "language": repository.language,
        "license": repository.license_name,
        "archived": repository.archived,
        "fork": repository.fork,
        "discussions_enabled": repository.has_discussions,
        "last_push": (
            repository.pushed_at.isoformat() if repository.pushed_at else None
        ),
        "size_kb": repository.size_kb,
        "latest_commit": (
            {
                "sha": item.latest_commit.sha,
                "message": item.latest_commit.message,
                "url": item.latest_commit.html_url,
                "committed_at": item.latest_commit.committed_at.isoformat(),
            }
            if item.latest_commit
            else None
        ),
        "latest_issue": (
            {
                "number": item.latest_issue.number,
                "title": item.latest_issue.title,
                "url": item.latest_issue.html_url,
            }
            if item.latest_issue
            else None
        ),
        "latest_pull_request": (
            {
                "number": item.latest_pull_request.number,
                "title": item.latest_pull_request.title,
                "url": item.latest_pull_request.html_url,
            }
            if item.latest_pull_request
            else None
        ),
    }


def _account_attributes(snapshot: GitHubSnapshot) -> Mapping[str, Any]:
    """Return bounded account, repository, and activity summary attributes."""
    languages: dict[str, int] = {}
    activity_by_repository: dict[str, int] = {}
    for item in snapshot.repository_insights:
        language = item.repository.language
        if language:
            languages[language] = languages.get(language, 0) + 1
        if item.activity:
            activity_by_repository[item.repository.full_name] = (
                item.activity.period_totals.get(30, 0)
            )
    return {
        "display_name": snapshot.account.name,
        "avatar_url": snapshot.account.avatar_url,
        "url": snapshot.account.html_url,
        "organizations": len(snapshot.organizations),
        "discovered_repositories": len(snapshot.repositories),
        "monitored_repositories": len(snapshot.repository_insights),
        "language_distribution": languages,
        "activity_by_repository_30d": activity_by_repository,
    }


class GitHubCopilotSensor(GitHubInsightsEntity, SensorEntity):
    """Official Copilot billing sensor for one GitHub billing scope."""

    def __init__(
        self,
        coordinator: GitHubInsightsCoordinator,
        usage: GitHubCopilotUsage,
        key: str,
        value_attribute: str,
    ) -> None:
        """Initialize a Copilot billing sensor."""
        super().__init__(
            coordinator,
            f"copilot_{usage.scope_type}_{usage.scope_id}_{key}",
        )
        self.scope = usage.scope
        self.scope_id = usage.scope_id
        self.scope_type = usage.scope_type
        self.key = key
        self.value_attribute = value_attribute
        self._attr_translation_key = key
        if key in {"copilot_premium_requests_used", "copilot_paid_usage"}:
            self._attr_native_unit_of_measurement = "requests"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "copilot_ai_credits_used":
            self._attr_native_unit_of_measurement = "credits"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key in {"copilot_active_users", "copilot_engaged_users"}:
            self._attr_native_unit_of_measurement = "users"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key in {
            "copilot_coding_agent_pull_requests",
            "copilot_coding_agent_merged_pull_requests",
            "copilot_code_review_pull_requests",
        }:
            self._attr_native_unit_of_measurement = "pull requests"
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def usage(self) -> GitHubCopilotUsage | None:
        """Return current usage for this scope."""
        return next(
            (
                usage
                for usage in self.coordinator.data.copilot
                if usage.scope_id == self.scope_id
                and usage.scope_type == self.scope_type
            ),
            None,
        )

    @property
    def available(self) -> bool:
        """Return whether the official billing value is available."""
        usage = self.usage
        return (
            super().available
            and usage is not None
            and getattr(usage, self.value_attribute) is not None
        )

    @property
    def native_value(self) -> SensorValue:
        """Return the official billing value."""
        usage = self.usage
        value = getattr(usage, self.value_attribute) if usage else None
        return value if isinstance(value, int | float | str) else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return official breakdowns without signed URLs or credentials."""
        usage = self.usage
        return {
            "scope": self.scope,
            "paid_quantity": (usage.premium_requests_paid if usage else None),
            "product_breakdown": (dict(usage.product_breakdown) if usage else {}),
            "model_breakdown": dict(usage.model_breakdown) if usage else {},
            "repository_breakdown": (dict(usage.repository_breakdown) if usage else {}),
            "reporting_day": usage.reporting_day if usage else None,
            ATTR_DATA_CLASS: DataClass.AUTHORITATIVE,
            ATTR_FRESHNESS: self.coordinator.data.fetched_at.isoformat(),
            ATTR_SOURCE: "GitHub billing API",
        }
