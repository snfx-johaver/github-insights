# Card specifications

## Implementation status

The bundled frontend registers all eleven cards and eleven visual editors from
one Lit/TypeScript bundle. Cards tolerate capability-dependent entities that
are absent or unavailable, and never fabricate backend data.

All cards are custom elements in one deterministic
`github-insights-cards.js` bundle installed with the `github_insights`
integration. Each card has a visual editor, `getStubConfig`, card-picker
metadata, validation, responsive grid options, and explicit
loading/empty/error/stale/partial states.

## Shared behavior

- Discovery reads Home Assistant entity/device registries, filters entity
  registry entries whose platform is `github_insights`, and keys metrics by the
  registry `translation_key`. The stable fallback is the suffix of the
  backend unique ID (`<immutable-owner-id>_<metric_key>`). Explicit
  `entities: { metric_key: entity_id }` mappings are available for migrations
  and unusual installations; discovery never depends on a display name.
- Concise and detailed YAML normalize into immutable typed config.
- Card defaults cascade to per-module or per-repository overrides.
- Repository selectors support auto discovery, explicit lists, include/exclude
  filters, favorites, search, and bounded results.
- Sorts are stable, ordered, typed, and configurable for nulls.
- Links come from backend-validated metadata and support GitHub Enterprise
  Server.
- Tap, hold, and double-tap use Home Assistant action semantics.
- Values include provenance and freshness; estimated values always contain the
  word "estimated".
- Rendering uses Lit text bindings and validated HTTP(S) links; GitHub content
  is never injected through unsafe HTML.
- All card shells are keyboard-focusable, expose progress semantics and status
  announcements, use touch-sized controls, and disable transitions under
  `prefers-reduced-motion`.

## Shared configuration

```yaml
type: custom:github-insights-actions
title: Actions
layout: responsive
metrics:
  - actions_runtime
  - actions_discounted_usage
  - actions_billable_usage
  - actions_cost
  - actions_budget
  - actions_estimated_minutes_remaining
entities: # optional override; registry discovery is the default
  actions_discounted_usage: sensor.github_insights_actions_discounted_or_included_consumption
tap_action:
  action: more-info
  entity: sensor.github_insights_actions_discounted_or_included_consumption
```

Every card supports `title`, `layout`, `metrics`, `entities`, `tap_action`,
`hold_action`, and `double_tap_action`. Editors expose the relevant common and
card-specific fields. All picker stubs are usable without YAML.

## Card suite

| Card | Primary purpose | Default content |
|---|---|---|
| `github-insights-overview` | Account landing card | Avatar, account, Actions usage/budget, AI availability, repos, PRs, workflow/security health, freshness |
| `github-insights-usage` | Flagship billing card | GitHub-reported quantities/costs, budget/enforcement, AI usage, storage, forecast, estimated equivalent minutes |
| `github-insights-repositories` | Multi-repository operations | Search, grouping, sorting, favorites, compact/grid rows, workflow/release/security indicators |
| `github-insights-repository` | One repository | Description, language, KPIs, latest events, workflow, usage, traffic, security, actions |
| `github-insights-actions` | Workflow and billing detail | Runtime, runs, failures, long jobs, usage by SKU/repo/workflow, cost, budget, estimate |
| `github-insights-copilot` | Authorized AI data | AI credits/premium requests, costs, adoption/activity, coding-agent/review, freshness |
| `github-insights-activity` | Development activity | Commits, PRs, issues, reviews, releases, selectable periods, simple trends |
| `github-insights-contributions` | Contribution patterns | Heatmap, totals, reliable streaks, repositories, weekday distribution |
| `github-insights-security` | Authorized alert posture | Alert counts/severity/repositories and safe GitHub links |
| `github-insights-compact` | Dense dashboard metric | One primary and secondary metric, icon, optional ring/bar/trend |
| `github-insights-dashboard` | Composite responsive surface | User-selected modules sharing layout and status context |

## Usage card rules

Never combine unlike units in one progress bar. Separate:

- workflow runtime;
- GitHub-reported included usage;
- GitHub-reported paid usage;
- gross, discount, and net monetary cost;
- GitHub-enforced monetary budget and consumed amount;
- stop-usage status; and
- estimated equivalent minutes.

The estimate presents the runner/SKU, price per minute, price source date, and
formula. It never labels itself as an allowance or hard limit.

## Repository card model

Central metric descriptors define key, translation key, value type, icon,
format, unit, availability rules, GitHub link relation, sort/filter support, and
editor options. Compact and expanded modes select from the same descriptors.

Default repository sort is:

1. favorites first;
2. unavailable/unknown last;
3. workflow health severity;
4. last push descending;
5. full name ascending.

## Visualizations

CSS and lightweight SVG provide progress bars/rings, sparklines, stacked bars,
heatmaps, status distributions, and trends. Every visualization has a text
equivalent, tooltip, empty/unknown handling, dark/light tokens, honest axes, and
reduced-motion behavior.

## Example

```yaml
type: custom:github-insights-repositories
repositories: auto
view: compact
group_by: organization
include:
  visibility:
    - public
    - private
exclude:
  archived: true
sort:
  - field: actions_usage
    direction: descending
    nulls: last
  - field: name
    direction: ascending
metrics:
  - stars
  - forks
  - open_issues
  - open_pull_requests
  - workflow_status
  - actions_usage
show_forks: true
```
