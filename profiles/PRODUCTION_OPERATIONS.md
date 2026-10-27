# Production operations profile

Kind: Profile. Status: Applies when PROJECT_PROFILE.md adopts the Production service tier, or when the owner adopts it explicitly for a lower tier. Otherwise it is reference material only. No collector command or target run is asserted. Adopt protocol values in PROJECT_PROFILE.md, and implement and verify the tooling under [TESTING_SPEC.md](../docs/TESTING_SPEC.md).

## Host hardening
These controls extend [SECURITY_PRODUCTION_SPEC.md](../docs/SECURITY_PRODUCTION_SPEC.md) for self-managed hosts:
- Protect releases, executables, configuration and every ancestor directory against modification by the runtime identity.
- Check effective inherited permissions and ACLs, ownership, symlinks and mount execution flags. Private upload locations and installed executable locations may need different policies; do not bypass execution restrictions.
- Validate the exact process, start time and executable identity before signalling, stopping or cleaning up. Never act on a process name or a stale PID alone.
- Cross-compilation is not native qualification. Qualify the selected runtime, ABI or kernel, filesystem, driver and process manager on the target platform.

## Qualification isolation and candidate
Use fresh, marked, disposable staging with explicit environment authorization, a dedicated non-admin identity, and an immutable executable, configuration and ancestor chain. Validate canonical paths, the selected database, and the process identity checks above. Preserve old runs and refuse ambiguous setup or cleanup.

Measure the source and artifact identity of the binary actually served; do not use an unrelated generator checkout. Test separate-process inspection and stripped or optimized build profiles. Compiler metadata may omit linker flags, so qualify the selected attestation mechanism rather than assuming flags stay readable. Labels cannot make dirty, synthetic or wrong-candidate evidence release-eligible.

## Workload and windows
Use real served workflows with independent, authenticated, role-valid sessions. Preflight successful persistent reads and writes. Run the adopted warm-up (excluded from results), the measured performance window and the full uninterrupted soak.

Wrong routes, login redirects, bad tokens and unexpected error responses never count as successful load. Consume response bodies before stopping the client timer. Keep server timings separate from network, render and client timings. Retain per-operation raw timing and status traces, success, error and sample counts, distributions, and the achieved mix and rate. Identify expected negative and fault scenarios separately from the uninterrupted workload, and assert they have no unintended effects.

## Telemetry, jobs and correctness
Collect baseline, bounded-interval and final process, host, storage and job metrics, along with uptime and restart detection and the declared measurement methods. Missing measurements make the run incomplete, not zero. Estimates need an explicitly adopted method, retained inputs and clear labels. Record cold start, representative background jobs, interaction with backup and restore, and session renewal. Supervise the exact owned child process without automatic restarts during uninterrupted qualification, and report any forced shutdown explicitly.

Capture the initial state and every acknowledged consequential operation. Then independently reconcile the final state, events, relationships, invariants, persistence integrity and audit data. Prove coherent capture and isolated restoration with the actual assets, configuration and session policy as applicable.

## Acceptance of a run
Review time-series resource growth, not only the endpoints. Define investigation thresholds and capacity budgets before the run. Any of the following prevents qualification:
- unresolved growth, an interruption or a restart,
- insufficient samples or rate,
- missing telemetry or failed effects,
- a breached budget.

Test the harness against each known bad outcome: tampering, missing data, wrong identity, early stop, restart, inadequate workload and invariant failure.

Retain incomplete and failing reports and their raw artifacts, with:
- the candidate and environment, methods and window definitions,
- counts and percentiles, the growth review and job receipts,
- checksums and byte counts.

Return non-success for a failed run; a failed report write is also a failure. Validate summary claims against the raw traces and time series. Keep artifacts contained under an explicit, caller-selected evidence root with portable references.

## Aggregate release verifier
Build the expected-gate inventory from the adopted requirements, not only from the supplied results. Record:
- the candidate commit and the actual source and artifact identity,
- the dirty state and build configuration,
- commands, statuses and exit codes,
- the environment and dates,
- raw evidence paths, hashes and sizes.

Mark synthetic test mode explicitly as release-ineligible. Compare the actual binary identity and source attestation, not a label from an unrelated checkout.

Reject missing or duplicate gates; malformed, wrong-candidate, stale or tampered evidence; unsupported exclusions; and contradictory eligibility. Validate the same qualification contract in direct checks, evidence intake and manifest validation. Pending, manual, blocked or failed required gates stay visible and prevent an aggregate pass. Test child failures, missing artifacts, false pass markers, synthetic eligibility and honest non-success results.

The verifier never deploys as a side effect. JSON consistency cannot establish owner consent or perform a manual check. Qualification intake still needs genuine authorization and the applicable manual review.

{{IMPLEMENTED_COMMANDS_TARGET_PROFILE_PROTOCOL_AND_CURRENT_EVIDENCE}}
