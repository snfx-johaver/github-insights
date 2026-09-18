"""Constants for GitHub Insights."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "github_insights"
NAME: Final = "GitHub Insights"
VERSION: Final = "0.1.0-beta.1"

PLATFORMS: Final = [Platform.SENSOR]

CONF_SERVER: Final = "server"
CONF_TOKEN: Final = "token"
CONF_ACCOUNT_ID: Final = "account_id"
CONF_ACCOUNT_LOGIN: Final = "account_login"
CONF_ORGANIZATIONS: Final = "organizations"
CONF_REPOSITORIES: Final = "repositories"
CONF_AUTO_DISCOVER: Final = "auto_discover"
CONF_UPDATE_INTERVAL: Final = "update_interval"

DEFAULT_SERVER: Final = "https://github.com"
DEFAULT_AUTO_DISCOVER: Final = True
DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 15
MIN_UPDATE_INTERVAL_MINUTES: Final = 5
MAX_UPDATE_INTERVAL_MINUTES: Final = 360
MAX_DISCOVERED_REPOSITORIES: Final = 100
API_VERSION: Final = "2022-11-28"

ATTR_DATA_CLASS: Final = "data_class"
ATTR_FRESHNESS: Final = "freshness"
ATTR_SOURCE: Final = "source"

DEFAULT_UPDATE_INTERVAL: Final = timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES)

LOGGER = logging.getLogger(__package__)
