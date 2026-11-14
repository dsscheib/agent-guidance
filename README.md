# Reusable project guidance

This package gives coding agents instructions, policies, templates and procedures for starting a new project. It works with Codex, Antigravity, Claude Code, Copilot CLI and any other agent that reads `AGENTS.md`. It is a starting point for a project. It is not evidence of implementation, testing, deployment authorization or release acceptance.

**Evaluating whether to use this package?** Before adopting it, read the [testing summary and adoption guide](maintainer/README.md) for what 2,000+ benchmark and blinded holdout runs showed about where this guidance helps, where it is overkill, and which tier to pick.

## Start here
**Existing project, or one that adopted an earlier version?** Do not use `--install`. Ask your agent to "upgrade the project guidance from `<path to this checkout>`". It follows the [upgrade procedure](docs/procedures/upgrade-guidance.md): it maps each upstream change onto the project's own documents, asks you the policy questions, and records the source commit. The steps below are for new repositories.

1. **Install into the new repository.** Pick the project's tier, and any features, then run:

   ```sh
   python3 check_package.py --install /path/to/project --tier internal --features ui --dry-run   # preview
   python3 check_package.py --install /path/to/project --tier internal --features ui
   ```

   Tiers are `prototype`, `internal`, `production` and `enterprise` (step 3 explains them); features are `ui`, `data`, `stack-go`, `stack-rust` and `embedded` (firmware and electronics design files). Without `--tier`, nothing is installed: the command lists the tiers and what each adds. `--dry-run` lists the modules and files it would copy and writes nothing. `--all` instead of `--tier` installs every module except Enterprise, as version 2 did. `--tools claude,codex,antigravity,copilot` names the agents the project uses, and only their adapters and guardrails are installed and checked; without it every tool's files are installed. Running `--install` again with a higher tier or another feature adds the missing modules without touching existing files; a rerun without `--tier` keeps the project's tier. The Enterprise tier adds `docs/ENTERPRISE.md` (roles, traceability, CI evidence, supply chain), a pull-request template and three release gates in the command inventory.

   This copies only the packaged files listed in `PACKAGE_MANIFEST.json`, and records this checkout's commit as `installed_from` in the copied manifest so later upgrades know where to start. It skips any file that already exists, and lists those files so you can merge them by hand. `--force` overwrites them; review the result before committing. Maintainer-only files are never copied.
2. **Bootstrap with your agent.** Ask it to "bootstrap the project guidance". The agent follows the [bootstrap procedure](docs/procedures/bootstrap-project.md): it inspects the repository, proposes the profile values in [PROJECT_PROFILE.md](PROJECT_PROFILE.md), asks you only the decisions it cannot infer, and records what you adopt.
3. **Confirm the tier.** The tier table in PROJECT_PROFILE.md sets which gates a release needs: Prototype, Internal, Production service or Enterprise product. Each change and each review deployment runs a smaller, fixed set of development gates. A small tool does not inherit production ceremony, and a production service does not lose it.
4. **Adopt only the profiles you need.** Server-rendered web ([Go](profiles/SERVER_RENDERED_WEB_GO.md) or [Rust](profiles/SERVER_RENDERED_WEB_RUST.md)), [embedded firmware and hardware](profiles/EMBEDDED_FIRMWARE.md) and [production operations](profiles/PRODUCTION_OPERATIONS.md) are optional and bind only once adopted. Exclude guides that do not apply, such as the UI guides for a non-UI project, and record the rationale.
5. **Fill in the rest as work proceeds.** `python3 check_package.py --require code` must pass before product code is written. `--require release` must pass before the first release. Registers start empty; never copy results or approvals from another project.

## Agent support
[AGENTS.md](AGENTS.md) is the single instruction source. Each tool gets a thin adapter:

| Agent | Instructions | Procedures as skills | Command guardrails |
|---|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills/` | `.codex/rules/guidance.rules` (trusted projects) |
| Antigravity | `AGENTS.md` | `.agents/skills/` | User-level only: app permission settings, or CLI `~/.gemini/antigravity-cli/settings.json` |
| Claude Code | `CLAUDE.md`, which imports `AGENTS.md` | `.claude/skills/` | `.claude/settings.json` |
| Copilot CLI | `AGENTS.md` | `.agents/skills/` and `.claude/skills/` | `.github/hooks/guidance.json` (trusted folders); optional user-level stop hook in `~/.copilot/hooks/` ([setup](docs/AGENT_TOOLS.md#shipped-guardrails)) |
| Other agents | `AGENTS.md` | Read `docs/procedures/` directly | Optional git hook in `scripts/hooks/` |

**Agent teams.** This package installs no specialist agents. A project can add its own team of project-local specialist agents, written by hand or with a separate team installer; the checker leaves agent files it did not generate alone. Anecdotal evidence suggests that running agent teams can also improve the quality of agentic development and workflows. Whichever agents do the work, the [delegation rules](docs/CHANGE_WORKFLOW.md#delegating-work) apply.

[docs/AGENT_TOOLS.md](docs/AGENT_TOOLS.md) explains each adapter, how to keep them in sync, and how to add a tool.

## What is included
| Kind | Files | Use |
|---|---|---|
| Entry and adapters | `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `.codex/`, `.github/hooks/` | Agent entry points. Skill wrappers are generated; never edit them by hand |
| Policy | `docs/ARCHITECTURE.md`, `CHANGE_WORKFLOW.md`, `DOCUMENTATION.md`, `TESTING_SPEC.md`, `SECURITY_PRODUCTION_SPEC.md`, `UX_DESIGN_SPEC.md`, `UI_PATTERNS.md`, `DATA_PORTABILITY.md`, `AGENT_TOOLS.md` | Copy as-is; change only by owner decision |
| Template | `PROJECT_PROFILE.md`, `DESIGN_DOC.md`, `docs/DOMAIN_RULES.md`, `BRANDING.md`, `RUNBOOKS.md`, review and handoff templates, ADR template | Fill in with project values |
| Register | `docs/OPEN_WORK.md`, `VERIFICATION_MATRIX.md`, `RELEASE_NOTES.md`, `PRODUCTION_READINESS.md`, `ROADMAP.md`, `SOURCES.md` | Start empty. OPEN_WORK and the matrix are updated in place; RELEASE_NOTES gets one short entry per deployment |
| Procedure | `docs/procedures/` | Bootstrap, upgrade, final audit, release readiness; exposed as skills |
| Profile | `profiles/` | Optional stack or tier rules |
| Tooling | `check_package.py`, `PACKAGE_MANIFEST.json`, `scripts/hooks/pre-commit` | Install, integrity and placeholder checks |

The instructions are language- and host-neutral. No application routes, entities, data model, credentials, host addresses, product backlog, production results or historical approvals are carried over. Choose your own workload sizes, budgets, soak duration, retention, recovery objectives and supported environments; no inherited number is a universal requirement.

## Checker
`check_package.py` detects its mode automatically:
- **Template mode** applies when `MAINTAINING.md` is present.
- **Project mode** applies after installation.

| Command | Effect |
|---|---|
| `python3 check_package.py` | Checks internal links, generated adapters, nested instruction shims and the [document budget](docs/DOCUMENTATION.md#document-budget) (profile and status sizes, no dated profile sections, pointer-only tool instruction files). In template mode it also checks manifest hashes, unlisted files, empty registers and the maintainer scenario fixtures. In project mode it reports remaining placeholders by stage, and lists absent packaged files unless the profile's Excluded guidance row names them in backticks |
| `--require code` / `--require release` | Fails if placeholders remain at that stage |
| `--verify [release]` | Runs the command-inventory rows marked as gates and prints a computed `Verification:` status for agents to quote, names the project's dependency files when the dependency audit is a gap, and fails a rename-only change that also edits guidance documents beyond the rename; `--receipt FILE` saves it as JSON. `--timeout S` limits each gate (default 900 seconds); a gate whose Gate cell says, for example, `timeout 60m` gets that limit instead |
| `--install DIR --tier T [--features F] [--tools T] [--dry-run] [--force]` | Copies the core plus the modules for a tier and features into a project, with the adapters and guardrails of the named agent tools only (default every tool); rerun to add modules or tools. Without `--tier` it copies nothing and lists the tiers; `--all` instead of `--tier` gives the version 2 set (every module except Enterprise); `--dry-run` previews |
| `--plan-upgrade DIR [--patch FILE]` | Run from a newer checkout. Compares a package-layout project with the release it installed and with this checkout, and lists each packaged file as replace, add, merge (clean three-way merge that keeps local changes), conflict or review (templates, registers and the profile the project filled in). Writes nothing in the project; `--patch` saves the replace, add, merge and remove changes and the new manifest as a `git apply` patch outside it |
| `--check-upgrade DIR [--since REV]` | After applying an upgrade, compares the project with its pre-upgrade commit (default `HEAD`) and fails if an open item disappeared or was closed, a deployed revision is no longer in any document, a local change to a packaged policy, procedure or tool file is gone, a deleted file is still named by code, or merge conflict markers remain |
| `--sync-adapters` | Regenerates the skill wrappers from `docs/procedures/`, and the AGENTS.md routing and procedure tables for the installed modules |
| `--update-manifest` | Refreshes manifest hashes after a reviewed edit (template mode) |

To run the checks on every commit, for any agent or person, enable the optional hook with `git config core.hooksPath scripts/hooks`.
