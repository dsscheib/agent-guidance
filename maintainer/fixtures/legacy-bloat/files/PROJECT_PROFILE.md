# Project profile

Kind: Template. Status: Unconfigured. Fill this in with the [bootstrap procedure](docs/procedures/bootstrap-project.md). Record who adopted each value. Do not silently select a stack, domain or tier.

## Required before implementation

Agents must not write product code while placeholders remain in this section (everything above the command inventory). Run `python3 check_package.py --require code` to check.

| Decision | Project value |
|---|---|
| Name, purpose and primary users | team-portal: the owner's portal for links and display preferences, self-hosted at home |
| Owner and decision authority | Scenario Owner (sole maintainer) |
| Project tier (see below) | Self-hosted personal (adopted by Scenario Owner) |
| Primary user journeys | Open the home page; navigate between pages; change display preferences |
| Included and excluded scope | Included: server-rendered pages and preference forms. Excluded: authentication (home network only), external APIs |
| Approved languages, frameworks and storage | Python 3.10+ standard library `http.server`; HTML rendered server-side; no storage yet |
| Adopted stack profiles (`profiles/`) or "none" | None |
| Repository structure and generation conventions | `app/` package, `tests/` unittest suite, `scripts/` operator scripts |
| Supported runtime/build platforms and browsers | Linux home server with Python 3.10+; current Firefox and Chromium |
| Data classification and trust boundaries | One owner's preferences; home network only; all request input is untrusted |
| Excluded guidance (for example, UI guides for a non-UI project) and rationale | DATA_PORTABILITY (no import/export) |

### Agent git and authorization policy

| Action | Policy |
|---|---|
| Create commits | {{AGENT_MAY_COMMIT: never / when asked / per work item}} |
| Branch naming; work on default branch allowed? | Task branches named task/<short-description> |
| Commit message format and attribution | Imperative subject line under 72 characters |
| Push, open pull requests, merge | {{AGENT_REMOTE_POLICY: never / when asked}} |
| Deploy, publish, send messages, change shared data | Never without explicit per-operation authorization |

The tool guardrails in [docs/AGENT_TOOLS.md](docs/AGENT_TOOLS.md) make remote and destructive git commands ask for confirmation by default. Loosen them only to match this policy.

### Project tiers

The tier sets the default applicability of each gate family. Record deviations from it, with the owner's decision, in [docs/VERIFICATION_MATRIX.md](docs/VERIFICATION_MATRIX.md). These defaults are proposals of the guidance package until the owner adopts a tier.

| Gate family | Prototype | Internal tool | Production service |
|---|---|---|---|
| Unit/integration tests for changed behavior | Required | Required | Required |
| Build, lint, static checks | Required | Required | Required |
| Authentication, authorization and validation tests | If auth exists | Required | Required |
| Automated browser and accessibility checks (UI projects) | Smoke | Required | Required |
| Manual accessibility and device checks | Optional | Primary journeys | Full adopted matrix |
| Migration and isolated restore tests | Optional | If persistent data | Required |
| Performance budgets | Optional | Optional | Required |
| Soak qualification ([production operations profile](profiles/PRODUCTION_OPERATIONS.md)) | Not applicable | Optional | Required unless justified |
| Aggregate release verifier | Not applicable | Optional | Required |
| Runbooks and readiness record | Not applicable | R1–R3 | All |
| Off-host backup and disaster recovery | Not applicable | Recommended | Required |

<!-- stage: release -->
## Command inventory

Record commands as they become real. A command stays "Not verified" until it has been run in the stated environment. Agents use only commands listed here or ones they discover and add.

| Purpose | Command | Environment | Evidence / limitations |
|---|---|---|---|
| Install dependencies | None needed (standard library only) | Local shell | Not verified |
| Run locally / dev server | `python3 -m app.server` | Local shell | Not verified |
| Format | None configured | Local shell | Not verified |
| Lint / static / concurrency checks | None configured | Local shell | Not verified |
| Build / generate | Not applicable: pure Python | Not applicable | Not verified |
| Unit / integration tests | `python3 -m unittest` | Local shell | Not verified |
| Browser / accessibility | None configured yet | Firefox and Chromium, current | Not verified |
| Migration / recovery | {{RECOVERY_TEST_COMMANDS}} | Isolated fixtures | Not verified |
| Performance / soak | {{QUALIFICATION_COMMANDS}} | Approved staging | Not verified |
| Aggregate verifier | {{VERIFIER_COMMAND}} | {{VERIFIER_ENVIRONMENT}} | Not verified |
| Guidance integrity | `python3 check_package.py` | Any | Not verified |

Declare the applicability of each gate in [docs/VERIFICATION_MATRIX.md](docs/VERIFICATION_MATRIX.md). For a project without a listed feature, record an exclusion; do not invent the feature to fill the template.

## Release qualification profile

Fill in before the first release at the adopted tier. Values left blank at a tier that does not require them should read "Not applicable at tier X".

| Decision | Project value |
|---|---|
| Deployment environments, including any owner review (UAT) environment, and authorization scope | Review environment: `scripts/deploy-review.sh` copies a committed revision to `review/` on this machine |
| Accessibility target and supported inputs | {{ACCESSIBILITY_TARGET}} |
| Performance/load/capacity budgets | {{PERFORMANCE_BUDGETS}} |
| Qualification dataset, concurrency, mix and durations | {{QUALIFICATION_PROTOCOL}} |
| Recovery point/time objectives and retention | {{RECOVERY_POLICY}} |
| Evidence retention, alerting and review cadence | {{OPERATIONS_POLICY}} |

## Status 2026-10-20: review deployment 1

Deployed revision `4f1c2a9` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 1; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (9 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-21: review deployment 2

Deployed revision `8b0d7e3` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 2; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (10 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-21: review deployment 3

Deployed revision `c29a114` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 3; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (11 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-22: review deployment 4

Deployed revision `e57f0b2` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 4; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (12 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-23: review deployment 5

Deployed revision `1a6c9d8` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 5; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (13 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-23: review deployment 6

Deployed revision `73be4f0` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 6; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (14 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-24: review deployment 7

Deployed revision `d04a3c6` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 7; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (15 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-25: review deployment 8

Deployed revision `9e21b57` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 8; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (16 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-26: review deployment 9

Deployed revision `2c7d8e1` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 9; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (17 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-27: review deployment 10

Deployed revision `b3f904a` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 10; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (18 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-28: review deployment 11

Deployed revision `5e0a6d2` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 11; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (19 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-29: review deployment 12

Deployed revision `a81c37f` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 12; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (20 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-30: review deployment 13

Deployed revision `6d4e2b9` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 13; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (21 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.

## Status 2026-10-31: review deployment 14

Deployed revision `f09b1c3` to the review environment with `scripts/deploy-review.sh`.

- Changes in this deployment: settings page iteration 14; theme and density controls adjusted after owner feedback.
- Tests: `python3 -m unittest` passed on the deployed revision (22 tests).
- Browser checks: not run; no browser harness yet (OW-12).
- Owner feedback received: button label wording; follow-up recorded in OPEN_WORK.
- Agent notes: the deployment was authorized in chat by the owner; the previous revision remains in git history.
- Previous checkpoint carried forward: the settings page renders with native form controls; navigation link present; no storage yet.
- Risks noted at this checkpoint: dark-theme contrast unmeasured; backup retention for future stored preferences undecided (OW-15).
- Next steps planned at this checkpoint: address feedback, redeploy, and re-check contrast manually.
