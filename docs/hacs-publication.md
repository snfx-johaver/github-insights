# HACS publication

## Current status

The repository is public and prepared structurally, but version `0.0.0` is not
functional, `hide_default_branch` is enabled, no release exists, and no HACS
catalog claim is made.

## Repository requirements

- Public GitHub repository with description, topics, issues, README, and
  supported license.
- Exactly one directory under `custom_components`: `github_insights`.
- Valid custom integration manifest with domain, name, code owner,
  documentation, issue tracker, and semantic version.
- Brand directory with at least `icon.png`.
- HACS Action and Hassfest passing without ignored failures before catalog
  submission.

## `hacs.json` design

```json
{
  "name": "GitHub Insights",
  "zip_release": true,
  "filename": "github_insights.zip",
  "hide_default_branch": true
}
```

`zip_release` supports the single-install invariant. `hide_default_branch`
prevents users from installing the nonfunctional architecture scaffold. It
remains appropriate after releases because installation should use validated
immutable artifacts.

## Release artifact

`github_insights.zip` contains one installable `github_insights` integration
directory with backend, translations, brand/runtime assets, and the single
source-map-free card bundle. It excludes development files. One artifact,
version, checksum, and release serve both backend and cards.

HACS normally treats integrations and dashboard plugins as different
categories. GitHub Insights deliberately chooses the less conventional bundled
integration path to satisfy the one-install requirement. Release is blocked
unless Phase 6 proves a supported Home Assistant resource-serving and
registration method; a second Dashboard/plugin repository is not an allowed
fallback.

## Custom repository process

After a validated release:

1. Add `https://github.com/snfx-johaver/github-insights` in HACS custom
   repositories.
2. Select category **Integration**.
3. Install the released GitHub Insights version.
4. Restart if HACS/Home Assistant requires it.
5. Configure the integration and register the bundled resource through the
   documented supported method.

This is Level 1 availability and does not imply standard catalog inclusion.

## Standard catalog submission

After custom installation is proven:

1. Confirm the submitter is owner/major contributor.
2. Confirm current HACS Action and Hassfest pass without ignores.
3. Publish a full release after those checks.
4. Confirm description, topics, issues, brand, README, and artifact.
5. Fork `hacs/default`, branch from its current default branch, and add the
   repository alphabetically to the integration list.
6. Complete the current pull-request template accurately and keep the PR
   editable.
7. Record the PR URL/status only after submission.
8. State that review is pending until HACS maintainers merge it.

External review can take months and cannot be bypassed.

## Branding

Phase 0 includes deterministic placeholder `icon.png` and `dark_icon.png`
assets for validation. Product-ready artwork and any required Home Assistant
Brands submission must be completed before catalog submission.

## Rollback and recovery

HACS users can reinstall the previous release. Release notes identify breaking
changes and config-entry migrations. A failed install restores only the prior
`github_insights` directory/resource and never touches unrelated dashboards.

## Release checklist

- [ ] Functional version is not `0.0.0`
- [ ] Tag, manifest, frontend, archive, and release versions match
- [ ] Backend and frontend validation pass
- [ ] HACS Action and Hassfest pass without ignores
- [ ] Archive content and checksum are verified
- [ ] Secret scans pass
- [ ] Isolated install/upgrade/removal tests pass
- [ ] Safe local validation passes
- [ ] README permissions and limitations match behavior
- [ ] Full GitHub Release exists
- [ ] HACS custom-repository install succeeds
- [ ] Catalog PR is submitted only after all preceding checks

## Sources

- [HACS general publishing requirements](https://www.hacs.xyz/docs/publish/start/)
- [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/)
- [HACS Action](https://www.hacs.xyz/docs/publish/action/)
- [HACS default inclusion](https://www.hacs.xyz/docs/publish/include/)
