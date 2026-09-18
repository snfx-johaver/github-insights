"""Tests for the GitHub API client."""

from __future__ import annotations

from typing import cast

import pytest
from aiohttp import ClientSession

from custom_components.github_insights.api import (
    GitHubAuthenticationError,
    GitHubClient,
    GitHubInvalidServerError,
    GitHubRateLimitError,
    normalize_server,
)

from .helpers import FakeResponse, FakeSession


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
    client = GitHubClient(
        cast(ClientSession, session), "token", "https://github.com"
    )

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
    client = GitHubClient(
        cast(ClientSession, session), "token", "https://github.com"
    )

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
