"""Config-entry option normalization for GitHub Insights."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    CONF_ACTIONS_INCLUDED_MINUTES,
    CONF_BILLING_INTERVAL,
    CONF_BUDGET_CRITICAL_THRESHOLD,
    CONF_BUDGET_WARNING_THRESHOLD,
    CONF_ESTIMATED_MINUTES,
    CONF_MAX_REPOSITORIES,
    CONF_UPDATE_INTERVAL,
)

INTEGER_OPTION_KEYS = (
    CONF_UPDATE_INTERVAL,
    CONF_BILLING_INTERVAL,
    CONF_MAX_REPOSITORIES,
    CONF_ESTIMATED_MINUTES,
    CONF_ACTIONS_INCLUDED_MINUTES,
    CONF_BUDGET_WARNING_THRESHOLD,
    CONF_BUDGET_CRITICAL_THRESHOLD,
)


def integer_option(
    options: Mapping[str, Any],
    key: str,
    default: int,
) -> int:
    """Return an integer-valued option from Home Assistant selector output."""
    value = options.get(key, default)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return default


def normalize_integer_options(options: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize present integer-valued NumberSelector options."""
    normalized = dict(options)
    for key in INTEGER_OPTION_KEYS:
        value = normalized.get(key)
        if (
            isinstance(value, float)
            and value.is_integer()
            and not isinstance(value, bool)
        ):
            normalized[key] = int(value)
    return normalized
