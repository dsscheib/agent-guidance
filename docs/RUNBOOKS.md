# Operator runbook templates

Status: Unconfigured procedures. Replace placeholders with inspected commands and role/path checks, rehearse in isolated staging and record evidence before operational use. These procedures do not authorize deployment or production access.

## R1 — Install and start
Verify owner authorization, supported platform, approved artifact/source identity and checksum, effective runtime identity, mount/volume readiness, ancestor ownership/permissions and configuration. Stage immutable files and private writable data under declared paths. Start exactly one supervised process; verify readiness, authentication and a critical read/write on disposable data. Record version/environment and diagnostics. No fallback empty production store.

## R2 — Coherent backup
Acquire job/maintenance coordination. Verify destination identity/capacity. Quiesce relevant writes/asset cleanup or use a qualified coherent capture mechanism. Create a unique incomplete set; capture database, matching assets/configuration/version and manifest/checksums. Validate before publishing success. Record local versus off-host receipt separately. Preserve previous known-good sets on failure; prune only under the adopted verified-retention policy.

## R3 — Upgrade and compatible rollback
Qualify candidate and pre-change recovery; authorize target operation. Enter maintenance, pause jobs, drain/stop, capture protected pre-migration state, rehearse/migrate explicitly and switch the release atomically where supported. Start one process and verify real behavior. On failure preserve diagnostics, stop before restoration and keep maintenance active. Use binary rollback only when schema compatibility is proved; otherwise restore the coherent pre-change set. Verify restored compatibility/readiness before resuming. Report lost writes and measured downtime.

## R4 — Runtime failure
Confirm exact process/executable/start identity, storage and configuration before action. Use bounded recovery under adopted policy; do not kill by name or stale PID alone. Preserve evidence and alert on deterministic failures, restart limits or unavailable storage.

## R5 — Isolated restore drill
Authorize disposable target and identify the actual archive. Verify off-host retrieval/decryption, integrity/checksums, schema/release support, relationships/assets and critical behavior. Revoke restored sessions as applicable. Measure actual recovery objectives; preserve failures. Do not overwrite production to manufacture a drill.

## R6 — Security or credential incident
Contain the affected boundary under authorized scope, preserve evidence, rotate/revoke affected secrets/sessions and assess exposure. Verify corrective controls and restoration before reopening. Record incident decision authority; send messages only when authorized.

## R7 — Qualification staging
Use SOAK_QUALIFICATION_COLLECTOR.md for selected-host performance/soak work. Validate marker/path/data/executable identity, permissions and no production overlap. Preserve prior runs and fail early on missing telemetry or invalid authentication. Graceful stop retains incomplete evidence; cleanup is a separately scoped operation with identity checks.

## Command and evidence record
{{ACTUAL_COMMANDS_REQUIRED_ROLES_PATHS_EXPECTED_RESULTS_AND_RECOVERY_ACTIONS}}
Link current operational results in PRODUCTION_READINESS.md and unresolved issues in OPEN_WORK.md. A successful shell syntax check is not native operational qualification.
