# Package audit

Repository-only. An independent, in-depth review of the guidance package, run by the [guidance-auditor](roles/guidance-auditor.md) role. It checks that the package is correct, that its claims match its evidence, and that it stays independent: of any one agent vendor, of any one project, and of the person or agent that wrote the change.

## When to run it
- **Before tagging a release.** Audit the range from the previous release tag to the candidate commit.
- **Before merging a consequential change:** AGENTS.md, a policy, a procedure, `check_package.py`, the install or upgrade path, or the scenario scorer. Audit the pull request's range.
- **When the maintainer asks.** Audit whatever range they name.

A routine documentation fix needs no audit.

## Independence rules
1. **Not the author.** The auditor never audits a change it wrote or helped write in the same session. Start it in a fresh context: a new session, or a subagent that does not inherit the conversation. In Codex, spawn with `fork_turns` set to `none`.
2. **Another vendor where possible.** Run the auditor on a different agent tool or model family from the one that wrote the change. For example, Codex or Copilot CLI audits work written with Claude Code, and the other way round. Every tool gets this role ([MAINTAINING](../MAINTAINING.md#maintainer-team)). Name the auditor's tool and model in the verdict.
3. **Evidence, not the description.** Give the auditor the range or pull request number, not the author's summary. It reads the diff and the files, runs the checks itself, and treats every stated result as a claim to verify.
4. **Read-only.** The auditor changes no files, makes no commits and writes no report file. It reports in its reply, or the maintainer posts the reply as a pull request comment. Fixes are made by someone else, and a fixed finding is re-checked by the auditor.
5. **Disclose limits.** Name every check it could not run (missing CLI, no network, an agent run it was not authorized to start) and every place it relied on the author's records.

## Checklist
For each item, record what was checked and how.

1. **Checks pass for the right reasons.** Run `python3 check_package.py` and `python3 maintainer/run_scenario.py --check`. For each behavior the range adds or fixes, confirm a test exists that fails without it. Where it matters, break the guarded condition in a scratch copy, outside the repository, and confirm the test fails.
2. **One home per rule.** No rule is stated in two places, and no adapter, role or generated file holds a rule that AGENTS.md or its routed documents do not ([MAINTAINING](../MAINTAINING.md) rule 2). AGENTS.md stays near its size target, and rules make sense with no optional module installed.
3. **Neutrality.** Policy text names no agent tool or vendor feature outside `docs/AGENT_TOOLS.md`, the adapters and the roles' model keys. The core names no stack outside `profiles/`. Shipped files carry no project specifics: names, hosts, dates of status, results, approvals or backlog items.
4. **Evidence integrity.** Every claim of a result in README.md, `maintainer/README.md`, RESULTS.md, HOLDOUT_RESULTS.md and the maintenance log matches recorded runs: counts, pass rates, agents, versions and settings. Comparisons use the same settings, or say they do not. No check was tuned on the holdout test set, and agents cannot see scenario criteria. A scorer change that alters earlier verdicts says so.
5. **Install and upgrade safety.** `--install`, `--plan-upgrade` and `--check-upgrade` never overwrite or drop a project's own content silently. A new packaged file has a manifest entry with the right kind and module, and an upgrade from the previous release handles it.
6. **Tool claims are current.** Each vendor claim in `docs/AGENT_TOOLS.md` has a source and a check date. Flag claims checked more than 60 days before the audit, and any the range changed without a new check.
7. **Bounded output.** Every rule that makes agents produce output says where it goes and how it stays bounded ([MAINTAINING](../MAINTAINING.md) rule 7).
8. **Records match history.** Each maintenance log entry in the range describes what its commits did, and its Verification column states only what was run.

## Report
In the reply, in this order:
- **Verdict:** one line, *ready*, *ready with fixes* or *not ready*. Name the range, and the auditor's tool and model.
- **Findings, most severe first.** Give each one:
  - a severity: *blocker*, *major*, *minor* or *note*
  - confidence: *confirmed* or *plausible*
  - its location as file and line
  - the evidence: the command and its output, or the quoted text
  - the smallest fix
- **Checks run and checks not run,** with the reason for each not run.

Keep it under about 600 words unless the maintainer asks for more. The author records the verdict and the auditor's tool in the release's maintenance log entry. The report itself stays in the reply or the pull request.
