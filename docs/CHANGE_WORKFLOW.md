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
1. Map the affected requirements in [VERIFICATION_MATRIX.md](VERIFICATION_MATRIX.md) before implementation.
2. Add regressions.
3. Run focused checks, then the broader required checks for the project tier.

## Operational failure review
For changes to operational code, inspect:
- ignored errors, broad catches and fallback paths or databases,
- partial writes and cleanup identity,
- inherited permissions,
- signal and drain behavior, locks, and timeout and retry bounds,
- schema-compatible rollback.

Prerequisite failures halt dependent actions. Test the actual shared execution paths, with observable state assertions on disposable data. Justify any intentional suppression and its safe outcome.

## Completion
Finish every change with the [final audit procedure](procedures/final-audit.md). It covers the requirement-by-requirement review, the delivery report and register updates. Documentation-only edits need a reference and content review, not unrelated application runs.
