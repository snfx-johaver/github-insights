"""Tests for the GitHub API client."""

from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession

from custom_components.github_insights.api import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubClient,
    GitHubInvalidServerError,
    GitHubRateLimitError,
    normalize_server,
)
from custom_components.github_insights.repository_data import (
    RepositoryCollectionOptions,
)

from .helpers import FakeResponse, FakeSession, snapshot


def test_normalize_github_dotcom() -> None:
    """GitHub.com must use the dedicated API origin."""
    server = normalize_server("https://www.github.com/")

    assert server.web_url == "https://github.com"
    assert server.api_url == "https://api.github.com"
    assert server.is_dotcom is True


@pytest.mark.parametrize(
    "server",
    [
        "http://github.example.com",
        "https://user@example.com",
        "https://127.0.0.1",
        "https://localhost",
        "https://github.example.com/path",
        "https://github.example.com?token=secret",
    ],
)
def test_rejects_unsafe_server_origins(server: str) -> None:
    """Only a credential-free HTTPS origin is accepted."""
    with pytest.raises(GitHubInvalidServerError):
        normalize_server(server)


async def test_account_parsing_and_scope_capture() -> None:
    """Account values and safe scope metadata are parsed."""
    session = FakeSession(
        FakeResponse(
            200,
            {
                "id": 42,
                "login": "octocat",
                "name": "The Octocat",
                "avatar_url": "https://avatars.githubusercontent.com/u/42",
                "html_url": "https://github.com/octocat",
                "public_repos": 8,
                "total_private_repos": 2,
                "followers": 10,
                "following": 4,
            },
            {"X-OAuth-Scopes": "repo, read:org"},
        )
    )
    client = GitHubClient(cast(ClientSession, session), "token", "https://github.com")

    account = await client.async_get_account()

    assert account.login == "octocat"
    assert client.token_scopes == ("read:org", "repo")
    assert session.requests[0]["headers"]["Authorization"] == "Bearer token"


async def test_pagination_and_repository_limit() -> None:
    """Repository discovery follows same-origin links and honors its cap."""
    repo = {
        "id": 1,
        "full_name": "octocat/example",
        "private": False,
        "archived": False,
        "fork": False,
        "html_url": "https://github.com/octocat/example",
    }
    session = FakeSession(
        FakeResponse(
            200,
            [repo],
            {"Link": '<https://api.github.com/user/repos?page=2>; rel="next"'},
        ),
        FakeResponse(200, [{**repo, "id": 2, "full_name": "octocat/second"}]),
    )
    client = GitHubClient(cast(ClientSession, session), "token", "https://github.com")

    repositories = await client.async_get_repositories()

    assert [item.id for item in repositories] == [1, 2]
    assert session.requests[1]["params"]["page"] == "2"


async def test_etag_uses_last_known_payload() -> None:
    """A 304 response reuses the cached response body."""
    payload = {
        "resources": {"core": {"limit": 5000, "remaining": 4999, "used": 1, "reset": 1}}
    }
    session = FakeSession(
        FakeResponse(200, payload, {"ETag": '"abc"'}),
        FakeResponse(304, None),
    )
    client = GitHubClient(cast(ClientSession, session), "token", "https://github.com")

    first = await client.async_get_rate_limit()
    second = await client.async_get_rate_limit()

    assert first == second
    assert session.requests[1]["headers"]["If-None-Match"] == '"abc"'


async def test_authentication_and_rate_limit_errors() -> None:
    """Authentication and backoff responses remain distinct."""
    auth_client = GitHubClient(
        cast(
            ClientSession,
            FakeSession(FakeResponse(401, {"message": "Bad credentials"})),
        ),
        "token",
        "https://github.com",
    )
    with pytest.raises(GitHubAuthenticationError):
        await auth_client.async_get_account()

    rate_client = GitHubClient(
        cast(
            ClientSession,
            FakeSession(FakeResponse(403, {}, {"Retry-After": "30"})),
        ),
        "token",
        "https://github.com",
    )
    with pytest.raises(GitHubRateLimitError, match="rate_limited") as caught:
        await rate_client.async_get_account()
    assert caught.value.retry_after == 30


async def test_secondary_rate_limit_without_header_gets_safe_backoff() -> None:
    """A documented secondary-limit response is not mistaken for permission loss."""
    client = GitHubClient(
        cast(
            ClientSession,
            FakeSession(
                FakeResponse(
                    403,
                    {"message": "You have exceeded a secondary rate limit."},
                )
            ),
        ),
        "token",
        "https://github.com",
    )

    with pytest.raises(GitHubRateLimitError) as caught:
        await client.async_get_account()

    assert caught.value.retry_after is not None
    assert caught.value.retry_after >= 2


async def test_post_auth_rate_limit_returns_partial_snapshot_and_stops_fanout() -> None:
    """Repository throttling yields safe partial data and stops later requests."""
    base = snapshot()
    client = GitHubClient(
        cast(ClientSession, FakeSession()),
        "github_pat_primary_fake",
        "https://github.com",
    )
    get_rate_limit = AsyncMock()
    collect_copilot = AsyncMock()

    with (
        patch.object(client, "async_get_account", AsyncMock(return_value=base.account)),
        patch.object(
            client,
            "async_get_organizations",
            AsyncMock(return_value=base.organizations),
        ),
        patch.object(
            client,
            "async_get_repositories",
            AsyncMock(return_value=base.repositories),
        ),
        patch.object(client, "async_get_rate_limit", get_rate_limit),
        patch(
            "custom_components.github_insights.repository_data."
            "async_collect_repository_insights",
            new=AsyncMock(
                side_effect=GitHubRateLimitError("rate_limited", retry_after=30)
            ),
        ),
        patch(
            "custom_components.github_insights.copilot_data."
            "async_collect_copilot_billing",
            new=collect_copilot,
        ),
    ):
        partial = await client.async_fetch_snapshot(
            repository_options=RepositoryCollectionOptions(
                selected=(),
                auto_discover=True,
                include_archived=True,
                include_forks=True,
                enabled_categories=frozenset({"workflows", "copilot"}),
            ),
            copilot_organizations=("example-org",),
        )

    assert partial.account == base.account
    assert partial.repositories == base.repositories
    assert partial.repository_insights == ()
    assert partial.retry_after == 30
    assert partial.errors["repository_insights"] == "rate_limited"
    assert partial.errors["workflows"] == "rate_limited"
    assert partial.errors["copilot"] == "rate_limited"
    assert partial.errors["rate_limit"] == "rate_limited"
    get_rate_limit.assert_not_awaited()
    collect_copilot.assert_not_awaited()
    assert "github_pat_primary_fake" not in str(partial.errors)
    assert "github_pat_primary_fake" not in str(partial.capabilities)


async def test_organization_rate_limit_skips_all_later_capabilities() -> None:
    """Organization throttling prevents repository and rate-limit fan-out."""
    base = snapshot()
    client = GitHubClient(
        cast(ClientSession, FakeSession()),
        "github_pat_primary_fake",
        "https://github.com",
    )
    get_repositories = AsyncMock()
    get_rate_limit = AsyncMock()
    with (
        patch.object(client, "async_get_account", AsyncMock(return_value=base.account)),
        patch.object(
            client,
            "async_get_organizations",
            AsyncMock(side_effect=GitHubRateLimitError("rate_limited", retry_after=25)),
        ),
        patch.object(client, "async_get_repositories", get_repositories),
        patch.object(client, "async_get_rate_limit", get_rate_limit),
    ):
        partial = await client.async_fetch_snapshot()

    assert partial.retry_after == 25
    assert partial.errors == {
        "organizations": "rate_limited",
        "repositories": "rate_limited",
        "rate_limit": "rate_limited",
    }
    get_repositories.assert_not_awaited()
    get_rate_limit.assert_not_awaited()


async def test_copilot_rate_limit_isolated_from_first_refresh() -> None:
    """Copilot throttling yields partial data and skips the later sensor request."""
    base = snapshot()
    client = GitHubClient(
        cast(ClientSession, FakeSession()),
        "github_pat_primary_fake",
        "https://github.com",
    )
    get_rate_limit = AsyncMock()
    with (
        patch.object(client, "async_get_account", AsyncMock(return_value=base.account)),
        patch.object(
            client,
            "async_get_organizations",
            AsyncMock(return_value=base.organizations),
        ),
        patch.object(
            client,
            "async_get_repositories",
            AsyncMock(return_value=base.repositories),
        ),
        patch.object(client, "async_get_rate_limit", get_rate_limit),
        patch(
            "custom_components.github_insights.repository_data."
            "async_collect_repository_insights",
            new=AsyncMock(return_value=()),
        ),
        patch(
            "custom_components.github_insights.copilot_data."
            "async_collect_copilot_billing",
            new=AsyncMock(
                side_effect=GitHubRateLimitError("rate_limited", retry_after=35)
            ),
        ),
    ):
        partial = await client.async_fetch_snapshot(
            repository_options=RepositoryCollectionOptions(
                selected=(),
                auto_discover=True,
                include_archived=True,
                include_forks=True,
                enabled_categories=frozenset({"copilot"}),
            ),
            copilot_organizations=("example-org",),
        )

    assert partial.retry_after == 35
    assert partial.errors["copilot"] == "rate_limited"
    assert partial.errors["rate_limit"] == "rate_limited"
    get_rate_limit.assert_not_awaited()


async def test_rate_limit_sensor_throttling_is_capability_failure() -> None:
    """The final rate-limit endpoint cannot invalidate successful data."""
    base = snapshot()
    client = GitHubClient(
        cast(ClientSession, FakeSession()),
        "github_pat_primary_fake",
        "https://github.com",
    )
    with (
        patch.object(client, "async_get_account", AsyncMock(return_value=base.account)),
        patch.object(
            client,
            "async_get_organizations",
            AsyncMock(return_value=base.organizations),
        ),
        patch.object(
            client,
            "async_get_repositories",
            AsyncMock(return_value=base.repositories),
        ),
        patch.object(
            client,
            "async_get_rate_limit",
            AsyncMock(side_effect=GitHubRateLimitError("rate_limited", retry_after=40)),
        ),
    ):
        partial = await client.async_fetch_snapshot()

    assert partial.organizations == base.organizations
    assert partial.repositories == base.repositories
    assert partial.rate_limit is None
    assert partial.retry_after == 40
    assert partial.errors["rate_limit"] == "rate_limited"


async def test_initial_account_rate_limit_remains_retriable() -> None:
    """The required account request still propagates rate-limit backoff."""
    client = GitHubClient(
        cast(ClientSession, FakeSession()),
        "github_pat_primary_fake",
        "https://github.com",
    )
    with patch.object(
        client,
        "async_get_account",
        AsyncMock(side_effect=GitHubRateLimitError("rate_limited", retry_after=20)),
    ):
        with pytest.raises(GitHubRateLimitError) as caught:
            await client.async_fetch_snapshot()

    assert caught.value.retry_after == 20


async def test_ghes_uses_compatible_api_version() -> None:
    """GHES requests retain the broadly supported API version."""
    session = FakeSession(
        FakeResponse(
            200,
            {
                "id": 42,
                "login": "octocat",
                "name": None,
                "avatar_url": "https://github.example.com/avatar",
                "html_url": "https://github.example.com/octocat",
                "public_repos": 1,
                "followers": 0,
                "following": 0,
            },
        )
    )
    client = GitHubClient(
        cast(ClientSession, session),
        "token",
        "https://github.example.com",
    )

    await client.async_get_account()

    assert session.requests[0]["headers"]["X-GitHub-Api-Version"] == "2022-11-28"


async def test_signed_report_download_is_bounded_and_credential_free() -> None:
    """Copilot report downloads use a strict host allow-list and no token."""
    session = FakeSession(FakeResponse(200, [{"daily_active_users": 3}]))
    client = GitHubClient(cast(ClientSession, session), "secret", "https://github.com")

    report = await client.async_get_signed_report(
        "https://copilot-reports.github.com/report.json"
    )

    assert report[0]["daily_active_users"] == 3
    assert "Authorization" not in session.requests[0]["headers"]

    with pytest.raises(GitHubAPIError, match="untrusted_report_url"):
        await client.async_get_signed_report("https://example.com/report.json")
