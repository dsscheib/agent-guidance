# Technical design and domain rules

Update only the sections your change affects. Descriptive code observations are not approved requirements or verification evidence.

## Purpose and scope
{{PURPOSE_USERS_JOURNEYS_AND_NON_GOALS}}

## Requirements
| ID | Outcome and failure behavior | Status / authority | Iteration | Acceptance evidence |
|---|---|---|---|---|
| {{REQUIREMENT_ID}} | {{OUTCOME_AND_FAILURE_BEHAVIOR}} | Proposed; {{DECISION_REFERENCE}} | {{ITERATION}} | Not verified |

## Architecture and public boundaries
{{MODULES_DEPENDENCIES_BOUNDARIES_AND_STATE_OWNERS}}

Document boundaries between components or with external callers (HTTP/RPC APIs, published library APIs, schemas, file and message formats): validation, permission, error semantics, session expiry, and retry behavior. Keep internal helpers in docstrings/tests and CLI options, usage, and output formats in `README.md` (not here). Record durable architecture or dependency tradeoffs as ADRs using [docs/decisions/ADR_TEMPLATE.md](docs/decisions/ADR_TEMPLATE.md).

| Interface | Inputs / permission | Result / errors | Compatibility / fallback | Implementation |
|---|---|---|---|---|
| {{INTERFACE}} | {{VALIDATION_AND_AUTHORIZATION}} | {{STATUS_AND_RESULT}} | {{COMPATIBILITY_AND_FALLBACK}} | Planned |

## Domain rules and invariants
{{DOMAIN_TERMS_TYPES_UNITS_AND_INVARIANTS}}

Keep internal IDs separate from mutable display names, define exact units/precision/overflow and null/unknown/zero distinctions, and record only confirmed domain rules (for undecided rules, follow [AGENTS.md](AGENTS.md)).

| Operation | Preconditions / permission | Atomic effects & invariants | Failure / retry / idempotency |
|---|---|---|---|
| {{OPERATION}} | {{PRECONDITIONS}} | {{EFFECTS_AND_INVARIANTS}} | {{ERROR_AND_CONFLICT_CONTRACT}} |

## Persistent model and migrations
{{IDENTITIES_RELATIONSHIPS_CONSTRAINTS_AND_LIFECYCLE}}

Version migrations and rehearse schema upgrades on isolated synthetic data; reviewed migrations own the live schema.

## Security and operations
{{TRUST_BOUNDARIES_CONFIGURATION_AND_LIMITATIONS}}

Follow [AGENTS.md](AGENTS.md) for secret handling and untrusted inputs; link [docs/OPEN_WORK.md](docs/OPEN_WORK.md) for unresolved security or operational gaps.
