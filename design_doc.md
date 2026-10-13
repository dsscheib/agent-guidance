# Technical design template

Status: Unconfigured. Authority by subject follows [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md). Descriptive code/schema observations are not accepted requirements or proof of testing.

## Purpose, users and scope
{{PURPOSE_USERS_JOURNEYS_AND_NON_GOALS}}

## Requirement inventory
| ID | Observable outcome | Status / authority | Iteration | Acceptance evidence |
|---|---|---|---|---|
| {{REQUIREMENT_ID}} | {{OUTCOME_AND_FAILURE_BEHAVIOR}} | Proposed; {{DECISION_REFERENCE}} | {{ITERATION}} | Not verified |

## Architecture and state ownership
{{MODULES_DEPENDENCIES_BOUNDARIES_AND_STATE_OWNERS}}
Cross-reference [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and domain invariants rather than duplicating policy.

## Public interfaces
| Interface | Inputs / permission | Result / errors | Compatibility / fallback | Implementation reference |
|---|---|---|---|---|
| {{INTERFACE}} | {{VALIDATION_AND_AUTHORIZATION}} | {{STATUS_AND_RESULT}} | {{COMPATIBILITY_AND_FALLBACK}} | Planned; not implemented |

For web interfaces document direct navigation, full-document and fragment variants, target/swap contracts, validation, authentication expiry and retry behavior. For other applications document the equivalent public interaction boundaries.

## Persistent model and transitions
{{IDENTITIES_RELATIONSHIPS_TYPES_UNITS_CONSTRAINTS_AND_LIFECYCLES}}
Record invariants, transactions, conflict/idempotency contracts and deletion/retention behavior. Reviewed migrations own the existing schema; illustrative DDL cannot replace them.

## Security, portability and operations
{{TRUST_BOUNDARIES_FORMATS_CONFIGURATION_AND_DEPLOYMENT_PROFILE}}
Reference the authoritative security, portability and runbook guides. List actual supported environments and observed limitations.

## Verification and delivery
{{ADOPTED_SCOPE_DEPENDENCIES_AND_ACCEPTANCE_CRITERIA}}
Link [docs/VERIFICATION_MATRIX.md](docs/VERIFICATION_MATRIX.md), [docs/OPEN_WORK.md](docs/OPEN_WORK.md) and [docs/ROADMAP.md](docs/ROADMAP.md). Do not rename incomplete committed scope as a future feature. Record separately what is proposed, implemented, verified and accepted.
