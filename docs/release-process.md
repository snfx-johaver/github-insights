# Release process

No Phase 1 release or tag is permitted.

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
4. Copy only runtime integration files and the compiled card bundle into a
   clean staging directory.
5. Generate `deployment-manifest.json` with paths and SHA-256 hashes.
6. Create deterministic `github_insights.zip`.
7. Inspect archive paths and reject tests, fixtures, source, node modules,
   secrets, maps, or extra top-level integrations.
8. Install-test the archive in an isolated Home Assistant environment.
9. Scan source, history, and artifact for secrets.
10. Publish SHA-256 checksum and build provenance/attestation where supported.
11. Create a full GitHub Release and attach the artifact.
12. Verify the release page and HACS custom-repository installation.

The current workflow runs `check_release_readiness.py`, which intentionally
blocks version `0.0.0`. Later phases must extend artifact validation rather than
remove the safety gate.

## Versioning

- `0.0.0`: unreleased architecture scaffold.
- `0.x.y`: functional prereleases while APIs/cards/deployment are incomplete.
- `1.0.0`: only after complete functionality, upgrade/removal tests, local
  validation, and stable documentation.

## Rollback

Retain the previous verified zip and deployment manifest. Restore only the
`custom_components/github_insights` directory and its GitHub Insights resource
registration. Never roll back unrelated Home Assistant files or dashboards.
