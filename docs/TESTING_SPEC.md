# Testing and verification policy

Kind: Policy. It applies as written; changing it needs an owner decision. Gate applicability by tier is set in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md). Status vocabulary is defined in [DOCUMENTATION.md](DOCUMENTATION.md).

## Workflow and matrix
This section is the home of the gap, first-failure and no-weakening rules.

1. **Map before changing.** Know which requirements and regressions the change affects and which tests, commands and gates prove them. Where the project keeps [VERIFICATION_MATRIX.md](VERIFICATION_MATRIX.md) (Production service and Enterprise), record that mapping there and update its rows in place; otherwise the tests and the `Verification:` line are the record. Release work covers the tier's full required inventory. Other work runs the [development gates](#development-and-release-gates).
2. **Missing tooling is a gap.** Missing tests or harnesses are implementation work or explicit blockers, never exclusions. Unavailable tools, insufficient duration and absent telemetry are not successful checks. A running check is in progress, not passed.
3. **Write the smallest meaningful regressions.** Inspect existing tests and reuse their conventions. Make each regression fail before the fix where practical. Run focused checks, then the broader gates.
4. **Keep failures honest.** Preserve the first failure and its diagnostics. Never weaken assertions, lower thresholds, remove required coverage or hide errors to get a green result.

## Development and release gates
This section is the home of the phase rule that AGENTS.md rule 15 summarizes. The tier table in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md) lists what a **release** needs. Work before a release runs a smaller, fixed set, so a small fix does not carry release ceremony.

| Phase | Required checks |
|---|---|
| Each change | Tests for the changed behavior, then the full unit and integration suite. Build, format, lint and static checks. Authentication and authorization tests when those paths change. For UI changes: a browser smoke run on one engine and viewport, and an automated accessibility scan of the changed screens. For schema changes: an upgrade test on isolated synthetic data |
| Review deployment | Everything above that can run, built from a committed revision. A coherent backup before any migration, and a check of the critical journeys after the deployment |
| Release | The tier's full required inventory, through the [release readiness procedure](procedures/release-readiness.md) |

`python3 check_package.py --verify` runs the command-inventory rows whose Gate is Development and prints the computed status; `--verify release` adds the Release rows; `--verify documentation` runs only the Documentation rows, for a change to documentation alone, and fails if the work changes any other file except the guidance records `PACKAGE_MANIFEST.json` and `docs/guidance-provenance.json`; and `--receipt FILE` saves the results as JSON evidence. A gate with no command is a gap, and so is a "Proposed: Not applicable: <reason>" exclusion the owner has not confirmed; "Not applicable: <reason>" records an owner-approved exclusion. For a schema change, also run the migration gate, which is a Release row.

The full browser matrix, manual accessibility and device checks, performance, soak, the aggregate verifier and restore drills run at release. Run one earlier only when the change targets it, such as a fix for a theme contrast defect. The gap and honesty rules above still apply in every phase: a check the phase requires but cannot run is a gap, not a pass. A gap the command inventory already shows is the project's known state: the `Verification:` line reports it, and a routine change adds no OPEN_WORK entry for it. Record in OPEN_WORK what the change itself leaves open, including new behavior that a missing gate cannot verify.

**Gaps do not block a review deployment the owner asked for.** If a required check cannot run because its tooling is missing, such as no browser harness yet, deploy anyway. Name the gap in the report and in OPEN_WORK, so the owner reviews knowing it is unverified. A check that ran and **failed** still blocks the deployment. At release, every gap must be closed or accepted as an exception by the owner.

## Isolation and test-path validity
Use:
- independent synthetic fixtures,
- the real selected persistence, migrations and settings for storage boundaries,
- managed resources,
- deterministic clocks and IDs where needed.

Bound concurrency, and synchronize on observable conditions rather than arbitrary sleeps. Mock external services in ordinary tests; dedicated isolated contract tests exercise adapter and network defenses. Never use production data for destructive tests.

Assert real consequences:
- persisted records and relationships,
- permission denial with no effects,
- atomicity, retry and deduplication,
- conflict handling, committed acknowledgments and recovery.

Test the actual shared operational paths, not substitute mock scripts that bypass the implementation. Coverage percentages, command names and pass counts do not prove the intended path was covered.

## Unit, integration and concurrency
- **Domain tests** exercise valid, invalid and boundary values; unknown versus zero; precision and overflow; identifier normalization; and lifecycle rules.
- **Persistence tests** verify constraints, transaction rollback and atomicity, concurrent updates, last-resource contention where relevant, lost responses, scoped idempotency, stale writes, bounded busy handling, deletion and history, and schema compatibility.
- **Interruption tests** use controlled, disposable subprocess interruption to check acknowledged versus uncommitted effects. This does not prove durability through physical power loss.

## Interface, UI and semantics
Test authentication, authorization, applicable request-forgery defenses, validation, status codes, redirects and expired sessions.

UI and workflow changes need real browser or client checks against the served application, across the adopted engine, viewport and theme matrix, plus the tier's manual evidence. Verify:
- the initial and the dynamically updated interface,
- native semantics, label relationships and valid nesting,
- keyboard and focus behavior, error states and responsive overflow,
- stale responses,
- any fallback the adopted stack profile requires.

Assert persisted outcomes, not only a toast. Automated accessibility scans do not replace assistive-technology and device checks.

## Security, migrations and operations
Test:
- secret redaction,
- input, upload and archive bounds, parser abuse and resource limits,
- the actual adapter defenses.

Migrations need evidence of isolated upgrade, idempotence and compatibility, and failure recovery. For operational code, exercise ownership and write denial, failures during stop, backup, migration and readiness, protected rollback stages, singleton identity, bounded retries, unavailable storage and cleanup safeguards. Syntax inspection alone cannot pass a behavior gate.

## Recovery
Test coherent archives of the actual implementation with real relationships, assets and configuration. Verify local integrity, off-host receipt and decryption, and isolated restore separately. Repository tests do not prove deployed schedules, alert delivery, transport configuration or recovery on the selected host.

## Performance, soak and aggregate verification
PROJECT_PROFILE.md owns the adopted budgets and qualification protocol; never inherit arbitrary values. Where the tier requires them, follow the full protocols in [profiles/PRODUCTION_OPERATIONS.md](../profiles/PRODUCTION_OPERATIONS.md). A short diagnostic cannot pass a longer gate, and wrong routes, login redirects or error responses never count as successful load.

## Evidence reuse and CI
Reuse unaffected evidence only with a recorded rationale for the candidate and environment, and the adopted requalification triggers. Relevant runtime, dependency, storage, interface, operational or workload changes may need new target evidence. Small unrelated changes do not need to repeat equivalent long runs.

CI builds pinned code and assets and runs the appropriate checks, without exposing operational secrets to untrusted contributions. Retain raw results under the adopted policy. Documentation-only scope uses a document and reference review, with no unrelated application-test claims.
