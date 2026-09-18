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
