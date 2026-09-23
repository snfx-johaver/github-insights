"""Official GitHub Copilot and AI billing usage collection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any
from urllib.parse import quote

from .api import (
    GitHubAPIError,
    GitHubClient,
    GitHubConnectionError,
    GitHubPermissionError,
)
from .models import (
    CapabilityStatus,
    GitHubAccount,
    GitHubCapability,
    GitHubCopilotUsage,
    GitHubOrganization,
    JsonObject,
)

_OPTIONAL_ERRORS = (
    GitHubPermissionError,
    GitHubConnectionError,
    GitHubAPIError,
)


@dataclass(frozen=True, slots=True)
class CopilotMetrics:
    """Normalized fields from an official Copilot usage report."""

    active_users: int | None
    engaged_users: int | None
    coding_agent_pull_requests: int | None
    coding_agent_merged_pull_requests: int | None
    code_review_pull_requests: int | None
    reporting_day: str | None


async def async_collect_copilot_billing(
    client: GitHubClient,
    account: GitHubAccount,
    organizations: tuple[GitHubOrganization, ...],
    *,
    billing_client: GitHubClient | None = None,
) -> tuple[
    tuple[GitHubCopilotUsage, ...],
    dict[str, GitHubCapability],
    dict[str, str],
]:
    """Collect user and organization AI-credit and premium-request billing."""
    if not client.server.is_dotcom:
        return (
            (),
            {
                "copilot": GitHubCapability(
                    CapabilityStatus.UNSUPPORTED, "github_com_only"
                )
            },
            {},
        )

    scopes = (("user", account.login, account.id),) + tuple(
        ("organization", organization.login, organization.id)
        for organization in organizations
    )
    if billing_client is None:
        results = tuple(
            _unavailable_billing_scope(scope_type, scope_id)
            for scope_type, _, scope_id in scopes
        )
    else:
        results = tuple(
            [
                await _async_collect_scope(
                    billing_client, scope_type, scope_name, scope_id
                )
                for scope_type, scope_name, scope_id in scopes
            ]
        )
    usages = tuple(result[0] for result in results if result[0] is not None)
    capabilities: dict[str, GitHubCapability] = {}
    errors: dict[str, str] = {}
    for _, result_capabilities, result_errors in results:
        capabilities.update(result_capabilities)
        errors.update(result_errors)

    usage_by_scope = {usage.scope: usage for usage in usages}
    for organization in organizations:
        scope = f"organization:{organization.login}"
        metrics, capability, error = await _async_collect_metrics(
            client, organization.login
        )
        capabilities[f"copilot_organization_{organization.id}_metrics"] = capability
        if error:
            errors[f"copilot_organization_{organization.id}_metrics"] = error
        if metrics:
            existing = usage_by_scope.get(scope) or GitHubCopilotUsage.create(
                scope=scope,
                scope_id=organization.id,
                scope_type="organization",
            )
            usage_by_scope[scope] = replace(
                existing,
                active_users=metrics.active_users,
                engaged_users=metrics.engaged_users,
                coding_agent_pull_requests=metrics.coding_agent_pull_requests,
                coding_agent_merged_pull_requests=(
                    metrics.coding_agent_merged_pull_requests
                ),
                code_review_pull_requests=metrics.code_review_pull_requests,
                reporting_day=metrics.reporting_day,
            )
    usages = tuple(usage_by_scope.values())
    if usages:
        capabilities["copilot"] = GitHubCapability(CapabilityStatus.AVAILABLE)
    elif "copilot" not in capabilities:
        capabilities["copilot"] = GitHubCapability(
            CapabilityStatus.FORBIDDEN, "missing_billing_permission"
        )
        errors["copilot"] = "missing_billing_permission"
    return usages, capabilities, errors


def _unavailable_billing_scope(
    scope_type: str,
    scope_id: int,
) -> tuple[
    GitHubCopilotUsage | None,
    dict[str, GitHubCapability],
    dict[str, str],
]:
    """Mark Copilot billing fields unavailable while leaving metrics independent."""
    capabilities = {
        f"copilot_{scope_type}_{scope_id}_{usage_type}": GitHubCapability(
            CapabilityStatus.FORBIDDEN,
            "billing_token_not_configured",
        )
        for usage_type in ("ai_credit", "premium_request")
    }
    return (
        None,
        capabilities,
        {key: "billing_token_not_configured" for key in capabilities},
    )


async def _async_collect_metrics(
    client: GitHubClient,
    organization: str,
) -> tuple[CopilotMetrics | None, GitHubCapability, str | None]:
    path = (
        f"/orgs/{quote(organization, safe='')}"
        "/copilot/metrics/reports/organization-28-day/latest"
    )
    try:
        envelope = _object(await client.async_get_json(path))
        links = envelope.get("download_links")
        if not isinstance(links, list) or not links:
            return (
                None,
                GitHubCapability(
                    CapabilityStatus.TEMPORARILY_UNAVAILABLE,
                    "report_not_ready",
                ),
                "report_not_ready",
            )
        records: list[JsonObject] = []
        for link in links[:10]:
            if not isinstance(link, str):
                continue
            records.extend(await client.async_get_signed_report(link))
        metrics = _aggregate_metrics(records)
        metrics = replace(
            metrics,
            reporting_day=_string(envelope.get("report_end_day")) or None,
        )
        return metrics, GitHubCapability(CapabilityStatus.AVAILABLE), None
    except _OPTIONAL_ERRORS as err:
        capability = _capability(err)
        return None, capability, capability.reason or capability.status


def _aggregate_metrics(records: list[JsonObject]) -> CopilotMetrics:
    daily: list[JsonObject] = []
    engaged_users = 0
    for record in records:
        totals = record.get("day_totals")
        if isinstance(totals, list):
            daily.extend(item for item in totals if isinstance(item, dict))
        elif "day" in record:
            daily.append(record)
        engagement = record.get("copilot_feature_engagement")
        if isinstance(engagement, dict):
            engaged_users += _integer(engagement.get("active_user_count"))
    latest_day = max(
        (_string(item.get("day")) for item in daily),
        default="",
    )
    latest = tuple(item for item in daily if _string(item.get("day")) == latest_day)
    return CopilotMetrics(
        active_users=max(
            (_integer(item.get("daily_active_users")) for item in latest),
            default=0,
        )
        if latest
        else None,
        engaged_users=engaged_users or None,
        coding_agent_pull_requests=(
            sum(
                _pull_request_value(item, "total_created_by_copilot") for item in latest
            )
            if latest
            else None
        ),
        coding_agent_merged_pull_requests=(
            sum(
                _pull_request_value(item, "total_merged_created_by_copilot")
                for item in latest
            )
            if latest
            else None
        ),
        code_review_pull_requests=(
            sum(
                _pull_request_value(item, "total_reviewed_by_copilot")
                for item in latest
            )
            if latest
            else None
        ),
        reporting_day=None,
    )


async def _async_collect_scope(
    client: GitHubClient,
    scope_type: str,
    scope_name: str,
    scope_id: int,
) -> tuple[
    GitHubCopilotUsage | None,
    dict[str, GitHubCapability],
    dict[str, str],
]:
    prefix = (
        f"/users/{quote(scope_name, safe='')}"
        if scope_type == "user"
        else f"/organizations/{quote(scope_name, safe='')}"
    )
    capabilities: dict[str, GitHubCapability] = {}
    errors: dict[str, str] = {}
    payloads: dict[str, JsonObject] = {}
    for usage_type, endpoint in {
        "ai_credit": f"{prefix}/settings/billing/ai_credit/usage",
        "premium_request": f"{prefix}/settings/billing/premium_request/usage",
    }.items():
        key = f"copilot_{scope_type}_{scope_id}_{usage_type}"
        try:
            payload = await client.async_get_json(endpoint)
            payloads[usage_type] = _object(payload)
            capabilities[key] = GitHubCapability(CapabilityStatus.AVAILABLE)
        except _OPTIONAL_ERRORS as err:
            capabilities[key] = _capability(err)
            errors[key] = capabilities[key].reason or capabilities[key].status

    if not payloads:
        return None, capabilities, errors

    ai_items = _usage_items(payloads.get("ai_credit"))
    premium_items = _usage_items(payloads.get("premium_request"))
    all_items = ai_items + premium_items
    reporting_day = _reporting_day(
        payloads.get("premium_request") or payloads.get("ai_credit")
    )
    return (
        GitHubCopilotUsage.create(
            scope=f"{scope_type}:{scope_name}",
            scope_id=scope_id,
            scope_type=scope_type,
            premium_requests_used=_sum(premium_items, "grossQuantity"),
            premium_requests_paid=_sum(premium_items, "netQuantity"),
            ai_credits_used=_sum(ai_items, "grossQuantity"),
            cost=(
                _sum(all_items, "netAmount")
                if {"ai_credit", "premium_request"} <= payloads.keys()
                else None
            ),
            currency=None,
            product_breakdown=(
                _breakdown(all_items, "product", "grossQuantity")
                if {"ai_credit", "premium_request"} <= payloads.keys()
                else None
            ),
            model_breakdown=(
                _breakdown(all_items, "model", "grossQuantity")
                if {"ai_credit", "premium_request"} <= payloads.keys()
                else None
            ),
            repository_breakdown={},
            reporting_day=reporting_day,
        ),
        capabilities,
        errors,
    )


def _usage_items(payload: JsonObject | None) -> tuple[JsonObject, ...]:
    if payload is None:
        return ()
    raw = payload.get("usageItems")
    if not isinstance(raw, list):
        return ()
    return tuple(item for item in raw if isinstance(item, dict))


def _sum(items: tuple[JsonObject, ...], key: str) -> float | None:
    values = [
        float(item[key]) for item in items if isinstance(item.get(key), int | float)
    ]
    return sum(values) if values else None


def _breakdown(
    items: tuple[JsonObject, ...], key: str, value_key: str
) -> Mapping[str, float]:
    values: dict[str, float] = {}
    for item in items:
        name = item.get(key)
        value = item.get(value_key)
        if isinstance(name, str) and isinstance(value, int | float):
            values[name] = values.get(name, 0.0) + float(value)
    return values


def _reporting_day(payload: JsonObject | None) -> str | None:
    if payload is None:
        return None
    period = payload.get("timePeriod")
    if not isinstance(period, dict):
        return None
    year = period.get("year")
    month = period.get("month")
    day = period.get("day")
    if not isinstance(year, int):
        return None
    if not isinstance(month, int):
        return str(year)
    if not isinstance(day, int):
        return f"{year:04d}-{month:02d}"
    return f"{year:04d}-{month:02d}-{day:02d}"


def _pull_request_value(item: JsonObject, key: str) -> int:
    pull_requests = item.get("pull_requests")
    if not isinstance(pull_requests, dict):
        return 0
    return _integer(pull_requests.get(key))


def _integer(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _object(value: Any) -> JsonObject:
    if not isinstance(value, dict):
        raise GitHubAPIError(502, "expected_object")
    return value


def _capability(error: Exception) -> GitHubCapability:
    if isinstance(error, GitHubPermissionError):
        return GitHubCapability(
            CapabilityStatus.FORBIDDEN, "missing_billing_permission"
        )
    if isinstance(error, GitHubAPIError) and error.status in {404, 410, 422}:
        return GitHubCapability(CapabilityStatus.UNSUPPORTED, "unsupported")
    return GitHubCapability(
        CapabilityStatus.TEMPORARILY_UNAVAILABLE, "temporarily_unavailable"
    )
