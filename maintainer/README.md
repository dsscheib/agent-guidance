# Maintainer overview: Version 4 focus and adoption guide

Repository-only. Version 4 refocuses this package on **strong frontier supervisor models coordinating specialist subagents** (such as `agent-team`), **multi-CLI repositories**, and **deterministic verification gates** (`scripts/verify.py`).

Earlier v1–v3 work evaluated cheaper/mid-tier models across ~50-file installs; Version 4 pivots away from older budget models to lean, tiered installs (~10–24 files) with selective on-demand skills (`release-review`, `release-readiness`, `ui-design`). The archived v3 evaluation, holdout study, and raw-run results live at pre-v4 commit `ce9ffe2` (`git show ce9ffe2:maintainer/EVALUATION.md` and `ce9ffe2:maintainer/HOLDOUT_RESULTS.md`) and in the `eval-2026-11-04` / `holdout-2026-11-06` GitHub releases.

---

## When to adopt this guidance (and when not to)

### Adopt it when:
- **You run frontier supervisors with specialist subagents or multiple agent CLIs.** [`AGENTS.md`](../AGENTS.md) and [`PROJECT_PROFILE.md`](../PROJECT_PROFILE.md) give Claude Code, Codex, Antigravity, and Copilot CLI a single instruction source, selective skill wrappers, and matching destructive-command and secret guardrails while preserving project specialist agents.
- **You need deterministic mechanical checks instead of prose reminders.** `scripts/verify.py --verify` runs your project's configured gates and prints a verbatim `Verification:` summary line, preventing unverified-work claims, enforcing document line/date budgets, and checking `CLAUDE.md` shims and link integrity.
- **Your project has real operational, hardware, or compliance rules.** Separation of duties (`S14`), ticket traceability (`S13`), vulnerable-dependency reporting (`S15`), batched review deployments from committed revisions (`S12`), embedded hardware rules, and vendor acceptance testing (`S16`, `S17`) require explicit policy and guardrails.

### Skip or strip it down when:
- **You are building a quick throwaway script or solo experiment** where a short project `README.md` and a test runner are enough. If you adopt the package there, use `--tier prototype` (`core` only, 10 files).

### Recommended adoption path

1. **Install only the tier and agent tools you need:**
   ```sh
   python3 manage.py --install /path/to/project --tier internal --tools claude,codex --dry-run
   python3 manage.py --install /path/to/project --tier internal --tools claude,codex
   ```
   Start at `prototype` (`core` files only) or `internal` (adds `DESIGN_DOC.md`, `OPEN_WORK.md`, and runbooks). Move up to `production` or `enterprise` only when the project needs release readiness records, verification matrices, or supply-chain and role gates.
2. **Wire up `--verify` immediately:** Fill in the command inventory in `PROJECT_PROFILE.md` with your real test and lint commands so `python3 scripts/verify.py --verify` runs them.
3. **Use `--plan-upgrade` and `--check-upgrade` when updating later:** Never overwrite a configured project with `--install --force`; let the upgrade planner diff your local customizations against the baseline commit recorded in `.guidance.json` (or legacy `PACKAGE_MANIFEST.json` for v2/v3 projects).

---

## Guide to files in `maintainer/`

| File or folder | Purpose |
|---|---|
| [SCENARIOS.md](SCENARIOS.md) | Active scenario catalog, pass criteria, and instructions for manual and automated runs |
| [RESULTS.md](RESULTS.md) | Clean v4 log of scenario runs (v1–v3 archive at commit `ce9ffe2`) |
| [AUDIT.md](AUDIT.md) | Independent pre-release / consequential-merge audit checklist |
| [`run_scenario.py`](run_scenario.py) & [`scenarios.json`](scenarios.json) | Reproducible scenario fixture builder and machine-readable scenario definitions |
| [`test_install.py`](test_install.py) | Deterministic test suite for `--install`, tiers, tools, budgets, `--verify`, `agent-team` interop, and upgrades |
| [`roles/`](roles/) | Maintainer team role definitions (`guidance-editor`, `tooling-engineer`, `scenario-evaluator`, `guidance-auditor`) |
| [`harness/`](harness/) | Bubblewrap sandbox, multi-CLI runner (`run.py`), automatic scorer (`score.py`), and unit tests (`test_score.py`) |
