# GitHub Insights

Bring your GitHub world home 🏠—keep an eye on repos, Actions, Copilot, usage
and costs from Home Assistant.

> [!IMPORTANT]
> Version `0.2.0-beta.1` brings the integration, GitHub data collectors,
> billing and budget tools, and all eleven bundled Lovelace cards together as
> one beta release candidate. No release or tag exists yet: publication remains
> blocked on the documented hosted and live Home Assistant validation gates.

## One integration and one installation

GitHub Insights is designed as exactly:

- one public repository;
- one HACS integration entry;
- one Home Assistant domain, `github_insights`;
- one config entry, authentication model, and GitHub API client;
- one version and release lifecycle; and
- one `github_insights.zip` artifact containing the backend and every Lovelace
  card.

The TypeScript source under `frontend/` is build-time source only. Its
deterministic bundle is placed in
`custom_components/github_insights/frontend/github-insights-cards.js` and
installed with the integration. There will be no separately installed frontend
package, plugin, repository, HACS entry, or version.

## Features

- GitHub account discovery, organization/repository selection, account sensors,
  API rate-limit diagnostics, reauthentication, repairs, and redacted
  diagnostics.
- Authoritative enhanced-billing detail and summary reports for personal,
  organization, and enterprise scopes on GitHub.com/GitHub Enterprise Cloud.
- Organization and enterprise budget discovery plus confirmed create, update,
  delete, and `prevent_further_usage` changes.
- Explicit separation of workflow runtime, included usage, paid usage, monetary
  cost, budgets, and estimated equivalent minutes.
- An optional user-configured Actions included-minutes allowance with derived
  configured used, remaining, and percent sensors when GitHub reports a single
  minute unit.
- Eleven responsive Lit-based cards, each with a visual editor, card-picker
  defaults, Home Assistant theme integration, keyboard support, screen-reader
  semantics, reduced-motion behavior, and missing/unavailable/error states.
- Read-only operation by default; budget writes require explicit opt-in and
  confirmation for every mutation.

Repository/workflow detail, activity/security reporting, and official
Copilot/AI collection are included with capability-aware empty and unavailable
states where GitHub does not authorize or provide data.

## Screenshots

Screenshot placeholders are retained until the cards are validated against a
live Home Assistant instance:

- Overview and usage desktop layout
- Repository operations grid
- Compact mobile layout
- Dark-theme executive dashboard

## Compatibility target

| Surface | Support |
|---|---|
| Home Assistant | Config-entry runtime targets current Home Assistant releases |
| HACS | Integration repository using a single zip release |
| GitHub.com | Primary target |
| GitHub Enterprise Server | Capability-detected; billing/Copilot parity is not assumed |
| Billing authentication | Personal access token (classic) required by GitHub; fine-grained PATs continue to work for supported non-billing data |
| Browser | Current Home Assistant-supported browsers |

## HACS custom-repository installation

After a validated prerelease exists:

1. Open HACS.
2. Add `https://github.com/snfx-johaver/github-insights` as a custom repository
   with category **Integration**.
3. Install **GitHub Insights**.
4. Restart Home Assistant if HACS requires it.
5. Add the GitHub Insights integration from **Settings > Devices & services**.
6. Add the bundled JavaScript module under
   **Settings > Dashboards > Resources**:
   `/github_insights/frontend/github-insights-cards.js`.
7. Under **Settings > Dashboards**, create a dashboard managed by Home
   Assistant, open its **Raw configuration editor**, and paste the exact
   contents of
   [`docs/release-candidate-dashboard.yaml`](docs/release-candidate-dashboard.yaml).

The integration serves this installed file through Home Assistant's static-path
API. Lovelace resource registration remains manual because Home Assistant does
not provide a stable public API for integrations to mutate dashboard resources.
The dashboard template may also be imported with Home Assistant's supported,
authenticated Lovelace WebSocket API. The default guidance is a storage-mode
dashboard so it remains editable in the UI. Declaring `github-insights` under
`lovelace: dashboards:` with `mode: yaml` is a valid advanced setup, but it
makes that dashboard intentionally non-editable in the UI.
Adding a custom repository is not acceptance into the standard HACS catalog.
When published, the `0.2.0-beta.1` candidate will be intended only for opt-in
prerelease/custom-repository validation. It is not currently installable as a
release asset. Standard HACS catalog submission is deferred until a stable
release is ready because the default catalog does not accept projects that are
still explicitly in alpha or beta testing.

## Manual installation

The release archive expands to one `github_insights` directory. Copy that
directory to:

```text
<config>/custom_components/github_insights
```

The directory contains both Python integration files and the frontend bundle.
Then add the same Lovelace module resource and import the dashboard template
into a user-created storage dashboard as shown above. Source files, tests,
source maps, and development dependencies are not shipped.

## Setup and permissions

The config flow requests a GitHub server and token, validates the
authenticated identity, discovers accessible organizations and repositories,
and explains unavailable capabilities. Read-only repository access is the
baseline. Billing, security, traffic, Copilot, and budget-management data each
require additional account roles, plans, policies, or token permissions.

Implemented sensors cover the authenticated account, rate limits, selected
repository metadata, open issue and pull-request counts, latest commit/release/
issue/pull request attributes, workflow health and bounded run/job runtime,
90-day activity with coverage-gated streaks, deployments, traffic, security
alerts, and official personal/organization AI-credit and premium-request
billing where authorized. Detailed traffic and streak entities are disabled by
default.

Copilot billing endpoints require a personal access token (classic);
fine-grained PATs are not supported for those endpoints. Organization Copilot
adoption, coding-agent, and code-review reports are collected only from the
official report API and HTTPS `copilot-reports.github.com` or
`githubusercontent.com` signed downloads, with no
authorization header sent to the download host and no signed URL retained.
No GitHub pages or undocumented endpoints are scraped.

Enhanced-billing usage endpoints require a **personal access token (classic)**.
GitHub explicitly does not support fine-grained PATs for these endpoints. A
fine-grained PAT remains valid for supported account/repository features; only
billing is marked unavailable.

Budget management is always disabled by default. The local management switch
only enables access to mutation services; it never changes a GitHub budget.
Every mutation service requires an exact action-specific confirmation string
and an authoritative post-write refresh. See [permissions](docs/permissions.md).

## Actions limits and estimates

GitHub's authoritative enforcement mechanism is a **monetary budget** with
`prevent_further_usage`, not a universal raw-minute ceiling. The current public
enhanced-billing API reports Actions gross quantity/cost, discounted-or-included
quantity/discount, and net quantity/cost, but it does not report the historical
plan included-minutes allowance.

Users may optionally configure their own included-minutes allowance in the
integration options. It defaults to unset (`0`), is always labeled
**Configured**, and produces configured used, remaining, and percentage values
only when GitHub reports an unambiguous Actions minute quantity. The derivation
prefers GitHub's discounted-or-included quantity and falls back to gross
quantity when the summary quantity is unavailable; it never treats net/billed
quantity as included-minute consumption. The configured allowance itself
remains available when set; mixed, non-minute, or unavailable usage makes the
used/remaining/percent derivations unavailable with an explicit reason.

An "estimated equivalent minutes" value may be calculated as:

```text
remaining monetary budget / selected runner price per minute
```

It will always be labeled **estimated**, identify the selected runner/SKU and
price snapshot, and never replace GitHub-reported quantities or enforcement
status.

## Entities and cards

The enhanced-billing API does not expose the billing UI's exact total included
plan allowance. GitHub Insights never invents one from plan lookup tables,
undocumented endpoints, or web scraping. A configured allowance is a local
planning input, while `grossQuantity`, `discountQuantity`, `netQuantity`, and
their monetary amounts remain authoritative GitHub values.

## Billing entities

Each configured billing scope receives a Billing device with billing period,
Actions gross/discount/net cost, unambiguous billed and discounted quantity,
optional configured included/used/remaining/percent minutes, budget count,
single-budget amount/remaining/utilization, estimated equivalent minutes,
warning/exhausted/blocked binary sensors, and a manual refresh button.
If multiple overlapping Actions budgets exist, aggregate amount sensors remain
unavailable and the individual budget summaries stay in bounded attributes.

Account-level local controls include:

- desired estimated Actions minutes (`number`);
- estimate reference runner (`select`); and
- budget-management service opt-in (`switch`).

These controls do not mutate GitHub. Financial changes use
`github_insights.create_budget`, `update_budget`, `delete_budget`, and
`set_stop_usage`, with the exact confirmation shown by the service error/help
text.

### Bundled cards

The initial design targets 24 default-enabled account/category entities plus 6
default-enabled entities per explicitly selected repository. Six write-capable
budget controls are conditional on budget-management mode. Detailed and
diagnostic entities are disabled by default.

Bundled cards:

- `custom:github-insights-overview`
- `custom:github-insights-usage`
- `custom:github-insights-repositories`
- `custom:github-insights-repository`
- `custom:github-insights-actions`
- `custom:github-insights-copilot`
- `custom:github-insights-activity`
- `custom:github-insights-contributions`
- `custom:github-insights-security`
- `custom:github-insights-compact`
- `custom:github-insights-dashboard`

Every card has a visual editor. The richer repository and billing experiences
remain bundled in the same integration installation: compact/expanded
repository views, favorites, deterministic multi-key sorting, safe GitHub deep
links, metric badges, configured allowance progress, authoritative cost
breakdowns, and an optional sanitized diagnostics panel. Entity discovery
filters the Home Assistant entity registry by the `github_insights` platform
and uses stable translation keys; explicit `entities` mappings are supported
as a compatibility override. See
[card specifications](docs/card-specifications.md).

## Example configuration

```yaml
type: custom:github-insights-usage
sections:
  - actions
  - ai
  - storage
  - budgets
layout: responsive
period: current_billing_cycle
show_forecast: true
actions_limit:
  show_enforcement: true
  show_estimated_minutes: true
  reference_runner: linux_standard
```

## Privacy and reliability

- Tokens remain in the Home Assistant config entry.
- Diagnostics redact credentials, headers, signed URLs, private identifiers,
  and local network details.
- GitHub is polled with conditional requests, pagination, rate-limit awareness,
  bounded concurrency, and capability-specific intervals.
- Partial failures retain last-known-good data and expose freshness and the
  affected capability rather than converting stale values into success.
- Reporting freshness depends on GitHub's own data pipeline.
- GitHub-provided strings are rendered as text and external actions accept only
  HTTP(S) URLs.

## Data availability and limitations

- Workflow runtime is not authoritative billed consumption.
- Included usage, paid usage, monetary budget usage, and workflow runtime are
  distinct and are never merged into one progress value.
- GitHub budgets are monetary limits. Equivalent minutes depend on a selected
  runner/SKU and are always labeled **estimated**.
- Billing and Copilot endpoints may require organization or enterprise scope,
  specific plans, account roles, or extra token permissions.
- Stop-usage enforcement is controlled by GitHub and can block workflows,
  including Actions workloads initiated by Copilot features.
- Repository, billing, security, activity, and Copilot card sections remain
  empty or unavailable when GitHub does not authorize or provide their data.
- Data freshness follows GitHub's reporting cadence and may lag source events.

## Dashboard companions

GitHub Insights does not require another card package. The
[release-candidate dashboard](docs/release-candidate-dashboard.yaml) is an
exact import template for a user-created, UI-editable storage dashboard; it is
not a file to install under `dashboards/`. The
[dashboard examples](docs/dashboard-examples.md) also show polished optional
layouts using separately installed Mushroom cards for headings/status,
ApexCharts for history, and Auto Entities for registry views, with native Home
Assistant fallbacks.

## Development

```text
python -m pip install -e .[dev]
npm install --prefix frontend
python scripts/generate_brand_assets.py
python scripts/validate_scaffold.py
ruff check .
ruff format --check .
mypy
pytest
npm run check --prefix frontend
python scripts/build_release.py
python scripts/validate_release_artifact.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/architecture.md),
and [the implementation plan](docs/implementation-plan.md).

## Release and publication status

No release has been created. The deterministic `github_insights.zip` builder
and validator are implemented, but release creation remains gated on successful
HACS Action, Hassfest, custom-repository installation, complete backend
validation, and safe Home Assistant validation. Standard HACS catalog
publication additionally requires a full release and external maintainer
review; it must not be described as available until merged.
See [release process](docs/release-process.md) and
[HACS publication](docs/hacs-publication.md).
