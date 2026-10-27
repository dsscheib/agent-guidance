# Requirement and gate verification matrix

Scope/profile/candidate: {{VERIFICATION_SCOPE}}
Kind: Register. Status: Unconfigured. Set default gate applicability from the project tier in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md); record each deviation with the owner decision.

| Requirement / scenario | Intended path and failure case | Coverage / actual command | Environment | Applicability | Result / raw evidence | Work ID |
|---|---|---|---|---|---|---|
| {{REQUIREMENT_ID}} | {{OBSERVABLE_OUTCOME_AND_NEGATIVE_CONTROL}} | {{ACTUAL_TEST_OR_MISSING_COVERAGE}} | {{ENVIRONMENT}} | Required / justified exclusion | Not verified | {{WORK_ID}} |

## Required-gate inventory
{{EXACT_UNIQUE_GATE_IDS_AND_ADOPTED_REQUIREMENT_REFERENCES}}
Map unit/integration, security, static/concurrency/build, browser/manual accessibility, harness validity, performance/soak, migration/recovery and selected-host/operational families as the tier requires. Manual and long checks remain explicit until completed. Gap and in-progress rules: [TESTING_SPEC.md](TESTING_SPEC.md).

## Evidence and final audit
{{CANDIDATE_ARTIFACTS_ENVIRONMENT_DATES_OPERATORS_COMMANDS_RAW_RESULTS_AND_REUSE_RATIONALE}}
Use the status vocabulary in [DOCUMENTATION.md](DOCUMENTATION.md) and the [final audit procedure](procedures/final-audit.md). Keep unresolved status in OPEN_WORK.md rather than duplicating a second backlog. This map does not replace authoritative requirements.

