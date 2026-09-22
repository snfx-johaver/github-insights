# GitHub Insights 0.2.0-beta.1

This beta candidate brings the complete GitHub Insights integration and two
configurable Lovelace cards together in one HACS integration artifact. It has not
been released or tagged yet; these notes describe the candidate that will be
published only after the remaining release gates pass.

## Highlights

- GitHub account, repository, workflow, release, deployment, activity, traffic,
  and authorized security insights.
- Authoritative enhanced-billing usage and cost data, monetary budgets,
  confirmed budget-management services, and clearly labeled runner-based
  estimated equivalent minutes.
- Optional configured Actions included-minutes tracking, with configured used,
  remaining, and percent values derived from minute-based GitHub usage without
  conflating net billed quantity.
- Official Copilot and AI billing, adoption, coding-agent, and code-review data
  where GitHub exposes it for the authenticated scope.
- One source-map-free frontend bundle with exactly
  `custom:github-insights-card` and
  `custom:github-insights-repository-card`; former card roles are presets and
  editor configuration rather than additional picker entries.
- Rich repository and billing presentation, safe GitHub deep links, favorites,
  stable sorting, metric badges, editors, and an optional sanitized diagnostics
  panel, all in that same bundled artifact.

## Install after publication

Once the prerelease and its `github_insights.zip` asset exist:

1. Add `https://github.com/snfx-johaver/github-insights` to HACS as a custom
   **Integration** repository.
2. Select prerelease `0.2.0-beta.1` and install it.
3. Restart Home Assistant when prompted.
4. Add GitHub Insights from **Settings > Devices & services**.
5. Register `/github_insights/frontend/github-insights-cards.js` as a
   JavaScript module under **Settings > Dashboards > Resources**.
6. Create a dashboard under **Settings > Dashboards** and paste the exact
   contents of `docs/release-candidate-dashboard.yaml` into its **Raw
   configuration editor**.

The template may also be imported through Home Assistant's supported,
authenticated Lovelace WebSocket API. The default is a storage-mode dashboard
that remains editable in the UI. Declaring `github-insights` under
`lovelace: dashboards:` with `mode: yaml` intentionally makes it file-backed
and non-editable in the UI. Never edit `.storage` directly.

## Upgrade

Back up the existing GitHub Insights integration and dashboard, install the
prerelease through HACS, restart Home Assistant, and confirm the config entry,
entities, bundled resource, and cards load. GitHub Insights uses one config
entry and preserves nonbilling account/repository operation when an optional
capability is unavailable.

To migrate an existing YAML dashboard, create a temporary storage dashboard
such as `github-insights-ui`, import and verify the template there, remove only
the old `github-insights` YAML dashboard declaration from `configuration.yaml`,
run Home Assistant's configuration check, and restart. Verify the storage
dashboard again, then optionally rename its URL. Keep the old YAML file for
rollback until validation is complete; do not edit `.storage`.

Dashboards created against the earlier beta catalog must update their YAML.
Map overview, usage, Actions, Copilot, activity, contributions, security,
dashboard, and compact cards to `custom:github-insights-card` with the matching
`preset`. Map repository collection and single-repository cards to
`custom:github-insights-repository-card`, preserving `repositories` or
`repository`. Legacy custom elements are intentionally not registered, so they
cannot continue to appear in the card picker.

## Important billing limitation

The billing usage endpoints used by GitHub Insights do not support fine-grained
PATs and require a personal access token (classic). Budget permissions and
availability are capability-detected separately. A fine-grained PAT continues
to provide supported account, repository, workflow, activity, traffic, and
security data; billing usage is reported unavailable with remediation guidance
instead of failing integration setup.

GitHub's current public enhanced-billing API exposes Actions gross, discount,
and net quantities and amounts, but not the historical included-minutes
endpoint. GitHub Insights does not call undocumented endpoints, scrape the
billing UI, or infer plan allowances. The optional configured allowance
defaults to unset and is always labeled as configured/derived.

## Rollback

Reinstall the previous verified GitHub Insights version or restore only the
backed-up `custom_components/github_insights` directory, resource registration,
and dashboard backup. Do not restore or modify unrelated Home Assistant files
or edit `.storage`.

This beta is for custom-repository validation only. No release or tag exists
yet, and it is not submitted to or available from the standard HACS catalog.
