# Release process

No release or tag is created by the Phase 6-8 frontend branch.

## Version and artifact invariant

The Git tag `vX.Y.Z`, integration manifest version, frontend package version,
archive contents, checksum, and release title must all identify `X.Y.Z`.
Artifacts are built in CI from the exact immutable tag. Manual replacement of a
release asset is prohibited; corrections require a new semantic version.

Backend and all cards always ship together in `github_insights.zip`. There is no
frontend release, npm publication, plugin artifact, or second HACS lifecycle.

## CI release flow

1. Run backend lint, formatting, typing, tests, Hassfest, and HACS Action.
2. Run frontend lint, typing, tests, accessibility/snapshots, and production
   build without source maps.
3. Verify repository/manifest/frontend/tag versions.
4. Require a committed frontend lockfile and install exactly with `npm ci`.
5. Copy only runtime integration files and the compiled card bundle into a
   clean staging directory.
6. Generate `deployment-manifest.json` with paths and SHA-256 hashes.
7. Create deterministic `github_insights.zip` with normalized ZIP timestamps,
   sorted paths, fixed permissions, and a hashed `deployment-manifest.json`.
8. Inspect archive paths and reject tests, fixtures, source, node modules,
   secrets, maps, or extra top-level integrations.
9. Install-test the archive in an isolated Home Assistant environment.
10. Scan source, history, and artifact for secrets.
11. Publish SHA-256 checksum and build provenance/attestation where supported.
12. Create a full GitHub Release and attach the artifact.
13. Verify the release page and HACS custom-repository installation.

`check_release_readiness.py` requires a version-matched `release-ready.json`
confirming successful HACS validation, Hassfest validation, and a clean HACS
custom-repository installation test. The marker is intentionally absent while
backend/product validation is incomplete. A tag must exactly match the
manifest/frontend version. `validate_release_artifact.py` independently rejects
extra roots, development files, missing bundles, and hash mismatches.

Before creating that marker, retain links to successful non-ignored HACS Action
and Hassfest runs. Only then create a full GitHub Release; a tag alone is not a
release and is insufficient for HACS catalog submission.

## Versioning

- `0.0.0`: unreleased architecture scaffold.
- `0.x.y`: functional prereleases while APIs/cards/deployment are incomplete.
- `1.0.0`: only after complete functionality, upgrade/removal tests, local
  validation, and stable documentation.

## Rollback

Retain the previous verified zip and deployment manifest. Restore only the
`custom_components/github_insights` directory and its GitHub Insights resource
registration. Never roll back unrelated Home Assistant files or dashboards.
