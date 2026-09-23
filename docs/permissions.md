# Permissions

GitHub Insights requests the least privilege needed for selected features.
Read-only operation is the default and remains useful when billing or
administrative data is unavailable.

## Permission matrix

| Capability | Typical fine-grained permission/role | Classic PAT fallback | Notes |
|---|---|---|---|
| Current user/public profile | Account metadata read | `read:user` where needed | Public fields may need no extra scope |
| Private repositories | Repository metadata/contents read | `repo` | Select only repositories the user wants monitored |
| Organizations | Organization members/metadata read | `read:org` | Organization selection and some Copilot metrics |
| Workflow runs/jobs/artifacts | Actions read | `repo` for private repositories | Runtime and status, not billing consumption |
| Traffic | Repository administration/metadata read with push access | `repo` | GitHub restricts traffic endpoints and retention windows |
| Dependabot alerts | Dependabot alerts read | `security_events` or `repo` | Plan/feature dependent |
| Code-scanning alerts | Code scanning alerts read | `security_events`, `repo`, or public-repo cases | Role restrictions apply |
| Secret-scanning alerts | Secret scanning alerts read | `security_events` or `repo` | Never expose literal secrets |
| Organization billing usage | Organization administration/billing-manager role | Classic PAT required | Enhanced billing may be required; fine-grained PATs are unsupported |
| Personal billing usage | Authenticated account holder | Classic PAT required | Applies only to usage billed personally; fine-grained PATs are unsupported |
| Enterprise billing usage | Enterprise billing role or documented enterprise billing access | Classic PAT for PAT authentication | GitHub Enterprise Cloud only |
| Copilot organization metrics | View organization Copilot metrics | `read:org` | Organization policy must enable metrics |
| Copilot enterprise metrics | View enterprise Copilot metrics and owner/billing role | `manage_billing:copilot` or `read:enterprise` | Reports use expiring signed URLs |
| Budget read | Organization/enterprise admin or billing manager at documented scope | Endpoint-specific | No documented personal budget endpoint |
| Budget create/update/delete | Same role plus write-capable credential | Endpoint-specific | Requested only after explicit opt-in; fine-grained PAT support is not documented |

GitHub documentation and live response headers are authoritative for a specific
endpoint. The UI must show detected capabilities instead of promising that a
named scope alone guarantees access.

Fine-grained PATs are limited to a resource owner and selected repositories, so
one token may not cover multiple organizations. Some endpoints still have token
model gaps. Classic PATs are broader and can require SAML SSO authorization.
GitHub App installation/user tokens are the preferred long-term organization
model, but remain future work. Endpoint documentation and
`X-Accepted-GitHub-Permissions` are the final authority.

GitHub's billing usage tutorial explicitly requires a personal access token
(classic) for the usage report endpoints and states that fine-grained PATs are
not supported. GitHub Insights therefore routes AI-credit, premium-request,
Actions billing, budgets, and other billing usage categories only through the
optional secondary classic PAT. The primary token remains exclusive to normal
GitHub APIs and Copilot activity. Capability probes remain authoritative, and a
rejected billing probe never disables repository-only read functionality.
Budget documentation does not make the same PAT-type guarantee, so GitHub
Insights feature-detects budget reads independently and does not claim
fine-grained PAT support.

## Token handling

- Store the primary token in config-entry data and the optional billing token in
  that same config entry's options.
- Never render either real token back into a form or place either token in
  entity state/attributes, frontend config, URLs, issue reports, logs, or
  diagnostics.
- Redact `Authorization`, cookies, query credentials, signed URLs, and common
  token-shaped fields recursively.
- Reauthentication replaces only the primary token. The masked billing-token
  option can be preserved, replaced, or cleared without changing stable entity
  IDs.
- Diagnostics report permission names and capability results, never credential
  values.
- Secret-scanning requests use response filtering where supported, and the
  literal `secret` field is never persisted or emitted.

## Budget-management escalation

Read-only users are not prompted for write permissions. Enabling budget
management starts a reconfigure/reauthentication path that explains the exact
additional capability. Write entities remain unavailable until a safe
capability probe succeeds.

Every create, update, enforcement toggle, amount change, or removal requires
action-specific confirmation. Removal and disabling stop-usage enforcement use
stronger confirmation because they can increase financial exposure or remove
guardrails.
