# Deployment

## Current status

Phase 9 candidate files were staged on 2026-09-22 against Home Assistant
2026.9.3. Automated source/artifact gates passed, and the existing GitHub
Insights installation and dashboard were backed up before direct UNC byte
writes. Home Assistant configuration check, restart, resource registration,
and post-restart runtime validation remain blocked because no authenticated
Home Assistant browser/API session is available. `release-ready.json` is
therefore intentionally absent.

The deployed files are pending a supported configuration check and restart.
They must not be treated as a completed live validation or HACS installation.

## 0.2.0-beta.1 candidate evidence

### Automated validation

- Local: scaffold/JSON/YAML validation, Ruff, Ruff format, strict mypy,
  frontend lint/typecheck/17 tests/build, and 13 standalone release-gate tests.
- Linux Validate workflow: backend including complete pytest, frontend, and
  metadata passed:
  <https://github.com/snfx-johaver/github-insights/actions/runs/35729806773>.
- HACS Action passed:
  <https://github.com/snfx-johaver/github-insights/actions/runs/35729809558>.
- Hassfest passed:
  <https://github.com/snfx-johaver/github-insights/actions/runs/35729813129>.
- Gitleaks passed:
  <https://github.com/snfx-johaver/github-insights/actions/runs/35729816223>.

The runtime-only archive was built twice with identical bytes and independently
validated:

| Property | Value |
|---|---|
| Version | `0.2.0-beta.1` |
| Archive | `github_insights.zip` |
| SHA-256 | `5983c05b16be9ffc32b7bfcf0659bbef274bae09f557f187b8266fed4ddd223d` |
| Size | 79,009 bytes |
| ZIP entries | 27 |
| Manifest-listed runtime files | 26 |

The archive has one `github_insights/` root, includes the bundled card asset and
deployment manifest, and excludes tests, fixtures, source trees, Node modules,
Markdown, TypeScript, source maps, and Python bytecode.

### Backup and deployment

Only these live paths were written:

- `custom_components/github_insights`
- `dashboards/github_insights.yaml`

No `configuration.yaml`, unrelated integration, dashboard, entity, resource,
or `.storage` file was written. The rollback backup is:

```text
\\192.168.1.4\config\dashboard-backups\github-insights-20260922-145622
```

Backup evidence:

| Item | Evidence |
|---|---|
| Prior integration files | 33, including 10 generated `.pyc` files |
| Prior manifest SHA-256 | `d7a450a55a90446cbb658e88a1f65f0eb43678a69cea0cdbb518701589f11acc` |
| Prior dashboard SHA-256 | `8b41421d10ac3eb2b92a7b5bd09bd0accfc668ac5df0b1e358712bc574271992` |
| Prior dashboard size | 1,859 bytes |

Post-write evidence:

| Item | Evidence |
|---|---|
| Installed manifest version | `0.2.0-beta.1` |
| Installed files | 27 exact runtime files |
| Deployment-manifest SHA-256 | `e8de1b78c3df43368169d42871fd4955ef6ac53287ac76626db2f1c08879c040` |
| Dashboard SHA-256 | `f126451a45cd585749ac874882a9a7891f5cb98d3b429c1f4472024f027c01d0` |
| Dashboard size | 13,935 bytes |
| Zero-length files | None |
| Extra files | None |
| `.pyc` files | None before restart |
| Development Markdown | None |

Every manifest-listed deployed file was compared to its SHA-256, the deployment
manifest itself matched the staged copy, and the dashboard matched the
repository candidate byte-for-byte. The obsolete installed
`frontend/README.md` was removed.

### Adaptive dashboard fallback

The original candidate dashboard referenced bundled card types before the
Lovelace module was registered. Its first native fallback then referenced
deployment-specific entity IDs and left capability tabs sparse. Both failure
modes were removed without modifying `.storage`:

- the live dashboard now has two useful views: **Overview** and **All entities**;
- Mushroom, ApexCharts, Auto Entities, and native cards remain in use;
- all GitHub Insights entities are selected through dynamic `entity_id` filters;
- no deployment-specific entity ID or `custom:github-insights-*` card is present;
- the dashboard automatically exposes new entities after a supported restart
  and config-entry reload.

The final live dashboard SHA-256 is
`b7565c77da1a4e976104fab6fcd6fd414e27cc0234f36dc56775195de350ad81`.
Its immediate rollback backup is:

```text
\\192.168.1.4\config\dashboard-backups\github-insights-dynamic-20260922-151538\github_insights.yaml
```

Home Assistant returned HTTP 200 after the write. This verifies process
availability only; authenticated configuration check, restart, resource
registration, and post-restart entity validation remain pending.

After the write, the Home Assistant root returned HTTP 200 and the Supervisor
observer reported **Connected**, **Supported**, and **Healthy**. This confirms
that the existing process remained healthy; it does not prove the new
integration loaded. The new static bundle URL still returned 404 because no
restart/reload or supported Lovelace resource registration occurred.

### Blocked live gates

The supported calls are Home Assistant's authenticated
`POST config/core/check_config`, `homeassistant.restart` service, and
Lovelace/HACS WebSocket commands. This session reached the login page but had no
authenticated `hass` object, API token, SSH key, or registered MCP tool. The
user was unavailable to authenticate. The following remain incomplete:

- Home Assistant configuration check;
- restart and post-restart HTTP/observer health;
- config-entry migration;
- device/entity count, availability, and capability-state validation;
- live confirmation that a fine-grained PAT leaves nonbilling data operational
  while billing usage reports the classic-PAT remediation;
- `/github_insights/frontend/github-insights-cards.js` static loading;
- supported Lovelace module registration while preserving the existing 24
  resources;
- dashboard/custom-card rendering;
- HACS custom-repository prerelease install/upgrade validation.

Do not set `live_home_assistant_validation` or
`custom_repository_install_test` to true until those exact gates are completed.

## One-install layout

The release artifact contains exactly:

```text
github_insights/
  __init__.py
  ...
  manifest.json
  translations/
  frontend/
    github-insights-cards.js
  deployment-manifest.json
```

HACS installs the single integration directory under
`custom_components/github_insights`. The frontend is not installed under a
separate `/community/` plugin and has no independent HACS entry.

## Resource registration

The integration idempotently registers its bundled `frontend/` directory with
Home Assistant's supported HTTP static-path API. Register this Lovelace module
resource manually:

```text
/github_insights/frontend/github-insights-cards.js
```

Manual resource registration is deliberate: Home Assistant does not document a
stable public API for integrations to mutate Lovelace resources. The static
path is isolated in `custom_components/github_insights/__init__.py` and tested.
If that supported API changes, the fallback is to copy the same bundled asset
to `www/` and update the resource URL; no second HACS repository is needed.
Until registration is completed through a supported Lovelace resource
mechanism, keep the deployable release-candidate dashboard on its dynamic
Mushroom, ApexCharts, Auto Entities, and native fallback. Reintroduce its full
`custom:github-insights-*` views only after a supported Home Assistant restart
or config-entry reload exposes the current entity set and the module
registration is configured or recorded as release evidence.

## Safe deployment procedure

1. Validate backend, frontend, HACS, Hassfest, artifact content, and secrets.
2. Build a clean staging directory from tracked release inputs.
3. Verify the deployment manifest has only GitHub Insights paths.
4. Read-only compare with
   `\\192.168.1.4\config\custom_components\github_insights`.
5. If present, back up only that directory and its registered resource record.
6. Copy the staged `github_insights` directory.
7. Register the frontend resource only through the selected supported method.
8. Run a supported Home Assistant configuration check.
9. Restart only when required and after approval/validation.
10. Confirm Home Assistant health, integration load, devices, entities,
    availability, resource load, and absence of unrelated changes.
11. On failure, restore only the backed-up GitHub Insights files/resource.

Do not copy tests, fixtures, TypeScript source, node modules, source maps,
coverage output, tokens, or local diagnostics.

## MCP-assisted validation plan

When the configured proxy becomes available, use read-only operations to obtain
the Home Assistant version/system overview, find the integration's config entry,
list devices/entities belonging to `github_insights`, inspect availability, and
confirm health after an approved restart. Do not expose the endpoint in normal
product configuration and do not operate unrelated entities or automations.
