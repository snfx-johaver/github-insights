# Configuration

Phase 2 implements this read-only setup flow. No release has been published yet.

The first release will support one config entry containing one GitHub server,
one authenticated identity, selected organizations, optional enterprise
reporting, and selected/auto-discovered repositories.

Options will cover repository filters, update intervals within safe bounds,
data categories, history granularity, API request limits, archived/forked
repositories, billing scope, currency/cost display, forecasting, security,
traffic, read-only budgets, optional budget management, reference runner/SKU,
and local warning thresholds.

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
