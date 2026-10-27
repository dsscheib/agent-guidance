# Verification implementation handoff template

Scope/candidate/date: {{HANDOFF_SCOPE}}
Kind: Template. Status: Unconfigured worklist. No tests or operations claimed.

Read AGENTS.md and applicable references. TESTING_SPEC.md owns protocols; this handoff assigns work and observations, not new policy or operational authorization. Track current ownership/status in OPEN_WORK.md.

| Observed gap | Inspected source / evidence | Required outcome | Regression / real-path proof | Work ID |
|---|---|---|---|---|
| {{OBSERVED_GAP}} | {{SOURCE_AND_INSPECTION_DATE}} | {{ADOPTED_REQUIREMENT}} | {{NEGATIVE_AND_POSITIVE_CHECKS}} | {{WORK_ID}} |

## Sequence
1. Reinspect current implementation and produce the verification matrix.
2. Demonstrate known harness/application failures on isolated fixtures where practical.
3. Implement authorized fixes and missing tooling using actual contracts.
4. Exercise real transport/persistence/UI/operational paths and appropriate failures.
5. Run short diagnostics before adopted complete performance/soak protocols.
6. Collect separate local, manual, recovery and selected-host evidence; continue independent work when target authorization/tooling is pending.
7. Update authoritative docs, matrix, readiness record and work register.
8. Run the [final audit procedure](procedures/final-audit.md).

## Deliverables
{{REVIEWABLE_CODE_TESTS_COMMAND_INVENTORY_RAW_EVIDENCE_AND_REMAINING_BOUNDARIES}}
No deployment side effects. Failure, threshold and evidence-reuse rules: [TESTING_SPEC.md](TESTING_SPEC.md).
