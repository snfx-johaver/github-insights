"""Test helpers for GitHub Insights."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from custom_components.github_insights.models import (
    CapabilityStatus,
    GitHubAccount,
    GitHubCapability,
    GitHubOrganization,
    GitHubRateLimit,
    GitHubRepository,
    GitHubSnapshot,
)


def snapshot(
    *,
    account_id: int = 42,
    errors: Mapping[str, str] | None = None,
    private_repositories: int | None = 2,
) -> GitHubSnapshot:
    """Return a stable synthetic coordinator snapshot."""
    return GitHubSnapshot.create(
        account=GitHubAccount(
            id=account_id,
            login="octocat",
            name="The Octocat",
            avatar_url="https://avatars.githubusercontent.com/u/42",
            html_url="https://github.com/octocat",
            public_repos=8,
            total_private_repos=private_repositories,
            followers=10,
            following=4,
        ),
        organizations=(
            GitHubOrganization(
                id=7,
                login="example-org",
                avatar_url="https://avatars.githubusercontent.com/u/7",
            ),
        ),
        repositories=(
            GitHubRepository(
                id=99,
                full_name="octocat/example",
                private=False,
                archived=False,
                fork=False,
                html_url="https://github.com/octocat/example",
            ),
        ),
        rate_limit=GitHubRateLimit(
            limit=5000,
            remaining=4990,
            used=10,
            reset_at=datetime(2026, 9, 18, 12, 0, tzinfo=UTC),
        ),
        token_scopes=("read:org", "repo"),
        capabilities={
            "account": GitHubCapability(CapabilityStatus.AVAILABLE),
            "organizations": GitHubCapability(CapabilityStatus.AVAILABLE),
            "repositories": GitHubCapability(CapabilityStatus.AVAILABLE),
            "rate_limit": GitHubCapability(CapabilityStatus.AVAILABLE),
        },
        fetched_at=datetime(2026, 9, 18, 11, 0, tzinfo=UTC),
        errors=errors,
    )


class FakeResponse:
    """Minimal aiohttp response context manager."""

    def __init__(
        self,
        status: int,
        payload: Any,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize a fake response."""
        self.status = status
        self._payload = payload
        self.headers = dict(headers or {})

    async def __aenter__(self) -> FakeResponse:
        """Enter the response context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit the response context."""

    async def json(self, *, content_type: None = None) -> Any:
        """Return the configured JSON payload."""
        return self._payload


class FakeSession:
    """Queue-driven aiohttp session substitute."""

    def __init__(self, *responses: FakeResponse) -> None:
        """Initialize queued responses."""
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        """Record a request and return the next response."""
        self.requests.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0)
