---
name: release-readiness
description: Assemble and evaluate the evidence for a release candidate against the project tier's required gates, and fill in the release readiness record. Use when preparing a release, asked whether a candidate can ship, or asked to qualify a build. It never grants release acceptance or deploys; only the user does.
---
# Release readiness procedure

Records go in [docs/PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md).

## 1. Identify the candidate
Record the commit SHA, source and artifact identities, build configuration, and target environment. A dirty working tree is a blocker: commit first and rebuild. Reuse earlier evidence only when the candidate/environment change does not affect that path, and record why.

## 2. Build the full gate inventory
Start from the project's adopted tier and [docs/VERIFICATION_MATRIX.md](../VERIFICATION_MATRIX.md). Every required gate appears once. Exclusions require recorded owner approval; missing tooling is a gap, never an exclusion.

## 3. Collect evidence
1. Run [release-review](release-review.md) on the candidate first unless the user explicitly skips it. Confirmed defects are blockers with [docs/OPEN_WORK.md](../OPEN_WORK.md) IDs; concerns and missing evidence must be resolved or recorded.
2. Run `python3 scripts/verify.py --verify release --receipt <file>` to execute every Development and Release gate in [PROJECT_PROFILE.md](../../PROJECT_PROFILE.md). Run any remaining tier gates and retain raw outputs, exit codes, dates, and environments.
3. Keep local suites, target-host qualification, manual checks, and authorizations distinct. An in-progress or partial check is not passed.

## 4. Update the readiness record and report
Fill in each gate row, the implementation completion line, and the verification completion line in [docs/PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md). Leave `Release acceptance: Not granted.` unless an authorized decision already accepted this candidate and environment.

Report the gate table, blockers with `OPEN_WORK` IDs, accepted exceptions with expiry dates, and a recommendation. Acceptance does not authorize deployment—deployment requires its own explicit approval. After deployment, add one short entry to [docs/RELEASE_NOTES.md](../RELEASE_NOTES.md).
