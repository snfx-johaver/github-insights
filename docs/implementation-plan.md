# Implementation plan

Phase 0 and Phase 1 are complete when this documentation and scaffold validate.
No Phase 2 production behavior belongs in the initial bootstrap.

## Global acceptance invariant

Every phase preserves one repository, one `github_insights` integration, one
config entry/auth/client model, one bundled frontend, one version, one zip
artifact, and one release lifecycle. A separate HACS frontend/plugin package is
out of scope and must be rejected in review.

## Phase 2: core integration

- Set manifest `config_flow: true` and `single_config_entry: true`.
- Implement PAT authentication abstraction for GitHub.com and one configured
  GitHub Enterprise Server.
- Prefer fine-grained PATs where every selected endpoint supports them; explain
  their single-resource-owner constraint and fall back to classic PATs only
  where official endpoint support requires it. Keep a GitHub App/OAuth adapter
  boundary for future work.
- Validate identity, organizations, repositories, permissions, API version, and
  capability categories without making writes.
- Implement typed runtime data, API transport, central coordinators, account and
  rate-limit entities, migrations, options, reauthentication, diagnostics,
  repairs, translations, devices, and entity descriptions.
- Test config/options/reauth/migrations, host validation, redaction, pagination,
  ETags, primary/secondary rate limits, partial failures, and last-known-good
  state.

Recommended Phase 2 scope is deliberately limited to the account device,
identity/rate-limit entities, safe repository discovery metadata, coordinator
infrastructure, and complete tests. Do not add budgets, detailed repository
entities, or cards until their later phases.

## Phase 3: Actions, billing, and budgets

- Implement authoritative enhanced-billing and budget adapters by detected
  scope.
- Keep runtime, included quantity, billed quantity, gross/discount/net cost,
  storage, budget, enforcement, and estimates distinct.
- Add read-only entities first.
- Add opt-in write controls with confirmation and authoritative read-back.
- Add runner/SKU-based estimated equivalent minutes with source-date metadata.
- Do not use closing workflow timing endpoints as a billing source or invent
  per-workflow costs when enhanced billing only attributes to repository/SKU.
- Test every budget mutation, permission failure, currency, exhaustion,
  enforcement transition, and idempotency boundary.

## Phase 4: repositories and workflows

Implement selected/auto-discovered repository devices, summaries, issues, pull
requests, releases, workflows/jobs/deployments, traffic, and authorized
security categories. Enforce repository caps and disabled-by-default details.

## Phase 5: Copilot and AI

Implement billing reports separately from organization/enterprise usage reports.
Download signed report links only in memory; sanitize and discard URLs.
Mark the newest three UTC days provisional where GitHub telemetry finalization
guidance applies.

## Phase 6: frontend foundation

Create the shared Lit system, metric registry, repository discovery adapter,
selector/filter/group/sort pipeline, visual-editor components, overview, usage,
and compact cards. Build directly to the bundled integration staging path.

## Phase 7: remaining cards

Add repository, Actions, Copilot, activity, contributions, security, and
dashboard cards using the shared components and model.

## Phase 8: product completion

Complete all visual editors, accessibility, examples, documentation,
translations, release packaging, HACS metadata, and clean installation tests.

## Phase 9: local deployment

Only after automated validation:

1. stage the exact artifact;
2. read-only compare with any existing installation;
3. back up only GitHub Insights files;
4. install the one integration directory and bundled frontend;
5. validate configuration through a supported mechanism;
6. restart only if required and explicitly safe;
7. verify health/entities/cards with supported read-only tooling;
8. roll back only GitHub Insights files on failure.

## Phase 10: release and HACS

Build from an immutable tag, validate tag/source/version/artifact identity,
publish a prerelease or stable release as appropriate, verify HACS custom
installation, then submit to `hacs/default` only after every external
requirement is satisfied.

## Entity budget

Initial target:

- 24 default-enabled account/category entities;
- 6 default-enabled entities per explicitly selected repository;
- 16 account/category detail or diagnostic entities disabled by default;
- up to 10 detailed entities per selected repository disabled by default; and
- 6 conditional write entities when budget management is enabled.

Automatic discovery defaults to at most 25 repository devices and requires
explicit expansion for more, preventing thousands of enabled entities.
