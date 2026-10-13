# Reusable project guidance

This package contains project-neutral adaptations of agent instructions, engineering policies, specification templates, acceptance checklists and operational guides. It is a starting point for a new project, not evidence of implementation, testing, deployment authorization or release acceptance.

## Start here
1. Copy this directory's contents into the new repository. Review files individually before overwriting existing documentation.
2. Complete [PROJECT_PROFILE.md](PROJECT_PROFILE.md) with the owner, goals, approved stack, domain, supported platforms, actual commands and required verification gates.
3. Populate [design_doc.md](design_doc.md) and the domain, UX, security and portability specifications with adopted requirements. Unfilled templates are not approved product defaults.
4. Keep applicable requirements. Record a reason and owner decision when excluding a gate; missing tooling is not inapplicability. Non-web projects may exclude the web UI guides with a recorded rationale.
5. Select an optional stack profile only when authorized. The included [server-rendered web profile](profiles/SERVER_RENDERED_WEB.md) is not the default architecture.
6. Establish the real test command inventory and required-gate matrix. Replace all `{{...}}` placeholders before claiming configuration or acceptance is complete.
7. Start a fresh unresolved-work register and readiness record. Do not copy results or approvals from another project.

## What is included
- AGENTS.md as the entry point and requirements router.
- Architecture, domain, portability, UX, testing, security, documentation and change policies.
- Technical design, roadmap, requirement-review, verification handoff, branding and decision templates.
- Empty work/evidence registers and operator/qualification procedures.
- A checksummed manifest and a local package checker.

The instructions are language- and host-neutral. No application routes, entities, data model, credentials, host addresses, product backlog, production results or historical approvals are carried over. Examples and placeholders do not establish implemented interfaces. Choose workload sizes, budgets, soak duration, retention, recovery objectives and supported environments for the new project; no inherited benchmark number is a universal requirement.

Historical project audits, archived plans, raw evidence, application source and deployment scripts are intentionally omitted. Their reusable review/verification contracts are represented by fresh templates. This package performs no deployments and sends no messages.

Run `python3 check_package.py` from this directory to check manifest hashes, internal references and placeholder inventory. Checksummed placeholders are intentional template content, not claims that setup is finished.
