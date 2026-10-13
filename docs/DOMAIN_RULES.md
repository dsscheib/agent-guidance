# Domain rules template

Status: Unconfigured. Populate accepted rules from the product's real domain; do not adopt sample entities or invariants by inference.

## Vocabulary and identity
{{DOMAIN_TERMS_ENTITIES_AND_RELATIONSHIPS}}
Define stable internal identity separately from mutable display names and external identifiers. Specify external-identifier scope, normalization, duplicates and merge behavior. Preserve input display values where promised; do not infer equivalence from name similarity. Unknown, absent, empty and zero are distinct where meaningful.

## Values and constraints
{{TYPES_UNITS_PRECISION_BOUNDS_AND_OVERFLOW_POLICY}}
Use exact representation where correctness requires it. Define conversion, rounding, invalid-value and boundary behavior explicitly; enforce critical invariants at the authoritative and persistence boundaries. Do not invent business limits, priorities or conflict-resolution rules.

## Operations and lifecycle
| Intent | Preconditions / permission | Atomic effects | Failure / retry / stale-state behavior |
|---|---|---|---|
| {{OPERATION}} | {{PRECONDITIONS}} | {{EFFECTS_AND_INVARIANTS}} | {{ERROR_AND_CONFLICT_CONTRACT}} |

{{ALLOWED_TRANSITIONS_ARCHIVE_DELETE_AND_RETENTION_RULES}}
Preserve references/history according to an approved contract. Corrections and reversals must have defined boundaries and auditable effects where required. A logical operation may create multiple or zero event rows; row-level uniqueness alone does not define operation-level retry semantics.

## Concurrency and audit
{{IDEMPOTENCY_SCOPE_PAYLOAD_RETENTION_RESULT_AND_STALE_WRITE_POLICY}}
Define atomicity, successful acknowledgments, conflict results and reconciliation equations. Test valid/invalid/boundary inputs, concurrent changes, lost responses, retries, forbidden access and interrupted transactions. Do not silently overwrite a newer state.

## Scope and decisions
{{SUPPORTED_UNSUPPORTED_AND_UNRESOLVED_RULES}}
Product decisions belong here after approval; unresolved choices belong in OPEN_WORK.md. Import/export uses the same authoritative rules under DATA_PORTABILITY.md. Actual schema/interfaces remain in design_doc.md. Inspection is not evidence of verification.
