"""Constants for GitHub Insights."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "github_insights"
NAME: Final = "GitHub Insights"
VERSION: Final = "0.2.0-beta.1"

PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONF_SERVER: Final = "server"
CONF_TOKEN: Final = "token"
CONF_ACCOUNT_ID: Final = "account_id"
CONF_ACCOUNT_LOGIN: Final = "account_login"
CONF_ORGANIZATIONS: Final = "organizations"
CONF_REPOSITORIES: Final = "repositories"
CONF_AUTO_DISCOVER: Final = "auto_discover"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_BILLING_INTERVAL: Final = "billing_interval"
CONF_PERSONAL_BILLING: Final = "personal_billing"
CONF_BILLING_ORGANIZATIONS: Final = "billing_organizations"
CONF_BILLING_ENTERPRISE: Final = "billing_enterprise"
CONF_BUDGET_MANAGEMENT: Final = "budget_management"
CONF_REFERENCE_RUNNER: Final = "reference_runner"
CONF_ESTIMATED_MINUTES: Final = "estimated_minutes"
CONF_ACTIONS_INCLUDED_MINUTES: Final = "actions_included_minutes"
CONF_BUDGET_WARNING_THRESHOLD: Final = "budget_warning_threshold"
CONF_BUDGET_CRITICAL_THRESHOLD: Final = "budget_critical_threshold"
CONF_INCLUDE_ARCHIVED: Final = "include_archived"
CONF_INCLUDE_FORKS: Final = "include_forks"
CONF_ENABLED_CATEGORIES: Final = "enabled_categories"
CONF_MAX_REPOSITORIES: Final = "max_repositories"

DEFAULT_SERVER: Final = "https://github.com"
DEFAULT_AUTO_DISCOVER: Final = True
DEFAULT_INCLUDE_ARCHIVED: Final = False
DEFAULT_INCLUDE_FORKS: Final = True
DEFAULT_ENABLED_CATEGORIES: Final = (
    "repositories",
    "workflows",
    "releases",
    "activity",
    "deployments",
)
DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 15
DEFAULT_BILLING_INTERVAL_MINUTES: Final = 60
DEFAULT_PERSONAL_BILLING: Final = True
DEFAULT_BUDGET_MANAGEMENT: Final = False
DEFAULT_REFERENCE_RUNNER: Final = "linux_standard"
DEFAULT_ESTIMATED_MINUTES: Final = 1000
DEFAULT_ACTIONS_INCLUDED_MINUTES: Final = 0
DEFAULT_BUDGET_WARNING_THRESHOLD: Final = 75
DEFAULT_BUDGET_CRITICAL_THRESHOLD: Final = 90
MIN_UPDATE_INTERVAL_MINUTES: Final = 5
MAX_UPDATE_INTERVAL_MINUTES: Final = 360
MIN_BILLING_INTERVAL_MINUTES: Final = 30
MAX_BILLING_INTERVAL_MINUTES: Final = 1440
MAX_DISCOVERED_REPOSITORIES: Final = 100
API_VERSION: Final = "2026-03-10"
MAX_BUDGET_PAGES: Final = 10

SERVICE_CREATE_BUDGET: Final = "create_budget"
SERVICE_UPDATE_BUDGET: Final = "update_budget"
SERVICE_DELETE_BUDGET: Final = "delete_budget"
SERVICE_SET_STOP_USAGE: Final = "set_stop_usage"

REFERENCE_RUNNER_PRICES: Final[dict[str, str]] = {
    "linux_standard": "0.008",
    "windows_standard": "0.016",
    "macos_standard": "0.080",
}
MIN_SELECTED_REPOSITORIES: Final = 1
MAX_SELECTED_REPOSITORIES: Final = 50
DEFAULT_MAX_REPOSITORIES: Final = 10
MAX_ACTIVITY_ITEMS: Final = 1000
MAX_RECENT_WORKFLOW_RUNS: Final = 20
MAX_SECURITY_ALERTS: Final = 1000
API_VERSION_DOTCOM: Final = "2026-03-10"
API_VERSION_GHES: Final = "2022-11-28"

ATTR_DATA_CLASS: Final = "data_class"
ATTR_FRESHNESS: Final = "freshness"
ATTR_SOURCE: Final = "source"

DEFAULT_UPDATE_INTERVAL: Final = timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES)

LOGGER = logging.getLogger(__package__)
