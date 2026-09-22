# Data availability

GitHub Insights uses feature detection. A metric can vary by account type,
role, plan, repository visibility, token type and permissions, GitHub API
version, enhanced-billing enrollment, Copilot policy, and GitHub.com versus
GitHub Enterprise Server.

## Availability classes

| Class | Behavior |
|---|---|
| Available | Create/update the entity from an official response |
| Missing permission | Keep unrelated categories working; omit or mark the affected entity unavailable with a concise reason |
| Unsupported | Do not create the entity; expose the capability reason in diagnostics/options |
| Temporarily failed | Preserve last-known-good value and mark stale/partial |
| Estimated | Create only when enabled and label every display and attribute as estimated |

Zero is never used as a fallback for unavailable data.

## Confirmed official data surfaces

Official GitHub documentation currently describes:

- authenticated user, organizations, repositories, issues, pull requests,
  releases, languages, workflows, runs, jobs, artifacts, deployments, and rate
  limits;
- repository traffic views, clones, referrers, and popular paths with limited
  historical windows and elevated repository access;
- Dependabot, code-scanning, and secret-scanning alerts where the feature,
  plan, role, and token allow them;
- enhanced-billing detail and public-preview summary reports containing product,
  SKU, quantity, unit type, unit price, gross amount, discount, net amount, and
  repository attribution at supported scopes;
- billing budgets containing amount, consumed amount, scope, product/SKU,
  alerting, and `prevent_further_usage`;
- personal and organization AI-credit and premium-request billing reports
  using a personal access token (classic); and
- organization/enterprise Copilot usage reports where policy and role permit.

These surfaces are **API availability**, not proof that a particular user's
token or plan can retrieve them.

Workflow/run/job timestamps are GitHub-reported. A duration calculated from
those timestamps is a **derived measurement**. GitHub's legacy workflow/run
timing endpoints are closing down, and enhanced billing reports do not preserve
complete per-workflow billing attribution. The integration must not reconstruct
an "authoritative workflow cost" from runtime.

## Data not universally retrievable

- The enhanced-billing response does not expose the billing UI's exact total
  included-plan allowance. GitHub Insights does not fabricate a remaining
  allowance from plan tables. `discountQuantity` is retained as authoritative
  discounted-or-included consumption, not total allowance.
- Workflow run duration cannot establish included, billable, or remaining
  minutes because runner SKU, rounding, public-repository treatment,
  self-hosting, discounts, and plan allowances affect billing.
- Budget amount divided by a runner price produces only estimated equivalent
  minutes.
- Private contribution details may be absent or aggregated.
- Reliable activity streaks require complete daily coverage for the evaluated
  period; otherwise no streak entity is created.
- Copilot adoption/activity reports and AI-credit/premium-request billing are
  different products and may have different scopes and reporting delays.
- Current Copilot adoption, coding-agent, and code-review reports are delivered
  through expiring signed JSON/NDJSON downloads. GitHub Insights accepts only
  HTTPS `copilot-reports.github.com` and `githubusercontent.com` report hosts,
  sends no authorization header to
  the download host, caps each report at 10 MB, parses documented aggregate
  fields, and never persists or exposes the signed URL.
- Copilot activity does not imply Actions consumption, although Copilot code
  review can consume Actions minutes for private repositories.
- GitHub Enterprise Server may not expose GitHub.com billing, budget, Copilot,
  or traffic features.
- GitHub's Events API is limited to recent/bounded activity and is not a
  complete immutable audit history.
- Repository traffic APIs provide only GitHub's bounded recent window (currently
  14 days); longer trends are locally calculated from snapshots collected while
  the integration is running.

## No documented public API identified

Phase 1 found no documented public API for:

- exact real-time Copilot prompt/token details or prompt/response content;
- a stable equivalent to GitHub's internal UI quota endpoints;
- exact live remaining Copilot quota across every plan and pooling model;
- future invoice prediction;
- retroactive per-workflow billing attribution after timing endpoints close;
- repository traffic older than the official window unless previously sampled;
  or
- a complete immutable user/organization/repository activity history through
  the Events API.

GitHub Insights will not call undocumented `copilot_internal` endpoints or
scrape GitHub billing pages.

## Freshness

Repository and workflow resources are near-real-time API snapshots subject to
polling intervals and rate limits. Billing and Copilot reporting can lag and
must display the GitHub report period and fetch time. GitHub documents Actions
artifact storage reporting delays of approximately 6–12 hours; the UI must not
present such values as live.

Copilot usage reports are generated daily. Recent IDE telemetry can take three
full UTC days to finalize, so those dates should be marked provisional.
Organization and enterprise reports can also depend on metrics-policy and IDE
telemetry settings. They are adoption/activity telemetry, not a productivity
score.

## Budget caveat

GitHub documents that usage incurred before a newly created budget in its first
billing cycle may not count against that budget. The integration must show the
budget creation/effective context and never imply retroactive enforcement.

Personal enhanced-billing usage is documented, but personal budget CRUD is not.
Budget CRUD is therefore limited to organization and enterprise endpoints.
Repository budgets are nested budget scopes rather than standalone repository
API routes.

## Phase 1 environment observation

On 2026-09-18 from this workspace:

- `\\192.168.1.4\config` was not reachable with a read-only `Test-Path`.
- TCP connection to `192.168.1.5:10513` failed and an independent HTTP probe
  reported by the coordinating session timed out.
- The Home Assistant MCP proxy is not registered as an available tool in this
  session.

These observations are current validation blockers, not evidence that the share
or service does not exist. No Home Assistant file was read, copied, modified,
or committed, and no restart or entity operation was attempted.

## Sources

- [GitHub billing usage API](https://docs.github.com/en/rest/billing/usage)
- [GitHub budgets API](https://docs.github.com/en/rest/billing/budgets)
- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [GitHub Copilot usage metrics API](https://docs.github.com/en/rest/copilot/copilot-usage-metrics)
- [GitHub rate limits API](https://docs.github.com/en/rest/rate-limit/rate-limit)
