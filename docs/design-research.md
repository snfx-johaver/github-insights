# Design research

## Research scope

Phase 1 reviewed two authorized Home Assistant GitHub card implementations,
current Home Assistant custom-card/config-entry/coordinator guidance, and
official GitHub billing, budget, Copilot, repository, workflow, security, and
rate-limit documentation.

Reference implementation names are intentionally absent from product naming,
labels, examples, and marketing. No source file was copied.

## Patterns retained

- Zero-configuration repository discovery, with explicit include, exclude, and
  per-repository overrides.
- Compact, high-signal repository KPIs with progressive disclosure into detail.
- Stable ordered multi-key sorting with typed comparisons and explicit null
  placement.
- One semantic metric model shared by compact and expanded modes.
- Card-level defaults cascading into immutable normalized per-repository config.
- Reusable card shell, row/detail components, editors, and visualizations.
- Metric-specific navigation to safe GitHub pages.
- Home Assistant theme tokens and localized relative-time presentation.
- Visual editor multi-selects, card-picker metadata, and stub configs.

## Problems explicitly avoided

- Identity based on entity IDs, editable device names, or icon/name substrings.
- A missing repository causing the complete card to disappear.
- Polling GitHub from the browser or duplicating backend data logic.
- In-place mutation that bypasses Lit reactivity.
- Numeric-only sorting of mixed string/date/number/unknown values.
- Hand-written template interpolation over untrusted values.
- Direct `window.open` calls and mouse-only clickable containers.
- Hard-coded `github.com` links that break GitHub Enterprise Server.
- Obsolete Polymer controls, Paper tokens, brittle fixed layouts, or source maps
  in the install payload.
- Silent handling of invalid card configuration or unavailable entities.
- Release assets built from source that differs from the tag or declared
  version.

## Repository discovery design

Cards obtain the integration's config entry, devices, and entities through
supported Home Assistant registry/context mechanisms. Repository identity uses
backend-provided GitHub numeric IDs and normalized owner/name metadata.
Registry changes trigger rediscovery; no permanent browser cache is trusted.

The pipeline is:

1. discover entities belonging to `github_insights`;
2. group by config entry and repository device identifier;
3. apply capability and availability states;
4. normalize concise/detailed YAML;
5. apply include/exclude/search filters;
6. group and stable-sort by typed metric descriptors;
7. render visible rows/cards with explicit loading, empty, stale, partial, and
   error states.

## Accessibility and visual language

The product complements Mushroom-style dashboards without depending on
Mushroom. It uses current Home Assistant theme variables, soft radii, restrained
tonal surfaces, clear value hierarchy, and responsive 12-column section sizing.

Interactions use semantic links/buttons, visible focus, keyboard activation,
screen-reader labels, minimum touch targets, reduced-motion media queries, and
non-color status indicators. SVG charts include accessible summaries and avoid
misleading mixed-unit scales.

## Release integrity lesson

Release automation must build from the exact immutable tag, verify that
manifest/frontend/tag versions match, create one deterministic archive, publish
a checksum and provenance/attestation where supported, and install-test that
archive. Locally rebuilt or manually substituted assets are not acceptable.

