# Reusable project guidance

This package gives coding agents instructions, policies, templates and procedures for starting a new project. It works with Codex, Antigravity, Claude Code and any other agent that reads `AGENTS.md`. It is a starting point for a project. It is not evidence of implementation, testing, deployment authorization or release acceptance.

## Start here
1. **Install into the new repository.** Run:

   ```sh
   python3 check_package.py --install /path/to/project
   ```

   This copies only the packaged files listed in `PACKAGE_MANIFEST.json`. It skips any file that already exists, and lists those files so you can merge them by hand. `--force` overwrites them; review the result before committing. Maintainer-only files are never copied.
2. **Bootstrap with your agent.** Ask it to "bootstrap the project guidance". The agent follows the [bootstrap procedure](docs/procedures/bootstrap-project.md): it inspects the repository, proposes the profile values in [PROJECT_PROFILE.md](PROJECT_PROFILE.md), asks you only the decisions it cannot infer, and records what you adopt.
3. **Choose a tier.** The tier table in PROJECT_PROFILE.md sets which gates apply by default: Prototype, Internal tool or Production service. A small tool does not inherit production ceremony, and a production service does not lose it.
4. **Adopt only the profiles you need.** [Server-rendered web](profiles/SERVER_RENDERED_WEB.md) and [production operations](profiles/PRODUCTION_OPERATIONS.md) are optional and bind only once adopted. Exclude guides that do not apply, such as the UI guides for a non-UI project, and record the rationale.
5. **Fill in the rest as work proceeds.** `python3 check_package.py --require code` must pass before product code is written. `--require release` must pass before the first release. Registers start empty; never copy results or approvals from another project.

## Agent support
[AGENTS.md](AGENTS.md) is the single instruction source. Each tool gets a thin adapter:

| Agent | Instructions | Procedures as skills | Command guardrails |
|---|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills/` | `.codex/rules/guidance.rules` (trusted projects) |
| Antigravity | `AGENTS.md` | `.agents/skills/` | User-level only: app permission settings, or CLI `~/.gemini/antigravity-cli/settings.json` |
| Claude Code | `CLAUDE.md`, which imports `AGENTS.md` | `.claude/skills/` | `.claude/settings.json` |
| Other agents | `AGENTS.md` | Read `docs/procedures/` directly | Optional git hook in `scripts/hooks/` |

[docs/AGENT_TOOLS.md](docs/AGENT_TOOLS.md) explains each adapter, how to keep them in sync, and how to add a tool.

## What is included
| Kind | Files | Use |
|---|---|---|
| Entry and adapters | `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `.codex/` | Agent entry points. Skill wrappers are generated; never edit them by hand |
| Policy | `docs/ARCHITECTURE.md`, `CHANGE_WORKFLOW.md`, `DOCUMENTATION.md`, `TESTING_SPEC.md`, `SECURITY_PRODUCTION_SPEC.md`, `UX_DESIGN_SPEC.md`, `UI_PATTERNS.md`, `DATA_PORTABILITY.md`, `AGENT_TOOLS.md` | Copy as-is; change only by owner decision |
| Template | `PROJECT_PROFILE.md`, `DESIGN_DOC.md`, `docs/DOMAIN_RULES.md`, `BRANDING.md`, `RUNBOOKS.md`, review and handoff templates, ADR template | Fill in with project values |
| Register | `docs/OPEN_WORK.md`, `VERIFICATION_MATRIX.md`, `PRODUCTION_READINESS.md`, `ROADMAP.md`, `SOURCES.md` | Start empty; append as work happens |
| Procedure | `docs/procedures/` | Bootstrap, final audit, release readiness; exposed as skills |
| Profile | `profiles/` | Optional stack or tier rules |
| Tooling | `check_package.py`, `PACKAGE_MANIFEST.json`, `scripts/hooks/pre-commit` | Install, integrity and placeholder checks |

The instructions are language- and host-neutral. No application routes, entities, data model, credentials, host addresses, product backlog, production results or historical approvals are carried over. Choose your own workload sizes, budgets, soak duration, retention, recovery objectives and supported environments; no inherited number is a universal requirement.

## Checker
`check_package.py` detects its mode automatically:
- **Template mode** applies when `MAINTAINING.md` is present.
- **Project mode** applies after installation.

| Command | Effect |
|---|---|
| `python3 check_package.py` | Checks internal links, generated adapters and nested instruction shims. In template mode it also checks manifest hashes, unlisted files and empty registers. In project mode it reports remaining placeholders by stage |
| `--require code` / `--require release` | Fails if placeholders remain at that stage |
| `--install DIR [--force]` | Copies the packaged files into a project |
| `--sync-adapters` | Regenerates the skill wrappers from `docs/procedures/` |
| `--update-manifest` | Refreshes manifest hashes after a reviewed edit (template mode) |

To run the checks on every commit, for any agent or person, enable the optional hook with `git config core.hooksPath scripts/hooks`.
