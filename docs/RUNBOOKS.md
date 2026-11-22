# Operator runbooks

Runbooks for internal (R1–R3, R5) and production/enterprise (all) projects. Replace placeholders with inspected commands, roles, and paths, and rehearse on isolated staging before production use.

**One reusable path per procedure:** Each runbook lives in one shared set of scripts. Never write a one-shot installer, upgrade script, or probe for a single release—extend the shared path, and delete one-shot scripts together with their tests once retired. Follow [AGENTS.md](../AGENTS.md) for committed release/deploy sources and batched review deployments. Missing test tooling does not block an owner-requested review deployment (record gaps in [docs/OPEN_WORK.md](OPEN_WORK.md)); failing checks always block.

## R1 — Install and start
Confirm authorization and supported host, verify the committed revision and checksum, check non-admin runtime ownership and directory permissions, start one supervised process, and verify readiness plus one critical read/write on disposable data. Never fall back to an empty production store.

## R2 — Coherent backup
Coordinate with jobs, verify destination capacity, quiesce writes (or use a coherent capture mechanism), bundle database + matching mutable assets + config + checksum manifest as incomplete until validated, and verify off-host receipt separately. Same-host copies or redundant disks are not disaster recovery.

## R3 — Upgrade and compatible rollback
Confirm a verified pre-change backup exists and authorization covers the target. Drain and stop jobs/service, capture pre-migration state, run the rehearsed migration explicitly, switch atomically, and verify readiness before resuming writes. Roll back the binary alone only when schema compatibility is proven; otherwise restore the coherent pre-change set and report any lost writes.

## R4 — Runtime failure
Verify the exact process, executable, and start time before acting—never kill by name or stale PID. Bound retries, stop and alert on deterministic failures or missing storage.

## R5 — Isolated restore drill
With explicit approval for a disposable target, retrieve and decrypt an off-host backup, verify checksums, schema/asset compatibility, and critical workflows, revoke restored sessions where applicable, and record actual RTO/RPO. Never overwrite production.

## R6 — Security or credential incident
Contain within authorized scope, preserve evidence, rotate/revoke exposed secrets and sessions, verify recovery, and send external notices only when explicitly authorized.

## Command and evidence record
{{ACTUAL_COMMANDS_REQUIRED_ROLES_PATHS_EXPECTED_RESULTS_AND_RECOVERY_ACTIONS}}

Record each deployment in [docs/RELEASE_NOTES.md](RELEASE_NOTES.md) and open issues in [docs/OPEN_WORK.md](OPEN_WORK.md).
