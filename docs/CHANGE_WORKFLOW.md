# Change workflow

## Scope and inspection
Follow the user's intended outcome. Explicit authorization persists for its scope; routine reversible choices do not require repeated permission. Ask before unrequested material architecture/dependency changes, destructive actions, publishing or deployment. Inspect instructions, source, actual commands and working-tree changes. Preserve unrelated edits; do not reset or overwrite them.

Distinguish proposals, accepted requirements, implementation observations and verification. Record conflicting references, impact and required decisions; continue independent authorized work while blocked questions remain. For substantial/risky changes prepare a reviewable plan with affected boundaries, compatibility, verification and recovery. Small changes need a proportionate explanation.

## Implementation and compatibility
Make the smallest cohesive change using approved patterns. No unrelated rewrites, renames, bulk formatting, upgrades or speculative features. Regenerate owned output rather than editing generated files directly. Preserve input on errors; never suppress failures or silently create substitute data/configuration.

Identifiers, formats, stored values, public interfaces and configuration are compatibility contracts. Explain breaks unless already authorized; supply reviewed transition and recovery procedures. Production migrations are explicit authorized operations. Durable architecture choices require an ADR; routine helpers do not.

## Verification
Create the affected requirement matrix in VERIFICATION_MATRIX.md before implementation, using TESTING_SPEC.md. Add meaningful regressions, failing before fixes when practical. Run focused checks, then required broader checks. Missing tooling/environment is work or a blocker, not inapplicability. Retain first failures; do not lower thresholds, mask errors or remove evidence to obtain green results.

## Operational failure review
Inspect ignored errors, broad catches, fallback paths/databases, partial writes, cleanup identity, inherited permissions/ancestors, signal/drain behavior, locks, timeout/retry bounds and schema-compatible rollback. Prerequisite failures halt dependent actions. Test actual shared execution paths with observable state assertions on disposable data. Justify any intentional suppression and its safe outcome.

## Final acceptance audit
After implementation/checks, conduct a separate review pass of final code/tests/docs/evidence against every applicable requirement. This does not require another agent or another approval checkpoint. A focused change explains excluded gate families; a release covers its full required inventory. Record pass/fail/blocked/in-progress/unverified or justified inapplicability, with evidence and work IDs.

Confirm tests exercised intended behavior, documentation describes the final implementation, source/evidence identify the same candidate and no secrets/unrelated files entered the diff. Missing required scope/evidence prevents a full completion claim.

## Delivery
Report changed behavior and purpose, actual commands/results, limitations, decisions and evidence links. State implementation, verification and release acceptance independently under DOCUMENTATION.md. Update OPEN_WORK.md; keep broader product gaps visible. Commit/push/merge/deploy only when authorized and use repository conventions. Documentation-only edits require reference/content review rather than unrelated application runs.
