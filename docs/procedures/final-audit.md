---
name: final-audit
description: Run the final acceptance audit and write the delivery report at the end of any change, before reporting it complete. Use when finishing implementation, documentation or test work, or when asked whether a change is done. Do not use to decide whether to release; use release-readiness for that.
---
# Final audit procedure

Kind: Procedure. This is the home of the final acceptance audit that [AGENTS.md](../../AGENTS.md) rule 15 requires. It needs no second agent and no extra approval checkpoint, but it is a separate review pass made after the implementation and checks are finished.

## 1. Re-read the scope
- Restate the requested outcome and its authorized scope.
- List the requirement IDs and the VERIFICATION_MATRIX rows the change affects.
- Note excluded gate families and why. A focused change explains its exclusions; a release covers the tier's full required inventory.

## 2. Review the final diff against every applicable requirement
For each requirement, record pass, fail, blocked, in progress, unverified, or justified inapplicability, with evidence and work IDs. Use the vocabulary in [DOCUMENTATION.md](../DOCUMENTATION.md). Then confirm:
- [ ] The tests exercised the intended behavior and the failure cases, not substitutes or mocks of the path under test.
- [ ] Commands were actually run. Results are quoted from real output, and first failures are kept.
- [ ] Documentation describes the final implementation. Every "update after" document in the AGENTS.md routing table for this change was updated, and no unaffected document was edited.
- [ ] The source and evidence identify the same candidate.
- [ ] The diff contains no secrets, unrelated files or reformatting.
- [ ] Generated files were regenerated, not hand-edited.
- [ ] `python3 check_package.py` passes if guidance files changed.

Missing required scope or evidence prevents a full completion claim.

## 3. Update registers
- Close or update the affected [OPEN_WORK.md](../OPEN_WORK.md) entries, with closure evidence.
- Add entries for every new gap, decision or blocker.
- Keep broader product gaps visible.

## 4. Deliver the report
Report:
- the changed behavior and its purpose,
- the actual commands and their results,
- limitations, decisions made and evidence links,
- open questions for the owner,
- these three states, each stated independently:
  - Implementation complete: yes, no or partial.
  - Verification complete: yes or no, with what is unverified.
  - Release accepted: normally "not evaluated". Only an authorized owner decision grants it.

Commit, push, merge or deploy only as the PROJECT_PROFILE git policy or the user allows, following repository conventions.
