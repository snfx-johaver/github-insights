# GitHub Insights

GitHub usage, Actions billing, Copilot metrics, and repository insights for
Home Assistant.

> [!IMPORTANT]
> GitHub Insights is currently at **Phase 2: core integration development**.
> Version `0.1.0-beta.1` implements a read-only Home Assistant config flow,
> GitHub account discovery, rate-limit diagnostics, and account sensors. It is
> intentionally unreleased while hosted and real-instance validation continues.

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
deterministic bundle will be placed in
`custom_components/github_insights/frontend/github-insights-cards.js` and
installed with the integration. There will be no separately installed frontend
package, plugin, repository, HACS entry, or version.

## Planned features

- GitHub account, organization, repository, workflow, activity, contribution,
  traffic, and authorized security data.
- Authoritative GitHub billing usage and monetary budgets where official APIs
  and permissions expose them.
- Copilot billing and usage metrics where the account scope and plan support
  official endpoints.
- Explicit separation of workflow runtime, included usage, paid usage, monetary
  cost, budgets, and estimated equivalent minutes.
- Eleven responsive Lit-based cards with visual editors and Home Assistant
  theme integration.
- Read-only operation by default; budget writes require explicit opt-in and
  confirmation for every mutation.

## Screenshots

Screenshots will be added after the Phase 6 frontend implementation. No mock
screenshots are presented as completed functionality.

## Compatibility target

| Surface | Phase 2 position |
|---|---|
| Home Assistant | Config-entry runtime targets current Home Assistant releases |
| HACS | Integration repository using a single zip release |
| GitHub.com | Primary target |
| GitHub Enterprise Server | Capability-detected; billing/Copilot parity is not assumed |
| Authentication | Personal access token first; GitHub App/OAuth abstraction reserved |
| Browser | Current Home Assistant-supported browsers |

## Planned HACS installation

After a validated prerelease exists:

1. Open HACS.
2. Add `https://github.com/snfx-johaver/github-insights` as a custom repository
   with category **Integration**.
3. Install **GitHub Insights**.
4. Restart Home Assistant if HACS requires it.
5. Add the GitHub Insights integration from **Settings > Devices & services**.
6. Register the bundled module resource only if the integration cannot do so
   through a supported Home Assistant mechanism:
   `/github_insights/frontend/github-insights-cards.js`.

The exact resource URL will be validated before the first release. Adding a
custom repository is not acceptance into the standard HACS catalog.

## Planned manual installation

The release archive will expand to one `github_insights` directory. Copy that
directory to:

```text
<config>/custom_components/github_insights
```

The directory will contain both Python integration files and the frontend
bundle. Source files, tests, source maps, and development dependencies will not
be shipped.

## Setup and permissions

The Phase 2 config flow requests a GitHub server and token, validates the
authenticated identity, discovers accessible organizations and repositories,
and explains unavailable capabilities. Read-only repository access is the
baseline. Billing, security, traffic, Copilot, and budget-management data each
require additional account roles, plans, policies, or token permissions.

Implemented sensors cover the authenticated account, public/private repository
counts when supplied by GitHub, followers/following, visible organizations,
core REST rate-limit remaining/reset, and last successful synchronization.
Repository discovery is bounded metadata for configuration; detailed repository
entities remain Phase 4 work.

Budget management is always disabled by default. Write-capable entities appear
only after explicit opt-in and successful capability detection. See
[permissions](docs/permissions.md).

## Actions limits and estimates

GitHub's authoritative enforcement mechanism is a **monetary budget** with
`prevent_further_usage`, not a universal raw-minute ceiling. GitHub-reported
usage quantity, gross cost, discount, net cost, included allowance, workflow
runtime, and budget consumption are distinct values.

An "estimated equivalent minutes" value may be calculated as:

```text
remaining monetary budget / selected runner price per minute
```

It will always be labeled **estimated**, identify the selected runner/SKU and
price snapshot, and never replace GitHub-reported quantities or enforcement
status.

## Planned entities and cards

The initial design targets 24 default-enabled account/category entities plus 6
default-enabled entities per explicitly selected repository. Six write-capable
budget controls are conditional on budget-management mode. Detailed and
diagnostic entities are disabled by default.

Cards:

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

See [card specifications](docs/card-specifications.md).

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
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/architecture.md),
and [the implementation plan](docs/implementation-plan.md).

## Release and publication status

No release has been created. HACS custom-repository installation and standard
catalog submission remain blocked until implementation, automated validation,
artifact installation testing, and safe Home Assistant validation succeed.
See [release process](docs/release-process.md) and
[HACS publication](docs/hacs-publication.md).
