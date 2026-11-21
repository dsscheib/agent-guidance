# Agent tool adapters

Repository-only reference explaining how guidance reaches each coding CLI, how selective skills and guardrails work, and how tool configuration stays consistent. Recheck [sources](#sources) before changing tool-specific claims.

## Principle: one source, thin adapters
[AGENTS.md](../AGENTS.md) and the documents it routes to hold every rule. Tool-specific files only:
- point to `AGENTS.md` (`CLAUDE.md`),
- expose explicit selective procedures (`release-review`, `release-readiness`, `ui-design`) as skills, or
- mechanically enforce destructive-command and secret guardrails that `AGENTS.md` states.

Never put a unique rule only in a tool adapter.

## What each agent loads

| Concern | Codex | Antigravity | Claude Code | Copilot CLI | Other agents |
|---|---|---|---|---|---|
| Always-on instructions | `AGENTS.md` at root and nested dirs down to cwd (`project_doc_max_bytes` cap) | `AGENTS.md` per dir plus `.agents/rules/*.md` | `CLAUDE.md` importing `@AGENTS.md` | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` combined | `AGENTS.md` |
| Selective on-demand skills | `.agents/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` | Both `.agents/skills/` and `.claude/skills/` | Read `docs/procedures/` |
| Command guardrails | `.codex/rules/*.rules` (`prefix_rule`) when trusted | User-level settings only (app preset or `~/.gemini/antigravity-cli/settings.json`) | `permissions` in `.claude/settings.json` | `preToolUse` in `.github/hooks/*.json` when trusted | Optional `scripts/hooks/pre-commit` |

## Rules for maintaining adapters
- **Keep AGENTS.md lean.** Template `AGENTS.md` ceiling is 6,800 bytes (installed tiers run ~3–5 KB). Move detailed playbooks into routed files or on-demand procedures.
- **Don't add a second always-on file.** Never duplicate `AGENTS.md` in `GEMINI.md` or `.github/copilot-instructions.md` (`scripts/verify.py` fails if either exceeds a 10-line pointer to `AGENTS.md`).
- **Generate selective skill wrappers only for heavy procedures.** Only packaged procedures (`release-review`, `release-readiness`, `ui-design`) generate `SKILL.md` wrappers; repo-only procedures like `upgrade-guidance.md` do not. Edit `docs/procedures/<name>.md` and run `python3 manage.py --sync [DIR]`. Wrappers in `.agents/skills/` and `.claude/skills/` are byte-identical so Copilot CLI never sees divergent copies.
- **Install only adopted tools.** `manage.py --install DIR --tools claude,codex` records `installed.tools` in `.guidance.json`. `scripts/verify.py`, `--sync DIR`, and `--plan-upgrade` ignore unconfigured tools and only enforce the `CLAUDE.md` shim rule when Claude Code is active.
- **Shim every nested AGENTS.md.** Any `<dir>/AGENTS.md` needs a sibling `<dir>/CLAUDE.md` containing `@AGENTS.md` when Claude Code is enabled.
- **Mirror only destructive git, secret, and Enterprise merge/publish rules in guardrails.** Pushes stay governed by `AGENTS.md` rather than static hooks; Enterprise adds `gh pr merge` and `gh release create` confirmation rules (`manage.py --install` and `scripts/verify.py` enforce those when `enterprise` is installed).

## Specialist agents
This package installs no specialist agents into projects (`agent-team` or hand-authored agents live in `.claude/agents/`, `.codex/agents/`, `.github/agents/`, `.agents/agents/`). Neither `scripts/verify.py` nor `manage.py --sync DIR` touches project agent files or sections appended below the generated markers in `AGENTS.md`. In this template repository only, `manage.py --sync` generates maintainer team files from `maintainer/roles/`.

## Shipped guardrails
- **`.claude/settings.json`** asks before `git reset --hard`, `git clean`, `git branch -D`, `git rebase`, `git checkout -- .`, and `gh pr review` (plus `gh pr merge` and `gh release create` at `enterprise`), and denies reading `.env` and `.env.*.local`. Personal overrides go in `.claude/settings.local.json` (git-ignored).
- **`.codex/rules/guidance.rules`** prompts for the same destructive git and PR commands when the repository is trusted.
- **`.github/hooks/guidance.json`** runs `.github/hooks/guidance_guardrail.py` on `preToolUse` (`bash`, `powershell`, `view`) with the same ask/deny lists (applies in trusted folders; `ask` becomes `deny` in unattended `-p` mode; indirection/aliases are out of scope).
- **Optional user-level Copilot stop hook (`.github/hooks/guidance_stop.py`).** Repository `.github/hooks/guidance.json` no longer ships `agentStop` by default (frontier models ask reliably when needed without extra stop-hook round trips). Users who want extra protection during upgrades or adoptions on weaker models can still reference `guidance_stop.py` from `~/.copilot/hooks/guidance.json`.
- **Antigravity** configures command rules once per user (Settings > General > Global Permissions in the app, or `permissions.ask` in `~/.gemini/antigravity-cli/settings.json` for CLI). Note: command substitutions `$(...)` bypass prefix matching.
- **`scripts/hooks/pre-commit`** runs `python3 scripts/verify.py` inside installed projects or `python3 manage.py` inside the template repo when `git config core.hooksPath scripts/hooks` is enabled.

## Sources
Checked 2026-10-27 to 2026-11-05:
- Codex skills & rules: <https://learn.chatgpt.com/docs/build-skills>, <https://learn.chatgpt.com/docs/agent-configuration/rules>
- Antigravity rules, permissions & skills: <https://antigravity.google/docs/rules>, <https://antigravity.google/docs/permissions?tab=cli>, <https://codelabs.developers.google.com/antigravity-cli-hands-on>, <https://codelabs.developers.google.com/getting-started-with-antigravity-skills>
- Antigravity CLI 1.4.12 (`~/.gemini/antigravity-cli/settings.json` `permissions.ask` precedence verified 2026-11-05)
- Claude Code: <https://docs.claude.com/en/docs/claude-code>
- Copilot CLI 1.0.105 custom instructions, skills & hooks: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>, <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills>, <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference>
