# Agent tool adapters

Kind: Policy. This document explains how the guidance reaches each coding agent and how to keep the per-tool files consistent. Tool behavior changes over time, so recheck the [sources](#sources) when upgrading and record changed claims in [SOURCES.md](SOURCES.md).

## Principle: one source, thin adapters
[AGENTS.md](../AGENTS.md) and the documents it routes to hold every rule. Tool-specific files must do only one of three things:
- point to AGENTS.md,
- expose a procedure from `docs/procedures/` as a skill,
- mechanically enforce a rule AGENTS.md already states.

Never put a rule only in an adapter, because the other agents would never see it.

## What each agent loads

| Concern | Codex | Antigravity | Claude Code | Copilot CLI | Other agents |
|---|---|---|---|---|---|
| Always-on instructions | `AGENTS.md` at the repo root and in nested directories down to the working directory. The combined size is capped by `project_doc_max_bytes` | `AGENTS.md` (or `GEMINI.md`) per directory, plus `.agents/rules/*.md` | `CLAUDE.md` per directory; ours contains `@AGENTS.md`, which imports this file | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` and `.github/copilot-instructions.md` from the repo root, the working directory and the directories between, all combined with no precedence order | `AGENTS.md` |
| On-demand procedures | Skills in `.agents/skills/<name>/SKILL.md` | Skills in `.agents/skills/<name>/SKILL.md` | Skills in `.claude/skills/<name>/SKILL.md` | Skills from both `.agents/skills/` and `.claude/skills/` (also `.github/skills/`) | Read `docs/procedures/*.md` |
| Command guardrails | `.codex/rules/*.rules` (`prefix_rule`), loaded only when the project's `.codex/` layer is trusted | User-level only, no repository file. App: permission preset in Settings (global, with per-project overrides). CLI: `permissions` in `~/.gemini/antigravity-cli/settings.json` | `permissions` in `.claude/settings.json` | `preToolUse` hooks in `.github/hooks/*.json`, loaded only for a trusted folder | Optional `scripts/hooks/pre-commit`, plus human review |

## Rules for maintaining adapters
- **Keep AGENTS.md small.** Every supported tool loads it on every session or turn. Aim to keep it under about 10 KB; move detail into routed documents and procedures. Antigravity's always-on content shares a token budget, and Codex truncates instructions beyond its byte cap.
- **Don't add a second always-on file.** Do not add `GEMINI.md`, `.github/copilot-instructions.md` or an `always_on` Antigravity rule that repeats AGENTS.md. Antigravity and Copilot CLI already read AGENTS.md, and a copy would drift. `check_package.py` fails when a `GEMINI.md` or `.github/copilot-instructions.md` holds more than a short pointer to AGENTS.md. Copilot CLI also loads the `CLAUDE.md` shim; the docs do not say whether it expands `@AGENTS.md`, and either way the shim adds no rule of its own.
- **Generate the skill wrappers.** Edit `docs/procedures/<name>.md`; its YAML frontmatter needs `name` and `description`, and the description says when to use the procedure. Then run `python3 check_package.py --sync-adapters`. The checker fails when the wrappers are stale. The wrappers in every adapter directory are byte-identical, because Copilot CLI loads more than one directory and does not document which copy of a duplicate name wins.
- **Install only the tools the project uses.** `check_package.py --install DIR --tools claude,codex` (any of `claude`, `codex`, `antigravity`, `copilot`) records the tools in `installed.tools` in the installed `PACKAGE_MANIFEST.json`. The checker, `--sync-adapters` and `--plan-upgrade` then ignore the other tools' adapters and guardrails, and the CLAUDE.md shim rule applies only with Claude Code. An install that recorded no tools keeps every tool's files. To drop a tool later, ask the owner, remove it from `installed.tools`, then delete its files.
- **Shim every nested AGENTS.md.** For a subdirectory that needs its own instructions, add `<dir>/AGENTS.md`, which Codex, Antigravity and Copilot CLI read, and a sibling `<dir>/CLAUDE.md` containing `@AGENTS.md`. The checker fails if the shim is missing.
- **Mirror only the authorization rules in guardrails.** Guardrails mirror AGENTS.md rules 2, 3 and 9: destructive git operations and approvals ask for confirmation, merges and releases do too in Enterprise projects, and secret files are unreadable to Claude Code and Copilot CLI. Align them with the adopted git policy in PROJECT_PROFILE.md. A guardrail may be looser than the default only when the policy allows it. Guardrails are defense in depth, not the source of the rule.
- **Pushes are left to rule 3, and merges and releases too outside Enterprise.** A guardrail matches command text, so it cannot tell an action the user asked for from one they did not: it asks either way, and where nobody can answer (unattended or print-mode runs) it refuses what the user explicitly requested. In the package's scenario runs the push rule refused many requested pushes and never stopped an unrequested one, because agents did not push unasked even without guidance; no agent merged or published unasked either. Enterprise projects keep the merge and release rules, because their policy reserves those actions for a person even when the user asks ([ENTERPRISE](ENTERPRISE.md#roles-and-separation-of-duties)); the installer writes them only when the Enterprise module is installed, and the checker fails an Enterprise project whose guardrails lack them. A project on another tier whose git policy reserves an action for a person can add its rule back: `Bash(git push:*)`, `Bash(gh pr merge:*)` or `Bash(gh release create:*)` in `.claude/settings.json`'s `ask` list, a prompt rule in `.codex/rules/guidance.rules`, and an entry in the Copilot guardrail's `ASK` or `GH_ASK` list.

## Specialist agents
The package installs no specialist agents. A project may keep its own in each tool's agents folder (`.claude/agents/`, `.codex/agents/`, `.github/agents/`, `.agents/agents/`), written by hand or by a separate team installer. The checker and `--sync-adapters` leave them alone: they touch only files that carry the "Generated by check_package.py" marker. Delegated work follows [CHANGE_WORKFLOW](CHANGE_WORKFLOW.md#delegating-work).

## Adding another agent
1. Confirm, from the vendor's documentation, which instruction file and skill directory the agent reads. Record the source and check date in SOURCES.md.
2. If it reads AGENTS.md, nothing else is needed for instructions. Otherwise add a one-line pointer file, as CLAUDE.md does.
3. If it supports `SKILL.md` skills in a new directory, add that directory to `adapters` in `PACKAGE_MANIFEST.json` and run `--sync-adapters`.
4. Add a column to the table above and update the README's agent table.

## Sources
Checked 2026-10-27:
- Codex skills: <https://learn.chatgpt.com/docs/build-skills>
- Codex rules: <https://learn.chatgpt.com/docs/agent-configuration/rules>
- Antigravity rules: <https://antigravity.google/docs/rules>
- Antigravity permissions, app and CLI tabs: <https://antigravity.google/docs/permissions?tab=cli>
- Antigravity CLI settings file and `/config` (codelab): <https://codelabs.developers.google.com/antigravity-cli-hands-on>
- Antigravity skills: <https://codelabs.developers.google.com/getting-started-with-antigravity-skills>
- Claude Code memory, skills and settings: <https://docs.claude.com/en/docs/claude-code>

Checked 2026-11-05 against Antigravity CLI 1.4.12: the `permissions` key and ask-before-allow precedence in `~/.gemini/antigravity-cli/settings.json`, by a live prompt (no published source).

Checked 2026-10-29 against Copilot CLI 1.0.105:
- Copilot CLI custom instructions: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>
- Copilot CLI skills: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills>
- Copilot CLI hooks reference: <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference>
- Copilot CLI hooks how-to, including the `toolArgs` sample: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks>
