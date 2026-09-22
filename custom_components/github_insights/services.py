"""Confirmed financial mutation services for GitHub Insights."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_BUDGET_MANAGEMENT,
    DOMAIN,
    SERVICE_CREATE_BUDGET,
    SERVICE_DELETE_BUDGET,
    SERVICE_SET_STOP_USAGE,
    SERVICE_UPDATE_BUDGET,
)
from .coordinator import GitHubInsightsConfigEntry
from .models import (
    BillingMutation,
    BillingScope,
    BillingScopeType,
    CapabilityStatus,
)

CONF_SCOPE_TYPE = "scope_type"
CONF_SCOPE_NAME = "scope_name"
CONF_BUDGET_ID = "budget_id"
CONF_BUDGET_AMOUNT = "budget_amount"
CONF_BUDGET_SCOPE = "budget_scope"
CONF_BUDGET_ENTITY_NAME = "budget_entity_name"
CONF_BUDGET_TYPE = "budget_type"
CONF_BUDGET_PRODUCT_SKU = "budget_product_sku"
CONF_PREVENT_FURTHER_USAGE = "prevent_further_usage"
CONF_WILL_ALERT = "will_alert"
CONF_ALERT_RECIPIENTS = "alert_recipients"
CONF_CONFIRMATION = "confirmation"

_SCOPE_SCHEMA: dict[Any, Any] = {
    vol.Required(CONF_SCOPE_TYPE): vol.In(
        [BillingScopeType.ORGANIZATION.value, BillingScopeType.ENTERPRISE.value]
    ),
    vol.Required(CONF_SCOPE_NAME): cv.string,
}

CREATE_SCHEMA = vol.Schema(
    {
        **_SCOPE_SCHEMA,
        vol.Required(CONF_BUDGET_AMOUNT): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required(CONF_BUDGET_SCOPE): vol.In(
            [
                "enterprise",
                "organization",
                "repository",
                "cost_center",
                "multi_user_customer",
                "multi_user_cost_center",
                "user",
            ]
        ),
        vol.Optional(CONF_BUDGET_ENTITY_NAME, default=""): cv.string,
        vol.Required(CONF_BUDGET_TYPE): vol.In(
            ["BundlePricing", "ProductPricing", "SkuPricing"]
        ),
        vol.Required(CONF_BUDGET_PRODUCT_SKU): cv.string,
        vol.Required(CONF_PREVENT_FURTHER_USAGE): cv.boolean,
        vol.Optional(CONF_WILL_ALERT, default=False): cv.boolean,
        vol.Optional(CONF_ALERT_RECIPIENTS, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Required(CONF_CONFIRMATION): cv.string,
    }
)

UPDATE_SCHEMA = vol.Schema(
    {
        **_SCOPE_SCHEMA,
        vol.Required(CONF_BUDGET_ID): cv.string,
        vol.Optional(CONF_BUDGET_AMOUNT): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(CONF_PREVENT_FURTHER_USAGE): cv.boolean,
        vol.Optional(CONF_WILL_ALERT): cv.boolean,
        vol.Optional(CONF_ALERT_RECIPIENTS): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(CONF_CONFIRMATION): cv.string,
    }
)

DELETE_SCHEMA = vol.Schema(
    {
        **_SCOPE_SCHEMA,
        vol.Required(CONF_BUDGET_ID): cv.string,
        vol.Required(CONF_CONFIRMATION): cv.string,
    }
)

STOP_USAGE_SCHEMA = vol.Schema(
    {
        **_SCOPE_SCHEMA,
        vol.Required(CONF_BUDGET_ID): cv.string,
        vol.Required(CONF_PREVENT_FURTHER_USAGE): cv.boolean,
        vol.Required(CONF_CONFIRMATION): cv.string,
    }
)


async def async_register_services(hass: HomeAssistant) -> None:
    """Register confirmed budget services once."""
    if hass.services.has_service(DOMAIN, SERVICE_CREATE_BUDGET):
        return

    async def async_create(call: ServiceCall) -> None:
        entry = _active_entry(hass)
        scope = _scope(call)
        _require_budget_capability(entry, scope)
        payload = {
            CONF_BUDGET_AMOUNT: call.data[CONF_BUDGET_AMOUNT],
            CONF_PREVENT_FURTHER_USAGE: call.data[CONF_PREVENT_FURTHER_USAGE],
            "budget_alerting": {
                CONF_WILL_ALERT: call.data[CONF_WILL_ALERT],
                CONF_ALERT_RECIPIENTS: call.data[CONF_ALERT_RECIPIENTS],
            },
            CONF_BUDGET_SCOPE: call.data[CONF_BUDGET_SCOPE],
            CONF_BUDGET_ENTITY_NAME: call.data[CONF_BUDGET_ENTITY_NAME],
            CONF_BUDGET_TYPE: call.data[CONF_BUDGET_TYPE],
            CONF_BUDGET_PRODUCT_SKU: call.data[CONF_BUDGET_PRODUCT_SKU],
        }
        expected = _create_confirmation(scope, payload)
        _require_confirmation(call, expected)
        budget = await entry.runtime_data.client.async_create_budget(scope, payload)
        await _refresh_after_mutation(entry, SERVICE_CREATE_BUDGET, scope, budget.id)

    async def async_update(call: ServiceCall) -> None:
        entry = _active_entry(hass)
        scope = _scope(call)
        _require_budget_capability(entry, scope)
        budget_id = str(call.data[CONF_BUDGET_ID])
        payload = {
            key: call.data[key]
            for key in (
                CONF_BUDGET_AMOUNT,
                CONF_PREVENT_FURTHER_USAGE,
            )
            if key in call.data
        }
        if CONF_WILL_ALERT in call.data or CONF_ALERT_RECIPIENTS in call.data:
            payload["budget_alerting"] = {
                key: call.data[key]
                for key in (CONF_WILL_ALERT, CONF_ALERT_RECIPIENTS)
                if key in call.data
            }
        expected = _update_confirmation(scope, budget_id, payload)
        _require_confirmation(call, expected)
        await entry.runtime_data.client.async_update_budget(scope, budget_id, payload)
        await _refresh_after_mutation(entry, SERVICE_UPDATE_BUDGET, scope, budget_id)

    async def async_delete(call: ServiceCall) -> None:
        entry = _active_entry(hass)
        scope = _scope(call)
        _require_budget_capability(entry, scope)
        budget_id = str(call.data[CONF_BUDGET_ID])
        _require_confirmation(
            call,
            f"DELETE BUDGET {budget_id} FROM {scope.scope_type.value} {scope.name}",
        )
        await entry.runtime_data.client.async_delete_budget(scope, budget_id)
        await _refresh_after_mutation(entry, SERVICE_DELETE_BUDGET, scope, budget_id)

    async def async_set_stop_usage(call: ServiceCall) -> None:
        entry = _active_entry(hass)
        scope = _scope(call)
        _require_budget_capability(entry, scope)
        budget_id = str(call.data[CONF_BUDGET_ID])
        enabled = bool(call.data[CONF_PREVENT_FURTHER_USAGE])
        verb = "ENABLE" if enabled else "DISABLE"
        _require_confirmation(
            call,
            f"{verb} STOP USAGE FOR BUDGET {budget_id} ON "
            f"{scope.scope_type.value} {scope.name}",
        )
        await entry.runtime_data.client.async_update_budget(
            scope,
            budget_id,
            {CONF_PREVENT_FURTHER_USAGE: enabled},
        )
        await _refresh_after_mutation(entry, SERVICE_SET_STOP_USAGE, scope, budget_id)

    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_BUDGET, async_create, schema=CREATE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_BUDGET, async_update, schema=UPDATE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_BUDGET, async_delete, schema=DELETE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_STOP_USAGE, async_set_stop_usage, schema=STOP_USAGE_SCHEMA
    )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Remove services when the single config entry unloads."""
    for service in (
        SERVICE_CREATE_BUDGET,
        SERVICE_UPDATE_BUDGET,
        SERVICE_DELETE_BUDGET,
        SERVICE_SET_STOP_USAGE,
    ):
        hass.services.async_remove(DOMAIN, service)


def _active_entry(hass: HomeAssistant) -> GitHubInsightsConfigEntry:
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise HomeAssistantError("GitHub Insights is not configured")
    entry = entries[0]
    if entry.state is not ConfigEntryState.LOADED:
        raise HomeAssistantError("GitHub Insights is not loaded")
    typed_entry = entry
    if not typed_entry.options.get(CONF_BUDGET_MANAGEMENT, False):
        raise HomeAssistantError(
            "Budget management is disabled; enable it in integration options first"
        )
    return typed_entry


def _scope(call: ServiceCall) -> BillingScope:
    scope = BillingScope(
        BillingScopeType(str(call.data[CONF_SCOPE_TYPE])),
        str(call.data[CONF_SCOPE_NAME]).strip(),
    )
    if not scope.name:
        raise HomeAssistantError("Billing scope name cannot be empty")
    return scope


def _require_confirmation(call: ServiceCall, expected: str) -> None:
    if call.data[CONF_CONFIRMATION] != expected:
        raise HomeAssistantError(f"Confirmation must exactly match: {expected}")


def _require_budget_capability(
    entry: GitHubInsightsConfigEntry, scope: BillingScope
) -> None:
    scope_data = entry.runtime_data.billing_coordinator.data.scopes.get(scope.key)
    if scope_data is None:
        raise HomeAssistantError(
            "The requested billing scope is not configured in integration options"
        )
    if scope_data.budget_capability.status is not CapabilityStatus.AVAILABLE:
        reason = scope_data.budget_capability.reason or "missing_budget_permission"
        raise HomeAssistantError(f"Budget management is unavailable: {reason}")


def _create_confirmation(scope: BillingScope, payload: dict[str, Any]) -> str:
    return (
        f"CREATE {scope.scope_type.value} {scope.name} "
        f"{payload[CONF_BUDGET_SCOPE]} "
        f"{payload[CONF_BUDGET_ENTITY_NAME] or '-'} "
        f"{payload[CONF_BUDGET_PRODUCT_SKU]} "
        f"{payload[CONF_BUDGET_AMOUNT]} USD "
        f"stop={str(payload[CONF_PREVENT_FURTHER_USAGE]).lower()}"
    )


def _update_confirmation(
    scope: BillingScope, budget_id: str, payload: dict[str, Any]
) -> str:
    amount = payload.get(CONF_BUDGET_AMOUNT, "unchanged")
    stop = payload.get(CONF_PREVENT_FURTHER_USAGE, "unchanged")
    if isinstance(stop, bool):
        stop = str(stop).lower()
    return (
        f"UPDATE {scope.scope_type.value} {scope.name} BUDGET {budget_id} "
        f"amount={amount} USD stop={stop}"
    )


async def _refresh_after_mutation(
    entry: GitHubInsightsConfigEntry,
    action: str,
    scope: BillingScope,
    budget_id: str | None,
) -> None:
    coordinator = entry.runtime_data.billing_coordinator
    coordinator.record_mutation(
        BillingMutation(
            action=action,
            scope_key=scope.key,
            budget_id=budget_id,
            completed_at=datetime.now(UTC),
        )
    )
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise HomeAssistantError(
            "GitHub accepted the mutation, but authoritative read-back failed; "
            "the previous confirmed state was preserved"
        )


def estimate_budget_amount(minutes: int, price_per_minute: Decimal) -> Decimal:
    """Return an estimated monetary budget without implying exact enforcement."""
    return (Decimal(minutes) * price_per_minute).quantize(Decimal("0.01"))
