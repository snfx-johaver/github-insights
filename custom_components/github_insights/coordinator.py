"""Data update coordinator for GitHub Insights."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    GitHubAuthenticationError,
    GitHubClient,
    GitHubConnectionError,
    GitHubInsightsError,
    GitHubRateLimitError,
)
from .const import (
    CONF_ACCOUNT_LOGIN,
    CONF_ACTIONS_INCLUDED_MINUTES,
    CONF_AUTO_DISCOVER,
    CONF_BILLING_ENTERPRISE,
    CONF_BILLING_INTERVAL,
    CONF_BILLING_ORGANIZATIONS,
    CONF_ENABLED_CATEGORIES,
    CONF_INCLUDE_ARCHIVED,
    CONF_INCLUDE_FORKS,
    CONF_MAX_REPOSITORIES,
    CONF_ORGANIZATIONS,
    CONF_PERSONAL_BILLING,
    CONF_REPOSITORIES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_ACTIONS_INCLUDED_MINUTES,
    DEFAULT_AUTO_DISCOVER,
    DEFAULT_BILLING_INTERVAL_MINUTES,
    DEFAULT_ENABLED_CATEGORIES,
    DEFAULT_INCLUDE_ARCHIVED,
    DEFAULT_INCLUDE_FORKS,
    DEFAULT_MAX_REPOSITORIES,
    DEFAULT_PERSONAL_BILLING,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    LOGGER,
)
from .models import (
    BillingMutation,
    BillingScope,
    BillingScopeData,
    BillingScopeType,
    BillingSnapshot,
    CapabilityStatus,
    GitHubCapability,
    GitHubCopilotUsage,
    GitHubRepositoryInsights,
    GitHubSecurityAlerts,
    GitHubSnapshot,
)
from .repairs import (
    async_update_billing_issues,
    async_update_capability_issues,
    async_update_configured_allowance_issue,
)
from .repository_data import RepositoryCollectionOptions


@dataclass(slots=True)
class GitHubInsightsRuntimeData:
    """Runtime objects for one GitHub Insights config entry."""

    client: GitHubClient
    billing_client: GitHubClient | None
    coordinator: GitHubInsightsCoordinator
    billing_coordinator: GitHubInsightsBillingCoordinator


type GitHubInsightsConfigEntry = ConfigEntry[GitHubInsightsRuntimeData]


class GitHubInsightsCoordinator(DataUpdateCoordinator[GitHubSnapshot]):
    """Coordinate account, repository discovery, and rate-limit data."""

    config_entry: GitHubInsightsConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GitHubInsightsConfigEntry,
        client: GitHubClient,
        billing_client: GitHubClient | None,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.billing_client = billing_client
        interval = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES
        )
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
            always_update=False,
        )

    async def _async_update_data(self) -> GitHubSnapshot:
        """Fetch a normalized GitHub snapshot."""
        try:
            snapshot = await self.client.async_fetch_snapshot(
                repository_options=RepositoryCollectionOptions(
                    selected=tuple(
                        self.config_entry.options.get(CONF_REPOSITORIES, ())
                    ),
                    auto_discover=self.config_entry.options.get(
                        CONF_AUTO_DISCOVER, DEFAULT_AUTO_DISCOVER
                    ),
                    include_archived=self.config_entry.options.get(
                        CONF_INCLUDE_ARCHIVED, DEFAULT_INCLUDE_ARCHIVED
                    ),
                    include_forks=self.config_entry.options.get(
                        CONF_INCLUDE_FORKS, DEFAULT_INCLUDE_FORKS
                    ),
                    enabled_categories=frozenset(
                        self.config_entry.options.get(
                            CONF_ENABLED_CATEGORIES,
                            DEFAULT_ENABLED_CATEGORIES,
                        )
                    ),
                    repository_limit=self.config_entry.options.get(
                        CONF_MAX_REPOSITORIES, DEFAULT_MAX_REPOSITORIES
                    ),
                ),
                copilot_organizations=tuple(
                    self.config_entry.options.get(CONF_ORGANIZATIONS, ())
                ),
                copilot_billing_client=self.billing_client,
            )
        except GitHubAuthenticationError as err:
            raise ConfigEntryAuthFailed("GitHub credentials were rejected") from err
        except GitHubRateLimitError as err:
            raise UpdateFailed(
                "GitHub rate limit reached", retry_after=err.retry_after
            ) from err
        except GitHubConnectionError as err:
            raise UpdateFailed("Unable to connect to GitHub") from err
        except GitHubInsightsError as err:
            raise UpdateFailed(f"GitHub API error: {err}") from err

        snapshot = _merge_last_known_good(self.data, snapshot)
        async_update_capability_issues(
            self.hass, self.config_entry.entry_id, snapshot.errors
        )
        return snapshot


class GitHubInsightsBillingCoordinator(DataUpdateCoordinator[BillingSnapshot]):
    """Coordinate enhanced-billing usage and budgets independently."""

    config_entry: GitHubInsightsConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GitHubInsightsConfigEntry,
        client: GitHubClient | None,
    ) -> None:
        """Initialize the billing coordinator."""
        self.client = client
        self._last_mutation: BillingMutation | None = None
        interval = entry.options.get(
            CONF_BILLING_INTERVAL, DEFAULT_BILLING_INTERVAL_MINUTES
        )
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_billing",
            update_interval=timedelta(minutes=interval),
            always_update=False,
        )

    @property
    def scopes(self) -> tuple[BillingScope, ...]:
        """Return configured official billing scopes."""
        options = self.config_entry.options
        scopes: list[BillingScope] = []
        if options.get(CONF_PERSONAL_BILLING, DEFAULT_PERSONAL_BILLING):
            scopes.append(
                BillingScope(
                    BillingScopeType.USER,
                    str(self.config_entry.data[CONF_ACCOUNT_LOGIN]),
                )
            )
        organizations = options.get(
            CONF_BILLING_ORGANIZATIONS,
            options.get(CONF_ORGANIZATIONS, []),
        )
        scopes.extend(
            BillingScope(BillingScopeType.ORGANIZATION, str(organization))
            for organization in organizations
        )
        enterprise = str(options.get(CONF_BILLING_ENTERPRISE, "")).strip()
        if enterprise:
            scopes.append(BillingScope(BillingScopeType.ENTERPRISE, enterprise))
        return tuple(scopes)

    async def _async_update_data(self) -> BillingSnapshot:
        """Fetch isolated billing scope snapshots."""
        if self.client is None:
            snapshot = _unavailable_billing_snapshot(
                self.scopes, "billing_token_not_configured"
            )
        else:
            try:
                snapshot = await self.client.async_fetch_billing_snapshot(self.scopes)
            except GitHubAuthenticationError:
                snapshot = _unavailable_billing_snapshot(
                    self.scopes, "billing_token_invalid"
                )
            except GitHubRateLimitError as err:
                raise UpdateFailed(
                    "GitHub billing rate limit reached", retry_after=err.retry_after
                ) from err
            except GitHubConnectionError as err:
                raise UpdateFailed("Unable to connect to GitHub billing") from err
            except GitHubInsightsError as err:
                raise UpdateFailed(f"GitHub billing API error: {err}") from err

        snapshot = _merge_billing_last_known_good(self.data, snapshot)
        if self._last_mutation is not None:
            snapshot = replace(snapshot, last_mutation=self._last_mutation)
        async_update_billing_issues(
            self.hass, self.config_entry.entry_id, snapshot.errors
        )
        allowance = self.config_entry.options.get(
            CONF_ACTIONS_INCLUDED_MINUTES, DEFAULT_ACTIONS_INCLUDED_MINUTES
        )
        async_update_configured_allowance_issue(
            self.hass,
            self.config_entry.entry_id,
            allowance if isinstance(allowance, int) else 0,
            {
                reason
                for scope_data in snapshot.scopes.values()
                if scope_data.usage is not None
                for _, _, reason in [scope_data.usage.configured_actions_minutes]
                if reason is not None
            },
        )
        return snapshot

    def record_mutation(self, mutation: BillingMutation) -> None:
        """Retain sanitized mutation metadata for diagnostics."""
        self._last_mutation = mutation


def _unavailable_billing_snapshot(
    scopes: tuple[BillingScope, ...],
    reason: str,
) -> BillingSnapshot:
    """Return truthful per-scope billing capabilities without making a request."""
    capability = GitHubCapability(CapabilityStatus.FORBIDDEN, reason)
    scope_data = {
        scope.key: BillingScopeData(
            scope=scope,
            usage=None,
            budgets=(),
            usage_capability=capability,
            budget_capability=capability,
            errors=MappingProxyType({"usage": reason, "budgets": reason}),
        )
        for scope in scopes
    }
    return BillingSnapshot.create(
        scopes=scope_data,
        fetched_at=datetime.now(UTC),
        errors={
            f"{scope.key}:{category}": reason
            for scope in scopes
            for category in ("usage", "budgets")
        },
    )


def _merge_last_known_good(
    previous: GitHubSnapshot | None,
    current: GitHubSnapshot,
) -> GitHubSnapshot:
    """Retain prior category values when an optional endpoint is stale."""
    if previous is None:
        return current

    return replace(
        current,
        organizations=(
            previous.organizations
            if "organizations" in current.errors
            else current.organizations
        ),
        repositories=(
            previous.repositories
            if "repositories" in current.errors
            else current.repositories
        ),
        repository_insights=(
            previous.repository_insights
            if "repository_insights" in current.errors
            else _merge_repository_insights(
                previous.repository_insights,
                current.repository_insights,
            )
        ),
        copilot=_merge_copilot_usage(
            previous.copilot,
            current.copilot,
            current.errors,
        ),
        rate_limit=(
            previous.rate_limit
            if "rate_limit" in current.errors
            else current.rate_limit
        ),
    )


def _merge_billing_last_known_good(
    previous: BillingSnapshot | None,
    current: BillingSnapshot,
) -> BillingSnapshot:
    """Retain prior billing categories when one endpoint is temporarily stale."""
    if previous is None or not current.errors:
        return current
    merged: dict[str, BillingScopeData] = {}
    for key, scope_data in current.scopes.items():
        old = previous.scopes.get(key)
        if old is None:
            merged[key] = scope_data
            continue
        merged[key] = replace(
            scope_data,
            usage=old.usage if "usage" in scope_data.errors else scope_data.usage,
            budgets=(
                old.budgets if "budgets" in scope_data.errors else scope_data.budgets
            ),
        )
    return BillingSnapshot.create(
        scopes=merged,
        fetched_at=current.fetched_at,
        errors=current.errors,
        last_mutation=current.last_mutation or previous.last_mutation,
    )


def _merge_repository_insights(
    previous: tuple[GitHubRepositoryInsights, ...],
    current: tuple[GitHubRepositoryInsights, ...],
) -> tuple[GitHubRepositoryInsights, ...]:
    """Retain last-known-good fields for failed per-repository capabilities."""
    previous_by_id = {item.repository.id: item for item in previous}
    merged: list[GitHubRepositoryInsights] = []
    for item in current:
        old = previous_by_id.get(item.repository.id)
        if old is None or not item.errors:
            merged.append(item)
            continue
        activity_failed = any(
            key in item.errors
            for key in ("commits", "pull_requests", "issues", "releases")
        )
        security_failed = any(
            key in item.errors
            for key in ("dependabot", "code_scanning", "secret_scanning")
        )
        security = item.security
        if security_failed and old.security is not None:
            current_security = item.security
            security = GitHubSecurityAlerts(
                dependabot=(
                    old.security.dependabot
                    if "dependabot" in item.errors
                    else current_security.dependabot
                    if current_security
                    else None
                ),
                code_scanning=(
                    old.security.code_scanning
                    if "code_scanning" in item.errors
                    else current_security.code_scanning
                    if current_security
                    else None
                ),
                secret_scanning=(
                    old.security.secret_scanning
                    if "secret_scanning" in item.errors
                    else current_security.secret_scanning
                    if current_security
                    else None
                ),
                severity=old.security.severity,
            )
        merged.append(
            replace(
                item,
                repository=(
                    old.repository
                    if "repository_metadata" in item.errors
                    else item.repository
                ),
                open_pull_requests=(
                    old.open_pull_requests
                    if "pull_requests" in item.errors
                    else item.open_pull_requests
                ),
                open_issues=(
                    old.open_issues if "issues" in item.errors else item.open_issues
                ),
                latest_commit=(
                    old.latest_commit
                    if "commits" in item.errors
                    else item.latest_commit
                ),
                latest_release=(
                    old.latest_release
                    if "releases" in item.errors
                    else item.latest_release
                ),
                latest_issue=(
                    old.latest_issue if "issues" in item.errors else item.latest_issue
                ),
                latest_pull_request=(
                    old.latest_pull_request
                    if "pull_requests" in item.errors
                    else item.latest_pull_request
                ),
                workflow_runs=(
                    old.workflow_runs
                    if "workflows" in item.errors
                    else item.workflow_runs
                ),
                workflow_status=(
                    old.workflow_status
                    if "workflows" in item.errors
                    else item.workflow_status
                ),
                deployment=(
                    old.deployment if "deployments" in item.errors else item.deployment
                ),
                environments=(
                    old.environments
                    if "deployments" in item.errors
                    else item.environments
                ),
                traffic=(old.traffic if "traffic" in item.errors else item.traffic),
                security=security,
                activity=old.activity if activity_failed else item.activity,
            )
        )
    return tuple(merged)


def _merge_copilot_usage(
    previous: tuple[GitHubCopilotUsage, ...],
    current: tuple[GitHubCopilotUsage, ...],
    errors: Mapping[str, str],
) -> tuple[GitHubCopilotUsage, ...]:
    """Retain only unavailable Copilot fields for each immutable billing scope."""
    previous_by_id = {(usage.scope_type, usage.scope_id): usage for usage in previous}
    current_ids: set[tuple[str, int]] = set()
    merged: list[GitHubCopilotUsage] = []
    for usage in current:
        key = (usage.scope_type, usage.scope_id)
        current_ids.add(key)
        old = previous_by_id.get(key)
        if old is None:
            merged.append(usage)
            continue
        merged.append(
            replace(
                usage,
                premium_requests_used=(
                    usage.premium_requests_used
                    if usage.premium_requests_used is not None
                    else old.premium_requests_used
                ),
                premium_requests_included=(
                    usage.premium_requests_included
                    if usage.premium_requests_included is not None
                    else old.premium_requests_included
                ),
                premium_requests_paid=(
                    usage.premium_requests_paid
                    if usage.premium_requests_paid is not None
                    else old.premium_requests_paid
                ),
                ai_credits_used=(
                    usage.ai_credits_used
                    if usage.ai_credits_used is not None
                    else old.ai_credits_used
                ),
                cost=usage.cost if usage.cost is not None else old.cost,
                currency=(
                    usage.currency if usage.currency is not None else old.currency
                ),
                active_users=(
                    usage.active_users
                    if usage.active_users is not None
                    else old.active_users
                ),
                engaged_users=(
                    usage.engaged_users
                    if usage.engaged_users is not None
                    else old.engaged_users
                ),
                coding_agent_pull_requests=(
                    usage.coding_agent_pull_requests
                    if usage.coding_agent_pull_requests is not None
                    else old.coding_agent_pull_requests
                ),
                coding_agent_merged_pull_requests=(
                    usage.coding_agent_merged_pull_requests
                    if usage.coding_agent_merged_pull_requests is not None
                    else old.coding_agent_merged_pull_requests
                ),
                code_review_pull_requests=(
                    usage.code_review_pull_requests
                    if usage.code_review_pull_requests is not None
                    else old.code_review_pull_requests
                ),
                product_breakdown=(
                    usage.product_breakdown
                    if usage.product_breakdown
                    else old.product_breakdown
                ),
                model_breakdown=(
                    usage.model_breakdown
                    if usage.model_breakdown
                    else old.model_breakdown
                ),
                repository_breakdown=(
                    usage.repository_breakdown
                    if usage.repository_breakdown
                    else old.repository_breakdown
                ),
                reporting_day=(
                    usage.reporting_day
                    if usage.reporting_day is not None
                    else old.reporting_day
                ),
            )
        )
    for key, old in previous_by_id.items():
        prefix = f"copilot_{old.scope_type}_{old.scope_id}_"
        if key not in current_ids and (
            "copilot" in errors
            or any(error_key.startswith(prefix) for error_key in errors)
        ):
            merged.append(old)
    return tuple(merged)
