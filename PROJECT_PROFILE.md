# Project profile

Kind: Template. Status: Unconfigured. Fill this in with the [bootstrap procedure](docs/procedures/bootstrap-project.md). Record who adopted each value. Do not silently select a stack, domain or tier.

## Required before implementation

Agents must not write product code while placeholders remain in this section (everything above the command inventory). Run `python3 check_package.py --require code` to check.

| Decision | Project value |
|---|---|
| Name, purpose and primary users | {{PROJECT_NAME_AND_PURPOSE}} |
| Owner and decision authority | {{OWNER}} |
| Project tier (see below) | {{PROJECT_TIER}} |
| Primary user journeys | {{PRIMARY_JOURNEYS}} |
| Included and excluded scope | {{SCOPE}} |
| Approved languages, frameworks and storage | {{TECHNOLOGY_STACK}} |
| Adopted stack profiles (`profiles/`) or "none" | {{ADOPTED_PROFILES}} |
| Repository structure and generation conventions | {{REPOSITORY_LAYOUT}} |
| Supported runtime/build platforms and browsers | {{SUPPORTED_ENVIRONMENTS}} |
| Data classification and trust boundaries | {{DATA_AND_TRUST_BOUNDARIES}} |
| Excluded guidance (for example, UI guides for a non-UI project) and rationale | {{EXCLUDED_GUIDES_OR_NONE}} |

### Agent git and authorization policy

| Action | Policy |
|---|---|
| Create commits | {{AGENT_MAY_COMMIT: never / when asked / per work item}} |
| Branch naming; work on default branch allowed? | {{BRANCH_POLICY}} |
| Commit message format and attribution | {{COMMIT_CONVENTION}} |
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
| Install dependencies | {{INSTALL_COMMAND}} | {{DEV_ENVIRONMENT}} | Not verified |
| Run locally / dev server | {{RUN_COMMAND}} | {{DEV_ENVIRONMENT}} | Not verified |
| Format | {{FORMAT_COMMAND}} | {{DEV_ENVIRONMENT}} | Not verified |
| Lint / static / concurrency checks | {{STATIC_AND_CONCURRENCY_COMMANDS}} | {{TEST_ENVIRONMENT}} | Not verified |
| Build / generate | {{BUILD_COMMAND}} | {{BUILD_ENVIRONMENT}} | Not verified |
| Unit / integration tests | {{TEST_COMMAND}} | {{TEST_ENVIRONMENT}} | Not verified |
| Browser / accessibility | {{UI_TEST_COMMANDS_OR_JUSTIFIED_EXCLUSION}} | {{BROWSER_MATRIX}} | Not verified |
| Migration / recovery | {{RECOVERY_TEST_COMMANDS}} | Isolated fixtures | Not verified |
| Performance / soak | {{QUALIFICATION_COMMANDS}} | Approved staging | Not verified |
| Aggregate verifier | {{VERIFIER_COMMAND}} | {{VERIFIER_ENVIRONMENT}} | Not verified |
| Guidance integrity | `python3 check_package.py` | Any | Not verified |

Declare the applicability of each gate in [docs/VERIFICATION_MATRIX.md](docs/VERIFICATION_MATRIX.md). For a project without a listed feature, record an exclusion; do not invent the feature to fill the template.

## Release qualification profile

Fill in before the first release at the adopted tier. Values left blank at a tier that does not require them should read "Not applicable at tier X".

| Decision | Project value |
|---|---|
| Deployment environments, including any owner review (UAT) environment, and authorization scope | {{DEPLOYMENT_BOUNDARIES}} |
| Accessibility target and supported inputs | {{ACCESSIBILITY_TARGET}} |
| Performance/load/capacity budgets | {{PERFORMANCE_BUDGETS}} |
| Qualification dataset, concurrency, mix and durations | {{QUALIFICATION_PROTOCOL}} |
| Recovery point/time objectives and retention | {{RECOVERY_POLICY}} |
| Evidence retention, alerting and review cadence | {{OPERATIONS_POLICY}} |
