"""Typed data models for GitHub Insights."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class CapabilityStatus(StrEnum):
    """Availability state for one GitHub feature."""

    AVAILABLE = "available"
    FORBIDDEN = "missing_permission"
    UNSUPPORTED = "unsupported"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"


class DataClass(StrEnum):
    """Provenance class for a metric."""

    AUTHORITATIVE = "authoritative"
    CALCULATED = "calculated"
    ESTIMATED = "estimated"


class BillingScopeType(StrEnum):
    """Official enhanced-billing account scopes."""

    USER = "user"
    ORGANIZATION = "organization"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True, slots=True)
class GitHubServer:
    """Normalized GitHub server URLs."""

    web_url: str
    api_url: str
    hostname: str
    is_dotcom: bool


@dataclass(frozen=True, slots=True)
class GitHubAccount:
    """Authenticated GitHub account."""

    id: int
    login: str
    name: str | None
    avatar_url: str
    html_url: str
    public_repos: int
    total_private_repos: int | None
    followers: int
    following: int


@dataclass(frozen=True, slots=True)
class GitHubOrganization:
    """Organization visible to the authenticated account."""

    id: int
    login: str
    avatar_url: str


@dataclass(frozen=True, slots=True)
class GitHubRepository:
    """Repository discovery metadata."""

    id: int
    name: str
    full_name: str
    description: str | None
    private: bool
    visibility: str
    archived: bool
    fork: bool
    html_url: str
    default_branch: str
    language: str | None
    license_name: str | None
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    has_discussions: bool
    size_kb: int
    pushed_at: datetime | None


@dataclass(frozen=True, slots=True)
class GitHubItem:
    """Latest repository item."""

    number: int | None
    title: str
    html_url: str
    created_at: datetime
    author: str | None = None
    state: str | None = None


@dataclass(frozen=True, slots=True)
class GitHubCommit:
    """Latest repository commit."""

    sha: str
    message: str
    html_url: str
    committed_at: datetime
    author: str | None


@dataclass(frozen=True, slots=True)
class GitHubWorkflowRun:
    """Normalized workflow-run metadata."""

    id: int
    name: str
    status: str
    conclusion: str | None
    event: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    runtime_seconds: int | None
    job_runtime_seconds: int | None = None
    jobs: int | None = None


@dataclass(frozen=True, slots=True)
class GitHubDeployment:
    """Latest deployment state."""

    id: int
    environment: str
    state: str | None
    created_at: datetime
    html_url: str | None


@dataclass(frozen=True, slots=True)
class GitHubTraffic:
    """Repository traffic within GitHub's API retention window."""

    views: int
    unique_visitors: int
    clones: int
    unique_cloners: int
    referrers: tuple[GitHubItem, ...]
    popular_paths: tuple[GitHubItem, ...]


@dataclass(frozen=True, slots=True)
class GitHubSecurityAlerts:
    """Open repository security-alert counts."""

    dependabot: int | None
    code_scanning: int | None
    secret_scanning: int | None
    severity: Mapping[str, int]

    @property
    def total(self) -> int | None:
        """Return the total when at least one alert family is available."""
        values = (
            value
            for value in (self.dependabot, self.code_scanning, self.secret_scanning)
            if value is not None
        )
        collected = tuple(values)
        return sum(collected) if collected else None


@dataclass(frozen=True, slots=True)
class GitHubActivity:
    """Bounded repository activity and coverage metadata."""

    commits: int
    pull_requests_opened: int
    pull_requests_merged: int | None
    issues_opened: int
    issues_closed: int | None
    reviews: int | None
    releases: int
    active_days: tuple[str, ...]
    period_totals: Mapping[int, int]
    weekday_distribution: Mapping[str, int]
    current_streak: int | None
    longest_streak: int | None
    coverage_days: int
    coverage_complete: bool


@dataclass(frozen=True, slots=True)
class GitHubRepositoryInsights:
    """Normalized data for one selected repository."""

    repository: GitHubRepository
    open_pull_requests: int | None
    open_issues: int | None
    latest_commit: GitHubCommit | None
    latest_release: GitHubItem | None
    latest_issue: GitHubItem | None
    latest_pull_request: GitHubItem | None
    workflow_runs: tuple[GitHubWorkflowRun, ...]
    workflow_status: str | None
    deployment: GitHubDeployment | None
    environments: tuple[str, ...]
    traffic: GitHubTraffic | None
    security: GitHubSecurityAlerts | None
    activity: GitHubActivity | None
    capabilities: Mapping[str, GitHubCapability]
    errors: Mapping[str, str]

    @classmethod
    def create(
        cls,
        *,
        repository: GitHubRepository,
        open_pull_requests: int | None = None,
        open_issues: int | None = None,
        latest_commit: GitHubCommit | None = None,
        latest_release: GitHubItem | None = None,
        latest_issue: GitHubItem | None = None,
        latest_pull_request: GitHubItem | None = None,
        workflow_runs: tuple[GitHubWorkflowRun, ...] = (),
        workflow_status: str | None = None,
        deployment: GitHubDeployment | None = None,
        environments: tuple[str, ...] = (),
        traffic: GitHubTraffic | None = None,
        security: GitHubSecurityAlerts | None = None,
        activity: GitHubActivity | None = None,
        capabilities: Mapping[str, GitHubCapability] | None = None,
        errors: Mapping[str, str] | None = None,
    ) -> GitHubRepositoryInsights:
        """Create immutable repository insights."""
        return cls(
            repository=repository,
            open_pull_requests=open_pull_requests,
            open_issues=open_issues,
            latest_commit=latest_commit,
            latest_release=latest_release,
            latest_issue=latest_issue,
            latest_pull_request=latest_pull_request,
            workflow_runs=workflow_runs,
            workflow_status=workflow_status,
            deployment=deployment,
            environments=environments,
            traffic=traffic,
            security=security,
            activity=activity,
            capabilities=MappingProxyType(dict(capabilities or {})),
            errors=MappingProxyType(dict(errors or {})),
        )


@dataclass(frozen=True, slots=True)
class GitHubCopilotUsage:
    """Official Copilot billing, adoption, or activity values."""

    scope: str
    scope_id: int
    scope_type: str
    premium_requests_used: float | None
    premium_requests_included: float | None
    premium_requests_paid: float | None
    ai_credits_used: float | None
    cost: float | None
    currency: str | None
    active_users: int | None
    engaged_users: int | None
    coding_agent_pull_requests: int | None
    coding_agent_merged_pull_requests: int | None
    code_review_pull_requests: int | None
    product_breakdown: Mapping[str, float]
    model_breakdown: Mapping[str, float]
    repository_breakdown: Mapping[str, float]
    reporting_day: str | None

    @classmethod
    def create(
        cls,
        *,
        scope: str,
        scope_id: int,
        scope_type: str,
        premium_requests_used: float | None = None,
        premium_requests_included: float | None = None,
        premium_requests_paid: float | None = None,
        ai_credits_used: float | None = None,
        cost: float | None = None,
        currency: str | None = None,
        active_users: int | None = None,
        engaged_users: int | None = None,
        coding_agent_pull_requests: int | None = None,
        coding_agent_merged_pull_requests: int | None = None,
        code_review_pull_requests: int | None = None,
        product_breakdown: Mapping[str, float] | None = None,
        model_breakdown: Mapping[str, float] | None = None,
        repository_breakdown: Mapping[str, float] | None = None,
        reporting_day: str | None = None,
    ) -> GitHubCopilotUsage:
        """Create immutable Copilot usage."""
        return cls(
            scope=scope,
            scope_id=scope_id,
            scope_type=scope_type,
            premium_requests_used=premium_requests_used,
            premium_requests_included=premium_requests_included,
            premium_requests_paid=premium_requests_paid,
            ai_credits_used=ai_credits_used,
            cost=cost,
            currency=currency,
            active_users=active_users,
            engaged_users=engaged_users,
            coding_agent_pull_requests=coding_agent_pull_requests,
            coding_agent_merged_pull_requests=coding_agent_merged_pull_requests,
            code_review_pull_requests=code_review_pull_requests,
            product_breakdown=MappingProxyType(dict(product_breakdown or {})),
            model_breakdown=MappingProxyType(dict(model_breakdown or {})),
            repository_breakdown=MappingProxyType(dict(repository_breakdown or {})),
            reporting_day=reporting_day,
        )


@dataclass(frozen=True, slots=True)
class GitHubRateLimit:
    """GitHub core REST rate-limit state."""

    limit: int
    remaining: int
    used: int
    reset_at: datetime


@dataclass(frozen=True, slots=True)
class GitHubCapability:
    """Availability and permission metadata for one category."""

    status: CapabilityStatus
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class BillingScope:
    """One configured enhanced-billing scope."""

    scope_type: BillingScopeType
    name: str

    @property
    def key(self) -> str:
        """Return a stable scope key."""
        return f"{self.scope_type.value}:{self.name}"


@dataclass(frozen=True, slots=True)
class BillingPeriod:
    """GitHub billing report period."""

    year: int
    month: int | None = None
    day: int | None = None

    @property
    def label(self) -> str:
        """Return an ISO-like period label."""
        if self.day is not None and self.month is not None:
            return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        if self.month is not None:
            return f"{self.year:04d}-{self.month:02d}"
        return f"{self.year:04d}"


@dataclass(frozen=True, slots=True)
class BillingUsageItem:
    """Normalized enhanced-billing usage row."""

    product: str
    sku: str
    unit_type: str
    price_per_unit: Decimal
    gross_quantity: Decimal | None
    gross_amount: Decimal
    discount_quantity: Decimal | None
    discount_amount: Decimal
    net_quantity: Decimal | None
    net_amount: Decimal
    date: str | None = None
    repository_name: str | None = None
    organization_name: str | None = None


@dataclass(frozen=True, slots=True)
class BillingUsageReport:
    """Authoritative report and its scope."""

    scope: BillingScope
    period: BillingPeriod
    summary_items: tuple[BillingUsageItem, ...]
    detail_items: tuple[BillingUsageItem, ...]
    currency: str = "USD"
    unavailable_sections: tuple[str, ...] = ()

    @property
    def actions_items(self) -> tuple[BillingUsageItem, ...]:
        """Return GitHub Actions rows only."""
        source = self.summary_items or self.detail_items
        return tuple(
            item
            for item in source
            if item.product.casefold() in {"actions", "github actions"}
        )


@dataclass(frozen=True, slots=True)
class BudgetAlerting:
    """Budget alert settings."""

    will_alert: bool
    recipients: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BillingBudget:
    """Normalized organization or enterprise budget."""

    id: str
    scope: BillingScope
    budget_scope: str
    entity_name: str
    budget_type: str
    product_sku: str
    amount: Decimal
    consumed_amount: Decimal
    prevent_further_usage: bool
    alerting: BudgetAlerting
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: str | None = None
    currency: str = "USD"

    @property
    def remaining_amount(self) -> Decimal:
        """Return a non-negative remaining budget."""
        return max(Decimal(), self.amount - self.consumed_amount)

    @property
    def used_percent(self) -> Decimal | None:
        """Return budget utilization."""
        if self.amount <= 0:
            return None
        return self.consumed_amount * Decimal(100) / self.amount

    @property
    def is_actions(self) -> bool:
        """Return whether this budget targets Actions."""
        value = self.product_sku.casefold()
        return "action" in value


@dataclass(frozen=True, slots=True)
class BillingScopeData:
    """Usage and budgets for one scope."""

    scope: BillingScope
    usage: BillingUsageReport | None
    budgets: tuple[BillingBudget, ...]
    usage_capability: GitHubCapability
    budget_capability: GitHubCapability
    errors: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BillingMutation:
    """Sanitized last successful financial mutation."""

    action: str
    scope_key: str
    budget_id: str | None
    completed_at: datetime


@dataclass(frozen=True, slots=True)
class BillingSnapshot:
    """Normalized Phase 3 enhanced-billing state."""

    scopes: Mapping[str, BillingScopeData]
    fetched_at: datetime
    errors: Mapping[str, str] = field(default_factory=dict)
    last_mutation: BillingMutation | None = None

    @classmethod
    def create(
        cls,
        *,
        scopes: Mapping[str, BillingScopeData],
        fetched_at: datetime,
        errors: Mapping[str, str] | None = None,
        last_mutation: BillingMutation | None = None,
    ) -> BillingSnapshot:
        """Create an immutable billing snapshot."""
        return cls(
            scopes=MappingProxyType(dict(scopes)),
            fetched_at=fetched_at,
            errors=MappingProxyType(dict(errors or {})),
            last_mutation=last_mutation,
        )


@dataclass(frozen=True, slots=True)
class GitHubSnapshot:
    """Normalized data collected by the GitHub Insights coordinator."""

    account: GitHubAccount
    organizations: tuple[GitHubOrganization, ...]
    repositories: tuple[GitHubRepository, ...]
    repository_insights: tuple[GitHubRepositoryInsights, ...]
    copilot: tuple[GitHubCopilotUsage, ...]
    rate_limit: GitHubRateLimit | None
    token_scopes: tuple[str, ...]
    capabilities: Mapping[str, GitHubCapability]
    fetched_at: datetime
    errors: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        account: GitHubAccount,
        organizations: tuple[GitHubOrganization, ...],
        repositories: tuple[GitHubRepository, ...],
        repository_insights: tuple[GitHubRepositoryInsights, ...] = (),
        copilot: tuple[GitHubCopilotUsage, ...] = (),
        rate_limit: GitHubRateLimit | None,
        token_scopes: tuple[str, ...],
        capabilities: Mapping[str, GitHubCapability],
        fetched_at: datetime,
        errors: Mapping[str, str] | None = None,
    ) -> GitHubSnapshot:
        """Create an immutable snapshot."""
        return cls(
            account=account,
            organizations=organizations,
            repositories=repositories,
            repository_insights=repository_insights,
            copilot=copilot,
            rate_limit=rate_limit,
            token_scopes=token_scopes,
            capabilities=MappingProxyType(dict(capabilities)),
            fetched_at=fetched_at,
            errors=MappingProxyType(dict(errors or {})),
        )


JsonObject = dict[str, Any]
