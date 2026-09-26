# Configuration

GitHub Insights combines account setup, repository capabilities, Copilot data,
and optional enhanced-billing scopes in one integration. No release or tag has
been published yet.

The first release will support one config entry containing one GitHub server,
one authenticated identity, an optional secondary Billing / Usage API token,
selected organizations, optional enterprise reporting, and
selected/auto-discovered repositories.

Options now cover the optional classic billing token, personal billing,
selected billing organizations, an optional enterprise slug, a 30–1440 minute
billing interval, read-only budgets, optional budget management, an optional
configured Actions included-minutes allowance, a reference runner, desired
estimated minutes, and local warning/critical thresholds.

Current options cover explicit repository selection, bounded automatic
discovery, archived/fork filters, a 1–50 repository request ceiling, enabled
repository/workflow/release/activity/deployment/traffic/security/Copilot
categories, and a safe 5–360 minute update interval. The default collection cap
is 10 repositories.

Copilot AI-credit/premium-request and other billing categories require the
optional personal access token (classic). GitHub's billing usage endpoints do
not support fine-grained personal access tokens. Copilot activity and
repository-only features continue using the primary token and its
least-privileged permission model.

Unavailable categories remain independently disabled with an explanation. The
flow will not request write permissions until the user explicitly enables
budget management.

The config and options forms link directly to the official sources for values
that users must obtain:

- create a [fine-grained PAT](https://github.com/settings/personal-access-tokens/new)
  for primary account, repository, workflow, security, and Copilot activity;
- create a [classic PAT](https://github.com/settings/tokens/new) only for the
  optional billing/usage credential;
- review [billing usage and organization access](https://docs.github.com/en/billing/tutorials/gather-insights);
- identify an enterprise slug using GitHub's
  [enterprise slug documentation](https://docs.github.com/en/enterprise-cloud@latest/admin/managing-your-enterprise-account/changing-the-url-for-your-enterprise);
- check [product usage included with each plan](https://docs.github.com/en/billing/reference/product-usage-included)
  before explicitly entering an Actions included-minutes allowance; and
- review [personal Copilot settings](https://github.com/settings/copilot) and
  [organization Copilot policies](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/manage-policies).

The enterprise slug is the `<slug>` URL segment in
`https://github.com/enterprises/<slug>`. Personal users normally leave this
option blank. Billing organizations should include only organizations where
the token owner has the required owner or billing-manager access.

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

## Dashboard import

Create a dashboard under **Settings > Dashboards**, keep it managed by Home
Assistant, then paste the exact contents of
[`release-candidate-dashboard.yaml`](release-candidate-dashboard.yaml) into
that dashboard's **Raw configuration editor**. A deployment tool may instead
use Home Assistant's supported, authenticated Lovelace WebSocket API.

Do not add the template as a default file-backed dashboard. A declaration such
as this is supported for users who deliberately prefer YAML management, but it
makes the dashboard intentionally non-editable in the UI:

```yaml
lovelace:
  dashboards:
    github-insights:
      mode: yaml
      filename: dashboards/github_insights.yaml
      title: GitHub Insights
      show_in_sidebar: true
```

Never create or modify Lovelace records by editing `.storage` directly.

Cards normally discover entities through Home Assistant's entity and device
registries. An explicit mapping is supported when required:

```yaml
type: custom:github-insights-card
preset: usage
entities:
  actions_cost: sensor.github_insights_actions_cost
  actions_budget: sensor.github_insights_actions_budget
  actions_estimated_minutes_remaining: sensor.github_insights_actions_estimated_minutes_remaining
```

The mapping keys are canonical metric keys, not translated names. Missing
entities remain empty or unavailable and do not prevent other metrics from
rendering.

## Configured Actions included minutes

Set **Configured Actions included minutes** in integration options only when
you want a local allowance comparison. The default is `0` (unset); no plan
allowance is inferred. GitHub's current public enhanced-billing API reports
gross, discount, and net quantities and amounts but does not report the
historical included-minutes allowance.

When configured, four clearly labeled sensors expose the configured allowance,
GitHub-reported minutes used, remaining minutes, and percent used. The used
value prefers an unambiguous `discountQuantity` (discounted or included
consumption) and falls back to `grossQuantity` when required. It never uses
`netQuantity`. If Actions rows contain mixed units, a non-minute unit, or no
usable quantity, the configured allowance remains visible while its
used/remaining/percent derivations are unavailable with an explicit reason.
These configured values remain separate from the existing runner-price
estimate and from GitHub-enforced monetary budgets.

## Authentication for billing

GitHub's official billing usage endpoints require a personal access token
(classic) and do not support fine-grained PATs. Store that credential in the
optional **Billing / Usage API token** option. It is used only for billing and
usage endpoints, including Actions usage, AI-credit/premium-request usage, and
budget reads or confirmed mutations. The primary credential remains isolated
to normal GitHub APIs and Copilot activity reports.

When no billing token is configured, setup remains successful and account,
repository, workflow, security, rate-limit, and Copilot activity capabilities
continue operating. Billing and derived Actions-minute entities are unavailable
with `billing_token_not_configured`. The masked options value preserves an
existing token; replacing it updates the secondary credential and clearing it
removes billing access without exposing the saved value.

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
