"""Tests for official Copilot billing capability collection."""

from __future__ import annotations

from typing import Any, cast

from custom_components.github_insights.api import GitHubClient
from custom_components.github_insights.copilot_data import (
    async_collect_copilot_billing,
)
from custom_components.github_insights.models import (
    CapabilityStatus,
    GitHubAccount,
    GitHubOrganization,
)

ACCOUNT = GitHubAccount(
    id=42,
    login="octocat",
    name="The Octocat",
    avatar_url="https://github.com/images/error/octocat_happy.gif",
    html_url="https://github.com/octocat",
    public_repos=2,
    total_private_repos=1,
    followers=10,
    following=3,
)
ORGANIZATION = GitHubOrganization(
    id=84,
    login="example-org",
    avatar_url="https://github.com/example-org.png",
)


async def test_user_and_org_billing_remain_separate() -> None:
    """Personal and organization billing scopes are not combined."""

    class Client:
        server = type("Server", (), {"is_dotcom": True})()

        async def async_get_json(
            self, path: str, *, params: dict[str, str] | None = None
        ) -> Any:
            if "/copilot/metrics/reports/" in path:
                return {
                    "download_links": [
                        "https://copilot-reports.github.com/report.json"
                    ],
                    "report_end_day": "2026-09-18",
                }
            quantity = 2 if path.startswith("/users/") else 5
            return {
                "timePeriod": {"year": 2026, "month": 9},
                "usageItems": [
                    {
                        "product": "Copilot",
                        "sku": "premium_requests",
                        "model": "model-a",
                        "grossQuantity": quantity,
                        "netQuantity": quantity,
                        "netAmount": quantity / 10,
                    }
                ],
            }

        async def async_get_signed_report(
            self, value: str
        ) -> tuple[dict[str, Any], ...]:
            return (
                {
                    "day_totals": [
                        {
                            "day": "2026-09-18",
                            "daily_active_users": 4,
                            "pull_requests": {
                                "total_created_by_copilot": 2,
                                "total_merged_created_by_copilot": 1,
                                "total_reviewed_by_copilot": 3,
                            },
                        }
                    ],
                    "copilot_feature_engagement": {"active_user_count": 5},
                },
            )

    primary_client = cast(GitHubClient, Client())
    billing_client = cast(GitHubClient, Client())
    usage, capabilities, errors = await async_collect_copilot_billing(
        primary_client,
        ACCOUNT,
        (ORGANIZATION,),
        billing_client=billing_client,
    )

    assert [item.scope for item in usage] == [
        "user:octocat",
        "organization:example-org",
    ]
    assert usage[0].premium_requests_used == 2
    assert usage[1].premium_requests_used == 5
    assert usage[1].active_users == 4
    assert usage[1].coding_agent_pull_requests == 2
    assert usage[1].code_review_pull_requests == 3
    assert capabilities["copilot"].status is CapabilityStatus.AVAILABLE
    assert errors == {}


async def test_copilot_activity_uses_primary_and_billing_uses_secondary() -> None:
    """Copilot metrics never receive the billing-only credential client."""

    class PrimaryClient:
        server = type("Server", (), {"is_dotcom": True})()
        paths: list[str] = []

        async def async_get_json(
            self, path: str, *, params: dict[str, str] | None = None
        ) -> Any:
            self.paths.append(path)
            return {
                "download_links": ["https://copilot-reports.github.com/report.json"],
                "report_end_day": "2026-09-18",
            }

        async def async_get_signed_report(
            self, value: str
        ) -> tuple[dict[str, Any], ...]:
            return ()

    class BillingClient:
        paths: list[str] = []

        async def async_get_json(
            self, path: str, *, params: dict[str, str] | None = None
        ) -> Any:
            self.paths.append(path)
            return {"timePeriod": {"year": 2026}, "usageItems": []}

    primary = PrimaryClient()
    billing = BillingClient()
    await async_collect_copilot_billing(
        cast(GitHubClient, primary),
        ACCOUNT,
        (ORGANIZATION,),
        billing_client=cast(GitHubClient, billing),
    )

    assert primary.paths == [
        "/orgs/example-org/copilot/metrics/reports/organization-28-day/latest"
    ]
    assert all("/settings/billing/" in path for path in billing.paths)


async def test_copilot_billing_is_not_probed_on_ghes() -> None:
    """Cloud billing endpoints are explicitly unsupported on GHES."""

    class Client:
        server = type("Server", (), {"is_dotcom": False})()

    usage, capabilities, errors = await async_collect_copilot_billing(
        cast(GitHubClient, Client()),
        ACCOUNT,
        (),
    )

    assert usage == ()
    assert capabilities["copilot"].status is CapabilityStatus.UNSUPPORTED
    assert capabilities["copilot"].reason == "github_com_only"
    assert errors == {}
