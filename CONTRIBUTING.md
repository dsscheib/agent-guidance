# Contributing

Thanks for contributing to **Reusable Project Guidance**. Maintainer rules, document budgets, and release workflows live in [MAINTAINING.md](MAINTAINING.md).

## What belongs in a PR vs. your own fork

- **Pull requests are welcome for:**
  - Bug fixes in `manage.py`, `scripts/verify.py`, tool guardrails, or v2/v3/v4 upgrade paths
  - Platform adapter or compatibility updates (backed by official vendor docs or tested CLI versions in [docs/AGENT_TOOLS.md](docs/AGENT_TOOLS.md))
  - Guidance clarity fixes, scenario/scorer improvements, and regression tests
- **Better kept in installed project files or your own fork:**
  - Project-specific stack conventions, team workflows, ticket patterns, or opinionated process rules

## Expectations for pull requests

- **Follow package rules:** Read [MAINTAINING.md](MAINTAINING.md) first (`one home per rule`, stack-neutral core, agent-neutral packaged docs, `AGENTS.md` within its template ceiling, no dated status sections in registers).
- **Stdlib only:** Keep `manage.py`, `scripts/verify.py`, guardrails, and tests free of third-party Python dependencies (Python 3.11+).
- **Edit sources, not generated outputs:** For selective skills, edit `docs/procedures/<name>.md` rather than `.agents/skills/` or `.claude/skills/`. For `AGENTS.md` routing/procedure tables, edit `PACKAGE_MANIFEST.json` (`agents_tables`) and sync.
- **Sync, verify, and add regression tests:** Add tests in `maintainer/test_install.py` or `maintainer/harness/test_score.py` for behavioral changes and run both:

```sh
python3 manage.py --sync --update-manifest
python3 manage.py
```

  In pull requests to this repository, paste the `python3 manage.py` output in the PR's Verification section instead of `scripts/verify.py --verify`.
  Note: `run_scenario.py --check` requires a remote `origin` URL (such as a GitHub clone or CI) and intentionally fails in clones whose `origin` is a local filesystem path.

- **No unapproved paid scenario runs:** Keep raw run logs outside the repo; use `python3 maintainer/harness/run.py --dry-run` unless live scenario benchmarking is explicitly planned.
