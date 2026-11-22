---
name: release-readiness
description: Assemble and evaluate the evidence for a release candidate against the project tier's required gates, and fill in the release readiness record. Use when preparing a release, asked whether a candidate can ship, or asked to qualify a build. It never grants release acceptance or deploys; only the user does.
---
# Release readiness procedure

Records go in [docs/PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md).

## 1. Identify the candidate
Record the commit SHA, source and artifact identities, build configuration, and target environment. A dirty working tree is a blocker: commit first and rebuild. Reuse earlier evidence only when the candidate/environment change does not affect that path, and record why.

## 2. Build the full gate inventory
Start from the project's adopted tier (see [Tier gate expectations](#tier-gate-expectations)) and [docs/VERIFICATION_MATRIX.md](../VERIFICATION_MATRIX.md). Every required gate appears once. Exclusions require recorded owner approval; missing tooling is a gap, never an exclusion.

## 3. Collect evidence
1. Run [release-review](release-review.md) on the candidate first unless the user explicitly skips it. Confirmed defects are blockers with [docs/OPEN_WORK.md](../OPEN_WORK.md) IDs; concerns and missing evidence must be resolved or recorded.
2. Run `python3 scripts/verify.py --verify release --receipt <outside-repo>/release-receipt.json` (writing the receipt outside the repo—or as a CI artifact—so the working tree stays clean) to execute every Development, Release, and Documentation gate in [PROJECT_PROFILE.md](../../PROJECT_PROFILE.md). Run any remaining tier gates and retain raw outputs, exit codes, dates, and environments.
3. Keep local suites, target-host qualification, manual checks, and authorizations distinct. An in-progress or partial check is not passed.

## 4. Update the readiness record and report
Fill in each gate row, the implementation completion line, and the verification completion line in [docs/PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md). Leave `Release acceptance: Not granted.` unless an authorized decision already accepted this candidate and environment.

Report the gate table, blockers with `OPEN_WORK` IDs, accepted exceptions with expiry dates, and a recommendation. Acceptance does not authorize deployment—deployment requires its own explicit approval. After deployment, add one short entry to [docs/RELEASE_NOTES.md](../RELEASE_NOTES.md).

## Tier gate expectations

Start from the lowest tier in [PROJECT_PROFILE.md](../../PROJECT_PROFILE.md) whose risks match the project:

| Gate | `prototype` (small / personal experiments) | `internal` (trusted users, data that matters) | `production` (external users or uptime commitments) | `enterprise` (roles, traceability, supply chain) |
|---|---|---|---|---|
| Profile + Command inventory | Required | Required | Required | Required |
| Automated tests + static checks | Smoke tests | Unit/integration + static | Full suite + concurrency | Full + CI receipts |
| Recovery / backup drill | Not required | Before relying on persistent data | Release gate (isolated fixtures) | Release gate + retention evidence |
| Pre-release review | Optional (`release-review`) | Optional (`release-review`) | Included (`release-review`) | Included (`release-review`) |
| Readiness + verification matrix | Not required | Not required | Included (`release-readiness`) | Included + named role approval |
| Dependency audit, SBOM, license check | Not required | Report known risks | Report gaps; release gate if tooling exists | Release gate rows added |
