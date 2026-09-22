# Dashboard examples

All GitHub Insights cards are installed by the single GitHub Insights HACS
integration. Mushroom, ApexCharts, Auto Entities, stack-in-card, layout-card,
card-mod, and mini-graph-card are optional companions and are never packaged
or required by GitHub Insights.

The examples use stable metric keys in `entities`. Omit `entities` to use
registry discovery when backend entities are available. A missing permission,
plan feature, or future backend phase produces an unavailable/empty state
instead of breaking the card.

## Resources

Register the GitHub Insights bundle once as a JavaScript module:

```text
/github_insights/frontend/github-insights-cards.js
```

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
    show_forecast: true
    show_estimated_minutes: true
    reference_runner: linux_standard
    severity:
      green: 0
      amber: 70
      red: 90
  - type: custom:apexcharts-card
    header:
      show: true
      title: Actions usage trend
    graph_span: 30d
    series:
      - entity: sensor.github_insights_actions_billable_usage
        name: Paid usage
      - entity: sensor.github_insights_actions_runtime
        name: Workflow runtime
```

Do not stack runtime and paid usage into one quantity: their units and billing
meaning can differ. The card always labels runner-converted values as
**estimated equivalent minutes**.

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
```

Auto Entities is optional convenience; registry discovery is built into the
GitHub Insights repositories card.

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

The bundled dashboard now has its own command-center layout with grouped usage,
delivery, risk, freshness, and repository sections. When Mushroom and
ApexCharts are installed and registered, it automatically embeds:

- a Mushroom status-chip rail for workflow, pull-request, security, and
  freshness state; and
- an ApexCharts 30-day engineering-activity chart for commits and merged pull
  requests.

No extra YAML is required for these enhancements. If either companion is not
installed, the dashboard keeps its complete native GitHub Insights layout
without an error or placeholder.

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
