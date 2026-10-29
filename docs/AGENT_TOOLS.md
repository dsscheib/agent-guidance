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
- **Don't add a second always-on file.** Do not add `GEMINI.md`, `.github/copilot-instructions.md` or an `always_on` Antigravity rule that repeats AGENTS.md. Antigravity and Copilot CLI already read AGENTS.md, and a copy would drift. Copilot CLI also loads the `CLAUDE.md` shim; the docs do not say whether it expands `@AGENTS.md`, and either way the shim adds no rule of its own.
- **Generate the skill wrappers.** Edit `docs/procedures/<name>.md`; its YAML frontmatter needs `name` and `description`, and the description says when to use the procedure. Then run `python3 check_package.py --sync-adapters`. The checker fails when the wrappers are stale. The wrappers in every adapter directory are byte-identical, because Copilot CLI loads more than one directory and does not document which copy of a duplicate name wins.
- **Shim every nested AGENTS.md.** For a subdirectory that needs its own instructions, add `<dir>/AGENTS.md`, which Codex, Antigravity and Copilot CLI read, and a sibling `<dir>/CLAUDE.md` containing `@AGENTS.md`. The checker fails if the shim is missing.
- **Mirror only the authorization rules in guardrails.** Guardrails mirror AGENTS.md rules 2, 3 and 9: remote and destructive git operations ask for confirmation, and secret files are unreadable to Claude Code and Copilot CLI. Align them with the adopted git policy in PROJECT_PROFILE.md. A guardrail may be looser than the default only when the policy allows it. Guardrails are defense in depth, not the source of the rule.

## Shipped guardrails
- **`.claude/settings.json`** asks before `git push`, `git reset --hard`, `git clean`, `git branch -D`, `git rebase` and `git checkout -- .`. It denies reading `.env` and `.env.*.local` files. Personal overrides belong in `.claude/settings.local.json`, which should not be committed.
- **`.codex/rules/guidance.rules`** prompts for the same git commands. Codex loads it only after you trust the project.
- **`.github/hooks/guidance.json`** runs `.github/hooks/guidance_guardrail.py` before each Copilot CLI `bash`, `powershell` and `view` call. The script asks before the same git commands, including inside compound commands and after `git -C <dir>`, and denies viewing `.env` and `.env.*.local` files. Every other call keeps Copilot's normal permission flow. It needs `python3` (`python` under PowerShell), which the package checker already requires. Limits:
  - Copilot applies a folder's configuration only after the folder is trusted. The hooks docs don't say this; it comes from the `--trust-folder` entry in `copilot --help`.
  - With no one to approve, `ask` becomes `deny`. That happens in autopilot mode, under the cloud agent, and in non-interactive `copilot -p` runs.
  - A hook that times out lets the call through.
  - Like the other guardrails, it matches command text, so indirection such as an alias or a script that pushes is not caught.
- **Antigravity** reads no command policy from the repository, so each person configures it once per machine. Rules use `command(<prefix>)` and are evaluated deny > ask > allow. The app and the CLI are configured separately; set up both if you use both.
  - **App:** in Settings > General > Global Permissions, choose a review-requiring preset, or add ask rules for the commands above. Under the app's Default preset, commands with no rule run in a sandbox without asking.
  - **CLI:** add an `ask` list to `~/.gemini/antigravity-cli/settings.json`, or add the rules interactively with `/permissions`:

    ```json
    {
      "permissions": {
        "ask": [
          "command(git push)",
          "command(git reset --hard)",
          "command(git clean)",
          "command(git branch -D)",
          "command(git rebase)",
          "command(git checkout --)"
        ]
      }
    }
    ```

    The official docs show the rule syntax and the `ask`/`allow`/`deny` arrays; the enclosing `permissions` key comes from community examples. If the CLI reports a malformed settings file at startup, use `/permissions` instead.
  - **Limits:**
    - A command containing `$(...)` turns off prefix matching, so only an exact rule matches it.
    - On Windows, subcommands need `command(regex:…)` rules.
    - `--dangerously-skip-permissions` bypasses every rule.

    The git hook and AGENTS.md rule 3 remain the backstop.
- **`scripts/hooks/pre-commit`** is agent-neutral and enabled with `git config core.hooksPath scripts/hooks`. It runs `check_package.py`, which blocks commits with broken internal links, stale skill wrappers or missing shims.

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

Checked 2026-10-29 against Copilot CLI 1.0.105:
- Copilot CLI custom instructions: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>
- Copilot CLI skills: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills>
- Copilot CLI hooks reference: <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference>
- Copilot CLI hooks how-to, including the `toolArgs` sample: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks>
