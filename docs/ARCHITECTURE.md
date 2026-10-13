# Architecture requirements

## Adopted architecture
{{ARCHITECTURE_SUMMARY_AND_APPROVAL_REFERENCE}}
Use the stack and repository conventions in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md). This guide defines responsibility boundaries, not a mandate to restructure existing code. Optional stack profiles apply only after adoption.

## Responsibilities
| Layer | Owns | Must not own |
|---|---|---|
| Transport / interaction boundary | Input decoding, established identity, orchestration, response selection | Duplicated business rules or trusted client assertions |
| Domain / service layer | Invariants, validation, permissions and transaction-level use cases | Rendering or transport-specific status logic |
| Persistence | Queries, constraints, identity mapping and transaction mechanics | UI or alternative business policy |
| Presentation | Escaped, accessible output from explicit view models | Database queries, hidden network calls or authoritative calculations |
| Client enhancements | Temporary local interaction state | Authorization or persistent business truth |
| Operational adapters | Platform-specific lifecycle, storage and external integration | Hidden schema changes or policy overrides |

Use interfaces at real replaceable boundaries, not per noun. A small application can combine packages while preserving clear responsibilities. Avoid global mutable state; inject clocks/adapters when useful for deterministic tests.

## State and contracts
Specify authority for each state. Validate inputs and use cases at the authoritative boundary; persistence constraints provide a final integrity boundary. Document retries, stale edits, result semantics and direct/full/partial response behavior where relevant. Native HTML composition follows UX_DESIGN_SPEC.md; fragments must remain valid in their target context.

## Transactions and storage
Define transaction scope at the use-case boundary. Related persistent effects commit atomically where promised. Do not make remote calls or wait for confirmation inside write transactions. Use parameter binding, allowlisted query identifiers, bounded deadlines and managed resources. Version migrations; ordinary startup verifies compatibility unless another explicit approved policy applies. Keep writable data/configuration outside immutable releases. No undocumented fallback database or duplicate truth cache.

## Configuration and integration
Document real configuration, validation, precedence and failure behavior. External adapters have bounded payloads/deadlines and explicit failures; unavailable integrations cannot fabricate local records. Inspect actual platform and filesystem capabilities. Build on authorized development/CI infrastructure; pin dependencies and document generation order.

Material dependency proposals explain the concrete need, existing alternatives, support/license/security, target impact, maintenance/removal cost and verification. Prefer existing components and standard libraries without inventing cryptography. Preserve approved architecture until a change is authorized.

## Review
Check state ownership, transaction scope, dependency direction, actual public contracts, UI replacement behavior, platform compatibility and meaningful test coverage. Document durable decisions and affected operations.
