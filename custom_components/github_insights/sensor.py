"""Sensor platform for GitHub Insights."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
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

from .const import ATTR_DATA_CLASS, ATTR_FRESHNESS, ATTR_SOURCE
from .coordinator import GitHubInsightsConfigEntry, GitHubInsightsCoordinator
from .entity import GitHubInsightsEntity
from .models import DataClass, GitHubSnapshot


@dataclass(frozen=True, kw_only=True)
class GitHubInsightsSensorDescription(SensorEntityDescription):
    """Describe a GitHub Insights sensor."""

    value_fn: Callable[[GitHubSnapshot], StateType]
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
    async_add_entities(
        GitHubInsightsSensor(coordinator, description) for description in SENSORS
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
    def native_value(self) -> StateType:
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
