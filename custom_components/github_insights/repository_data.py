"""Capability-gated repository, workflow, activity, traffic, and security data."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

from .api import (
    GitHubAPIError,
    GitHubClient,
    GitHubConnectionError,
    GitHubPermissionError,
    GitHubRateLimitError,
    _repository,
)
from .const import (
    MAX_ACTIVITY_ITEMS,
    MAX_RECENT_WORKFLOW_RUNS,
    MAX_SECURITY_ALERTS,
    MAX_SELECTED_REPOSITORIES,
)
from .models import (
    CapabilityStatus,
    GitHubActivity,
    GitHubCapability,
    GitHubCommit,
    GitHubDeployment,
    GitHubItem,
    GitHubRepository,
    GitHubRepositoryInsights,
    GitHubSecurityAlerts,
    GitHubTraffic,
    GitHubWorkflowRun,
    JsonObject,
)

_OPTIONAL_ERRORS = (
    GitHubPermissionError,
    GitHubConnectionError,
    GitHubAPIError,
    GitHubRateLimitError,
)


@dataclass(frozen=True, slots=True)
class RepositoryCollectionOptions:
    """Bounded repository collection options."""

    selected: tuple[str, ...]
    auto_discover: bool
    include_archived: bool
    include_forks: bool
    enabled_categories: frozenset[str]
    repository_limit: int = MAX_SELECTED_REPOSITORIES


async def async_collect_repository_insights(
    client: GitHubClient,
    discovered: tuple[GitHubRepository, ...],
    options: RepositoryCollectionOptions,
) -> tuple[GitHubRepositoryInsights, ...]:
    """Collect selected repository data with bounded concurrency."""
    selected = _select_repositories(discovered, options)
    semaphore = asyncio.Semaphore(4)

    async def collect(repository: GitHubRepository) -> GitHubRepositoryInsights:
        async with semaphore:
            return await _async_collect_repository(client, repository, options)

    return tuple(
        await asyncio.gather(*(collect(repository) for repository in selected))
    )


def _select_repositories(
    discovered: tuple[GitHubRepository, ...],
    options: RepositoryCollectionOptions,
) -> tuple[GitHubRepository, ...]:
    """Apply explicit selection and discovery filters deterministically."""
    selected_names = set(options.selected)
    repositories = (
        discovered
        if options.auto_discover
        else tuple(repo for repo in discovered if repo.full_name in selected_names)
    )
    if selected_names:
        repositories = tuple(
            repo
            for repo in repositories
            if options.auto_discover or repo.full_name in selected_names
        )
    return tuple(
        repo
        for repo in repositories
        if (options.include_archived or not repo.archived)
        and (options.include_forks or not repo.fork)
    )[: max(1, min(options.repository_limit, MAX_SELECTED_REPOSITORIES))]


async def _async_collect_repository(
    client: GitHubClient,
    discovered: GitHubRepository,
    options: RepositoryCollectionOptions,
) -> GitHubRepositoryInsights:
    path = f"/repos/{quote(discovered.full_name, safe='/')}"
    errors: dict[str, str] = {}
    capabilities: dict[str, GitHubCapability] = {}
    try:
        detail = await client.async_get_json(path)
        repository = _repository(_object(detail))
        capabilities["repository_metadata"] = _available()
    except _OPTIONAL_ERRORS as err:
        errors["repository_metadata"] = _reason(err)
        capabilities["repository_metadata"] = _capability(err)
        repository = discovered

    pulls: tuple[JsonObject, ...] = ()
    issues: tuple[JsonObject, ...] = ()
    releases: tuple[JsonObject, ...] = ()
    latest_commit: GitHubCommit | None = None
    workflow_runs: tuple[GitHubWorkflowRun, ...] = ()
    workflow_status: str | None = None
    deployment: GitHubDeployment | None = None
    environments: tuple[str, ...] = ()
    traffic: GitHubTraffic | None = None
    security: GitHubSecurityAlerts | None = None
    activity: GitHubActivity | None = None

    try:
        pulls_page = await client.async_get_page(
            f"{path}/pulls",
            params={"state": "all", "sort": "created", "direction": "desc"},
            item_limit=MAX_ACTIVITY_ITEMS,
        )
        pulls = pulls_page.items
        capabilities["pull_requests"] = _available()
    except _OPTIONAL_ERRORS as err:
        errors["pull_requests"] = _reason(err)
        capabilities["pull_requests"] = _capability(err)
        pulls_page = None

    try:
        issues_page = await client.async_get_page(
            f"{path}/issues",
            params={"state": "all", "sort": "created", "direction": "desc"},
            item_limit=MAX_ACTIVITY_ITEMS,
        )
        issues = tuple(item for item in issues_page.items if "pull_request" not in item)
        capabilities["issues"] = _available()
    except _OPTIONAL_ERRORS as err:
        errors["issues"] = _reason(err)
        capabilities["issues"] = _capability(err)
        issues_page = None

    try:
        commits_page = await client.async_get_page(
            f"{path}/commits",
            params={"since": _since(90)},
            item_limit=MAX_ACTIVITY_ITEMS,
        )
        latest_commit = _commit(commits_page.items[0]) if commits_page.items else None
        capabilities["commits"] = _available()
    except _OPTIONAL_ERRORS as err:
        errors["commits"] = _reason(err)
        capabilities["commits"] = _capability(err)
        commits_page = None

    if "releases" in options.enabled_categories:
        try:
            release_page = await client.async_get_page(
                f"{path}/releases", item_limit=MAX_ACTIVITY_ITEMS
            )
            releases = release_page.items
            capabilities["releases"] = _available()
        except _OPTIONAL_ERRORS as err:
            errors["releases"] = _reason(err)
            capabilities["releases"] = _capability(err)
            release_page = None
    else:
        release_page = None

    if "workflows" in options.enabled_categories:
        try:
            workflow_runs = await _async_workflows(
                client,
                path,
            )
            workflow_status = _workflow_health(workflow_runs)
            capabilities["workflows"] = _available()
        except _OPTIONAL_ERRORS as err:
            errors["workflows"] = _reason(err)
            capabilities["workflows"] = _capability(err)

    if "deployments" in options.enabled_categories:
        deployment, environments = await _async_deployments(
            client, path, capabilities, errors
        )
    if "traffic" in options.enabled_categories:
        traffic = await _async_traffic(client, path, capabilities, errors)
    if "security" in options.enabled_categories:
        security = await _async_security(client, path, capabilities, errors)

    if "activity" in options.enabled_categories:
        activity = _activity(
            commits_page.items if commits_page else (),
            pulls,
            issues,
            releases,
            complete=all(
                page is not None and page.complete
                for page in (commits_page, pulls_page, issues_page)
            )
            and (release_page is None or release_page.complete),
        )
        capabilities["activity"] = _available()

    open_pulls = sum(1 for item in pulls if item.get("state") == "open")
    open_issues = sum(1 for item in issues if item.get("state") == "open")
    return GitHubRepositoryInsights.create(
        repository=repository,
        open_pull_requests=(
            open_pulls if pulls_page is not None and pulls_page.complete else None
        ),
        open_issues=(
            open_issues if issues_page is not None and issues_page.complete else None
        ),
        latest_commit=latest_commit,
        latest_release=(
            _item(
                next(
                    (
                        release
                        for release in releases
                        if not release.get("draft") and not release.get("prerelease")
                    ),
                    releases[0],
                )
            )
            if releases
            else None
        ),
        latest_issue=_item(issues[0]) if issues else None,
        latest_pull_request=_item(pulls[0]) if pulls else None,
        workflow_runs=workflow_runs,
        workflow_status=workflow_status,
        deployment=deployment,
        environments=environments,
        traffic=traffic,
        security=security,
        activity=activity,
        capabilities=capabilities,
        errors=errors,
    )


async def _async_deployments(
    client: GitHubClient,
    path: str,
    capabilities: dict[str, GitHubCapability],
    errors: dict[str, str],
) -> tuple[GitHubDeployment | None, tuple[str, ...]]:
    try:
        deployments = await client.async_get_page(f"{path}/deployments", item_limit=20)
        environment_data = _object(await client.async_get_json(f"{path}/environments"))
        raw_environments = environment_data.get("environments")
        environments = (
            tuple(
                str(item["name"])
                for item in raw_environments
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            )
            if isinstance(raw_environments, list)
            else ()
        )
        latest = deployments.items[0] if deployments.items else None
        deployment = _deployment(latest) if latest else None
        if deployment is not None:
            statuses = await client.async_get_page(
                f"{path}/deployments/{deployment.id}/statuses",
                item_limit=1,
            )
            if statuses.items:
                deployment = replace(
                    deployment,
                    state=_string(statuses.items[0].get("state")) or None,
                    html_url=(
                        _string(statuses.items[0].get("target_url"))
                        or deployment.html_url
                    ),
                )
        capabilities["deployments"] = _available()
        return deployment, environments
    except _OPTIONAL_ERRORS as err:
        errors["deployments"] = _reason(err)
        capabilities["deployments"] = _capability(err)
        return None, ()


async def _async_traffic(
    client: GitHubClient,
    path: str,
    capabilities: dict[str, GitHubCapability],
    errors: dict[str, str],
) -> GitHubTraffic | None:
    try:
        views, clones, referrers, popular = await asyncio.gather(
            client.async_get_json(f"{path}/traffic/views"),
            client.async_get_json(f"{path}/traffic/clones"),
            client.async_get_json(f"{path}/traffic/popular/referrers"),
            client.async_get_json(f"{path}/traffic/popular/paths"),
        )
        capabilities["traffic"] = _available()
        return GitHubTraffic(
            views=_int(_object(views).get("count")),
            unique_visitors=_int(_object(views).get("uniques")),
            clones=_int(_object(clones).get("count")),
            unique_cloners=_int(_object(clones).get("uniques")),
            referrers=tuple(
                GitHubItem(None, _string(item.get("referrer")), "", datetime.now(UTC))
                for item in _objects(referrers)
            ),
            popular_paths=tuple(
                GitHubItem(
                    None,
                    _string(item.get("title")) or _string(item.get("path")),
                    "",
                    datetime.now(UTC),
                )
                for item in _objects(popular)
            ),
        )
    except _OPTIONAL_ERRORS as err:
        errors["traffic"] = _reason(err)
        capabilities["traffic"] = _capability(err)
        return None


async def _async_security(
    client: GitHubClient,
    path: str,
    capabilities: dict[str, GitHubCapability],
    errors: dict[str, str],
) -> GitHubSecurityAlerts | None:
    counts: dict[str, int | None] = {}
    severity: dict[str, int] = {}
    endpoints = {
        "dependabot": f"{path}/dependabot/alerts",
        "code_scanning": f"{path}/code-scanning/alerts",
        "secret_scanning": f"{path}/secret-scanning/alerts",
    }
    for key, endpoint in endpoints.items():
        try:
            page = await client.async_get_page(
                endpoint,
                params={"state": "open"},
                item_limit=MAX_SECURITY_ALERTS,
            )
            counts[key] = len(page.items) if page.complete else None
            if not page.complete:
                errors[key] = "coverage_limited"
            if key != "secret_scanning":
                for alert in page.items:
                    alert_severity = _alert_severity(alert)
                    if alert_severity:
                        severity[alert_severity] = severity.get(alert_severity, 0) + 1
            capabilities[key] = _available()
        except _OPTIONAL_ERRORS as err:
            counts[key] = None
            errors[key] = _reason(err)
            capabilities[key] = _capability(err)
    if all(value is None for value in counts.values()):
        return None
    capabilities["security"] = _available()
    return GitHubSecurityAlerts(
        dependabot=counts["dependabot"],
        code_scanning=counts["code_scanning"],
        secret_scanning=counts["secret_scanning"],
        severity=severity,
    )


async def _async_workflows(
    client: GitHubClient,
    path: str,
) -> tuple[GitHubWorkflowRun, ...]:
    payload = _object(
        await client.async_get_json(
            f"{path}/actions/runs",
            params={"per_page": str(MAX_RECENT_WORKFLOW_RUNS)},
        )
    )
    raw_runs = payload.get("workflow_runs")
    runs = (
        tuple(_workflow_run(item) for item in raw_runs if isinstance(item, dict))
        if isinstance(raw_runs, list)
        else ()
    )
    enriched: list[GitHubWorkflowRun] = []
    for run in runs[:5]:
        jobs = await client.async_get_page(
            f"{path}/actions/runs/{run.id}/jobs",
            item_limit=100,
        )
        runtime = sum(_job_runtime(job) for job in jobs.items)
        enriched.append(
            replace(
                run,
                jobs=len(jobs.items) if jobs.complete else None,
                job_runtime_seconds=runtime,
            )
        )
    return tuple(enriched) + runs[5:]


def _activity(
    commits: Iterable[JsonObject],
    pulls: Iterable[JsonObject],
    issues: Iterable[JsonObject],
    releases: Iterable[JsonObject],
    *,
    complete: bool,
) -> GitHubActivity:
    cutoff = datetime.now(UTC) - timedelta(days=90)
    recent_commits = tuple(item for item in commits if _date(item, "commit") >= cutoff)
    recent_pulls = tuple(item for item in pulls if _date(item) >= cutoff)
    recent_issues = tuple(item for item in issues if _date(item) >= cutoff)
    recent_releases = tuple(item for item in releases if _date(item) >= cutoff)
    active_days = sorted(
        {_date(item, "commit").date().isoformat() for item in recent_commits}
        | {_date(item).date().isoformat() for item in recent_pulls}
        | {_date(item).date().isoformat() for item in recent_issues}
        | {_date(item).date().isoformat() for item in recent_releases}
    )
    current, longest = _streaks(active_days) if complete else (None, None)
    return GitHubActivity(
        commits=len(recent_commits),
        pull_requests_opened=len(recent_pulls),
        pull_requests_merged=sum(
            1 for item in recent_pulls if item.get("merged_at") is not None
        ),
        issues_opened=len(recent_issues),
        issues_closed=sum(
            1 for item in recent_issues if item.get("closed_at") is not None
        ),
        reviews=None,
        releases=len(recent_releases),
        active_days=tuple(active_days),
        period_totals={
            period: _period_total(
                period,
                recent_commits,
                recent_pulls,
                recent_issues,
                recent_releases,
            )
            for period in (7, 28, 30, 90)
        },
        weekday_distribution=_weekday_distribution(active_days),
        current_streak=current,
        longest_streak=longest,
        coverage_days=90,
        coverage_complete=complete,
    )


def _period_total(
    days: int,
    commits: tuple[JsonObject, ...],
    pulls: tuple[JsonObject, ...],
    issues: tuple[JsonObject, ...],
    releases: tuple[JsonObject, ...],
) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    return sum(
        1
        for item in (*commits, *pulls, *issues, *releases)
        if _date(item, "commit" if "commit" in item else None) >= cutoff
    )


def _weekday_distribution(days: list[str]) -> Mapping[str, int]:
    distribution = {
        "monday": 0,
        "tuesday": 0,
        "wednesday": 0,
        "thursday": 0,
        "friday": 0,
        "saturday": 0,
        "sunday": 0,
    }
    for day in days:
        key = datetime.fromisoformat(day).strftime("%A").lower()
        distribution[key] += 1
    return distribution


def _streaks(days: list[str]) -> tuple[int, int]:
    values = {datetime.fromisoformat(day).date() for day in days}
    if not values:
        return 0, 0
    longest = 0
    running = 0
    previous = None
    for day in sorted(values):
        running = running + 1 if previous and day == previous + timedelta(days=1) else 1
        longest = max(longest, running)
        previous = day
    current = 0
    cursor = datetime.now(UTC).date()
    if cursor not in values:
        cursor -= timedelta(days=1)
    while cursor in values:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def _commit(item: Mapping[str, Any]) -> GitHubCommit:
    commit = item.get("commit")
    commit_data = commit if isinstance(commit, dict) else {}
    author_data = commit_data.get("author")
    author = author_data if isinstance(author_data, dict) else {}
    return GitHubCommit(
        sha=_string(item.get("sha")),
        message=_string(commit_data.get("message")).splitlines()[0][:240],
        html_url=_string(item.get("html_url")),
        committed_at=_datetime(author.get("date")),
        author=_string(author.get("name")) or None,
    )


def _workflow_run(item: Mapping[str, Any]) -> GitHubWorkflowRun:
    created = _datetime(item.get("created_at"))
    updated = _datetime(item.get("updated_at"))
    runtime = max(0, int((updated - created).total_seconds()))
    return GitHubWorkflowRun(
        id=_int(item.get("id")),
        name=_string(item.get("name")) or _string(item.get("display_title")),
        status=_string(item.get("status")),
        conclusion=_string(item.get("conclusion")) or None,
        event=_string(item.get("event")),
        html_url=_string(item.get("html_url")),
        created_at=created,
        updated_at=updated,
        runtime_seconds=runtime,
    )


def _job_runtime(item: Mapping[str, Any]) -> int:
    started = _datetime(item.get("started_at"))
    completed = _datetime(item.get("completed_at"))
    if started == datetime.min.replace(tzinfo=UTC):
        return 0
    end = (
        completed
        if completed != datetime.min.replace(tzinfo=UTC)
        else datetime.now(UTC)
    )
    return max(0, int((end - started).total_seconds()))


def _deployment(item: Mapping[str, Any]) -> GitHubDeployment:
    return GitHubDeployment(
        id=_int(item.get("id")),
        environment=_string(item.get("environment")),
        state=None,
        created_at=_datetime(item.get("created_at")),
        html_url=_string(item.get("statuses_url")) or None,
    )


def _item(item: Mapping[str, Any]) -> GitHubItem:
    return GitHubItem(
        number=item.get("number") if isinstance(item.get("number"), int) else None,
        title=_string(item.get("name")) or _string(item.get("title")),
        html_url=_string(item.get("html_url")),
        created_at=_datetime(item.get("published_at") or item.get("created_at")),
        author=_nested_login(item.get("user") or item.get("author")),
        state=_string(item.get("state")) or None,
    )


def _workflow_health(runs: tuple[GitHubWorkflowRun, ...]) -> str | None:
    if not runs:
        return None
    if any(run.status != "completed" for run in runs):
        return "in_progress"
    if any(run.conclusion not in {"success", "skipped", "neutral"} for run in runs):
        return "failure"
    return "success"


def _alert_severity(alert: Mapping[str, Any]) -> str | None:
    security = alert.get("security_advisory") or alert.get("rule")
    if not isinstance(security, dict):
        return None
    severity = security.get("severity") or security.get("security_severity_level")
    return severity if isinstance(severity, str) else None


def _date(item: Mapping[str, Any], nested: str | None = None) -> datetime:
    source = item.get(nested) if nested else item
    if not isinstance(source, dict):
        return datetime.min.replace(tzinfo=UTC)
    author = source.get("author")
    if isinstance(author, dict) and author.get("date"):
        return _datetime(author.get("date"))
    return _datetime(
        source.get("created_at")
        or source.get("published_at")
        or source.get("committed_at")
    )


def _since(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def _objects(value: Any) -> tuple[JsonObject, ...]:
    return (
        tuple(item for item in value if isinstance(item, dict))
        if isinstance(value, list)
        else ()
    )


def _object(value: Any) -> JsonObject:
    if not isinstance(value, dict):
        raise GitHubAPIError(502, "expected_object")
    return value


def _datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        return datetime.min.replace(tzinfo=UTC)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _int(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _nested_login(value: Any) -> str | None:
    if isinstance(value, dict):
        login = value.get("login")
        if isinstance(login, str):
            return login
    return None


def _available() -> GitHubCapability:
    return GitHubCapability(CapabilityStatus.AVAILABLE)


def _capability(error: Exception) -> GitHubCapability:
    if isinstance(error, GitHubPermissionError):
        return GitHubCapability(CapabilityStatus.FORBIDDEN, "missing_permission")
    if isinstance(error, GitHubAPIError) and error.status in {404, 410, 422}:
        return GitHubCapability(CapabilityStatus.UNSUPPORTED, "unsupported")
    return GitHubCapability(
        CapabilityStatus.TEMPORARILY_UNAVAILABLE, "temporarily_unavailable"
    )


def _reason(error: Exception) -> str:
    capability = _capability(error)
    return capability.reason or capability.status
