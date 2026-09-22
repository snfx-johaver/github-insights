"""Tests for coordinator reliability behavior."""

from __future__ import annotations

from custom_components.github_insights.coordinator import (
    _merge_copilot_usage,
    _merge_last_known_good,
    _merge_repository_insights,
)
from custom_components.github_insights.models import (
    GitHubCopilotUsage,
    GitHubRepositoryInsights,
)

from .helpers import snapshot


def test_partial_failure_retains_last_known_good_categories() -> None:
    """A temporary endpoint failure must not publish a false zero."""
    previous = snapshot()
    current = snapshot(
        errors={
            "organizations": "temporarily_unavailable",
            "repositories": "temporarily_unavailable",
            "rate_limit": "temporarily_unavailable",
        }
    )
    current = current.__class__.create(
        account=current.account,
        organizations=(),
        repositories=(),
        rate_limit=None,
        token_scopes=current.token_scopes,
        capabilities=current.capabilities,
        fetched_at=current.fetched_at,
        errors=current.errors,
    )

    merged = _merge_last_known_good(previous, current)

    assert merged.organizations == previous.organizations
    assert merged.repositories == previous.repositories
    assert merged.rate_limit == previous.rate_limit
    assert merged.errors == current.errors


def test_repository_and_copilot_stale_values_are_retained() -> None:
    """Capability failures retain repository and Copilot last-known-good data."""
    base = snapshot()
    insight = GitHubRepositoryInsights.create(repository=base.repositories[0])
    previous = base.__class__.create(
        account=base.account,
        organizations=base.organizations,
        repositories=base.repositories,
        repository_insights=(insight,),
        copilot=(),
        rate_limit=base.rate_limit,
        token_scopes=base.token_scopes,
        capabilities=base.capabilities,
        fetched_at=base.fetched_at,
    )
    current = base.__class__.create(
        account=base.account,
        organizations=base.organizations,
        repositories=base.repositories,
        repository_insights=(),
        copilot=(),
        rate_limit=base.rate_limit,
        token_scopes=base.token_scopes,
        capabilities=base.capabilities,
        fetched_at=base.fetched_at,
        errors={"repository_insights": "temporarily_unavailable"},
    )

    merged = _merge_last_known_good(previous, current)

    assert merged.repository_insights == (insight,)


def test_repository_field_failure_retains_only_failed_field() -> None:
    """A partial repository refresh preserves failed fields and fresh successes."""
    base = snapshot()
    previous = GitHubRepositoryInsights.create(
        repository=base.repositories[0],
        open_pull_requests=4,
        open_issues=3,
    )
    current = GitHubRepositoryInsights.create(
        repository=base.repositories[0],
        open_pull_requests=None,
        open_issues=2,
        errors={"pull_requests": "temporarily_unavailable"},
    )

    merged = _merge_repository_insights((previous,), (current,))

    assert merged[0].open_pull_requests == 4
    assert merged[0].open_issues == 2


def test_copilot_merge_retains_only_missing_fields_by_immutable_scope() -> None:
    """A failed report does not freeze fresh billing data for the same scope."""
    previous = GitHubCopilotUsage.create(
        scope="organization:old-name",
        scope_id=84,
        scope_type="organization",
        premium_requests_used=2,
        active_users=5,
    )
    current = GitHubCopilotUsage.create(
        scope="organization:new-name",
        scope_id=84,
        scope_type="organization",
        premium_requests_used=3,
    )

    merged = _merge_copilot_usage(
        (previous,),
        (current,),
        {"copilot_organization_84_metrics": "temporarily_unavailable"},
    )

    assert merged[0].scope == "organization:new-name"
    assert merged[0].premium_requests_used == 3
    assert merged[0].active_users == 5
