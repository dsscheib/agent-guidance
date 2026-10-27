# Maintaining the guidance package

This file exists only in the template repository and is never installed into projects. Its presence switches `check_package.py` to template mode, and it tells agents (AGENTS.md, first paragraph) that they are editing the package rather than working in a project.

## Rules for editing the package
1. **Templates stay empty.** Registers (`docs/OPEN_WORK.md`, `docs/VERIFICATION_MATRIX.md`, `docs/PRODUCTION_READINESS.md`, `docs/ROADMAP.md`, `docs/SOURCES.md`) contain only placeholder rows. Record package history in the log below, never in a shipped file. The checker rejects dated entries in registers.
2. **One home per rule.** Before adding a sentence, find the rule's home through the routing table in AGENTS.md and the status section of `docs/DOCUMENTATION.md`. Link to it instead of restating it.
3. **Keep AGENTS.md small and concrete.** Write each rule as a rule, a reason and an example. Move detail into routed documents or procedures. Target size: under about 10 KB.
4. **Stay agent-neutral.** Use no tool-specific names or features in policy text. Tool specifics belong in `docs/AGENT_TOOLS.md` and the adapter files, and every adapter only points to, exposes or enforces rules from AGENTS.md.
5. **Keep the core stack-neutral.** Mechanism-specific rules (HTMX, a particular database, host hardening) belong in `profiles/`.
6. **Keep tier sizing proportional.** A new gate needs a default in the PROJECT_PROFILE tier table.

## Workflow for a change
1. Edit the source files. For skills, edit `docs/procedures/<name>.md`, never `.agents/skills/` or `.claude/skills/`.
2. For a new packaged file, add an entry with its `kind` (and `stage` if relevant) to `PACKAGE_MANIFEST.json`. Repository-only files go under `repo_only`.
3. Run `python3 check_package.py --sync-adapters --update-manifest`, then `python3 check_package.py`. Both must pass.
4. Run the affected scenarios in [maintainer/SCENARIOS.md](maintainer/SCENARIOS.md) with at least one agent, and preferably with every supported agent for changes to AGENTS.md or the adapters. `python3 maintainer/run_scenario.py <ID> <dir>` builds each fixture. Record runs in [maintainer/RESULTS.md](maintainer/RESULTS.md). If a change alters the files or profile fields a scenario depends on, update `maintainer/scenarios.json` or the fixture in the same change; `check_package.py` fails until the fixtures build again.
5. Add a log entry below.

## Maintenance log

| ID | Date | Change | Verification |
|---|---|---|---|
| DOC-001 | 2026-10-17 | Renamed the technical design document to `DESIGN_DOC.md` and updated references (by Codex) | Path, unchanged-content and old-reference assertions; package checker passed |
| DOC-002 | 2026-10-27 | Applied the guidance review: agent-neutral AGENTS.md with routing table and 15 rules; Codex, Antigravity and Claude Code adapters; procedures as generated skills; project tiers; bootstrap protocol and placeholder stages; deduplicated rules; web and production-ops specifics moved to profiles; maintainer history moved out of shipped registers; checker install, sync, update-manifest and project modes | `python3 check_package.py` (template mode), an install into a scratch directory with project-mode `--require code` failing as expected, and the negative checks recorded in the delivery report. Agent scenario walkthroughs not yet run |
| DOC-003 | 2026-10-27 | Documented Antigravity CLI command guardrails (`~/.gemini/antigravity-cli/settings.json` permissions) alongside the app settings in `docs/AGENT_TOOLS.md` and the README; added sources | `python3 check_package.py` passed. The CLI snippet has not been loaded in Antigravity CLI |
| DOC-004 | 2026-10-27 | Merged upstream commit c8b4fa6, which adds the UAT delivery guidance for UI/workflow changes. Its rule now lives in the final-audit delivery step, with a one-line summary in AGENTS.md rule 11, the UX checklist item, and a UAT environment in the PROJECT_PROFILE deployment row | `python3 check_package.py` passed |
| DOC-005 | 2026-10-27 | Added reproducible scenario fixtures: `maintainer/scenarios.json` as the single source, layered fixtures under `maintainer/fixtures/`, `maintainer/run_scenario.py` (build, list, write-table, check), a generated catalog in SCENARIOS.md, and the RESULTS.md log. Template-mode `check_package.py` now builds every scenario | `run_scenario.py --check` passes (10 scenarios). Negative controls: unmatched patch, unknown profile key, wrong expected test state and stale catalog are each reported; a git-hook environment (`GIT_DIR`, `GIT_INDEX_FILE`) leaves this repository unchanged; a non-empty target is refused. No agent runs recorded yet |
