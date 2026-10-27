# Verification review template

Candidate/scope/reviewer/date: {{REVIEW_CONTEXT}}
Kind: Template. Status: Unconfigured; no closure claims.

| Requirement / prior claim | Intended behavior | Inspected path | Positive / negative evidence | Disposition / work ID |
|---|---|---|---|---|
| {{REQUIREMENT_OR_CLAIM}} | {{REQUIRED_OUTCOME}} | {{ACTUAL_PATH}} | Not verified | {{WORK_ID}} |

Audit source/artifact identity, complete expected-gate inventory, manual/target provenance, real persisted effects and honest incomplete/failing exits. For production-tier verifiers also apply the checks in [profiles/PRODUCTION_OPERATIONS.md](../profiles/PRODUCTION_OPERATIONS.md). Operational tests must execute the shared implementation and prove effective permission/rollback state, not manufacture it with fixture postprocessing.

{{FIRST_FAILURES_FIXES_COMMANDS_RESULTS_AND_LIMITATIONS}}
Preserve historical misleading claims with a clear superseded label; keep current status in OPEN_WORK.md. Reporting and approval rules: [DOCUMENTATION.md](DOCUMENTATION.md).
