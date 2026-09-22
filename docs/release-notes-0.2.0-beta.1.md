# GitHub Insights 0.2.0-beta.1

This beta candidate brings the complete GitHub Insights integration and all
eleven Lovelace cards together in one HACS integration artifact. It has not
been released or tagged yet; these notes describe the candidate that will be
published only after the remaining release gates pass.

## Highlights

- GitHub account, repository, workflow, release, deployment, activity, traffic,
  and authorized security insights.
- Authoritative enhanced-billing usage and cost data, monetary budgets,
  confirmed budget-management services, and clearly labeled runner-based
  estimated equivalent minutes.
- Official Copilot and AI billing, adoption, coding-agent, and code-review data
  where GitHub exposes it for the authenticated scope.
- One source-map-free frontend bundle with overview, usage, repositories,
  repository, Actions, Copilot, activity, contributions, security, compact,
  and dashboard cards.

## Install after publication

Once the prerelease and its `github_insights.zip` asset exist:

1. Add `https://github.com/snfx-johaver/github-insights` to HACS as a custom
   **Integration** repository.
2. Select prerelease `0.2.0-beta.1` and install it.
3. Restart Home Assistant when prompted.
4. Add GitHub Insights from **Settings > Devices & services**.
5. Register `/github_insights/frontend/github-insights-cards.js` as a
   JavaScript module under **Settings > Dashboards > Resources**.

## Upgrade

Back up the existing GitHub Insights integration and dashboard, install the
prerelease through HACS, restart Home Assistant, and confirm the config entry,
entities, bundled resource, and cards load. GitHub Insights uses one config
entry and preserves nonbilling account/repository operation when an optional
capability is unavailable.

## Important billing limitation

The billing usage endpoints used by GitHub Insights do not support fine-grained
PATs and require a personal access token (classic). Budget permissions and
availability are capability-detected separately. A fine-grained PAT continues
to provide supported account, repository, workflow, activity, traffic, and
security data; billing usage is reported unavailable with remediation guidance
instead of failing integration setup.

## Rollback

Reinstall the previous verified GitHub Insights version or restore only the
backed-up `custom_components/github_insights` directory and
`dashboards/github_insights.yaml`. Do not restore or modify unrelated Home
Assistant files or `.storage`.

This beta is for custom-repository validation only. No release or tag exists
yet, and it is not submitted to or available from the standard HACS catalog.
