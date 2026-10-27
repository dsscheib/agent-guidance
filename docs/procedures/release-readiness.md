---
name: release-readiness
description: Assemble and evaluate the evidence for a release candidate against the project tier's required gates, and fill in the release readiness record. Use when preparing a release, asked whether a candidate can ship, or asked to qualify a build. It never grants release acceptance or deploys; only the owner does.
---
# Release readiness procedure

Kind: Procedure. Records go in [PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md); gate definitions are in [TESTING_SPEC.md](../TESTING_SPEC.md); production-tier qualification is in [profiles/PRODUCTION_OPERATIONS.md](../../profiles/PRODUCTION_OPERATIONS.md).

## 1. Identify the candidate
Record the commit, the source and artifact identities, the dirty state, the build configuration, and the target environment. Evidence produced by a different candidate does not count unless TESTING_SPEC's reuse rule applies, and the reuse rationale is recorded.

## 2. Build the full gate inventory
Start from the tier column in [PROJECT_PROFILE.md](../../PROJECT_PROFILE.md) and the adopted gates in [VERIFICATION_MATRIX.md](../VERIFICATION_MATRIX.md). Every required gate appears exactly once. Exclusions need a recorded owner decision, and missing tooling is a gap, not an exclusion.

## 3. Collect evidence
- Run each automated gate with the commands from the command inventory. Keep the raw output, exit codes, dates and environment.
- Keep manual checks, target-host qualification and authorization separate from local results. A running or partial check is "in progress", not passed.
- For the Production service tier, run the qualification protocol and the aggregate verifier from the production operations profile.

## 4. Fill in the readiness record
For each gate, record the requirement, procedure, result, current evidence and work ID. Then fill in the implementation completion and verification completion lines. Leave "Release acceptance: Not granted" unless the owner has recorded an acceptance decision for this candidate and environment.

## 5. Report
Report the gate table, blockers with their OPEN_WORK IDs, accepted exceptions with their expiry, and a recommendation. Acceptance does not authorize deployment. Deployment needs its own explicit authorization (AGENTS.md rule 3).
