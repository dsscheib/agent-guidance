# Requirement and gate verification matrix

Scope/profile/candidate: {{VERIFICATION_SCOPE}}
Status: Product verification remains unconfigured. Repository maintenance checks are recorded separately below.

| Requirement / scenario | Intended path and failure case | Coverage / actual command | Environment | Applicability | Result / raw evidence | Work ID |
|---|---|---|---|---|---|---|
| {{REQUIREMENT_ID}} | {{OBSERVABLE_OUTCOME_AND_NEGATIVE_CONTROL}} | {{ACTUAL_TEST_OR_MISSING_COVERAGE}} | {{ENVIRONMENT}} | Required / justified exclusion | Not verified | {{WORK_ID}} |

## Required-gate inventory
{{EXACT_UNIQUE_GATE_IDS_AND_ADOPTED_REQUIREMENT_REFERENCES}}
Map unit/integration, security, static/concurrency/build, browser/manual accessibility, harness validity, performance/soak, migration/recovery and selected-host/operational families as applicable. Manual and long checks remain explicit until completed. A running check is in progress, not a pass. Missing tooling is a gap, not an exclusion.

## Evidence and final audit
{{CANDIDATE_ARTIFACTS_ENVIRONMENT_DATES_OPERATORS_COMMANDS_RAW_RESULTS_AND_REUSE_RATIONALE}}
Use the shared completion/status definitions in DOCUMENTATION.md and final audit in CHANGE_WORKFLOW.md. Keep unresolved status in OPEN_WORK.md rather than duplicating a second backlog. This map does not replace authoritative requirements.

## Repository maintenance verification

| Requirement | Checks | Result | Work ID |
|---|---|---|---|
| Rename the technical design file to `DESIGN_DOC.md` and update all references | Confirm the new path exists, the old path is absent, content is unchanged, no old-name references remain, and `python3 check_package.py` passes | Passed 2026-10-17: path, unchanged-content and old-reference assertions; package checker reports 28 intact files and resolved internal links | DOC-001 |

Application, UI, security, performance and release gates are inapplicable to this documentation-only rename.
