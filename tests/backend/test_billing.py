"""Tests for enhanced billing, budgets, estimates, and safety boundaries."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest
import voluptuous as vol
from aiohttp import ClientSession
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from custom_components.github_insights.api import GitHubAPIError, GitHubClient
from custom_components.github_insights.binary_sensor import _budget_flags
from custom_components.github_insights.const import CONF_ACTIONS_INCLUDED_MINUTES
from custom_components.github_insights.coordinator import (
    _merge_billing_last_known_good,
)
from custom_components.github_insights.models import (
    BillingScope,
    BillingScopeType,
    CapabilityStatus,
    DataClass,
)
from custom_components.github_insights.repairs import (
    async_update_configured_allowance_issue,
)
from custom_components.github_insights.sensor import (
    GitHubInsightsBillingSensor,
    GitHubInsightsConfiguredAllowanceSensor,
)
from custom_components.github_insights.services import (
    CREATE_SCHEMA,
    _create_confirmation,
    _require_confirmation,
    _update_confirmation,
    estimate_budget_amount,
)

from .helpers import FakeResponse, FakeSession, billing_snapshot

DETAIL_USAGE = {
    "usageItems": [
        {
            "date": "2026-09-01",
            "product": "Actions",
            "sku": "actions_linux",
            "quantity": 1000,
            "unitType": "Minutes",
            "pricePerUnit": 0.008,
            "grossAmount": 8,
            "discountAmount": 2,
            "netAmount": 6,
            "repositoryName": "example-org/example",
        }
    ]
}

SUMMARY_USAGE = {
    "timePeriod": {"year": 2026, "month": 9},
    "usageItems": [
        {
            "product": "Actions",
            "sku": "actions_linux",
            "unitType": "Minutes",
            "pricePerUnit": 0.008,
            "grossQuantity": 1000,
            "grossAmount": 8,
            "discountQuantity": 250,
            "discountAmount": 2,
            "netQuantity": 750,
            "netAmount": 6,
        }
    ],
}

BUDGET = {
    "id": "budget-1",
    "budget_scope": "repository",
    "budget_entity_name": "example-org/example",
    "budget_type": "ProductPricing",
    "budget_product_sku": "Actions",
    "budget_amount": 100,
    "consumed_amount": 75.5,
    "prevent_further_usage": True,
    "budget_alerting": {
        "will_alert": True,
        "alert_recipients": ["billing@example.invalid"],
    },
    "created_at": "2026-09-01T00:00:00Z",
}


@pytest.mark.parametrize(
    ("scope", "expected_path"),
    [
        (
            BillingScope(BillingScopeType.USER, "octocat"),
            "/users/octocat/settings/billing/usage",
        ),
        (
            BillingScope(BillingScopeType.ORGANIZATION, "example-org"),
            "/organizations/example-org/settings/billing/usage",
        ),
        (
            BillingScope(BillingScopeType.ENTERPRISE, "example-enterprise"),
            "/enterprises/example-enterprise/settings/billing/usage",
        ),
    ],
)
async def test_usage_scopes_and_authoritative_schema(
    scope: BillingScope, expected_path: str
) -> None:
    """All documented scopes parse gross, discount, net, period, and repository."""
    session = FakeSession(
        FakeResponse(200, DETAIL_USAGE),
        FakeResponse(200, SUMMARY_USAGE),
    )
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.com"
    )

    report = await client.async_get_billing_usage(scope, year=2026, month=9)

    assert session.requests[0]["url"].endswith(expected_path)
    assert session.requests[1]["url"].endswith(f"{expected_path}/summary")
    assert report.period.label == "2026-09"
    assert report.currency == "USD"
    assert report.actions_items[0].gross_quantity == Decimal("1000")
    assert report.actions_items[0].discount_quantity == Decimal("250")
    assert report.actions_items[0].net_amount == Decimal("6")
    assert report.detail_items[0].repository_name == "example-org/example"


async def test_usage_summary_failure_preserves_detailed_report() -> None:
    """A preview-summary failure does not suppress authoritative detail usage."""
    session = FakeSession(
        FakeResponse(200, DETAIL_USAGE),
        FakeResponse(404, {"message": "Not Found"}),
    )
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.com"
    )

    report = await client.async_get_billing_usage(
        BillingScope(BillingScopeType.USER, "octocat"),
        year=2026,
        month=9,
    )

    assert report.summary_items == ()
    assert report.actions_items == report.detail_items
    assert report.actions_items[0].net_amount == Decimal("6")
    assert report.unavailable_sections == ("summary",)


async def test_usage_detail_failure_preserves_summary_report() -> None:
    """A detail failure does not suppress authoritative aggregate usage."""
    session = FakeSession(
        FakeResponse(404, {"message": "Not Found"}),
        FakeResponse(200, SUMMARY_USAGE),
    )
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.com"
    )

    report = await client.async_get_billing_usage(
        BillingScope(BillingScopeType.ORGANIZATION, "example-org"),
        year=2026,
        month=9,
    )

    assert report.detail_items == ()
    assert report.actions_items == report.summary_items
    assert report.actions_items[0].net_quantity == Decimal("750")
    assert report.unavailable_sections == ("detail",)


async def test_fine_grained_pat_marks_usage_unavailable_without_request() -> None:
    """GitHub's documented classic-PAT-only restriction is detected locally."""
    session = FakeSession()
    client = GitHubClient(
        cast(ClientSession, session), "github_pat_redacted", "https://github.com"
    )
    scope = BillingScope(BillingScopeType.USER, "octocat")

    result = await client.async_fetch_billing_snapshot((scope,))

    assert session.requests == []
    data = result.scopes[scope.key]
    assert data.usage is None
    assert data.usage_capability.status is CapabilityStatus.FORBIDDEN
    assert data.usage_capability.reason == "classic_pat_required"
    assert data.budget_capability.status is CapabilityStatus.UNSUPPORTED


async def test_insufficient_org_permissions_are_partial() -> None:
    """A billing 403 does not turn into an authentication failure."""
    session = FakeSession(
        FakeResponse(403, {"message": "Resource not accessible"}),
        FakeResponse(403, {"message": "Resource not accessible"}),
        FakeResponse(403, {"message": "Resource not accessible"}),
    )
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.com"
    )
    scope = BillingScope(BillingScopeType.ORGANIZATION, "example-org")

    result = await client.async_fetch_billing_snapshot((scope,))

    data = result.scopes[scope.key]
    assert data.usage_capability.status is CapabilityStatus.FORBIDDEN
    assert data.budget_capability.status is CapabilityStatus.FORBIDDEN
    assert "organization:example-org:usage" in result.errors
    assert "organization:example-org:budgets" in result.errors


async def test_ghes_billing_is_capability_unsupported() -> None:
    """GHES keeps core functionality without attempting GitHub.com billing calls."""
    session = FakeSession()
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.example.com"
    )
    scope = BillingScope(BillingScopeType.ORGANIZATION, "example-org")

    result = await client.async_fetch_billing_snapshot((scope,))

    assert session.requests == []
    assert (
        result.scopes[scope.key].usage_capability.status is CapabilityStatus.UNSUPPORTED
    )
    assert (
        result.scopes[scope.key].budget_capability.status
        is CapabilityStatus.UNSUPPORTED
    )


async def test_budget_pagination_and_exhausted_state() -> None:
    """Budget pages are bounded and monetary values retain decimal precision."""
    session = FakeSession(
        FakeResponse(200, {"budgets": [BUDGET], "has_next_page": True}),
        FakeResponse(
            200,
            {
                "budgets": [
                    {
                        **BUDGET,
                        "id": "budget-2",
                        "budget_amount": "50",
                        "consumed_amount": "50",
                    }
                ],
                "has_next_page": False,
            },
        ),
    )
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.com"
    )
    scope = BillingScope(BillingScopeType.ORGANIZATION, "example-org")

    budgets = await client.async_get_budgets(scope)

    assert [budget.id for budget in budgets] == ["budget-1", "budget-2"]
    assert budgets[0].consumed_amount == Decimal("75.5")
    assert budgets[1].remaining_amount == Decimal("0")
    assert session.requests[1]["params"]["page"] == "2"


async def test_budget_mutations_use_official_paths_and_payloads() -> None:
    """Create, update, stop-usage update, and delete use documented CRUD."""
    session = FakeSession(
        FakeResponse(200, {"message": "created", "budget": BUDGET}),
        FakeResponse(
            200,
            {
                "message": "updated",
                "budget": {**BUDGET, "budget_amount": 125},
            },
        ),
        FakeResponse(200, {"message": "deleted", "id": "budget-1"}),
    )
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.com"
    )
    scope = BillingScope(BillingScopeType.ORGANIZATION, "example-org")

    created = await client.async_create_budget(
        scope,
        {
            "budget_amount": 100,
            "budget_scope": "repository",
            "budget_entity_name": "example-org/example",
            "budget_type": "ProductPricing",
            "budget_product_sku": "Actions",
            "prevent_further_usage": True,
        },
    )
    updated = await client.async_update_budget(
        scope, created.id, {"budget_amount": 125}
    )
    await client.async_delete_budget(scope, updated.id)

    assert session.requests[0]["method"] == "POST"
    assert session.requests[1]["method"] == "PATCH"
    assert session.requests[2]["method"] == "DELETE"
    assert session.requests[1]["json"] == {"budget_amount": 125}


async def test_invalid_billing_schema_fails_explicitly() -> None:
    """Malformed monetary payloads never become success-shaped zeroes."""
    session = FakeSession(
        FakeResponse(200, DETAIL_USAGE),
        FakeResponse(
            200,
            {
                **SUMMARY_USAGE,
                "usageItems": [
                    {
                        **cast(
                            dict[str, Any],
                            cast(list[object], SUMMARY_USAGE["usageItems"])[0],
                        ),
                        "netAmount": "invalid",
                    }
                ],
            },
        ),
    )
    client = GitHubClient(
        cast(ClientSession, session), "ghp_classic", "https://github.com"
    )

    with pytest.raises(GitHubAPIError, match="invalid_netAmount"):
        await client.async_get_billing_usage(
            BillingScope(BillingScopeType.USER, "octocat")
        )


def test_confirmation_phrases_include_financial_effect() -> None:
    """Financial confirmations contain scope, amount, currency, and enforcement."""
    scope = BillingScope(BillingScopeType.ORGANIZATION, "example-org")
    payload = {
        "budget_scope": "repository",
        "budget_entity_name": "example-org/example",
        "budget_product_sku": "Actions",
        "budget_amount": 100,
        "prevent_further_usage": True,
    }

    assert _create_confirmation(scope, payload) == (
        "CREATE organization example-org repository example-org/example "
        "Actions 100 USD stop=true"
    )
    assert _update_confirmation(
        scope,
        "budget-1",
        {"budget_amount": 125, "prevent_further_usage": False},
    ) == ("UPDATE organization example-org BUDGET budget-1 amount=125 USD stop=false")


def test_confirmation_is_required_and_exact() -> None:
    """Mutation schemas and handlers reject missing or mismatched confirmation."""
    with pytest.raises(vol.Invalid):
        CREATE_SCHEMA(
            {
                "scope_type": "organization",
                "scope_name": "example-org",
                "budget_amount": 100,
                "budget_scope": "organization",
                "budget_type": "ProductPricing",
                "budget_product_sku": "Actions",
                "prevent_further_usage": True,
            }
        )
    call = cast(
        ServiceCall,
        type("Call", (), {"data": {"confirmation": "wrong"}})(),
    )
    with pytest.raises(HomeAssistantError, match="exactly match"):
        _require_confirmation(call, "expected")


def test_reference_runner_estimate_is_decimal_and_explicit() -> None:
    """Reference-runner conversion remains an estimate, not billed minutes."""
    assert estimate_budget_amount(1000, Decimal("0.008")) == Decimal("8.00")


def test_exhausted_and_blocked_states_remain_separate() -> None:
    """Exhaustion and GitHub enforcement are not conflated."""
    stopped = billing_snapshot(
        consumed=Decimal("100"), amount=Decimal("100"), prevent_further_usage=True
    )
    warning, exhausted, blocked = _budget_flags(
        stopped.scopes["organization:example-org"].budgets[0], Decimal("75")
    )
    assert (warning, exhausted, blocked) == (True, True, True)

    allowed = billing_snapshot(
        consumed=Decimal("100"), amount=Decimal("100"), prevent_further_usage=False
    )
    assert _budget_flags(
        allowed.scopes["organization:example-org"].budgets[0], Decimal("75")
    ) == (True, True, False)


def test_billing_last_known_good_preserves_failed_category() -> None:
    """A stale billing refresh retains the last confirmed values."""
    previous = billing_snapshot()
    current = billing_snapshot(
        errors={
            "organization:example-org:usage": "billing_usage_failed",
            "organization:example-org:budgets": "budgets_failed",
        }
    )
    scope_data = current.scopes["organization:example-org"]
    current = current.__class__.create(
        scopes={
            "organization:example-org": scope_data.__class__(
                scope=scope_data.scope,
                usage=None,
                budgets=(),
                usage_capability=scope_data.usage_capability,
                budget_capability=scope_data.budget_capability,
                errors={"usage": "billing_usage_failed", "budgets": "budgets_failed"},
            )
        },
        fetched_at=current.fetched_at,
        errors=current.errors,
    )

    merged = _merge_billing_last_known_good(previous, current)

    assert merged.scopes["organization:example-org"].usage is not None
    assert merged.scopes["organization:example-org"].budgets


def test_configured_actions_allowance_uses_discounted_minutes() -> None:
    """Configured allowance derivations use included/discounted, never net quantity."""
    snapshot = billing_snapshot()
    scope_data = snapshot.scopes["organization:example-org"]
    coordinator = cast(
        Any,
        SimpleNamespace(
            data=snapshot,
            config_entry=SimpleNamespace(
                data={"account_id": 42},
                options={CONF_ACTIONS_INCLUDED_MINUTES: 3000},
            ),
            last_update_success=True,
        ),
    )

    account_coordinator = cast(
        Any,
        SimpleNamespace(
            data=SimpleNamespace(
                account=SimpleNamespace(
                    id=42,
                    login="octocat",
                    html_url="https://github.com/octocat",
                )
            ),
            config_entry=coordinator.config_entry,
            last_update_success=False,
        ),
    )
    included = GitHubInsightsConfiguredAllowanceSensor(account_coordinator)
    used = GitHubInsightsBillingSensor(
        coordinator, scope_data, "actions_configured_minutes_used"
    )
    remaining = GitHubInsightsBillingSensor(
        coordinator, scope_data, "actions_configured_minutes_remaining"
    )
    percent = GitHubInsightsBillingSensor(
        coordinator, scope_data, "actions_configured_minutes_used_percent"
    )

    assert included.available
    assert included.native_value == Decimal("3000")
    assert used.native_value == Decimal("250")
    assert remaining.native_value == Decimal("2750")
    assert percent.native_value == Decimal("8.333333333333333333333333333")
    assert included.extra_state_attributes["data_class"] is DataClass.CONFIGURED
    assert used.extra_state_attributes["data_class"] is DataClass.CALCULATED
    assert remaining.extra_state_attributes["data_class"] is DataClass.CALCULATED
    assert percent.extra_state_attributes["data_class"] is DataClass.CALCULATED
    assert "user-configured" in remaining.extra_state_attributes["source"]
    assert used.extra_state_attributes["usage_basis"] == (
        "discounted_or_included_quantity"
    )
    assert "net or billed quantity" in used.extra_state_attributes["derivation"]


def test_configured_actions_allowance_falls_back_to_gross_minutes() -> None:
    """Detailed usage can derive configured consumption from gross minutes."""
    snapshot = billing_snapshot()
    scope_data = snapshot.scopes["organization:example-org"]
    usage = scope_data.usage
    assert usage is not None
    detail_only = replace(usage, summary_items=())

    assert detail_only.configured_actions_minutes == (
        Decimal("1000"),
        "gross_quantity",
        None,
    )


def test_configured_actions_allowance_can_exceed_one_hundred_percent() -> None:
    """Usage beyond the configured allowance remains visible while remaining floors."""
    snapshot = billing_snapshot()
    scope_data = snapshot.scopes["organization:example-org"]
    coordinator = cast(
        Any,
        SimpleNamespace(
            data=snapshot,
            config_entry=SimpleNamespace(
                data={"account_id": 42},
                options={CONF_ACTIONS_INCLUDED_MINUTES: 200},
            ),
            last_update_success=True,
        ),
    )
    remaining = GitHubInsightsBillingSensor(
        coordinator, scope_data, "actions_configured_minutes_remaining"
    )
    percent = GitHubInsightsBillingSensor(
        coordinator, scope_data, "actions_configured_minutes_used_percent"
    )

    assert remaining.native_value == Decimal()
    assert percent.native_value == Decimal("125")


@pytest.mark.parametrize(
    ("unit_types", "reason"),
    [
        (("Minutes", "GigabyteHours"), "actions_usage_units_mixed"),
        (("GigabyteHours",), "actions_usage_unit_not_minutes"),
    ],
)
def test_configured_actions_allowance_rejects_non_minute_usage(
    unit_types: tuple[str, ...], reason: str
) -> None:
    """Mixed or non-minute usage is unavailable instead of being conflated."""
    snapshot = billing_snapshot()
    scope_data = snapshot.scopes["organization:example-org"]
    usage = scope_data.usage
    assert usage is not None
    source = usage.summary_items[0]
    items = tuple(
        replace(source, sku=f"sku-{index}", unit_type=unit)
        for index, unit in enumerate(unit_types)
    )
    invalid_usage = replace(usage, summary_items=items)
    invalid_scope = replace(scope_data, usage=invalid_usage)
    invalid_snapshot = snapshot.__class__.create(
        scopes={invalid_scope.scope.key: invalid_scope},
        fetched_at=snapshot.fetched_at,
    )
    coordinator = cast(
        Any,
        SimpleNamespace(
            data=invalid_snapshot,
            config_entry=SimpleNamespace(
                data={"account_id": 42},
                options={CONF_ACTIONS_INCLUDED_MINUTES: 3000},
            ),
            last_update_success=True,
        ),
    )
    sensor = GitHubInsightsBillingSensor(
        coordinator, invalid_scope, "actions_configured_minutes_remaining"
    )

    assert not sensor.available
    assert sensor.native_value is None
    assert sensor.extra_state_attributes["availability_reason"] == reason


def test_configured_actions_allowance_unset_is_explicitly_unavailable() -> None:
    """Zero is the safe unset default and does not imply a GitHub allowance."""
    snapshot = billing_snapshot()
    scope_data = snapshot.scopes["organization:example-org"]
    coordinator = cast(
        Any,
        SimpleNamespace(
            data=snapshot,
            config_entry=SimpleNamespace(
                data={"account_id": 42},
                options={CONF_ACTIONS_INCLUDED_MINUTES: 0},
            ),
            last_update_success=True,
        ),
    )
    sensor = GitHubInsightsBillingSensor(
        coordinator, scope_data, "actions_configured_minutes_remaining"
    )

    assert not sensor.available
    assert sensor.extra_state_attributes["availability_reason"] == (
        "configured_allowance_unset"
    )


def test_configured_allowance_remains_available_without_usage() -> None:
    """The configured value does not depend on GitHub billing availability."""
    snapshot = billing_snapshot()
    scope_data = replace(
        snapshot.scopes["organization:example-org"],
        usage=None,
    )
    unavailable_snapshot = snapshot.__class__.create(
        scopes={scope_data.scope.key: scope_data},
        fetched_at=snapshot.fetched_at,
    )
    coordinator = cast(
        Any,
        SimpleNamespace(
            data=unavailable_snapshot,
            config_entry=SimpleNamespace(
                data={"account_id": 42},
                options={CONF_ACTIONS_INCLUDED_MINUTES: 3000},
            ),
            last_update_success=True,
        ),
    )
    account_coordinator = cast(
        Any,
        SimpleNamespace(
            data=SimpleNamespace(
                account=SimpleNamespace(
                    id=42,
                    login="octocat",
                    html_url="https://github.com/octocat",
                )
            ),
            config_entry=coordinator.config_entry,
        ),
    )
    allowance = GitHubInsightsConfiguredAllowanceSensor(account_coordinator)
    used = GitHubInsightsBillingSensor(
        coordinator, scope_data, "actions_configured_minutes_used"
    )

    assert allowance.available
    assert allowance.native_value == Decimal("3000")
    assert allowance.extra_state_attributes["data_class"] is DataClass.CONFIGURED
    assert not used.available
    assert used.extra_state_attributes["availability_reason"] == (
        "actions_usage_unavailable"
    )


def test_configured_actions_allowance_repair_is_sanitized() -> None:
    """Allowance repairs report only bounded reasons and clear when unset."""
    hass = cast(HomeAssistant, object())
    with (
        patch(
            "custom_components.github_insights.repairs.ir.async_create_issue"
        ) as create_issue,
        patch(
            "custom_components.github_insights.repairs.ir.async_delete_issue"
        ) as delete_issue,
    ):
        async_update_configured_allowance_issue(
            hass,
            "entry-id",
            3000,
            {"actions_usage_units_mixed"},
        )
        create_issue.assert_called_once()
        assert "example-org" not in str(create_issue.call_args)
        async_update_configured_allowance_issue(
            hass,
            "entry-id",
            0,
            {"actions_usage_units_mixed"},
        )
        delete_issue.assert_called_once()
