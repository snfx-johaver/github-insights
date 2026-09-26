# Card specifications

## Public card catalog

The bundled frontend registers exactly two custom elements and two visual
editors from one deterministic `github-insights-cards.js` artifact:

| Card | Purpose |
|---|---|
| `custom:github-insights-card` | Account, overview, usage, Actions, Copilot, activity, contributions, security, and dashboard-style content |
| `custom:github-insights-repository-card` | Auto-discovered repository collection, an explicit repository list, or one selected repository |

Layouts and former card identities are configuration, not registrations.
The picker therefore remains limited to these two entries.

## Shared behavior

- Entity discovery reads Home Assistant entity and device registries, filters
  the `github_insights` platform, and keys metrics by stable translation keys.
  Explicit `entities` mappings remain available for unusual installations.
- GitHub-provided text uses Lit text bindings. External links must pass URL
  validation and open with `noopener noreferrer`.
- Missing permissions and unavailable capabilities render explicit empty or
  unavailable states instead of fabricated values.
- Configured Actions allowance, GitHub-authoritative gross/discount/net costs,
  and runner-based estimated equivalent minutes remain distinct and labeled.
- Card shells are keyboard-focusable; progress, alerts, status, and heatmaps
  have accessible semantics and reduced-motion support.
- Optional diagnostics contain normalized configuration and anonymized entity
  mappings only, never entity states, attributes, tokens, signed URLs, or
  repository names.

## Account card

```yaml
type: custom:github-insights-card
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
metrics:
  - account
  - actions_configured_minutes_used_percent
  - actions_configured_minutes_remaining
  - actions_gross_cost
  - actions_discount
  - actions_cost
  - copilot_paid_usage
  - workflow_health
  - commits
  - contributions
  - dependabot_alerts
  - last_successful_sync
```

The editor can enable, disable, and reorder sections and metrics. Presets are
`overview`, `usage`, `actions`, `copilot`, `activity`, `contributions`,
`security`, `dashboard`, and `compact`. Selecting a preset seeds editable
sections, metrics, and presentation. Supported presentations are
`responsive`, `compact`, and `expanded`.

Section order controls visual order. Metric order is preserved inside each
section. Estimated metrics may be hidden without hiding authoritative usage.

## Repository card

```yaml
type: custom:github-insights-repository-card
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
  - stars
  - forks
  - open_issues
  - open_pull_requests
  - workflow_health
  - actions_usage_percent
```

Set `repository: owner/name` for one repository, `repositories` to a list for
an explicit collection, or `repositories: auto` for discovery. The editor
also exposes search, favorites, deterministic sorting, metric ordering, and
JSON repository overrides. Presentations are `responsive`, `compact`,
`expanded`, and `detail`. Per-repository overrides can change title,
presentation, favorite status, metrics, and metric badges.

## Beta migration from the former catalog

No obsolete custom element is registered at runtime. Update YAML before
loading the new bundle:

| Former type | Replacement |
|---|---|
| `custom:github-insights-overview` | `custom:github-insights-card` with `preset: overview` |
| `custom:github-insights-usage` | `custom:github-insights-card` with `preset: usage` |
| `custom:github-insights-actions` | `custom:github-insights-card` with `preset: actions` |
| `custom:github-insights-copilot` | `custom:github-insights-card` with `preset: copilot` |
| `custom:github-insights-activity` | `custom:github-insights-card` with `preset: activity` |
| `custom:github-insights-contributions` | `custom:github-insights-card` with `preset: contributions` |
| `custom:github-insights-security` | `custom:github-insights-card` with `preset: security` |
| `custom:github-insights-dashboard` | `custom:github-insights-card` with `preset: dashboard` |
| `custom:github-insights-compact` | `custom:github-insights-card` with `preset: compact` |
| `custom:github-insights-repositories` | `custom:github-insights-repository-card` with `repositories: auto` |
| `custom:github-insights-repository` | `custom:github-insights-repository-card` with the existing `repository` value |

Existing `metrics`, `entities`, actions, repository filters, sorting,
favorites, overrides, badges, severity, forecast, estimate, and diagnostics
settings can be copied to the replacement card. Old layout names should be
mapped to `responsive`, `compact`, `expanded`, or `detail`.
