"""Async GitHub API client for GitHub Insights."""

from __future__ import annotations

import ipaddress
import json
import random
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any
from urllib.parse import parse_qs, urlencode

from aiohttp import ClientError, ClientResponse, ClientSession
from yarl import URL

from .const import (
    API_VERSION_DOTCOM,
    API_VERSION_GHES,
    MAX_BUDGET_PAGES,
    MAX_DISCOVERED_REPOSITORIES,
)
from .models import (
    BillingBudget,
    BillingPeriod,
    BillingScope,
    BillingScopeData,
    BillingScopeType,
    BillingSnapshot,
    BillingUsageItem,
    BillingUsageReport,
    BudgetAlerting,
    CapabilityStatus,
    GitHubAccount,
    GitHubCapability,
    GitHubCopilotUsage,
    GitHubOrganization,
    GitHubRateLimit,
    GitHubRepository,
    GitHubRepositoryInsights,
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


@dataclass(frozen=True, slots=True)
class GitHubPage:
    """Bounded paginated result with coverage metadata."""

    items: tuple[JsonObject, ...]
    complete: bool


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
        self.token_type = (
            "fine_grained_pat" if token.startswith("github_pat_") else "classic_pat"
        )
        self.server = normalize_server(server)
        self._etag_cache: dict[str, tuple[str, Any]] = {}
        self._token_scopes: tuple[str, ...] = ()
        self._secondary_rate_limit_attempts = 0

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
        return tuple(_repository(item) for item in items)

    async def async_get_json(
        self,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
    ) -> Any:
        """Return JSON from a same-origin GitHub API path."""
        return await self._request_json("GET", path, params=params)

    async def async_get_page(
        self,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        item_limit: int,
    ) -> GitHubPage:
        """Return bounded items and whether all available pages were covered."""
        items, complete = await self._request_pages(
            path,
            params=params,
            item_limit=item_limit,
        )
        return GitHubPage(tuple(items), complete)

    async def async_get_signed_report(self, value: str) -> tuple[JsonObject, ...]:
        """Download a bounded GitHub-hosted Copilot report without credentials."""
        url = URL(value)
        hostname = (url.host or "").lower().rstrip(".")
        if (
            url.scheme != "https"
            or url.user is not None
            or url.password is not None
            or url.fragment
            or not (
                hostname == "copilot-reports.github.com"
                or hostname == "githubusercontent.com"
                or hostname.endswith(".githubusercontent.com")
            )
        ):
            raise GitHubAPIError(502, "untrusted_report_url")
        try:
            async with self._session.get(
                url,
                headers={"Accept": "application/x-ndjson, application/json"},
                allow_redirects=False,
            ) as response:
                if response.status >= 400:
                    raise GitHubAPIError(response.status, "report_download_failed")
                if int(response.headers.get("Content-Length", "0") or 0) > 10_000_000:
                    raise GitHubAPIError(413, "report_too_large")
                raw = await response.read()
        except ClientError as err:
            raise GitHubConnectionError("cannot_download_report") from err
        if len(raw) > 10_000_000:
            raise GitHubAPIError(413, "report_too_large")
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as err:
            raise GitHubAPIError(502, "invalid_report_encoding") from err
        try:
            payload = json.loads(decoded)
        except json.JSONDecodeError:
            try:
                payload = [
                    json.loads(line) for line in decoded.splitlines() if line.strip()
                ]
            except json.JSONDecodeError as err:
                raise GitHubAPIError(502, "invalid_report") from err
        if isinstance(payload, dict):
            return (payload,)
        if isinstance(payload, list) and all(
            isinstance(item, dict) for item in payload
        ):
            return tuple(payload)
        raise GitHubAPIError(502, "invalid_report")

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

    async def async_get_billing_usage(
        self,
        scope: BillingScope,
        *,
        year: int | None = None,
        month: int | None = None,
    ) -> BillingUsageReport:
        """Return official enhanced-billing detail and summary reports."""
        if not self.server.is_dotcom:
            raise GitHubAPIError(404, "enhanced_billing_unsupported")
        now = datetime.now(UTC)
        selected_year = year or now.year
        selected_month = month or now.month
        params = {"year": str(selected_year), "month": str(selected_month)}
        base_path = _billing_scope_path(scope)
        detail_items: tuple[BillingUsageItem, ...] = ()
        summary_items: tuple[BillingUsageItem, ...] = ()
        unavailable: list[str] = []
        detail_error: GitHubInsightsError | None = None
        summary_error: GitHubInsightsError | None = None
        try:
            detail = await self._request_json(
                "GET", f"{base_path}/usage", params=params
            )
            detail_items = _parse_detail_usage_items(
                _as_object(detail, "invalid_usage_report").get("usageItems")
            )
        except GitHubInsightsError as err:
            if isinstance(err, GitHubAuthenticationError) or (
                isinstance(err, GitHubAPIError) and err.status == 502
            ):
                raise
            detail_error = err
            unavailable.append("detail")
        try:
            summary = await self._request_json(
                "GET", f"{base_path}/usage/summary", params=params
            )
            summary_object = _as_object(summary, "invalid_usage_summary")
            time_period = _required_object(summary_object, "timePeriod")
            period = BillingPeriod(
                year=_required_int(time_period, "year"),
                month=_optional_int(time_period.get("month")),
                day=_optional_int(time_period.get("day")),
            )
            summary_items = _parse_summary_usage_items(summary_object.get("usageItems"))
        except GitHubInsightsError as err:
            if isinstance(err, GitHubAuthenticationError) or (
                isinstance(err, GitHubAPIError) and err.status == 502
            ):
                raise
            summary_error = err
            unavailable.append("summary")
            period = BillingPeriod(selected_year, selected_month)
        if detail_error is not None and summary_error is not None:
            raise summary_error
        return BillingUsageReport(
            scope=scope,
            period=period,
            summary_items=summary_items,
            detail_items=detail_items,
            unavailable_sections=tuple(unavailable),
        )

    async def async_get_budgets(
        self,
        scope: BillingScope,
    ) -> tuple[BillingBudget, ...]:
        """Return all documented budgets for an organization or enterprise."""
        if scope.scope_type is BillingScopeType.USER:
            raise GitHubAPIError(404, "personal_budgets_unsupported")
        if not self.server.is_dotcom:
            raise GitHubAPIError(404, "enhanced_billing_unsupported")
        base_path = f"{_billing_scope_path(scope)}/budgets"
        budgets: list[BillingBudget] = []
        for page in range(1, MAX_BUDGET_PAGES + 1):
            data = _as_object(
                await self._request_json(
                    "GET",
                    base_path,
                    params={"page": str(page), "per_page": "100"},
                ),
                "invalid_budgets",
            )
            raw_budgets = data.get("budgets")
            if not isinstance(raw_budgets, list):
                raise GitHubAPIError(502, "invalid_budgets")
            budgets.extend(_parse_budget(item, scope) for item in raw_budgets)
            if data.get("has_next_page") is not True:
                break
        else:
            raise GitHubAPIError(502, "budget_page_limit_exceeded")
        return tuple(budgets)

    async def async_create_budget(
        self,
        scope: BillingScope,
        payload: Mapping[str, Any],
    ) -> BillingBudget:
        """Create a documented organization or enterprise budget."""
        data = _as_object(
            await self._request_json(
                "POST",
                f"{_billing_scope_path(scope)}/budgets",
                json_data=payload,
            ),
            "invalid_budget",
        )
        return _parse_budget(_required_object(data, "budget"), scope)

    async def async_update_budget(
        self,
        scope: BillingScope,
        budget_id: str,
        payload: Mapping[str, Any],
    ) -> BillingBudget:
        """Update a documented organization or enterprise budget."""
        data = _as_object(
            await self._request_json(
                "PATCH",
                f"{_billing_scope_path(scope)}/budgets/{budget_id}",
                json_data=payload,
            ),
            "invalid_budget",
        )
        return _parse_budget(_required_object(data, "budget"), scope)

    async def async_delete_budget(
        self,
        scope: BillingScope,
        budget_id: str,
    ) -> None:
        """Delete a documented organization or enterprise budget."""
        await self._request_json(
            "DELETE", f"{_billing_scope_path(scope)}/budgets/{budget_id}"
        )

    async def async_fetch_billing_snapshot(
        self,
        scopes: tuple[BillingScope, ...],
    ) -> BillingSnapshot:
        """Fetch configured billing scopes with capability-level isolation."""
        results: dict[str, BillingScopeData] = {}
        errors: dict[str, str] = {}
        for scope in scopes:
            usage: BillingUsageReport | None = None
            budgets: tuple[BillingBudget, ...] = ()
            scope_errors: dict[str, str] = {}
            if not self.server.is_dotcom:
                usage_capability = GitHubCapability(
                    CapabilityStatus.UNSUPPORTED, "github_dotcom_only"
                )
            elif self.token_type == "fine_grained_pat":
                usage_capability = GitHubCapability(
                    CapabilityStatus.FORBIDDEN,
                    "classic_pat_required",
                )
                scope_errors["usage"] = "classic_pat_required"
            else:
                try:
                    usage = await self.async_get_billing_usage(scope)
                except GitHubPermissionError:
                    usage_capability = GitHubCapability(
                        CapabilityStatus.FORBIDDEN,
                        "classic_pat_required_or_missing_billing_permission",
                    )
                    scope_errors["usage"] = usage_capability.reason or ""
                except GitHubAPIError as err:
                    if err.status == 404:
                        usage_capability = GitHubCapability(
                            CapabilityStatus.UNSUPPORTED,
                            "enhanced_billing_unavailable",
                        )
                    else:
                        usage_capability = GitHubCapability(
                            CapabilityStatus.TEMPORARILY_UNAVAILABLE,
                            "billing_usage_failed",
                        )
                    scope_errors["usage"] = usage_capability.reason or ""
                except GitHubConnectionError:
                    usage_capability = GitHubCapability(
                        CapabilityStatus.TEMPORARILY_UNAVAILABLE,
                        "billing_usage_failed",
                    )
                    scope_errors["usage"] = usage_capability.reason or ""
                else:
                    usage_capability = GitHubCapability(CapabilityStatus.AVAILABLE)

            if scope.scope_type is BillingScopeType.USER:
                budget_capability = GitHubCapability(
                    CapabilityStatus.UNSUPPORTED,
                    "personal_budget_api_not_documented",
                )
            elif not self.server.is_dotcom:
                budget_capability = GitHubCapability(
                    CapabilityStatus.UNSUPPORTED, "github_dotcom_only"
                )
            else:
                try:
                    budgets = await self.async_get_budgets(scope)
                except GitHubPermissionError:
                    budget_capability = GitHubCapability(
                        CapabilityStatus.FORBIDDEN,
                        "missing_budget_permission",
                    )
                    scope_errors["budgets"] = budget_capability.reason or ""
                except GitHubAPIError as err:
                    if err.status == 404:
                        budget_capability = GitHubCapability(
                            CapabilityStatus.UNSUPPORTED,
                            "enhanced_billing_or_budgets_unavailable",
                        )
                    else:
                        budget_capability = GitHubCapability(
                            CapabilityStatus.TEMPORARILY_UNAVAILABLE,
                            "budgets_failed",
                        )
                    scope_errors["budgets"] = budget_capability.reason or ""
                except GitHubConnectionError:
                    budget_capability = GitHubCapability(
                        CapabilityStatus.TEMPORARILY_UNAVAILABLE,
                        "budgets_failed",
                    )
                    scope_errors["budgets"] = budget_capability.reason or ""
                else:
                    budget_capability = GitHubCapability(CapabilityStatus.AVAILABLE)

            results[scope.key] = BillingScopeData(
                scope=scope,
                usage=usage,
                budgets=budgets,
                usage_capability=usage_capability,
                budget_capability=budget_capability,
                errors=MappingProxyType(scope_errors),
            )
            errors.update(
                {f"{scope.key}:{key}": value for key, value in scope_errors.items()}
            )
        return BillingSnapshot.create(
            scopes=results,
            fetched_at=datetime.now(UTC),
            errors=errors,
        )

    async def async_fetch_snapshot(
        self,
        *,
        repository_options: object | None = None,
        copilot_organizations: tuple[str, ...] = (),
        copilot_billing_client: GitHubClient | None = None,
    ) -> GitHubSnapshot:
        """Fetch account data and tolerate capability-specific failures."""
        account = await self.async_get_account()
        capabilities: dict[str, GitHubCapability] = {
            "account": GitHubCapability(CapabilityStatus.AVAILABLE)
        }
        errors: dict[str, str] = {}

        organizations: tuple[GitHubOrganization, ...] = ()
        repositories: tuple[GitHubRepository, ...] = ()
        rate_limit: GitHubRateLimit | None = None
        repository_insights: tuple[GitHubRepositoryInsights, ...] = ()
        copilot: tuple[GitHubCopilotUsage, ...] = ()
        retry_after: int | None = None
        rate_limited = False
        repository_collection_requested = False
        repository_categories: frozenset[str] = frozenset()
        if repository_options is not None:
            from .repository_data import RepositoryCollectionOptions

            if isinstance(repository_options, RepositoryCollectionOptions):
                repository_collection_requested = True
                repository_categories = repository_options.enabled_categories

        try:
            organizations = await self.async_get_organizations()
        except GitHubRateLimitError as err:
            retry_after = err.retry_after
            rate_limited = True
            _record_capability_failure(
                capabilities, errors, "organizations", "rate_limited"
            )
        except GitHubPermissionError:
            _record_capability_failure(
                capabilities, errors, "organizations", "missing_permission"
            )
        except (GitHubConnectionError, GitHubAPIError):
            _record_capability_failure(
                capabilities,
                errors,
                "organizations",
                "temporarily_unavailable",
            )
        else:
            capabilities["organizations"] = GitHubCapability(CapabilityStatus.AVAILABLE)

        if rate_limited:
            _record_capability_failure(
                capabilities, errors, "repositories", "rate_limited"
            )
            if repository_collection_requested:
                _record_repository_rate_limit(
                    repository_categories, capabilities, errors
                )
        else:
            try:
                repositories = await self.async_get_repositories()
            except GitHubRateLimitError as err:
                retry_after = err.retry_after
                rate_limited = True
                _record_capability_failure(
                    capabilities, errors, "repositories", "rate_limited"
                )
                if repository_collection_requested:
                    _record_repository_rate_limit(
                        repository_categories, capabilities, errors
                    )
            except GitHubPermissionError:
                _record_capability_failure(
                    capabilities, errors, "repositories", "missing_permission"
                )
            except (GitHubConnectionError, GitHubAPIError):
                _record_capability_failure(
                    capabilities,
                    errors,
                    "repositories",
                    "temporarily_unavailable",
                )
            else:
                capabilities["repositories"] = GitHubCapability(
                    CapabilityStatus.AVAILABLE
                )
                if repository_options is not None:
                    from .repository_data import (
                        async_collect_repository_insights,
                    )

                    if isinstance(repository_options, RepositoryCollectionOptions):
                        try:
                            repository_insights = (
                                await async_collect_repository_insights(
                                    self, repositories, repository_options
                                )
                            )
                        except GitHubRateLimitError as err:
                            retry_after = err.retry_after
                            rate_limited = True
                            _record_repository_rate_limit(
                                repository_categories, capabilities, errors
                            )
                        except (GitHubConnectionError, GitHubAPIError):
                            _record_capability_failure(
                                capabilities,
                                errors,
                                "repository_insights",
                                "temporarily_unavailable",
                            )
                        else:
                            _record_repository_capabilities(
                                repository_insights,
                                repository_options.enabled_categories,
                                capabilities,
                                errors,
                            )

        if "copilot" in repository_categories:
            if rate_limited:
                _record_capability_failure(
                    capabilities, errors, "copilot", "rate_limited"
                )
            else:
                from .copilot_data import async_collect_copilot_billing

                try:
                    (
                        copilot,
                        copilot_capabilities,
                        copilot_errors,
                    ) = await async_collect_copilot_billing(
                        self,
                        account,
                        tuple(
                            organization
                            for organization in organizations
                            if organization.login in set(copilot_organizations)
                        ),
                        billing_client=copilot_billing_client,
                    )
                except GitHubRateLimitError as err:
                    retry_after = err.retry_after
                    rate_limited = True
                    _record_capability_failure(
                        capabilities, errors, "copilot", "rate_limited"
                    )
                else:
                    capabilities.update(copilot_capabilities)
                    errors.update(copilot_errors)

        if rate_limited:
            _record_capability_failure(
                capabilities, errors, "rate_limit", "rate_limited"
            )
        else:
            try:
                rate_limit = await self.async_get_rate_limit()
            except GitHubRateLimitError as err:
                retry_after = err.retry_after
                _record_capability_failure(
                    capabilities, errors, "rate_limit", "rate_limited"
                )
            except GitHubPermissionError:
                _record_capability_failure(
                    capabilities, errors, "rate_limit", "missing_permission"
                )
            except (GitHubConnectionError, GitHubAPIError):
                _record_capability_failure(
                    capabilities,
                    errors,
                    "rate_limit",
                    "temporarily_unavailable",
                )
            else:
                capabilities["rate_limit"] = GitHubCapability(
                    CapabilityStatus.AVAILABLE
                )

        return GitHubSnapshot.create(
            account=account,
            organizations=organizations,
            repositories=repositories,
            repository_insights=repository_insights,
            copilot=copilot,
            rate_limit=rate_limit,
            token_scopes=self.token_scopes,
            capabilities=capabilities,
            fetched_at=datetime.now(UTC),
            errors=errors,
            retry_after=retry_after,
        )

    async def _request_all_pages(
        self,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        item_limit: int = MAX_DISCOVERED_REPOSITORIES,
    ) -> list[JsonObject]:
        """Follow GitHub Link pagination up to a bounded item count."""
        items, _ = await self._request_pages(
            path,
            params=params,
            item_limit=item_limit,
        )
        return items

    async def _request_pages(
        self,
        path: str,
        *,
        params: Mapping[str, str] | None,
        item_limit: int,
    ) -> tuple[list[JsonObject], bool]:
        """Follow GitHub Link pagination with a hard coverage boundary."""
        page = 1
        collected: list[JsonObject] = []
        complete = True
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
            if next_url is None:
                break
            if len(collected) == item_limit:
                complete = False
                break
            self._validate_next_url(next_url)
            next_page = parse_qs(URL(next_url).query_string).get("page")
            page = int(next_page[0]) if next_page else page + 1
        return collected, complete

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json_data: Mapping[str, Any] | None = None,
    ) -> Any:
        """Request a JSON response."""
        data, _ = await self._request_json_with_response(
            method, path, params=params, json_data=json_data
        )
        return data

    async def _request_json_with_response(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json_data: Mapping[str, Any] | None = None,
    ) -> tuple[Any, ClientResponse]:
        """Request JSON and retain an ETag-backed response cache."""
        url = f"{self.server.api_url}{path}"
        cache_key = f"{url}?{urlencode(sorted((params or {}).items()))}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": (
                API_VERSION_DOTCOM if self.server.is_dotcom else API_VERSION_GHES
            ),
        }
        headers["Authorization"] = "Bearer " + self._token
        cached = self._etag_cache.get(cache_key) if method == "GET" else None
        if cached:
            headers["If-None-Match"] = cached[0]

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data,
                allow_redirects=False,
            ) as response:
                self._record_scopes(response.headers)
                if response.status == 304 and cached:
                    return cached[1], response
                if response.status == 401:
                    raise GitHubAuthenticationError("invalid_auth")
                if response.status == 403:
                    retry_after = _retry_after(response)
                    message = await _safe_error_message(response)
                    if (
                        retry_after is not None
                        or response.headers.get("X-RateLimit-Remaining") == "0"
                        or "secondary rate limit" in message.lower()
                        or "abuse detection" in message.lower()
                    ):
                        if retry_after is None:
                            self._secondary_rate_limit_attempts += 1
                            retry_after = min(
                                900,
                                int(
                                    2**self._secondary_rate_limit_attempts
                                    + random.uniform(0, 3)
                                ),
                            )
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
                self._secondary_rate_limit_attempts = 0
        except ClientError as err:
            raise GitHubConnectionError("cannot_connect") from err

        etag = response.headers.get("ETag")
        if etag and method == "GET":
            self._etag_cache[cache_key] = (etag, data)
        elif method != "GET":
            self._etag_cache.clear()
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


def _billing_scope_path(scope: BillingScope) -> str:
    """Return the documented enhanced-billing base path."""
    if scope.scope_type is BillingScopeType.USER:
        return f"/users/{scope.name}/settings/billing"
    if scope.scope_type is BillingScopeType.ORGANIZATION:
        return f"/organizations/{scope.name}/settings/billing"
    return f"/enterprises/{scope.name}/settings/billing"


def _parse_summary_usage_items(value: Any) -> tuple[BillingUsageItem, ...]:
    """Parse aggregated usage rows with authoritative quantities and amounts."""
    return tuple(
        BillingUsageItem(
            product=_required_str(item, "product"),
            sku=_required_str(item, "sku"),
            unit_type=_required_str(item, "unitType"),
            price_per_unit=_required_decimal(item, "pricePerUnit"),
            gross_quantity=_required_decimal(item, "grossQuantity"),
            gross_amount=_required_decimal(item, "grossAmount"),
            discount_quantity=_required_decimal(item, "discountQuantity"),
            discount_amount=_required_decimal(item, "discountAmount"),
            net_quantity=_required_decimal(item, "netQuantity"),
            net_amount=_required_decimal(item, "netAmount"),
            organization_name=_optional_str(item.get("organization")),
        )
        for item in _object_list(value, "invalid_usage_items")
    )


def _parse_detail_usage_items(value: Any) -> tuple[BillingUsageItem, ...]:
    """Parse detailed usage rows used for dated repository breakdowns."""
    return tuple(
        BillingUsageItem(
            product=_required_str(item, "product"),
            sku=_required_str(item, "sku"),
            unit_type=_required_str(item, "unitType"),
            price_per_unit=_required_decimal(item, "pricePerUnit"),
            gross_quantity=_required_decimal(item, "quantity"),
            gross_amount=_required_decimal(item, "grossAmount"),
            discount_quantity=None,
            discount_amount=_required_decimal(item, "discountAmount"),
            net_quantity=None,
            net_amount=_required_decimal(item, "netAmount"),
            date=_optional_str(item.get("date")),
            repository_name=_optional_str(item.get("repositoryName")),
            organization_name=_optional_str(item.get("organizationName")),
        )
        for item in _object_list(value, "invalid_usage_items")
    )


def _parse_budget(value: Mapping[str, Any], scope: BillingScope) -> BillingBudget:
    """Parse a budget while tolerating documented optional response fields."""
    item = _as_object(value, "invalid_budget")
    alerting_raw = item.get("budget_alerting")
    alerting = (
        _as_object(alerting_raw, "invalid_budget_alerting")
        if alerting_raw is not None
        else {}
    )
    recipients = alerting.get("alert_recipients", [])
    if not isinstance(recipients, list) or not all(
        isinstance(recipient, str) for recipient in recipients
    ):
        raise GitHubAPIError(502, "invalid_alert_recipients")
    return BillingBudget(
        id=_required_identifier(item, "id"),
        scope=scope,
        budget_scope=(
            _optional_str(item.get("budget_scope")) or scope.scope_type.value
        ),
        entity_name=_optional_str(item.get("budget_entity_name")) or "",
        budget_type=_optional_str(item.get("budget_type")) or "",
        product_sku=_optional_str(item.get("budget_product_sku")) or "",
        amount=_required_decimal(item, "budget_amount"),
        consumed_amount=_decimal_or_zero(item.get("consumed_amount")),
        prevent_further_usage=item.get("prevent_further_usage") is True,
        alerting=BudgetAlerting(
            will_alert=alerting.get("will_alert") is True,
            recipients=tuple(recipients),
        ),
        created_at=_optional_datetime(item.get("created_at")),
        updated_at=_optional_datetime(item.get("updated_at")),
        expires_at=_optional_str(item.get("expires_at")),
    )


def _as_object(value: Any, message: str) -> JsonObject:
    """Return a JSON object or raise a typed API error."""
    if not isinstance(value, dict):
        raise GitHubAPIError(502, message)
    return value


def _object_list(value: Any, message: str) -> tuple[JsonObject, ...]:
    """Return a strictly validated JSON object list."""
    if not isinstance(value, list):
        raise GitHubAPIError(502, message)
    return tuple(_as_object(item, message) for item in value)


def _required_identifier(value: Mapping[str, Any], key: str) -> str:
    """Return a non-empty string or integer identifier."""
    item = value.get(key)
    if isinstance(item, (str, int)) and not isinstance(item, bool) and str(item):
        return str(item)
    raise GitHubAPIError(502, f"invalid_{key}")


def _required_decimal(value: Mapping[str, Any], key: str) -> Decimal:
    """Parse a required JSON number without binary floating-point loss."""
    if key not in value:
        raise GitHubAPIError(502, f"invalid_{key}")
    try:
        return Decimal(str(value[key]))
    except (InvalidOperation, ValueError) as err:
        raise GitHubAPIError(502, f"invalid_{key}") from err


def _decimal_or_zero(value: Any) -> Decimal:
    """Parse an optional JSON number."""
    if value is None:
        return Decimal()
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as err:
        raise GitHubAPIError(502, "invalid_decimal") from err


def _optional_datetime(value: Any) -> datetime | None:
    """Parse an optional GitHub ISO timestamp."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
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


def _record_repository_capabilities(
    repositories: tuple[GitHubRepositoryInsights, ...],
    enabled_categories: frozenset[str],
    capabilities: dict[str, GitHubCapability],
    errors: dict[str, str],
) -> None:
    """Summarize per-repository capability state without exposing repo names."""
    for category in enabled_categories & {
        "workflows",
        "releases",
        "activity",
        "deployments",
        "traffic",
        "security",
    }:
        category_capabilities = tuple(
            repository.capabilities.get(category) for repository in repositories
        )
        if any(
            capability is not None and capability.status is CapabilityStatus.AVAILABLE
            for capability in category_capabilities
        ):
            capabilities[category] = GitHubCapability(CapabilityStatus.AVAILABLE)
            continue
        if category_capabilities:
            capability = next(
                (item for item in category_capabilities if item is not None),
                GitHubCapability(
                    CapabilityStatus.TEMPORARILY_UNAVAILABLE,
                    "temporarily_unavailable",
                ),
            )
            capabilities[category] = capability
            errors[category] = capability.reason or capability.status


def _record_repository_rate_limit(
    enabled_categories: frozenset[str],
    capabilities: dict[str, GitHubCapability],
    errors: dict[str, str],
) -> None:
    """Mark repository collection and enabled categories as rate limited."""
    _record_capability_failure(
        capabilities, errors, "repository_insights", "rate_limited"
    )
    for category in enabled_categories & {
        "workflows",
        "releases",
        "activity",
        "deployments",
        "traffic",
        "security",
    }:
        _record_capability_failure(capabilities, errors, category, "rate_limited")


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
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str):
            return message[:160]
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


def _repository(item: Mapping[str, Any]) -> GitHubRepository:
    """Normalize repository metadata from discovery or detail responses."""
    full_name = _required_str(item, "full_name")
    license_value = item.get("license")
    license_name = (
        _optional_str(license_value.get("name"))
        if isinstance(license_value, dict)
        else None
    )
    return GitHubRepository(
        id=_required_int(item, "id"),
        name=_optional_str(item.get("name")) or full_name.rsplit("/", 1)[-1],
        full_name=full_name,
        description=_optional_str(item.get("description")),
        private=_required_bool(item, "private"),
        visibility=_optional_str(item.get("visibility"))
        or ("private" if _required_bool(item, "private") else "public"),
        archived=_required_bool(item, "archived"),
        fork=_required_bool(item, "fork"),
        html_url=_required_str(item, "html_url"),
        default_branch=_optional_str(item.get("default_branch")) or "",
        language=_optional_str(item.get("language")),
        license_name=license_name,
        stargazers_count=_optional_int(item.get("stargazers_count")) or 0,
        watchers_count=_optional_int(item.get("subscribers_count"))
        or _optional_int(item.get("watchers_count"))
        or 0,
        forks_count=_optional_int(item.get("forks_count")) or 0,
        open_issues_count=_optional_int(item.get("open_issues_count")) or 0,
        has_discussions=_optional_bool(item.get("has_discussions")) or False,
        size_kb=_optional_int(item.get("size")) or 0,
        pushed_at=_optional_datetime(item.get("pushed_at")),
    )


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
