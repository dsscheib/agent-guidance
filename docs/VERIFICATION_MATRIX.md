# Requirement and gate verification matrix

Scope/profile/candidate: {{VERIFICATION_SCOPE}}

Set default gate applicability from [Tier gate expectations](procedures/release-readiness.md#tier-gate-expectations) for the tier recorded in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md); record each deviation with owner approval. Keep one row per requirement updated in place with the latest evidence (never append a row per run). Link bulky artifacts outside git.

| Requirement / scenario | Intended path and failure case | Coverage / actual command | Environment | Applicability | Result / evidence | Work ID |
|---|---|---|---|---|---|---|
| {{REQUIREMENT_ID}} | {{OBSERVABLE_OUTCOME_AND_NEGATIVE_CONTROL}} | {{ACTUAL_TEST_OR_MISSING_COVERAGE}} | {{ENVIRONMENT}} | Required / justified exclusion | Not verified | {{WORK_ID}} |

## Required-gate inventory
{{EXACT_UNIQUE_GATE_IDS_AND_ADOPTED_REQUIREMENT_REFERENCES}}

## Evidence summary
{{CANDIDATE_ARTIFACTS_ENVIRONMENT_DATES_OPERATORS_COMMANDS_RAW_RESULTS_AND_REUSE_RATIONALE}}

Keep unresolved blockers and gaps in [docs/OPEN_WORK.md](OPEN_WORK.md).
