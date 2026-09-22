"""Tests for enhanced billing, budgets, estimates, and safety boundaries."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

import pytest
import voluptuous as vol
from aiohttp import ClientSession
from homeassistant.core import ServiceCall
from homeassistant.exceptions import HomeAssistantError

from custom_components.github_insights.api import GitHubAPIError, GitHubClient
from custom_components.github_insights.binary_sensor import _budget_flags
from custom_components.github_insights.coordinator import (
    _merge_billing_last_known_good,
)
from custom_components.github_insights.models import (
    BillingScope,
    BillingScopeType,
    CapabilityStatus,
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
