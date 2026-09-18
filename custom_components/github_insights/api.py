"""Async GitHub API client for GitHub Insights."""

from __future__ import annotations

import ipaddress
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlencode

from aiohttp import ClientError, ClientResponse, ClientSession
from yarl import URL

from .const import API_VERSION, MAX_DISCOVERED_REPOSITORIES
from .models import (
    CapabilityStatus,
    GitHubAccount,
    GitHubCapability,
    GitHubOrganization,
    GitHubRateLimit,
    GitHubRepository,
    GitHubServer,
    GitHubSnapshot,
    JsonObject,
)


class GitHubInsightsError(Exception):
    """Base GitHub Insights error."""


class GitHubInvalidServerError(GitHubInsightsError):
    """Raised when a GitHub server URL is unsafe or malformed."""


class GitHubAuthenticationError(GitHubInsightsError):
    """Raised when GitHub rejects authentication."""


class GitHubPermissionError(GitHubInsightsError):
    """Raised when a token cannot access a capability."""


class GitHubRateLimitError(GitHubInsightsError):
    """Raised when GitHub requests backoff."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Initialize a rate-limit error."""
        super().__init__(message)
        self.retry_after = retry_after


class GitHubConnectionError(GitHubInsightsError):
    """Raised when GitHub cannot be reached."""


class GitHubAPIError(GitHubInsightsError):
    """Raised for an unexpected GitHub response."""

    def __init__(self, status: int, message: str) -> None:
        """Initialize an API error."""
        super().__init__(f"GitHub API returned HTTP {status}: {message}")
        self.status = status


def normalize_server(value: str) -> GitHubServer:
    """Normalize and validate a GitHub.com or GitHub Enterprise Server URL."""
    raw = value.strip().rstrip("/")
    try:
        url = URL(raw)
    except ValueError as err:
        raise GitHubInvalidServerError("invalid_url") from err

    if (
        url.scheme != "https"
        or not url.host
        or url.user is not None
        or url.password is not None
        or url.query_string
        or url.fragment
        or url.path not in {"", "/"}
    ):
        raise GitHubInvalidServerError("https_origin_required")

    hostname = url.host.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(
        ".localhost"
    ):
        raise GitHubInvalidServerError("local_host_forbidden")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        raise GitHubInvalidServerError("ip_literal_forbidden")

    port = f":{url.port}" if url.port else ""
    origin = f"https://{hostname}{port}"
    if hostname in {"github.com", "www.github.com", "api.github.com"}:
        return GitHubServer(
            web_url="https://github.com",
            api_url="https://api.github.com",
            hostname="github.com",
            is_dotcom=True,
        )

    return GitHubServer(
        web_url=origin,
        api_url=f"{origin}/api/v3",
        hostname=hostname,
        is_dotcom=False,
    )


class GitHubClient:
    """Small async GitHub REST client with conditional response caching."""

    def __init__(
        self,
        session: ClientSession,
        token: str,
        server: str,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._token = token
        self.server = normalize_server(server)
        self._etag_cache: dict[str, tuple[str, Any]] = {}
        self._token_scopes: tuple[str, ...] = ()

    @property
    def token_scopes(self) -> tuple[str, ...]:
        """Return scopes reported by GitHub."""
        return self._token_scopes

    async def async_get_account(self) -> GitHubAccount:
        """Return the authenticated account."""
        data = await self._request_json("GET", "/user")
        return GitHubAccount(
            id=_required_int(data, "id"),
            login=_required_str(data, "login"),
            name=_optional_str(data.get("name")),
            avatar_url=_required_str(data, "avatar_url"),
            html_url=_required_str(data, "html_url"),
            public_repos=_required_int(data, "public_repos"),
            total_private_repos=_optional_int(data.get("total_private_repos")),
            followers=_required_int(data, "followers"),
            following=_required_int(data, "following"),
        )

    async def async_get_organizations(self) -> tuple[GitHubOrganization, ...]:
        """Return organizations visible to the authenticated account."""
        items = await self._request_all_pages("/user/orgs")
        return tuple(
            GitHubOrganization(
                id=_required_int(item, "id"),
                login=_required_str(item, "login"),
                avatar_url=_required_str(item, "avatar_url"),
            )
            for item in items
        )

    async def async_get_repositories(self) -> tuple[GitHubRepository, ...]:
        """Return bounded repository discovery metadata."""
        items = await self._request_all_pages(
            "/user/repos",
            params={
                "affiliation": "owner,collaborator,organization_member",
                "sort": "full_name",
                "direction": "asc",
            },
            item_limit=MAX_DISCOVERED_REPOSITORIES,
        )
        return tuple(
            GitHubRepository(
                id=_required_int(item, "id"),
                full_name=_required_str(item, "full_name"),
                private=_required_bool(item, "private"),
                archived=_required_bool(item, "archived"),
                fork=_required_bool(item, "fork"),
                html_url=_required_str(item, "html_url"),
            )
            for item in items
        )

    async def async_get_rate_limit(self) -> GitHubRateLimit:
        """Return the core REST rate-limit state."""
        data = await self._request_json("GET", "/rate_limit")
        resources = _required_object(data, "resources")
        core = _required_object(resources, "core")
        return GitHubRateLimit(
            limit=_required_int(core, "limit"),
            remaining=_required_int(core, "remaining"),
            used=_required_int(core, "used"),
            reset_at=datetime.fromtimestamp(_required_int(core, "reset"), UTC),
        )

    async def async_fetch_snapshot(self) -> GitHubSnapshot:
        """Fetch account data and tolerate capability-specific failures."""
        account = await self.async_get_account()
        capabilities: dict[str, GitHubCapability] = {
            "account": GitHubCapability(CapabilityStatus.AVAILABLE)
        }
        errors: dict[str, str] = {}

        organizations: tuple[GitHubOrganization, ...] = ()
        repositories: tuple[GitHubRepository, ...] = ()
        rate_limit: GitHubRateLimit | None = None

        try:
            organizations = await self.async_get_organizations()
        except GitHubPermissionError:
            _record_capability_failure(
                capabilities, errors, "organizations", "missing_permission"
            )
        except (GitHubConnectionError, GitHubAPIError, GitHubRateLimitError):
            _record_capability_failure(
                capabilities,
                errors,
                "organizations",
                "temporarily_unavailable",
            )
        else:
            capabilities["organizations"] = GitHubCapability(CapabilityStatus.AVAILABLE)

        try:
            repositories = await self.async_get_repositories()
        except GitHubPermissionError:
            _record_capability_failure(
                capabilities, errors, "repositories", "missing_permission"
            )
        except (GitHubConnectionError, GitHubAPIError, GitHubRateLimitError):
            _record_capability_failure(
                capabilities,
                errors,
                "repositories",
                "temporarily_unavailable",
            )
        else:
            capabilities["repositories"] = GitHubCapability(CapabilityStatus.AVAILABLE)

        try:
            rate_limit = await self.async_get_rate_limit()
        except GitHubPermissionError:
            _record_capability_failure(
                capabilities, errors, "rate_limit", "missing_permission"
            )
        except (GitHubConnectionError, GitHubAPIError, GitHubRateLimitError):
            _record_capability_failure(
                capabilities,
                errors,
                "rate_limit",
                "temporarily_unavailable",
            )
        else:
            capabilities["rate_limit"] = GitHubCapability(CapabilityStatus.AVAILABLE)

        return GitHubSnapshot.create(
            account=account,
            organizations=organizations,
            repositories=repositories,
            rate_limit=rate_limit,
            token_scopes=self.token_scopes,
            capabilities=capabilities,
            fetched_at=datetime.now(UTC),
            errors=errors,
        )

    async def _request_all_pages(
        self,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        item_limit: int = MAX_DISCOVERED_REPOSITORIES,
    ) -> list[JsonObject]:
        """Follow GitHub Link pagination up to a bounded item count."""
        page = 1
        collected: list[JsonObject] = []
        while len(collected) < item_limit:
            page_params = dict(params or {})
            page_params.update({"page": str(page), "per_page": "100"})
            data, response = await self._request_json_with_response(
                "GET", path, params=page_params
            )
            if not isinstance(data, list):
                raise GitHubAPIError(response.status, "expected_list")
            for item in data:
                if not isinstance(item, dict):
                    raise GitHubAPIError(response.status, "invalid_list_item")
                collected.append(item)
                if len(collected) == item_limit:
                    break
            next_url = _next_link(response.headers.get("Link"))
            if next_url is None or len(collected) == item_limit:
                break
            self._validate_next_url(next_url)
            next_page = parse_qs(URL(next_url).query_string).get("page")
            page = int(next_page[0]) if next_page else page + 1
        return collected

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
    ) -> Any:
        """Request a JSON response."""
        data, _ = await self._request_json_with_response(method, path, params=params)
        return data

    async def _request_json_with_response(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
    ) -> tuple[Any, ClientResponse]:
        """Request JSON and retain an ETag-backed response cache."""
        url = f"{self.server.api_url}{path}"
        cache_key = f"{url}?{urlencode(sorted((params or {}).items()))}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        }
        headers["Authorization"] = "Bearer " + self._token
        cached = self._etag_cache.get(cache_key)
        if cached:
            headers["If-None-Match"] = cached[0]

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                params=params,
                allow_redirects=False,
            ) as response:
                self._record_scopes(response.headers)
                if response.status == 304 and cached:
                    return cached[1], response
                if response.status == 401:
                    raise GitHubAuthenticationError("invalid_auth")
                if response.status == 403:
                    retry_after = _retry_after(response)
                    if (
                        retry_after is not None
                        or response.headers.get("X-RateLimit-Remaining") == "0"
                    ):
                        raise GitHubRateLimitError(
                            "rate_limited", retry_after=retry_after
                        )
                    raise GitHubPermissionError("forbidden")
                if response.status == 429:
                    raise GitHubRateLimitError(
                        "rate_limited", retry_after=_retry_after(response)
                    )
                if response.status >= 400:
                    raise GitHubAPIError(
                        response.status, await _safe_error_message(response)
                    )
                if response.status == 204:
                    data: Any = {}
                else:
                    data = await response.json(content_type=None)
        except ClientError as err:
            raise GitHubConnectionError("cannot_connect") from err

        etag = response.headers.get("ETag")
        if etag:
            self._etag_cache[cache_key] = (etag, data)
        return data, response

    def _record_scopes(self, headers: Mapping[str, str]) -> None:
        """Record non-secret classic token scopes when GitHub reports them."""
        raw_scopes = headers.get("X-OAuth-Scopes", "")
        if raw_scopes:
            self._token_scopes = tuple(
                sorted(
                    scope.strip() for scope in raw_scopes.split(",") if scope.strip()
                )
            )

    def _validate_next_url(self, value: str) -> None:
        """Reject pagination links that leave the configured API origin."""
        next_url = URL(value)
        api_url = URL(self.server.api_url)
        if (
            next_url.scheme != api_url.scheme
            or next_url.host != api_url.host
            or next_url.port != api_url.port
            or not next_url.path.startswith(api_url.path)
        ):
            raise GitHubAPIError(502, "cross_origin_pagination")


def _next_link(value: str | None) -> str | None:
    """Extract the next URL from a GitHub Link header."""
    if not value:
        return None
    for part in value.split(","):
        url_part, *parameters = part.split(";")
        if any(parameter.strip() == 'rel="next"' for parameter in parameters):
            return url_part.strip().removeprefix("<").removesuffix(">")
    return None


def _record_capability_failure(
    capabilities: dict[str, GitHubCapability],
    errors: dict[str, str],
    key: str,
    reason: str,
) -> None:
    """Record one optional endpoint failure without exposing response details."""
    status = (
        CapabilityStatus.FORBIDDEN
        if reason == "missing_permission"
        else CapabilityStatus.TEMPORARILY_UNAVAILABLE
    )
    capabilities[key] = GitHubCapability(status, reason)
    errors[key] = reason


def _retry_after(response: ClientResponse) -> int | None:
    """Return a safe retry interval from response headers."""
    value = response.headers.get("Retry-After")
    if value and value.isdigit():
        return max(1, int(value))
    reset = response.headers.get("X-RateLimit-Reset")
    if reset and reset.isdigit():
        return max(1, int(reset) - int(datetime.now(UTC).timestamp()))
    return None


async def _safe_error_message(response: ClientResponse) -> str:
    """Extract a bounded public API error message without returning response data."""
    try:
        payload = await response.json(content_type=None)
    except (ClientError, json.JSONDecodeError):
        return "request_failed"
    if isinstance(payload, dict) and isinstance(payload.get("message"), str):
        return payload["message"][:160]
    return "request_failed"


def _required_object(value: Mapping[str, Any], key: str) -> JsonObject:
    item = value.get(key)
    if not isinstance(item, dict):
        raise GitHubAPIError(502, f"invalid_{key}")
    return item


def _required_str(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise GitHubAPIError(502, f"invalid_{key}")
    return item


def _required_int(value: Mapping[str, Any], key: str) -> int:
    item = value.get(key)
    if not isinstance(item, int):
        raise GitHubAPIError(502, f"invalid_{key}")
    return item


def _required_bool(value: Mapping[str, Any], key: str) -> bool:
    item = value.get(key)
    if not isinstance(item, bool):
        raise GitHubAPIError(502, f"invalid_{key}")
    return item


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None
