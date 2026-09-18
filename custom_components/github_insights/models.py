"""Typed data models for GitHub Insights."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
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
