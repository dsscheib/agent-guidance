# Performance and soak collector contract

Status: Generic specification; no collector command or target run is asserted. Adopt protocol values in PROJECT_PROFILE.md and implement/verify tooling under TESTING_SPEC.md.

## Isolation and candidate
Use fresh marked disposable staging, explicit environment authorization, dedicated non-admin identity and immutable executable/configuration/ancestors. Validate canonical paths, symlinks, effective ACLs, mount flags, selected database and exact process/start/executable identity. Private uploads and installed executable locations may need different policies; do not bypass execution restrictions. Preserve old runs and refuse ambiguous setup/cleanup.

Measure the actual served binary's source/artifact identity; do not use an unrelated generator checkout. Test separate-process inspection and stripped/optimized build profiles. Compiler metadata may omit linker flags; qualify the selected attestation mechanism rather than assuming flags remain readable. Dirty, synthetic or wrong-candidate evidence cannot become release-eligible through labels.

## Workload and windows
Preflight independent role-valid authenticated clients and successful persistent reads/writes. Run the adopted excluded warm-up, measured performance window and full uninterrupted soak. Keep per-operation raw timing/status traces, successful/error/sample counts and achieved mix/rate. Server and full-client timings remain distinct. Expected negative scenarios are identified separately and assert no unintended effects.

## Telemetry, jobs and correctness
Retain baseline, bounded-interval and final process/host/storage metrics, workload distributions, uptime/restarts and declared jobs. Missing metrics fail; estimates need an approved labelled method with retained counters. Record cold start, background load, backup/restore interaction and session renewal. Supervise the exact owned child without automatic restarts during uninterrupted qualification; report forced shutdown explicitly.

Capture initial state and every acknowledged consequential operation, then independently reconcile final state/events/relationships/invariants and persistence integrity. Prove coherent capture and isolated restoration with actual assets/configuration/session policy as applicable. Same-host restoration does not close off-host disaster recovery.

## Reports and validation
Retain incomplete/failing reports and raw artifacts, with candidate/environment, methods, window definitions, counts/percentiles, growth review, job receipts and checksums/byte counts. Validate summary claims against raw traces and time series. Protect artifact-root containment and make references portable with an explicit caller-selected evidence root. Test tamper, missing data, wrong identity, early stop, restart, inadequate workload and invariant failures. Qualification intake also needs genuine authorization and applicable human/manual review; generated acknowledgment fields cannot supply them.

{{IMPLEMENTED_COMMANDS_TARGET_PROFILE_PROTOCOL_AND_CURRENT_EVIDENCE}}
