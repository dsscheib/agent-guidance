# Release readiness record

Candidate/source/artifacts: {{CANDIDATE_IDENTITIES}}
Environment/profile: {{TARGET_ENVIRONMENT}}
Reviewer/operator/date: {{REVIEW_RECORD}}

Fill in with [release-readiness](procedures/release-readiness.md). Keep local-suite runs, target-host qualification, manual checks, and authorization distinct.

| Required gate | Requirement / procedure | Result | Current evidence | Work ID |
|---|---|---|---|---|
| Domain / persistence / security | {{GATE_REFERENCE}} | Not verified | None | {{WORK_ID}} |
| Static / concurrency / build | {{GATE_REFERENCE}} | Not verified | None | {{WORK_ID}} |
| Browser / semantics / accessibility | {{GATE_OR_JUSTIFIED_EXCLUSION}} | Not verified | None | {{WORK_ID}} |
| Performance / complete soak | {{QUALIFICATION_PROTOCOL}} | Not verified | None | {{WORK_ID}} |
| Migration / coherent recovery | {{GATE_REFERENCE}} | Not verified | None | {{WORK_ID}} |
| Native runtime / permissions / alerts | {{GATE_REFERENCE}} | Not verified | None | {{WORK_ID}} |
| Operational authorization | {{ACTUAL_OWNER_SCOPE_REFERENCE}} | Not verified | None | {{WORK_ID}} |

## Qualification and aggregate-verifier rules
- Qualify the actual served binary and committed revision on isolated target-architecture staging, with dedicated non-admin permissions and immutable release/config paths.
- Use real authenticated workflows (wrong routes, redirects, and error responses never count as load), review time-series resource growth across warm-up, measured window, and uninterrupted soak, and independently reconcile final persisted state.
- Reject missing/duplicate gates, synthetic test mode, wrong-candidate/stale/tampered evidence, or missing telemetry (never treat missing data as zero or passed).

Implementation completion: Not evaluated.
Verification completion: Not evaluated.
Release acceptance: Not granted.

{{FINAL_AUDIT_SUPPORTED_EXCEPTIONS_REMAINING_BLOCKERS_AND_ACCEPTANCE_DECISION}}

Update gate mapping in [docs/VERIFICATION_MATRIX.md](VERIFICATION_MATRIX.md). Acceptance does not authorize deployment.
