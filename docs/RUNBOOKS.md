# Operator runbook templates

Kind: Template. Applies at the tiers listed in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md): R1–R3 and R5 for Internal, all for Production service and Enterprise product. Status: Unconfigured procedures.

Replace the placeholders with commands you have inspected, plus the roles and paths each step checks. Rehearse each procedure on isolated staging and record the evidence before using it for real. These procedures do not authorize deployment or production access.

**One path per procedure.** Each runbook below is implemented once, by reusable scripts that every release uses. Do not write a new installer, upgrade script or probe for a single release; extend the shared path instead ([CHANGE_WORKFLOW.md](CHANGE_WORKFLOW.md#deployment-and-review-cadence)).

## R1 — Install and start
1. Confirm the owner's authorization and that the platform is supported.
2. Confirm the artifact identifies a committed revision, and check its checksum.
3. Check the runtime identity, that mounts and volumes are ready, and the ownership and permissions of every parent directory and the configuration.
4. Stage immutable files and private writable data under the declared paths.
5. Start exactly one supervised process.
6. Verify readiness, authentication, and one critical read and write on disposable data.
7. Record the version, environment and diagnostics.

Never fall back to an empty production store.

## R2 — Coherent backup
1. Coordinate with jobs and maintenance windows.
2. Confirm the destination's identity and free capacity.
3. Quiesce writes and asset cleanup, or use a capture mechanism qualified as coherent.
4. Create a new set marked incomplete. Capture the database, the matching assets, configuration and version, and a manifest with checksums.
5. Validate the set before marking it complete.
6. Record local capture and off-host receipt as separate results.

If a backup fails, keep the previous known-good sets. Prune only under the adopted retention policy, and only sets that were verified.

## R3 — Upgrade and compatible rollback
1. Qualify the candidate and confirm a pre-change recovery set exists. Get authorization for this target and operation.
2. Enter maintenance, pause jobs, then drain and stop the service.
3. Capture protected pre-migration state.
4. Run the migration explicitly, after rehearsing it on a copy. Switch the release atomically where the platform supports it.
5. Start one process and verify real behavior.

On failure: keep the diagnostics, stop before restoring, and stay in maintenance. Roll back only the binary when schema compatibility is proven. Otherwise restore the coherent pre-change set. Verify compatibility and readiness before resuming. Report lost writes and the measured downtime.

## R4 — Runtime failure
Before acting, confirm the exact process, executable, start identity, storage and configuration. Never kill a process by name or by a stale PID alone. Recover within the adopted retry bounds. Keep evidence, and alert on deterministic failures, exhausted restart limits or unavailable storage.

## R5 — Isolated restore drill
1. Get authorization for a disposable target, and identify the archive being tested.
2. Retrieve it from off-host storage and decrypt it.
3. Check integrity and checksums, schema and release support, relationships and assets.
4. Verify critical behavior. Revoke restored sessions where applicable.
5. Measure the actual recovery time and recovery point. Keep any failures.

Never overwrite production to create a drill.

## R6 — Security or credential incident
Contain the affected boundary within the authorized scope. Preserve evidence. Rotate or revoke the affected secrets and sessions, and assess what was exposed. Verify the fixes and the restoration before reopening. Record who has decision authority. Send messages only when authorized.

## R7 — Qualification staging
Use [profiles/PRODUCTION_OPERATIONS.md](../profiles/PRODUCTION_OPERATIONS.md) for performance and soak work on the selected host. Validate the marker, paths, data and executable identity, the permissions, and that nothing overlaps production. Keep earlier runs. Fail early on missing telemetry or failed authentication. A graceful stop keeps incomplete evidence. Cleanup is a separately scoped operation with its own identity checks.

## Command and evidence record
{{ACTUAL_COMMANDS_REQUIRED_ROLES_PATHS_EXPECTED_RESULTS_AND_RECOVERY_ACTIONS}}

Link current operational results from PRODUCTION_READINESS.md and unresolved issues from OPEN_WORK.md. Record each deployment in RELEASE_NOTES.md. A passing shell syntax check is not native operational qualification.
