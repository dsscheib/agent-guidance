# Documentation, authority and decisions

## One authoritative home
AGENTS.md is a concise router. User-authorized decisions govern scope; update the affected authoritative specification so later agents can apply the adopted rule. Keep examples, proposals, inspected implementation and executed evidence distinct.

| Subject | Authoritative home |
|---|---|
| Project identity, adopted stack, support and actual command inventory | [PROJECT_PROFILE.md](../PROJECT_PROFILE.md) |
| Technical interfaces/model and delivery scope | [DESIGN_DOC.md](../DESIGN_DOC.md) |
| Domain meaning and invariants | [DOMAIN_RULES.md](DOMAIN_RULES.md) |
| Architecture responsibility boundaries | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Portable formats and import/export semantics | [DATA_PORTABILITY.md](DATA_PORTABILITY.md) |
| UX / component interactions / UX review | [UX_DESIGN_SPEC.md](UX_DESIGN_SPEC.md), [UI_PATTERNS.md](UI_PATTERNS.md), [UX_ACCEPTANCE_CHECKLIST.md](UX_ACCEPTANCE_CHECKLIST.md) |
| Brand assets and visual identity | [BRANDING.md](BRANDING.md) |
| Security and operational policy | [SECURITY_PRODUCTION_SPEC.md](SECURITY_PRODUCTION_SPEC.md) |
| Operator procedures / readiness evidence | [RUNBOOKS.md](RUNBOOKS.md), [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) |
| Testing policy / requirement-to-evidence map | [TESTING_SPEC.md](TESTING_SPEC.md), [VERIFICATION_MATRIX.md](VERIFICATION_MATRIX.md) |
| Scope and delivery workflow | [CHANGE_WORKFLOW.md](CHANGE_WORKFLOW.md) |
| Future scope and sequencing | [ROADMAP.md](ROADMAP.md) |
| Current unresolved work | [OPEN_WORK.md](OPEN_WORK.md) |
| Documentation process | This document |

Authority is assigned by subject. Technical design must implement domain, UX and security contracts. Code establishes what exists, not permission to change requirements. For conflicts record competing references, inspected behavior, impact, proposed resolution and required owner decision. Preserve behavior while unresolved; never weaken security to hide an implementation gap.

## Status and completion
- Proposed: awaits a decision; no implementation authorization.
- Accepted requirement: supported by a decision/reference; no implementation claim.
- Implemented/inspected: source/revision and inspection date; no test claim.
- Verified: executed check, result, environment, candidate, date, operator and evidence.
- Blocked/failed/not verified/in progress: explicit reason and next action.
- Accepted exception: specific scope, authority, review/expiry and remediation; retains failed/unverified gate disposition.

Report three states independently: implementation complete means authorized scope is delivered and reviewed; verification complete requires current passing evidence for all applicable checks; release accepted requires the final audit, required gates and an authorized acceptance decision for the identified candidate/environment. A scoped documentation check can pass without accepting an application release. None of these states authorizes deployment.

## Registers and history
OPEN_WORK.md is the single current register with stable IDs, status, owner, impact, next action and closure evidence. Keep closed entries and first failures. Reviews and archived plans are advisory/historical, not alternate live registers. Do not fabricate signatures or infer consent from generated acknowledgment fields.

## Useful documentation
Document actual setup/build/test/operations commands after inspection. Label illustrative commands and planned files explicitly. Maintain configuration names, defaults, units, precedence, secret locations and restart requirements. Date time-sensitive support claims and cite primary evidence in [SOURCES.md](SOURCES.md).

Update affected guides when behavior, schema/formats, UI, dependencies, configuration, backup/jobs or compatibility change. Do not require irrelevant edits to every guide. Record durable architecture tradeoffs using [decisions/ADR_TEMPLATE.md](decisions/ADR_TEMPLATE.md); routine helpers need no ADR.

Release records include candidate, schema/configuration, executed checks, known limitations, upgrade/recovery steps and evidence. Review links, examples, fences, secret exposure and consistency before delivery. Correct documentation drift without concealing defects. Use clearly synthetic placeholders, not plausible real credentials.
