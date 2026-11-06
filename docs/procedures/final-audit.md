---
name: final-audit
description: Run the final acceptance audit and give the short delivery report at the end of any change, before reporting it complete. Use when finishing implementation, documentation or test work, or when asked whether a change is done. Do not use to decide whether to release; use release-readiness for that.
---
# Final audit procedure

Kind: Procedure. This is the home of the final acceptance audit that [AGENTS.md](../../AGENTS.md) rule 15 requires. It needs no second agent and no extra approval checkpoint, but it is a separate review pass made after the implementation and checks are finished.

## 1. Re-read the scope
- Restate the requested outcome and its authorized scope.
- List the requirement IDs the change affects, and the VERIFICATION_MATRIX rows where the project keeps one.
- Note excluded gate families and why. A focused change explains its exclusions; a release covers the tier's full required inventory.

## 2. Review the final diff against every applicable requirement
For each requirement, record pass, fail, blocked, in progress, unverified, or justified inapplicability, with evidence and work IDs. Use the vocabulary in [DOCUMENTATION.md](../DOCUMENTATION.md). Then confirm:
- [ ] The tests exercised the intended behavior and the failure cases, not substitutes or mocks of the path under test.
- [ ] `python3 check_package.py --verify` ran on the final tree (`--verify documentation` for a change to documentation alone). Its `Verification:` line is quoted as-is, and first failures are kept.
- [ ] Documentation describes the final implementation. Every "update after" document in the AGENTS.md routing table for this change was updated, and no unaffected document was edited.
- [ ] The source and evidence identify the same candidate. Anything built or deployed came from a committed revision.
- [ ] The diff contains no secrets, unrelated files or reformatting.
- [ ] Generated files were regenerated, not hand-edited.
- [ ] `python3 check_package.py` passes. It checks the [document budget](../DOCUMENTATION.md#document-budget) as well as guidance integrity.
- [ ] Status was overwritten, not appended. No dated section was added to PROJECT_PROFILE.md, and no report file was created for this change.
- [ ] No one-shot deployment, upgrade or probe script was added ([review cadence](../CHANGE_WORKFLOW.md#deployment-and-review-cadence)).

Missing required scope or evidence prevents a full completion claim.

## 3. Update registers
- Update the affected [OPEN_WORK.md](../OPEN_WORK.md) entries in place. Shorten closed entries to one row with their closure evidence.
- Add an entry for each decision, blocker or gap this change leaves open. When the `Verification:` line names a gap that leaves the change's new behavior unverified, such as browser checks for a new page, record that this behavior is unverified. A gap the inventory already shows, with nothing new depending on it, needs no entry.
- Keep broader product gaps visible.

## 4. Check scope against the baseline
Compare the work with the baseline scope in DESIGN_DOC.md and the ROADMAP. When the work finishes a feature, or the last several work items were follow-ups or fix rounds on one feature while baseline features remain unstarted, add one line to the report saying which baseline features are done, in progress and not started. The owner decides what to do about it; the agent only makes the drift visible.

## 5. Deliver the report
Give the report in chat or the pull request description, not in a new file. Keep it as short as the change: **two to five lines for a routine change**, longer only when the owner has decisions to make. The checklists above are for you; do not recite them in the report. Write it in your own voice, as in the example below, not as a form to fill in.

Include, in this order:
1. What changed, in one or two sentences, naming the files or behavior.
2. The `Verification:` line from `python3 check_package.py --verify`, quoted exactly. Do not add your own verdict such as "verified" or "all checks pass", and do not explain gaps the line already names.
3. Only what applies: a failed check, each decision the owner must make, written as a direct question to them, even if you also recorded it (with what you built meanwhile, or why nothing could be built without the answer), local UAT steps for a UI or workflow change (here, not in README or another file), the scope line from step 4, and whether you committed. Deploy to a review environment only when the owner asks, with fixes batched ([review cadence](../CHANGE_WORKFLOW.md#deployment-and-review-cadence)).

Leave out what did not happen: documents that needed no change, files you left alone, actions you did not take. Mention one only if the owner must act on it.

A routine report looks like this:

> I added a `--dry-run` option to `sync_photos.py`. It lists the files it would copy without copying anything, and the README usage section shows how to use it.
> Verification: incomplete (development gates: 3 passed; 1 gap: Lint; 1 excluded)
> It's committed on `task/sync-dry-run`.

Add release acceptance only for a release, or when the owner asks whether the work is done: it is normally "not evaluated", and only an authorized owner decision grants it.

Commit, push, merge or deploy only as the PROJECT_PROFILE git policy or the user allows, following repository conventions.
