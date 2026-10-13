# Agent instructions

Read [PROJECT_PROFILE.md](PROJECT_PROFILE.md) for the actual project, approved stack and supported environments. Unfilled templates or proposed defaults do not authorize behavior changes. Follow the user's requested outcome and preserve unrelated work.

## Mandatory references
Before relevant changes, read:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): responsibilities, state and dependencies.
- [docs/DOMAIN_RULES.md](docs/DOMAIN_RULES.md): terminology, invariants and transactions.
- [docs/DATA_PORTABILITY.md](docs/DATA_PORTABILITY.md): interfaces, identities and compatibility.
- [docs/CHANGE_WORKFLOW.md](docs/CHANGE_WORKFLOW.md): scope, review and verification.
- [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md): authority, statuses and decisions.
- [design_doc.md](design_doc.md): technical contracts and adopted delivery scope.
- [docs/UX_DESIGN_SPEC.md](docs/UX_DESIGN_SPEC.md), [docs/UI_PATTERNS.md](docs/UI_PATTERNS.md) and [docs/UX_ACCEPTANCE_CHECKLIST.md](docs/UX_ACCEPTANCE_CHECKLIST.md): applicable UI contracts.
- [docs/ROADMAP.md](docs/ROADMAP.md) when planning future work; inclusion does not authorize implementation.

Before changing authentication, authorization, persistence, dependencies, deployment or automation, read [docs/SECURITY_PRODUCTION_SPEC.md](docs/SECURITY_PRODUCTION_SPEC.md), [docs/RUNBOOKS.md](docs/RUNBOOKS.md) and [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md). Before behavior changes, read [docs/TESTING_SPEC.md](docs/TESTING_SPEC.md). Use the selected stack profile if applicable.

## Engineering and scope
- Inspect existing implementation, tests, configuration and working-tree changes. Reuse established conventions; do not invent routes, fields, dependencies or commands.
- Keep one authoritative home per requirement. Product, domain and security contracts override cosmetic preferences. Report discrepancies and preserve current behavior until an authorized change resolves them.
- Keep business truth, validation and permissions in the authoritative application layer. Client state may assist interaction but cannot establish authorization or persistent truth.
- Do not invent uncertain business rules. Ask about blocking decisions while continuing independent authorized work.
- Material dependency or architecture changes need a concrete justification and authorization unless already in scope. Routine internal helpers do not need another approval.
- Do not reset, overwrite, bulk reformat or refactor unrelated work. Do not commit, push, merge, publish, deploy or perform destructive data changes without applicable authorization.
- Complete authorized work, update affected documentation and run appropriate checks. Do not stop at a plan when implementation was requested.

## UI invariants
- Prioritize the adopted user journeys. Show identities, values, units and states accurately; never advertise unsupported features.
- Prefer native HTML semantics over nested generic containers: landmarks, logical headings, lists, description lists, tables, forms, labels and native controls. Layout-only wrappers remain appropriate. Do not replace every wrapper with a section/article or recreate native controls with ARIA.
- Use approved design tokens and components. Verify keyboard, focus, names, contrast, motion preferences and responsive reading order.
- Preserve form input on errors. Distinguish loading, empty, error, success, conflict and unavailable states. Show persisted authoritative results.
- Use links for navigation and buttons for actions. Apply confirmations to destructive non-reversible actions; offer undo only when supported.
- Keep a plain form or navigable fallback for critical web workflows where feasible. Verify dynamic replacement preserves valid HTML, focus, component lifecycle and target contracts.
- Test the configured browser/theme/viewport matrix and manual accessibility scenarios. Never claim a check ran when it did not.

## Operations and testing
- Treat clients and external inputs as untrusted. Enforce authorization, validation, escaping and applicable request-forgery protections at the authoritative boundary.
- Inspect actual platform/filesystem/runtime support. Do not assume a process manager, container runtime, driver or backup capability exists.
- Use least-privilege runtime identities, immutable releases and protected ancestors, separate writable data, explicit migrations, singleton jobs, bounded retries and graceful shutdown.
- Prove coherent recovery before risky migrations or release acceptance. Do not copy an active database main file alone, discard journal files to clear errors, or roll back a binary against an incompatible schema.
- No unattended application releases/schema changes unless specifically adopted and authorized. Never log secrets or store them in source, arguments, examples or evidence.
- Map affected requirements to verification before implementation. Missing UI/performance/soak tooling is work or a blocker, never an implicit waiver.
- Use isolated synthetic data and the real persistence path where relevant. Add meaningful regressions and negative controls; demonstrate failure before a fix when practical.
- Report implementation completion, verification completion and release acceptance separately. Track unresolved work in [docs/OPEN_WORK.md](docs/OPEN_WORK.md); perform the final audit in CHANGE_WORKFLOW.md. A green local suite or running long test is not release acceptance.
