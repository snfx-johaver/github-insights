# Troubleshooting

GitHub Insights has a functional Phase 2 core but remains unreleased.

When implementation begins, troubleshooting will distinguish:

- invalid/expired authentication and reauthentication;
- missing endpoint permission;
- unsupported plan/server/API capability;
- primary or secondary rate limiting;
- stale or partial category data;
- delayed GitHub billing/Copilot reports;
- unavailable entities versus missing entities;
- missing bundled frontend resource; and
- version mismatch between integration and cached browser bundle.

Diagnostics must be sanitized before sharing. Never post tokens, authorization
headers, signed URLs, private repository names, Home Assistant storage, or
local-network details.
# Troubleshooting

## Account data works but billing is unavailable

GitHub billing usage endpoints require a personal access token (classic).
Fine-grained PATs, including tokens with the `github_pat_` prefix, are not
supported by those endpoints. GitHub Insights keeps all other authorized data
working and reports billing as `classic_pat_required`.

Create a classic PAT with only the account/organization access required for the
selected billing scope, authorize SAML SSO if the organization requires it, and
use the integration reauthentication flow. Do not broaden repository access
solely for billing.

An HTTP 403 from billing is treated as a capability failure, not as global
credential failure. A 404 can mean enhanced billing or budgets are not enabled
for the scope.

## Included minutes are missing

The enhanced-billing API does not return the billing UI's exact total included
allowance. GitHub Insights intentionally does not infer it from a plan name or
static plan table. The discounted quantity is available when returned, but it
must not be interpreted as total or remaining allowance.

## Budget amount sensors are unavailable

If a scope has multiple potentially overlapping Actions budgets, GitHub
Insights avoids summing them because that could overstate the effective limit.
The budget count and bounded budget attributes remain available. Manage a
specific budget by ID through the confirmed services.
