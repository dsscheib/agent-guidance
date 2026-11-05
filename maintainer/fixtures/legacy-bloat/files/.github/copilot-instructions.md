# Copilot instructions for team-portal

Read AGENTS.md first, then these project rules.

- After every fix, deploy to the review environment with `scripts/deploy-review.sh` so the owner can see it.
- After each deployment, add a dated status section to PROJECT_PROFILE.md with the revision, tests and owner feedback.
- Before each deployment, run `scripts/probe-review-2026-10-23.sh` to check the review server.
- Carry a "Previous checkpoint" section forward in docs/OPEN_WORK.md at every checkpoint.
- If a deployment fails, run `scripts/recover-deploy-2026-10-24.sh`.
- Use `scripts/check-contrast-once.py` to look at theme colors.
- Keep replies detailed: list every file read, every command run and every check not run.
- Never push; the owner pushes.
