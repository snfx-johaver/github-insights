"""Tests for repository capability collection."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import pytest

from custom_components.github_insights.api import (
    GitHubClient,
    GitHubPage,
    GitHubPermissionError,
    GitHubRateLimitError,
)
from custom_components.github_insights.models import (
    CapabilityStatus,
    GitHubCapability,
    GitHubRepository,
)
from custom_components.github_insights.repository_data import (
    RepositoryCollectionOptions,
    _activity,
    _async_security,
    _select_repositories,
    async_collect_repository_insights,
)


def _repository(
    repository_id: int,
    full_name: str,
    *,
    archived: bool = False,
    fork: bool = False,
) -> GitHubRepository:
    return GitHubRepository(
        id=repository_id,
        name=full_name.rsplit("/", 1)[-1],
        full_name=full_name,
        description=None,
        private=False,
        visibility="public",
        archived=archived,
        fork=fork,
        html_url=f"https://github.com/{full_name}",
        default_branch="main",
        language="Python",
        license_name="MIT",
        stargazers_count=1,
        watchers_count=1,
        forks_count=1,
        open_issues_count=1,
        has_discussions=True,
        size_kb=1,
        pushed_at=datetime(2026, 9, 20, tzinfo=UTC),
    )


def test_repository_selection_is_bounded_and_filtered() -> None:
    """Automatic discovery honors archive, fork, and safety boundaries."""
    repositories = (
        _repository(1, "octocat/one"),
        _repository(2, "octocat/two", archived=True),
        _repository(3, "octocat/three", fork=True),
    )
    selected = _select_repositories(
        repositories,
        RepositoryCollectionOptions(
            selected=(),
            auto_discover=True,
            include_archived=False,
            include_forks=False,
            enabled_categories=frozenset(),
            repository_limit=1,
        ),
    )

    assert [item.id for item in selected] == [1]


def test_repository_selection_accepts_float_shaped_selector_limit() -> None:
    """Home Assistant NumberSelector output cannot break tuple slicing."""
    repositories = tuple(
        _repository(index, f"octocat/repository-{index}") for index in range(1, 12)
    )
    selected = _select_repositories(
        repositories,
        RepositoryCollectionOptions(
            selected=(),
            auto_discover=True,
            include_archived=True,
            include_forks=True,
            enabled_categories=frozenset(),
            repository_limit=cast(Any, 10.0),
        ),
    )

    assert len(selected) == 10


def test_streaks_require_complete_coverage() -> None:
    """Truncated activity never produces a supposedly reliable streak."""
    commit = {
        "commit": {
            "author": {"date": "2026-09-20T10:00:00Z"},
        }
    }

    activity = _activity((commit,), (), (), (), complete=False)

    assert activity.commits == 1
    assert activity.coverage_complete is False
    assert activity.current_streak is None
    assert activity.longest_streak is None


def test_merged_activity_uses_merge_date() -> None:
    """Merged pull requests are counted by merge time, not creation time."""
    activity = _activity(
        (),
        (
            {
                "created_at": "2025-01-01T00:00:00Z",
                "merged_at": datetime.now(UTC).isoformat(),
            },
        ),
        (),
        (),
        complete=True,
    )

    assert activity.pull_requests_opened == 0
    assert activity.pull_requests_merged == 1


async def test_workflow_jobs_produce_runtime_without_billing_claims() -> None:
    """Job runtime remains runtime metadata and selected data stays bounded."""

    class Client:
        server = type("Server", (), {"is_dotcom": True})()

        async def async_get_json(
            self, path: str, *, params: dict[str, str] | None = None
        ) -> Any:
            if path.endswith("/actions/runs"):
                return {
                    "workflow_runs": [
                        {
                            "id": 10,
                            "name": "CI",
                            "status": "completed",
                            "conclusion": "success",
                            "event": "push",
                            "html_url": "https://github.com/octocat/example/actions/runs/10",
                            "created_at": "2026-09-20T10:00:00Z",
                            "updated_at": "2026-09-20T10:10:00Z",
                        }
                    ]
                }
            if path.endswith("/environments"):
                return {"environments": []}
            return {
                "id": 1,
                "name": "example",
                "full_name": "octocat/example",
                "private": False,
                "archived": False,
                "fork": False,
                "html_url": "https://github.com/octocat/example",
            }

        async def async_get_page(
            self,
            path: str,
            *,
            params: dict[str, str] | None = None,
            item_limit: int,
        ) -> GitHubPage:
            if path.endswith("/jobs"):
                return GitHubPage(
                    (
                        {
                            "started_at": "2026-09-20T10:00:00Z",
                            "completed_at": "2026-09-20T10:05:00Z",
                        },
                    ),
                    True,
                )
            return GitHubPage((), True)

    insights = await async_collect_repository_insights(
        cast(GitHubClient, Client()),
        (_repository(1, "octocat/example"),),
        RepositoryCollectionOptions(
            selected=("octocat/example",),
            auto_discover=False,
            include_archived=False,
            include_forks=True,
            enabled_categories=frozenset({"workflows"}),
            repository_limit=1,
        ),
    )

    assert insights[0].workflow_status == "success"
    assert insights[0].workflow_runs[0].jobs == 1
    assert insights[0].workflow_runs[0].runtime_seconds == 600
    assert insights[0].workflow_runs[0].job_runtime_seconds == 300


async def test_security_permission_failure_is_not_zero_alerts() -> None:
    """Unavailable security APIs remain unavailable instead of reporting zero."""

    class Client:
        async def async_get_page(
            self,
            path: str,
            *,
            params: dict[str, str] | None = None,
            item_limit: int,
        ) -> GitHubPage:
            raise GitHubPermissionError("forbidden")

    capabilities: dict[str, GitHubCapability] = {}
    errors: dict[str, str] = {}
    security = await _async_security(
        cast(GitHubClient, Client()),
        "/repos/octocat/example",
        capabilities,
        errors,
    )

    assert security is None
    assert errors["dependabot"] == "missing_permission"
    assert capabilities["secret_scanning"].status is CapabilityStatus.FORBIDDEN


async def test_rate_limits_propagate_from_optional_capabilities() -> None:
    """Rate limits abort collection so the coordinator can back off."""

    class Client:
        async def async_get_page(
            self,
            path: str,
            *,
            params: dict[str, str] | None = None,
            item_limit: int,
        ) -> GitHubPage:
            raise GitHubRateLimitError("rate_limited", retry_after=30)

    with pytest.raises(GitHubRateLimitError):
        await _async_security(
            cast(GitHubClient, Client()),
            "/repos/octocat/example",
            {},
            {},
        )
