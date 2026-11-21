---
name: upgrade-guidance
description: Adopt agent guidance into an existing project or upgrade an earlier v2/v3/v4 adoption cleanly without overwriting project work.
---
# Upgrade procedure

Repository-only playbook run from the `agent-guidance` checkout. Goal: apply upstream improvements cleanly onto an existing repository (whether v2/v3 using `PACKAGE_MANIFEST.json` or v4 using `.guidance.json`), preserving every open item, deployed revision, `agent-team` setup, and local rule.

## 0. Choose the path

| Situation | Path |
|---|---|
| Empty or new repository | Not this procedure. Run `python3 manage.py --install DIR --tier T` (add `--features release-review` or `ui-design` if wanted), then bootstrap [PROJECT_PROFILE.md](../../PROJECT_PROFILE.md). |
| Existing repo with no package install | **First adoption:** map the v4 concepts onto the repo's existing doc locations instead of dumping templates over existing files. |
| Earlier package install (`PACKAGE_MANIFEST.json` or `.guidance.json`) | **Upgrade:** use `--plan-upgrade` and `--check-upgrade` below. |

## 1. Inspect the project (read-only first)
Do steps 1–3 before modifying anything in the target repository; ask owner questions first and apply only after approval.
- Check `git status` and preserve uncommitted work.
- Check `.guidance.json` (v4) or `PACKAGE_MANIFEST.json` (v2/v3) for `installed_from.commit`, tier, modules, and tools.
- Map any existing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, and custom agent directories (`.claude/agents/`, `.codex/agents/`, `.github/agents/`, `.agents/agents/`).

## 2. Generate the upgrade plan
From the `agent-guidance` checkout:

```sh
python3 manage.py --plan-upgrade /path/to/project --patch /tmp/upgrade.patch
```

What `--plan-upgrade` does automatically:
- Writes nothing inside the target repo.
- Maps v3 modules (`production-ops`, `release` -> `release-review`, `release`; retired `data`, `team` dropped).
- Plans removal of legacy `PACKAGE_MANIFEST.json`, `check_package.py`, untouched retired v3 docs (`DOCUMENTATION.md`, `TESTING_SPEC.md`, `CHANGE_WORKFLOW.md`, etc.), and retired routine skill wrappers (`bootstrap-project`, `final-audit`, `upgrade-guidance`) while automatically adding `scripts/verify.py` and `.guidance.json`.
- Flags customized retired files or filled-in templates (`PROJECT_PROFILE.md`, `DESIGN_DOC.md`, `docs/OPEN_WORK.md`, etc.) as **review** or **conflict** so you never silently delete or overwrite project rules.
- Runs 3-way merge on `AGENTS.md` when both sides changed cleanly, keeping any appended sections (such as `agent-team` escalation blocks).

## 3. Present plan & ask owner in one batch
Show the plan summary, conflicts, and `review` items side-by-side in your reply with a concrete recommendation for each (for example, merging any local rule from an edited `docs/TESTING_SPEC.md` or `docs/CHANGE_WORKFLOW.md` into `PROJECT_PROFILE.md`, `DESIGN_DOC.md`, or `AGENTS.md` before deleting the retired file). Ask about tool selection (`--tools`), tier/features (`release-review`, `ui-design`), and whether to preserve or retire one-shot scripts. Stop and wait for approval.

## 4. Apply approved changes
1. Apply the approved patch: `git apply /tmp/upgrade.patch`.
2. Resolve each approved `conflict` and `review` item:
   - Fold any surviving custom rule from retired docs into its v4 home (`PROJECT_PROFILE.md`, `DESIGN_DOC.md`, `AGENTS.md`, or `docs/RUNBOOKS.md`), then delete retired files you no longer need.
   - Move any dated status sections or bloat out of `PROJECT_PROFILE.md` (limit 250 lines) and `docs/OPEN_WORK.md` (limit 150 lines) into short entries in `docs/RELEASE_NOTES.md`.
   - Ensure `COMMAND INVENTORY` has explicit commands in backticks or `Not applicable: <reason>` and update `Guidance integrity` to `python3 scripts/verify.py`.
3. Regenerate project `AGENTS.md` blocks and selective skills if needed (never edits project specialist agent directories):
   ```sh
   python3 /path/to/agent-guidance/manage.py --sync /path/to/project
   ```
4. If the project tracks `docs/guidance-provenance.json`, append a valid JSON provenance entry recording source commit and owner decisions.
5. Add an `OPEN_WORK.md` item only for unresolved follow-ups, and one brief `docs/RELEASE_NOTES.md` entry.

## 5. Verify before finishing
1. Run project checks in the upgraded repo:
   ```sh
   python3 scripts/verify.py
   ```
2. Run the post-upgrade check from the `agent-guidance` checkout:
   ```sh
   python3 /path/to/agent-guidance/manage.py --check-upgrade /path/to/project --since <pre-upgrade-commit>
   ```
   Confirm no open items disappeared or closed silently, no deployed revision disappeared, no local customization or script reference was dropped, and no conflict markers remain.
3. Validate JSON files and report changed files, checks run, remaining owner actions, and any unverified areas plainly.
