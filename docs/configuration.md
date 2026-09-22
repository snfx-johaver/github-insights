# Configuration

Phases 2-5 implement account setup, repository capabilities, Copilot data, and
optional enhanced-billing scopes. No release has been published yet.

The first release will support one config entry containing one GitHub server,
one authenticated identity, selected organizations, optional enterprise
reporting, and selected/auto-discovered repositories.

Options now cover personal billing, selected billing organizations, an optional
enterprise slug, a 30–1440 minute billing interval, read-only budgets, optional
budget management, a reference runner, desired estimated minutes, and local
warning/critical thresholds.

Current options cover explicit repository selection, bounded automatic
discovery, archived/fork filters, a 1–50 repository request ceiling, enabled
repository/workflow/release/activity/deployment/traffic/security/Copilot
categories, and a safe 5–360 minute update interval. The default collection cap
is 10 repositories.

Copilot billing categories require a personal access token (classic). GitHub's
billing usage endpoints do not support fine-grained personal access tokens.
Repository-only features may still use the least-privileged token model
supported by their individual endpoints.

Unavailable categories remain independently disabled with an explanation. The
flow will not request write permissions until the user explicitly enables
budget management.

## Lovelace resource

The integration serves its installed bundle through Home Assistant's supported
static-path API:

```text
/github_insights/frontend/github-insights-cards.js
```

Add that URL once under **Settings > Dashboards > Resources** with resource
type **JavaScript module**. Automatic mutation of Lovelace resources is not
used because Home Assistant does not expose a stable public integration API for
it. If static-path behavior changes in a future Home Assistant release, the
cards remain inside the same HACS-installed integration payload and only this
small adapter/resource URL needs compatibility work.

Cards normally discover entities through Home Assistant's entity and device
registries. An explicit mapping is supported when required:

```yaml
type: custom:github-insights-usage
entities:
  actions_cost: sensor.github_insights_actions_cost
  actions_budget: sensor.github_insights_actions_budget
  actions_estimated_minutes_remaining: sensor.github_insights_actions_estimated_minutes_remaining
```

The mapping keys are canonical metric keys, not translated names. Missing
entities remain empty or unavailable and do not prevent other metrics from
rendering.

## Authentication for billing

GitHub's official billing usage endpoints require a personal access token
(classic) and do not support fine-grained PATs. Tokens beginning with
`github_pat_` are detected locally and billing usage is marked unavailable
without making a doomed billing request. Account and repository capabilities
continue operating.

Organization usage requires an organization owner/admin or billing role.
Enterprise usage requires an eligible enterprise billing role. GitHub
Enterprise Server does not expose the enhanced-billing endpoints; the optional
enterprise field refers to GitHub Enterprise Cloud.

## Safe budget changes

Budget CRUD is implemented only for the documented organization and enterprise
endpoints. Personal budget CRUD is not exposed because GitHub does not document
it. Repository budgets are created as `repository` scopes within an
organization or enterprise budget API.

Budget management must be enabled first. Each service then requires a literal
confirmation containing the affected scope, amount/currency, product or SKU,
and enforcement state. Deletion and disabling stop-usage use stronger phrases.
The integration never retries a mutation automatically and refreshes the
authoritative budget state after success.
