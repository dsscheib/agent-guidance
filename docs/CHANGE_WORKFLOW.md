# Change workflow

Kind: Policy. It applies as written; changing it needs an owner decision. Authorization, scope and preservation rules are in [AGENTS.md](../AGENTS.md) rules 1–5.

## Scope and inspection
Follow the user's intended outcome. Explicit authorization persists for its stated scope, and routine reversible choices do not need repeated permission. Before editing, inspect the instructions, source, actual commands and working-tree changes.

Distinguish proposals, accepted requirements, implementation observations and verification. Record conflicting references, their impact and the decisions required in [OPEN_WORK.md](OPEN_WORK.md). Continue independent authorized work while blocked questions remain open.

Size the plan to the change:
- **Substantial or risky changes** need a reviewable plan covering affected boundaries, compatibility, verification and recovery.
- **Small changes** need only a proportionate explanation.

## Implementation and compatibility
Make the smallest cohesive change using approved patterns. Regenerate owned output instead of editing generated files directly. Preserve input on errors. Never suppress failures or silently create substitute data or configuration.

Identifiers, formats, stored values, public interfaces and configuration are compatibility contracts. Explain any break unless it is already authorized, and supply reviewed transition and recovery procedures. Production migrations are explicit, authorized operations. Durable decisions follow the ADR rule in [DOCUMENTATION.md](DOCUMENTATION.md).

## Verification
Follow the workflow in [TESTING_SPEC.md](TESTING_SPEC.md):
1. Know which requirements the change affects before implementation. Where the project keeps [VERIFICATION_MATRIX.md](VERIFICATION_MATRIX.md) (Production service and Enterprise), map them there.
2. Add regressions.
3. Run focused checks, then the broader required checks for the project tier.

## Deployment and review cadence
This section is the home of the review-cadence and committed-source rules that AGENTS.md rules 3 and 11 summarize.
- **Build only from committed source.** Every release or review artifact identifies one commit. A dirty working tree is not a candidate. If the owner wants to deploy uncommitted work, commit it on a task branch first, or ask to.
- **Do UAT locally first.** Give the owner UAT steps to run against a local fixture. Collect feedback and batch the fixes.
- **Deploy to a review environment at the end of an iteration**, or when the owner asks. Do not redeploy after each fix. One deployment carries every batched fix since the last one.
- **Use one reusable deployment path.** [RUNBOOKS.md](RUNBOOKS.md) owns the install, upgrade and recovery procedures, and the project keeps one set of scripts that implements them. Do not write a new installer, upgrade script or probe for a single release. If the reusable path cannot handle a change, such as a new kind of migration, raise it with the owner as a design question and extend the shared path.
- **Delete one-shot scripts after use.** Git history keeps them. Docs point to the commit, not to a script that must never be rerun.
- **Record each deployment** as one entry in [RELEASE_NOTES.md](RELEASE_NOTES.md).

## Operational failure review
Apply this review to the shared operational path when it changes, not again for each release that uses it. For changes to operational code, inspect:
- ignored errors, broad catches and fallback paths or databases,
- partial writes and cleanup identity,
- inherited permissions,
- signal and drain behavior, locks, and timeout and retry bounds,
- schema-compatible rollback.

Prerequisite failures halt dependent actions. Test the actual shared execution paths, with observable state assertions on disposable data. Justify any intentional suppression and its safe outcome.

## Completion
Finish every change with the [final audit procedure](procedures/final-audit.md). It covers the requirement-by-requirement review, the delivery report and register updates. Keep the result within the [document budget](DOCUMENTATION.md#document-budget). Documentation-only edits need a reference and content review, not unrelated application runs.
