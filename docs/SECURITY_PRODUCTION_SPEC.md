# Security and production policy

Status: General engineering controls plus unconfigured project policy. Complete PROJECT_PROFILE.md and the fields below before claiming operational readiness.

## Trust and authorization
{{DATA_CLASSIFICATION_AUTHENTICATION_AUTHORIZATION_AND_NETWORK_TOPOLOGY}}
Treat network clients, browser state, uploads and integration responses as untrusted. Enforce identity, object/action permission, input bounds, validation and output encoding at authoritative boundaries. Adopt appropriate session, request-forgery, cookie, origin/proxy and transport controls; test expiry, revocation and forbidden access. UI visibility is not authorization.

Minimize exposed services and privileges. Record actual ingress, management boundaries, trusted proxy addresses and egress. Do not disable certificate validation or silently weaken a control to fit a platform. Secret material is kept outside source, command arguments, logs, examples and routine evidence. Use maintained security primitives, not homegrown cryptography.

## Host, dependencies and storage
{{SUPPORTED_PLATFORM_DEPENDENCY_AND_STORAGE_PROFILE}}
Inspect actual runtime, ABI/kernel, filesystem, driver, process manager and tool support. Cross-compilation is not native qualification. Unsupported platforms need a specifically reviewed exception with limitations and expiry; tests cannot convert unsupported infrastructure into supported infrastructure.

Pin/review dependencies and assets according to the adopted policy. Use a dedicated non-admin runtime identity. Protect releases, executables, configuration and all ancestors against runtime modification; check effective inherited permissions/ACLs, ownership, symlinks and mount execution flags. Writable data/logs/jobs/backups are separate and appropriately restricted. Keep local-file databases on supported local storage; use the selected database's documented persistence mechanisms.

## Lifecycle, migrations and rollback
Use reviewed immutable versioned releases and an adopted supervisor/lifecycle adapter. Stop gracefully, drain writes, validate process identity and enforce singleton locks. Bound retries and restart bursts; latch/alert deterministic failures instead of looping indefinitely. Unavailable configured storage must not create an empty replacement database.

Deployment requires explicit environment-specific authorization. Coordinate jobs/maintenance, prove coherent pre-change recovery, rehearse reviewed migrations on an isolated copy, migrate explicitly and verify readiness plus critical behavior before resuming writes. Do not promise zero downtime without evidence. Binary-only rollback requires proven schema compatibility; otherwise restore the matching database/assets/configuration/release while protected from writes and disclose possible post-change data loss. Do not run blind destructive down migrations.

## Backup and recovery
{{RECOVERY_OBJECTIVES_CADENCE_RETENTION_ENCRYPTION_KEYS_AND_DESTINATIONS}}
Objectives are targets until demonstrated. Capture a coherent database plus matching mutable assets/configuration/version using a qualified mechanism, quiescence or offline procedure. A database-only snapshot cannot prove consistency of independently changing assets. Never copy an active database main file alone or delete journals to clear errors.

Verify completion, integrity, relationships, assets, release/schema compatibility and actual restore behavior. Encrypt sensitive off-host material; protect recovery keys independently. Ensure a source compromise cannot delete all historical copies. Distinguish local capture, off-host receipt, decryptability and isolated restoration. A same-host copy or redundant storage is not disaster recovery. Adopt session revocation after recovery where appropriate.

## Jobs, observability and budgets
{{JOB_CADENCES_RETRY_LIMITS_ALERT_DESTINATIONS_AND_RETENTION}}
Jobs use bounded runtimes, singleton locks, durable outcomes and controlled overlap with deployment/restore. No hidden schema changes or self-updates. Liveness should be lightweight; readiness must reflect actual prerequisites without unbounded expensive scans. Health checks do not perform business mutations or establish full qualification.

Structured logs use bounded classifications and redaction. Test actual alert delivery; maintenance silences expire. Define memory/CPU/storage/latency budgets from representative use and reserve capacity for backup/migration. Runtime tuning knobs are not measured resource guarantees. Warn and halt dependent work when required safe capacity is absent.

Readiness requires the actual evidence in PRODUCTION_READINESS.md and TESTING_SPEC.md; implementation existence and status strings cannot pass gates.
