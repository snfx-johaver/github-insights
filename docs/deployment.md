# Deployment

## Phase 1 status

No deployment was attempted. The repository contains only an architecture
scaffold and release guards. Home Assistant must not receive version `0.0.0`.

The configured share `\\192.168.1.4\config` was inaccessible from this
workspace on 2026-09-18. TCP connection to `192.168.1.5:10513` failed, and the
coordinating session's safe HTTP probe timed out. The named Home Assistant MCP
proxy was not available as a configured tool in this session. No files were
read or modified and Home Assistant was not restarted.

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

Phase 6 must select a supported Home Assistant resource-registration path and
validate the final URL. Preferred order:

1. integration-served static URL registered through supported Home Assistant
   APIs; or
2. documented manual Lovelace module resource pointing to the bundle inside the
   installed integration.

No undocumented frontend internals may be used without a small isolated adapter
and documented compatibility risk.

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

