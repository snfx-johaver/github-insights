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
    full_name: str
    private: bool
    archived: bool
    fork: bool
    html_url: str


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

    @property
    def actions_items(self) -> tuple[BillingUsageItem, ...]:
        """Return GitHub Actions rows only."""
        return tuple(
            item
            for item in self.summary_items
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
    """Normalized data collected by the Phase 2 coordinator."""

    account: GitHubAccount
    organizations: tuple[GitHubOrganization, ...]
    repositories: tuple[GitHubRepository, ...]
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
            rate_limit=rate_limit,
            token_scopes=token_scopes,
            capabilities=MappingProxyType(dict(capabilities)),
            fetched_at=fetched_at,
            errors=MappingProxyType(dict(errors or {})),
        )


JsonObject = dict[str, Any]
