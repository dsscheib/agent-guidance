---
name: release-review
description: Run the final release review, a systematic read-only audit of a release candidate across every risk area, before release readiness is decided. Use when asked for a pre-release audit, a final or full release review, or a thorough check of a candidate before it ships. It changes no repository files and touches nothing outside the machine. Not for filling the readiness record (release-readiness).
---
# Release review procedure

Systematic read-only audit to find defects automated gates and checklists miss. Changes no repository files, touches no production system or real data, and makes no external change. Temporary reproductions go outside the repository using synthetic data.

## 1. Identify the candidate and build the coverage checklist
Record the commit SHA and whether the working tree is clean. List every applicable area from below plus project-specific areas in `DESIGN_DOC.md`, `docs/RUNBOOKS.md`, or hardware docs:

Authentication; authorization; secrets; domain invariants; concurrency; migrations and schema; backups and restoration; deployment and rollback (including alternate deployment paths); CLI commands; imports and exports; resource limits; dependencies; UI; hardware/safety (if applicable); release evidence.

Mark an area not applicable only with evidence the project lacks it.

## 2. Review each area (and delegate to independent reviewers when available)
Work through every area; never stop after finding the first serious bug.

- **Use installed read-only reviewers when available:** Delegate independent risk slices (such as security, architecture, or hardware review) to installed read-only reviewers at your project's highest audit thoroughness/escalation setting. Give each reviewer the exact file paths, diffs, and evidence reports to inspect (some tools restrict read-only reviewers to file reads), and verify their findings before accepting them.
- **Trace real execution paths**, including indirect calls, scheduled jobs, scripts, and alternate deployment paths—not just the main entry point.
- **Check failure modes:** interruption, retry, concurrency, partial success, and state left halfway through failure.
- **Verify claims against code:** Treat recorded passes in `README.md`, `docs/RUNBOOKS.md`, `docs/PRODUCTION_READINESS.md`, `docs/VERIFICATION_MATRIX.md`, and `docs/OPEN_WORK.md` as unverified until underlying evidence confirms them for this candidate.
- **Read what tests assert and omit:** Passing tests support an area; they never close it.
- **Reproduce suspected defects** in a temporary directory outside the repo using synthetic data.

## 3. Classify results and area coverage
Sort every finding with file, line, traced path, and evidence into:
- **Confirmed defect:** reproduced or certain from code.
- **Plausible concern:** allowed by code, not reproduced; state what confirms or clears it.
- **Missing evidence:** a claim or requirement lacking evidence for this candidate.

Mark each checklist area **reviewed**, **partially reviewed**, or **unreviewed** with explicit limits (never mark an area reviewed if part of it was skipped).

## 4. Report in chat (do not write a file)
1. Candidate commit and clean/dirty tree state.
2. Area coverage table (area, status, limits).
3. Findings (confirmed defects most severe first, plausible concerns, missing evidence).
4. Recommendation on release readiness plus any decisions needed as direct questions.

Offer to record findings in [docs/OPEN_WORK.md](../OPEN_WORK.md) and release blockers through `release-readiness` only once approved.
