# Project profile — complete before implementation

Status: Unconfigured template. Record the adopted profile and approving authority; do not silently select a stack or domain.

| Decision | Project value |
|---|---|
| Name, purpose and primary users | {{PROJECT_NAME_AND_PURPOSE}} |
| Owner and decision authority | {{OWNER}} |
| Primary user journeys | {{PRIMARY_JOURNEYS}} |
| Included and excluded scope | {{SCOPE}} |
| Approved languages, frameworks and storage | {{TECHNOLOGY_STACK}} |
| Repository structure and generation conventions | {{REPOSITORY_LAYOUT}} |
| Supported runtime/build platforms and browsers | {{SUPPORTED_ENVIRONMENTS}} |
| Data classification and trust boundaries | {{DATA_AND_TRUST_BOUNDARIES}} |
| Deployment environments and authorization scope | {{DEPLOYMENT_BOUNDARIES}} |
| Accessibility target and supported inputs | {{ACCESSIBILITY_TARGET}} |
| Performance/load/capacity budgets | {{PERFORMANCE_BUDGETS}} |
| Qualification dataset, concurrency, mix and durations | {{QUALIFICATION_PROTOCOL}} |
| Recovery point/time objectives and retention | {{RECOVERY_POLICY}} |
| Evidence retention, alerting and review cadence | {{OPERATIONS_POLICY}} |

## Actual command inventory

| Purpose | Verified command | Environment | Evidence / limitations |
|---|---|---|---|
| Build / generate | {{BUILD_COMMAND}} | {{BUILD_ENVIRONMENT}} | Not verified |
| Unit / integration | {{TEST_COMMAND}} | {{TEST_ENVIRONMENT}} | Not verified |
| Static / concurrency checks | {{STATIC_AND_CONCURRENCY_COMMANDS}} | {{TEST_ENVIRONMENT}} | Not verified |
| Browser / accessibility | {{UI_TEST_COMMANDS_OR_JUSTIFIED_EXCLUSION}} | {{BROWSER_MATRIX}} | Not verified |
| Migration / recovery | {{RECOVERY_TEST_COMMANDS}} | Isolated fixtures | Not verified |
| Performance / soak | {{QUALIFICATION_COMMANDS}} | Approved staging | Not verified |
| Aggregate verifier | {{VERIFIER_COMMAND}} | {{VERIFIER_ENVIRONMENT}} | Not verified |

Declare applicability of each gate in [docs/VERIFICATION_MATRIX.md](docs/VERIFICATION_MATRIX.md). For projects without a listed feature, document an exclusion; do not invent that feature to fill a template. Commands are placeholders until inspected and exercised.
