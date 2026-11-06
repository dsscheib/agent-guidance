---
name: release-review
description: Run the final release review, a systematic read-only audit of a release candidate across every risk area, before release readiness is decided. Use when asked for a pre-release audit, a final or full release review, or a thorough check of a candidate before it ships. It changes no repository files and touches nothing outside the machine. Not for finishing a single change (final-audit) or filling the readiness record (release-readiness).
---
# Release review procedure

Kind: Procedure. The review looks for defects that the gates and the readiness record can miss. [release-readiness](release-readiness.md) then records its results. The review is read-only: it changes no file in the repository, uses no production system or real data, and makes no external change (AGENTS.md rules 3 and 10). Temporary files and synthetic reproductions go outside the repository.

## 1. Identify the candidate and build the coverage checklist
Record the commit you review and whether the working tree is clean. Before reviewing anything, write the checklist of areas. Start from this list, then add the project's own areas from DOMAIN_RULES, DESIGN_DOC, SECURITY_PRODUCTION_SPEC and RUNBOOKS, such as each domain invariant or lifecycle:

Authentication; authorization; secrets; domain invariants; concurrency; migrations and schema; backups and restoration; deployment and rollback, including alternate deployment paths; command-line commands; imports and exports; resource limits; dependencies; UI; release evidence.

Mark an area not applicable only with evidence that the project lacks it, for example no UI code and no UI requirement.

## 2. Review each area
Work through every area, and keep going after serious findings: one defect does not end the review. For each area:
- **Trace the real execution paths**, including indirect calls, scheduled jobs, scripts and alternate deployment paths, not only the documented entry point.
- **Check the bad cases**: failure, interruption, retry, concurrency and partial success. Ask what state remains when a step fails halfway.
- **Compare claims with the code.** Read README, RUNBOOKS, PRODUCTION_READINESS, VERIFICATION_MATRIX and OPEN_WORK against the implementation, git history and the evidence that exists. A recorded pass is unverified until the evidence behind it confirms it for this candidate.
- **Read what the tests assert and what they leave out.** Passing tests support a conclusion; they do not end the review of an area.
- **Reproduce suspected defects** where practical, with isolated synthetic data in a temporary folder outside the repository. Never use real data or a production system.

## 3. Classify the results
Sort every result into one of three groups, each with the file and line, the path traced, and how you know:
- **Confirmed defect**: reproduced, or certain from the code. Say what fails and how.
- **Plausible concern**: the code allows it but you did not reproduce it. Say what would confirm or clear it.
- **Missing evidence**: a claim or requirement with nothing behind it for this candidate.

Mark each area **reviewed**, **partially reviewed** or **unreviewed**, with concrete limitations such as "no target host to test the restore" or "migration 14 not traced". Never call an area reviewed when you skipped part of it.

## 4. Report
Give the report in chat, not in a file ([document budget](../DOCUMENTATION.md#document-budget)). Write it plainly:
1. The candidate commit and whether its tree was clean.
2. The area table: each area, its status and its limitations.
3. Confirmed defects, most severe first, then plausible concerns, then missing evidence.
4. Your recommendation on whether the candidate is ready for release readiness, and each decision you need from the user, as a direct question.

Offer to record the findings in OPEN_WORK, and as blockers in the readiness record through [release-readiness](release-readiness.md). Record them only when the user agrees, because the review itself changes nothing.
