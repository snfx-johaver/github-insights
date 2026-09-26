# Dashboard examples

GitHub Insights installs one integration and one frontend artifact. Register
`/github_insights/frontend/github-insights-cards.js` once as a JavaScript
module. The card picker then exposes exactly two GitHub Insights cards.

## Account dashboard

```yaml
type: custom:github-insights-card
title: Engineering overview
preset: dashboard
layout: expanded
sections:
  - overview
  - usage
  - actions
  - copilot
  - activity
  - contributions
  - security
show_forecast: true
show_estimated_minutes: true
show_debug: false
```

Use `preset: usage`, `actions`, `copilot`, `activity`, `contributions`,
`security`, `overview`, or `compact` as a starting point. The visual editor
can then add, remove, and reorder sections and metrics.

## Repository collection

```yaml
type: custom:github-insights-repository-card
title: Repository operations
repositories: auto
layout: compact
group_by: organization
favorites:
  - octo/important
sort:
  - field: workflow_health
    direction: ascending
    nulls: last
  - field: last_push
    direction: descending
    nulls: last
  - field: name
    direction: ascending
    nulls: last
metrics:
  - open_pull_requests
  - workflow_health
  - actions_usage_percent
show_archived: false
show_forks: true
```

## One repository

```yaml
type: custom:github-insights-repository-card
title: Home Assistant development
repository: owner/home-assistant-config
layout: detail
metrics:
  - stars
  - forks
  - open_issues
  - open_pull_requests
  - latest_commit
  - latest_release
  - workflow_health
  - actions_usage_percent
  - traffic_views
  - dependabot_alerts
```

## Mobile snapshot

```yaml
type: custom:github-insights-card
title: Actions snapshot
preset: compact
layout: compact
sections:
  - usage
  - actions
metrics:
  - actions_configured_minutes_used_percent
  - actions_budget_remaining
```

## Beta migration

Replace former account-oriented types with `custom:github-insights-card` and
the matching preset. Replace both former repository types with
`custom:github-insights-repository-card`; retain `repository` for a detail
card or use `repositories: auto` for a collection. The complete mapping is in
[card specifications](card-specifications.md). Legacy elements are not
registered, so stale YAML reports an unknown custom element until migrated.
