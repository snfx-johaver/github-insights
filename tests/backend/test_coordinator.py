"""Tests for coordinator reliability behavior."""

from __future__ import annotations

from custom_components.github_insights.coordinator import (
    _merge_last_known_good,
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
