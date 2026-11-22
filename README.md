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

   Running `--install` again never overwrites existing files without `--force`; it writes `.guidance.json`, strips optional sections that do not apply (such as `## Release qualification profile` below `production`), and preserves custom sections appended to `AGENTS.md` (such as an `agent-team` install).

2. **Add specialist subagents (recommended):** install [agent-team](https://github.com/dsscheib/agent-team) (`bootstrap.py --project /path/to/project --with-agents-md --apply`) in either order before or after this installer. `manage.py --sync DIR` and `--plan-upgrade` preserve sections appended at the end of `AGENTS.md` and leave project specialist files in `.{claude,codex,github,agents}/agents` alone.

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

## Tiers and gate expectations

Choose the lowest tier whose risks match your project:

| Gate | `prototype` (small / personal experiments) | `internal` (trusted users, data that matters) | `production` (external users or uptime commitments) | `enterprise` (roles, traceability, supply chain) |
|---|---|---|---|---|
| Profile + Command inventory | Required | Required | Required | Required |
| Automated tests + static checks | Smoke tests | Unit/integration + static | Full suite + concurrency | Full + CI receipts |
| Recovery / backup drill | Not required | Before relying on persistent data | Release gate (isolated fixtures) | Release gate + retention evidence |
| Pre-release review | Optional (`--features release-review`) | Optional (`--features release-review`) | Included (`release-review` skill) | Included (`release-review` skill) |
| Readiness + verification matrix | Not required | Not required | Included (`release-readiness` skill) | Included + named role approval |
| Dependency audit, SBOM, license check | Not required | Report known risks | Report gaps; release gate if tooling exists | Release gate rows added (`enterprise`) |

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
- **Copilot CLI:** `AGENTS.md`, `.github/hooks/guidance.json` + `guidance_guardrail.py`, `.agents/skills/`, `.claude/skills/`.

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
