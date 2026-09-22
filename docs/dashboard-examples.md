# Dashboard examples

All GitHub Insights cards are installed by the single GitHub Insights HACS
integration. Mushroom, ApexCharts, Auto Entities, stack-in-card, layout-card,
card-mod, and mini-graph-card are optional companions and are never packaged
or required by GitHub Insights.

## UI-editable release-candidate dashboard

[`release-candidate-dashboard.yaml`](release-candidate-dashboard.yaml) is the
exact import template, not an installed dashboard file. Create a dashboard
under **Settings > Dashboards**, keep it managed by Home Assistant, and paste
the template into its **Raw configuration editor**. Automated deployment may
use the supported, authenticated Lovelace WebSocket API instead.

Do not edit `.storage` directly. Declaring `github-insights` under
`lovelace: dashboards:` with `mode: yaml` intentionally creates a file-backed
dashboard that cannot be edited in the UI.

The examples use stable metric keys in `entities`. Omit `entities` to use
registry discovery when backend entities are available. A missing permission,
plan feature, or unavailable GitHub capability produces an unavailable/empty
state instead of breaking the card.

## Resources

Register the GitHub Insights bundle once as a JavaScript module:

```text
/github_insights/frontend/github-insights-cards.js
```

The release-candidate import template intentionally uses a compact
Mushroom, ApexCharts, Auto Entities, and native fallback until this resource is
registered through a supported Lovelace resource mechanism. Its entity filters
are dynamic, so GitHub usernames and capability-dependent entity IDs are not
hardcoded. Reintroduce its full bundled-card views only after a supported Home
Assistant restart or config-entry reload exposes the current entity set and
resource registration is configured or recorded as release evidence.

Optional companion resources, when separately installed through HACS:

```text
/hacsfiles/lovelace-mushroom/mushroom.js
/hacsfiles/apexcharts-card/apexcharts-card.js
/hacsfiles/auto-entities/auto-entities.js
```

## 1. Personal GitHub overview

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: GitHub
    subtitle: Personal overview
  - type: custom:mushroom-chips-card
    chips:
      - type: entity
        entity: sensor.github_insights_octocat_account
        icon: mdi:github
      - type: entity
        entity: sensor.github_insights_octocat_api_rate_limit_remaining
        icon: mdi:speedometer
  - type: custom:github-insights-overview
    layout: responsive
    sections: [actions, repositories, workflows, security]
```

Native fallback: replace the Mushroom title/chips with a Markdown card and an
Entities card; the GitHub Insights overview remains unchanged.

## 2. GitHub Actions usage and limits

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: GitHub Actions
    subtitle: Runtime, billing, budget, and enforcement are separate
  - type: custom:github-insights-usage
    layout: hero
    sections: [actions, storage, budgets]
    metrics:
      - actions_configured_minutes_remaining
      - actions_configured_minutes_used_percent
      - actions_gross_cost
      - actions_discount
      - actions_cost
    show_forecast: true
    show_estimated_minutes: true
    reference_runner: linux_standard
    severity:
      green: 0
      amber: 70
      red: 90
  - type: custom:auto-entities
    card:
      type: custom:apexcharts-card
      header:
        show: true
        title: Actions usage trend
      graph_span: 30d
    card_param: series
    filter:
      include:
        - entity_id: sensor.github_insights_*actions_billed_consumption
          options:
            name: Paid usage
        - entity_id: sensor.github_insights_*actions_discounted_or_included_consumption
          options:
            name: Discounted or included consumption
    show_empty: false
```

The configured allowance defaults to unset and must be entered in integration
options. It is not a GitHub-reported plan allowance. Do not stack runtime and
paid usage into one quantity: their units and billing meaning can differ. The
card always labels gross/discount/net cost as GitHub-reported and
runner-converted values as **estimated equivalent minutes**.

## 3. GitHub Copilot and AI usage

```yaml
type: grid
columns: 2
square: false
cards:
  - type: custom:github-insights-copilot
    layout: responsive
  - type: custom:apexcharts-card
    header:
      show: true
      title: Premium request trend
    series:
      - entity: sensor.github_insights_copilot_paid_usage
        name: Paid AI usage
      - entity: sensor.github_insights_copilot_included_quantity
        name: Included AI usage
```

Copilot billing endpoints are scope-, plan-, and permission-dependent. An empty
card is expected when GitHub does not provide the capability.

## 4. Repository operations

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: Repository operations
  - type: custom:auto-entities
    card:
      type: entities
      title: GitHub repository entities
    filter:
      include:
        - integration: github_insights
          domain: sensor
  - type: custom:github-insights-repositories
    repositories: auto
    view: grid
    group_by: organization
    sort:
      - field: workflow_status
        direction: ascending
      - field: name
        direction: ascending
    metrics: [open_pull_requests, workflow_health, actions_usage_percent]
    show_archived: false
    show_forks: true
    show_debug: false
```

Auto Entities is optional convenience; registry discovery is built into the
GitHub Insights repositories card. Set `view: compact` for dense rows or
`view: expanded` for richer repository cards with metric badges and safe GitHub
links. Favorites and stable multi-key sorting are available in both modes.

The optional debug panel can be enabled in the visual editor or with
`show_debug: true`. It includes only sanitized resolved configuration and
discovered metric-to-entity mappings, never entity states or attributes.

## 5. Home Assistant development

```yaml
type: sections
sections:
  - type: grid
    cards:
      - type: custom:mushroom-title-card
        title: Home Assistant development
        subtitle: Repository health and delivery
      - type: custom:github-insights-repository
        repository: owner/home-assistant-config
        metrics:
          - workflow_health
          - open_pull_requests
          - actions_usage_percent
          - dependabot_alerts
      - type: custom:github-insights-activity
        period: 28d
      - type: custom:apexcharts-card
        header:
          show: true
          title: Commit activity
        series:
          - entity: sensor.github_insights_commits
```

## 6. Mobile GitHub status

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-chips-card
    alignment: justify
    chips:
      - type: entity
        entity: binary_sensor.github_insights_actions_blocked
        icon: mdi:block-helper
      - type: entity
        entity: binary_sensor.github_insights_actions_budget_warning
        icon: mdi:alert-outline
  - type: horizontal-stack
    cards:
      - type: custom:github-insights-compact
        primary_metric: actions_usage_percent
        secondary_metric: actions_budget_remaining
      - type: custom:github-insights-compact
        primary_metric: workflow_health
        secondary_metric: open_pull_requests
```

Native fallback: use two GitHub Insights compact cards without the chips row.

## 7. Security overview

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: GitHub security
    subtitle: Only alerts authorized by GitHub are shown
  - type: custom:github-insights-security
    layout: responsive
    metrics:
      - dependabot_alerts
      - code_scanning_alerts
      - secret_scanning_alerts
      - last_successful_sync
```

## 8. Combined executive overview

```yaml
type: sections
max_columns: 4
sections:
  - type: grid
    cards:
      - type: custom:mushroom-title-card
        title: Engineering overview
        subtitle: GitHub account, delivery, spend, and risk
      - type: custom:github-insights-dashboard
        layout: responsive
        sections: [usage, repositories, activity, security]
      - type: custom:apexcharts-card
        header:
          show: true
          title: 30-day engineering trend
        graph_span: 30d
        series:
          - entity: sensor.github_insights_commits
            name: Commits
          - entity: sensor.github_insights_pull_requests_merged
            name: Merged pull requests
      - type: custom:github-insights-contributions
        period: 90d
```

## Native-only fallback

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "## GitHub Insights"
  - type: custom:github-insights-overview
  - type: custom:github-insights-usage
  - type: custom:github-insights-repositories
  - type: entities
    title: Diagnostics
    entities:
      - sensor.github_insights_api_rate_limit_remaining
      - sensor.github_insights_last_successful_sync
```
