# Testing and verification policy

Kind: Policy. It applies as written; changing it needs an owner decision. Gate applicability by tier is set in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md). Status vocabulary is defined in [DOCUMENTATION.md](DOCUMENTATION.md).

## Workflow and matrix
This section is the home of the gap, first-failure and no-weakening rules.

1. **Map before changing.** Map the affected requirements and regressions to actual tests, commands, environments, evidence and gate dispositions in [VERIFICATION_MATRIX.md](VERIFICATION_MATRIX.md). Release work covers the tier's full required inventory; focused work explains its exclusions.
2. **Missing tooling is a gap.** Missing tests or harnesses are implementation work or explicit blockers, never exclusions. Unavailable tools, insufficient duration and absent telemetry are not successful checks. A running check is in progress, not passed.
3. **Write the smallest meaningful regressions.** Inspect existing tests and reuse their conventions. Make each regression fail before the fix where practical. Run focused checks, then the broader gates.
4. **Keep failures honest.** Preserve the first failure and its diagnostics. Never weaken assertions, lower thresholds, remove required coverage or hide errors to get a green result.

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
