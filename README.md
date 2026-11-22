# Reusable project guidance (v4)

Lean project instructions, tiers, templates, and deterministic verification built for strong frontier supervisor models coordinating `agent-team` specialists. It works with Claude Code, Codex, Antigravity, Copilot CLI, and any agent that reads `AGENTS.md`. It is a starting point for a project—not evidence of implementation, testing, deployment authorization, or release acceptance.

## Quick start

**Existing repository, or upgrading from v2/v3?** Do not overwrite it with `--install`. From a checkout of this repository, read [the upgrade procedure](docs/procedures/upgrade-guidance.md) and run `python3 manage.py --plan-upgrade /path/to/project --patch /tmp/upgrade.patch`.

For a new project:

1. **Install the tier and features your project needs** (from this checkout):

   ```sh
   python3 manage.py --install /path/to/project --tier internal --dry-run
   python3 manage.py --install /path/to/project --tier internal
   ```

   Optional flags:
   - `--features release-review,ui,ui-design,stack-go,stack-rust,embedded` — opt-in modules (`release-review` adds the deep pre-release audit skill to `prototype`/`internal`; `ui` adds `docs/UI.md`; `ui-design` adds the interactive `ui-design` skill on top of `ui`).
   - `--tools claude,codex,antigravity,copilot` — install adapters and guardrails only for the agent CLIs you use (default: all).
   - `--all` — install all standard v2/v3-equivalent modules (everything except `enterprise` and `ui-design`).

   Fresh installs omit optional sections that do not apply (such as `## Release qualification profile` below `production`). Running `--install` again never overwrites customized files without `--force`; it updates `.guidance.json`, refreshes generated tables inside `AGENTS.md`, adds applicable sections and inventory rows in `PROJECT_PROFILE.md`, updates unmodified guardrail files when modules change, and preserves custom sections appended to `AGENTS.md` (such as an `agent-team` install).

2. **Add specialist subagents (recommended):** install [agent-team](https://github.com/dsscheib/agent-team) (`bootstrap.py --project /path/to/project --with-agents-md --apply`) after this installer so `manage.py --install` writes the template `AGENTS.md` first and `agent-team` appends to it (if `agent-team` runs first and writes `AGENTS.md`, `--install` keeps that existing file and asks you to merge by hand or rerun with `--force` before re-applying `--with-agents-md`). `manage.py --sync DIR` and `--plan-upgrade` preserve sections appended at the end of `AGENTS.md` and leave project specialist files in `.{claude,codex,github,agents}/agents` alone.

3. **Fill [PROJECT_PROFILE.md](PROJECT_PROFILE.md):** ask your agent to inspect the repo, fill inferable values above `## Command inventory` as `Proposed — inferred from <file>`, mark inapplicable inventory rows `Proposed: Not applicable: <reason>`, ask you the remaining decisions in one batch, and confirm:

   ```sh
   python3 scripts/verify.py --require code
   ```

4. **Verify changes before handoff:**

   ```sh
   python3 scripts/verify.py --verify            # development gates
   python3 scripts/verify.py --verify docs       # docs-only changes
   python3 scripts/verify.py --verify release    # release candidates
   ```

## Choosing a tier

Pick the lowest tier whose risks match your project; see [Tier gate expectations](docs/procedures/release-readiness.md#tier-gate-expectations) for the full gate matrix.

| Tier | Intended use | Included modules & extras |
|---|---|---|
| `prototype` | Small / personal experiments | Core guidance, verifier, open-work register (`--features release-review` optional) |
| `internal` | Trusted users, data that matters | Adds `DESIGN_DOC.md` and `docs/RUNBOOKS.md` (`--features release-review` optional) |
| `production` | External users or uptime commitments | Adds `release-review`, `release-readiness`, readiness & verification registers |
| `enterprise` | Roles, traceability, supply chain | Adds `docs/ENTERPRISE.md`, PR template, CI/supply-chain gate rows, strict guardrails |

## Agent support and selective skills

[AGENTS.md](AGENTS.md) holds the compact universal and supervisor rules (plus generated routing and on-demand skill rows for installed modules). Always-on `AGENTS.md` does not load routine procedure skills; only explicit heavy workflows expose `SKILL.md` wrappers when their module is installed:

| Skill | Installed with | Purpose |
|---|---|---|
| `release-review` | `production`, `enterprise`, or `--features release-review` | Deep read-only pre-release audit across risk areas and subagents |
| `release-readiness` | `production`, `enterprise` | Assembling gate evidence and recording candidate readiness |
| `ui-design` | `--features ui-design` | Intentional visual direction, typography, layout rhythm, and craft polish |

Per-tool adapters installed inside projects:
- **Claude Code:** `CLAUDE.md` (`@AGENTS.md`), `.claude/settings.json` (git/PR guardrails + `.env` read deny), `.claude/skills/`.
- **Codex:** `AGENTS.md`, `.codex/rules/guidance.rules`, `.agents/skills/`.
- **Antigravity:** `AGENTS.md`, `.agents/skills/` (user-level command rules live outside repos).
- **Copilot CLI:** `AGENTS.md`, `.github/hooks/guidance.json` + `guidance_guardrail.py`, `.agents/skills/` (validating/syncing existing generated `.claude/skills/` wrappers when present).

## Commands

**In an installed project** (`scripts/verify.py`, zero repo tooling bloat):
- `python3 scripts/verify.py` — checks links, `CLAUDE.md` shims, selective skill wrappers, document budgets (`PROJECT_PROFILE.md` <= 250 lines, `docs/OPEN_WORK.md` <= 150 lines, pointer files <= 10 lines), enterprise guardrails/notes, and placeholder counts.
- `python3 scripts/verify.py --require code` / `--require release` — fails if placeholders remain at that stage.
- `python3 scripts/verify.py --verify [development|docs|release]` — runs configured command-inventory gates (`timeout 60m` overrides `--timeout 900`; `--receipt FILE` writes JSON) and prints the verbatim `Verification:` summary line.

**From this template repository** (`manage.py`):
- `python3 manage.py` — validates templates, links, adapters, budgets, manifest SHA-256 hashes, `test_install.py`, harness scorer tests, and `run_scenario.py --check`.
- `python3 manage.py --install DIR --tier T [--features ...] [--tools ...] [--dry-run] [--force]` — installs modules into a project and writes `.guidance.json`.
- `python3 manage.py --sync [DIR]` — regenerates `AGENTS.md` generated tables, selective `SKILL.md` wrappers (skipping repo-only procedures), and maintainer role agents (in template mode).
- `python3 manage.py --plan-upgrade DIR [--patch FILE]` — plans safe upgrades from v2/v3 (`PACKAGE_MANIFEST.json`) or v4 (`.guidance.json`), auto-removing untouched retired v3 docs and flagging customized ones for review.
- `python3 manage.py --check-upgrade DIR [--since REV]` — verifies open items, deployed revisions, and local edits survived an upgrade.
- `python3 manage.py --update-manifest` — refreshes `PACKAGE_MANIFEST.json` entries and hashes (template mode).

To run checks on every commit, enable the hook: `git config core.hooksPath scripts/hooks`.

## Further reading and benchmark results

- **Adoption guide & v4 overview:** see [maintainer/README.md](maintainer/README.md) for when to adopt (or skip) this package, recommended tier adoption steps, and a map of repository tooling.
- **Evaluation results:** see [maintainer/RESULTS.md](maintainer/RESULTS.md) for the no-guidance vs. v4 benchmark summary and full per-run log across Claude Code, Codex, and Antigravity.
