# Changelog

User-facing release history for the Reusable Project Guidance template package. For detailed maintainer entries, see [MAINTAINING.md](MAINTAINING.md).

## 4.0 (2026-11-22)

- **Frontier supervisor redesign & leaner `AGENTS.md`:** Focused `AGENTS.md` on universal/supervisor judgment, consolidated specialist subagent integration with `agent-team`, retired overlapping process docs (`DESIGN_DOC.md` absorbed `DOMAIN_RULES.md`, `docs/UI.md` consolidated UI/accessibility guidance), and introduced selective `SKILL.md` wrappers (`release-review`, `release-readiness`, opt-in `ui-design`).
- **Repo-side management & slim project verifier:** Replaced in-project `check_package.py` + `PACKAGE_MANIFEST.json` with repository-side `manage.py` (`--install`, `--sync`, `--plan-upgrade`, `--check-upgrade`, `--all`, `--tools`) plus lightweight project-side `scripts/verify.py` and `.guidance.json`.
- **Stronger gate verification & Enterprise guardrails:** Added explicit `Gate` label checking (`Development`, `Release`, `Documentation`, `Manual`, `—`), strict Enterprise guardrail verification across Claude Code, Codex, and Copilot CLI (`gh pr merge` and `gh release create`), and safer default Copilot hooks (without `agentStop`).
- **v2/v3 → v4 migration:** Added `--plan-upgrade` / `--check-upgrade` to migrate `PACKAGE_MANIFEST.json` layouts to `.guidance.json`, auto-remove untouched retired files, route modified retired files for review, and preserve custom `AGENTS.md` sections (`agent-team`). See [README.md](README.md) and [docs/procedures/upgrade-guidance.md](docs/procedures/upgrade-guidance.md).

## 3.0.2

- Version 3 maintenance release: guardrails no longer block `git push` (on branch `release/3.0`).

## 3.0.1 / 3.0

- Tiered module installation (`prototype`, `internal`, `production`, `enterprise`) and computed verification (`--verify`).

## 2.0

- Agent-neutral guidance layout with per-tool adapters for Claude Code, Codex, Antigravity, and Copilot CLI.

## 1.0

- Initial Claude Code project guidance template.
