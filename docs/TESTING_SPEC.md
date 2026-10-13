# Testing and verification policy

## Workflow and matrix
Before behavior changes, map affected requirements and regressions to actual tests, commands, environments, evidence and gate dispositions. Release work covers the full adopted required inventory; focused work explains exclusions. Missing tests/harnesses are implementation work or explicit blockers. Unsupported/unavailable tools, insufficient duration or absent telemetry are not successful checks.

Inspect existing tests and reuse conventions. Add the smallest meaningful regressions with failure-before-fix when practical. Run focused checks, then appropriate broader gates. Preserve the first failure and diagnostics; do not weaken assertions, remove required coverage or hide errors to obtain green results.

## Isolation and test-path validity
Use independent synthetic fixtures, real selected persistence/migrations/settings for storage boundaries, managed resources and deterministic clocks/IDs where needed. Bound concurrency and synchronize with observable conditions rather than arbitrary sleeps. Mock external services for ordinary tests; dedicated isolated contract tests exercise adapter/network defenses. Never use production data for destructive tests.

Assert real consequences: persisted records and relationships, permission denial with no effects, atomicity, retry/deduplication, conflict handling, committed acknowledgments and recovery. Test actual shared operational paths, not substitute mock scripts that bypass the implementation. Coverage percentages, command names and pass counts do not prove intended-path coverage.

## Unit, integration and concurrency
Exercise domain valid/invalid/boundary values, unknown versus zero, precision/overflow, identifier normalization and lifecycle rules. Persistence tests verify constraints, transaction rollback/atomicity, concurrent updates, last-resource contention where relevant, lost responses, scoped idempotency, stale writes, bounded busy handling, deletion/history and schema compatibility. Use controlled disposable subprocess interruption to check acknowledged versus uncommitted effects; it does not prove physical power-loss durability.

## Transport, browser and semantics
Test authentication, authorization, applicable request-forgery defenses, validation/status/fallback contracts, redirects and expired sessions. UI/workflow changes require real served-application browser checks across the adopted engine/viewport/theme matrix and appropriate manual evidence. Verify initial and dynamically replaced DOM, native semantics, label relationships, valid nesting, keyboard/focus, errors, responsive overflow, stale responses and direct/no-script fallback where applicable. Assert persisted outcomes, not only a toast. Automated accessibility scans do not replace assistive-technology/device checks.

## Security, migrations and operations
Test secrets redaction, input/upload/archive bounds, parser abuse, resource limits and actual adapter defenses. Migrations need isolated upgrade, idempotence/compatibility and failure recovery evidence. Exercise actual ownership/write denial, stop/backup/migration/readiness failures, protected rollback stages, singleton identity, bounded retries, unavailable storage and cleanup safeguards. Syntax inspection alone cannot pass behavior gates.

## Recovery
Test coherent implemented archives with real relationships/assets/configuration. Verify local integrity, off-host receipt/decryption and isolated restore separately. Confirm session revocation and measured recovery objectives where required. Repository tests do not prove deployed schedules, alert delivery, transport configuration or selected-host recovery.

## Performance and soak
PROJECT_PROFILE.md owns the adopted dataset, user/client concurrency, workload mix, warm-up, measured performance window, complete soak duration, minimum samples, throughput and capacity budgets. Populate them before acceptance; do not inherit arbitrary values. Initial release qualification includes applicable complete performance/soak protocols unless explicitly justified as inapplicable. A short diagnostic cannot pass a longer gate.

Use real served workflows and independent authenticated role-valid sessions. Preflight reads/writes and verify successful persisted effects. Wrong routes, login redirects, bad tokens and unexpected error responses cannot count as successful load. Separate expected negative/fault scenarios from uninterrupted workload. Consume response bodies before client timing; separate actual server timings from network/render/client timings. Retain per-operation counts/errors/distributions, achieved throughput and raw traces.

Collect baseline, bounded-interval and final process/host/storage/job telemetry with actual process/executable/start identity, restart detection and declared measurement methods. Missing measurements make the run incomplete, not zero. Estimates require an explicitly adopted method, retained inputs and clear labels. Record representative background jobs, backup interaction and session renewal. Reconcile initial state plus acknowledged operations against final persistent invariants, integrity, relationships and audit data.

Review time-series resource growth, not endpoints alone. Define investigation thresholds and capacity budgets before the run. Unresolved growth, interruption, restart, insufficient samples/rate, missing telemetry, failed effects or breached budgets prevent qualification. Test the harness against each known bad outcome. Retain failed/incomplete reports and return non-success; failed report persistence also fails.

## Aggregate release verifier
Use a complete expected-gate inventory from adopted requirements, not only supplied results. Record candidate commit plus actual source/artifact identity, dirty state, build configuration, commands/status/exit codes, environment, dates and raw evidence paths/hashes/sizes. Identify synthetic test mode explicitly as release-ineligible. Compare actual binary identity and source attestation, not a label from an unrelated checkout.

Reject missing/duplicate gates, malformed/wrong-candidate/stale/tampered evidence, unsupported exclusions and contradictory eligibility. Validate the same qualification contract in direct checks, evidence intake and manifest validation. Pending/manual/blocked/failed required gates remain visible and prevent an aggregate pass. Test child failures, missing artifacts, false pass markers, synthetic eligibility and honest non-success results. The verifier never deploys as a side effect. JSON consistency cannot establish owner consent or perform a manual check.

## Evidence reuse, CI and delivery
Reuse unaffected evidence only with the candidate/environment applicability rationale and adopted requalification triggers. Relevant runtime, dependency, storage, interface, operational or workload changes may require new target evidence; small unrelated changes need not repeat equivalent long runs. CI builds pinned code/assets and runs appropriate checks without exposing operational secrets to untrusted contributions.

Retain raw results under the adopted policy. Report implementation, verification and release acceptance independently with the final audit, matrix, actual commands/results, first failures, exclusions, manual/target gaps and OPEN_WORK.md references. Documentation-only scope uses document/reference review; no unrelated application-test claims.
