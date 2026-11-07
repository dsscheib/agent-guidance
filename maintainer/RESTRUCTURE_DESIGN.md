# Restructure design: core plus tier modules

Repository-only. **Status: implemented; this is the design record of version 3.** Approved by the owner on 2026-11-03, with the decisions recorded at the end, and built in all five phases: modules and tier-aware install (DOC-018 to DOC-020), the merged Internal tier (DOC-030), friction budgets (DOC-031 to DOC-038) and the upgrade procedure with adoption cleanup (DOC-039 to DOC-041). Where the build differs from the design, a note says so. Current plans are in the [Version 4 roadmap](REDESIGN_NOTES.md#version-4-roadmap); background and evidence are in [REDESIGN_NOTES.md](REDESIGN_NOTES.md), and finding numbers below refer to it.

## Why
- **Every project gets everything.** Today `--install` copies all 49 files (about 155 KB) whatever the tier, and lower tiers "exclude" the rest by a note in the profile. Agents still read and edit those files: on one-line changes, Codex edited about three guidance documents per task (finding 4).
- **Mechanical rules work; prose rules often do not reach weaker agents.** The computed verification status took overclaiming to zero (finding 14). A routing row fixed README updates (finding 17). A rule moved into tool output reached Haiku when the same rule in a procedure did not (finding 24).
- **Rigor belongs at the right tier and the right gate.** A corporation needs traceability, separation of duties and release evidence. A hobby project needs almost none of it, and should not pay for it in every reply.

## Design principles
1. **Install only what the tier and features need.** A file that is not installed cannot be read, misapplied or bloated.
2. **Enforce with tools before prose.** Every module states which of its rules the checker, `--verify`, a hook or CI enforces. Prose covers judgment that no tool can check.
3. **Put instructions where the agent already looks:** in tool output, the command inventory and the routing table, not in documents an agent may never open.
4. **One small core for every tier.** The core is the same for a hobby project and an enterprise product, so behavior learned at one tier carries over.
5. **Measure friction.** Each tier has a budget for what a routine change may touch, checked by scenarios (see Testing).

## Two axes: tier and features
- **Tier** sets rigor. It is chosen once at bootstrap: **Prototype**, **Internal** (Internal tool and Self-hosted personal merged, decision 2), **Production service** and a new **Enterprise product**.
- **Features** are orthogonal facts about the project: it has a UI, it imports or exports data, it uses an adopted stack profile. A prototype can have a UI; an enterprise service may have none.

## What goes where
| Unit | Files | Installed for |
|---|---|---|
| **Core** | AGENTS.md, CLAUDE.md, README.md, guardrails and adapters, PROJECT_PROFILE.md, docs/OPEN_WORK.md, docs/CHANGE_WORKFLOW.md, docs/TESTING_SPEC.md, docs/DOCUMENTATION.md, docs/AGENT_TOOLS.md, check_package.py, procedures bootstrap-project, final-audit and upgrade-guidance | Every tier |
| **design** | DESIGN_DOC.md, docs/ARCHITECTURE.md, docs/DOMAIN_RULES.md, docs/decisions/ADR_TEMPLATE.md, docs/ROADMAP.md | Internal and above |
| **operations** | docs/RUNBOOKS.md, docs/RELEASE_NOTES.md, docs/SECURITY_PRODUCTION_SPEC.md | Any tier with a deployed environment; required from Internal |
| **release** | docs/VERIFICATION_MATRIX.md, docs/PRODUCTION_READINESS.md, procedure release-readiness, docs/REQUIREMENTS_REVIEW.md, docs/VERIFICATION_REVIEW.md, docs/TEST_VERIFICATION_HANDOFF.md, docs/SOURCES.md | Production service and Enterprise |
| **production-ops** | profiles/PRODUCTION_OPERATIONS.md | Production service and Enterprise |
| **enterprise** (new) | Traceability and change-record rules, roles and separation of duties, dependency and SBOM gates, CI evidence, PR template | Enterprise |
| **ui** (feature) | docs/UX_DESIGN_SPEC.md, docs/UI_PATTERNS.md, docs/UX_ACCEPTANCE_CHECKLIST.md, docs/BRANDING.md | Projects with a user interface |
| **data** (feature) | docs/DATA_PORTABILITY.md | Projects that import or export data |
| **stack** (feature) | profiles/SERVER_RENDERED_WEB_GO.md or _RUST.md | Projects that adopt one |

Measured from the manifest: today every project receives 155 KB, of which 102 KB is prose agents are pointed at. The core is 99 KB, but only **46 KB of it is agent-facing prose** (AGENTS.md 10, DOCUMENTATION 8, TESTING_SPEC 8, PROJECT_PROFILE 7, final-audit 5, bootstrap and CHANGE_WORKFLOW 4 each); the rest is the checker, guardrails, adapters and maintainer-facing documents agents run but rarely read. So a Prototype project's agent-facing guidance falls from 102 KB to 46 KB (about 55% less), Internal adds about 21 KB and Production service with a UI about 38 KB more. The core prose is then the next thing to slim, starting with the generated routing table (below).

## The Enterprise tier
Everything in Production service, plus:
- **Traceability.** Every change names a requirement or ticket ID. The checker can verify that commit messages or the PR description carry one; the pattern (for example `PROJ-123`) is set in the profile.
- **Separation of duties.** The profile records roles (product owner, approver, release manager) instead of one owner. An agent never approves, merges or accepts its own work; the guardrails ask before `gh pr merge` and similar. *Since DOC-088 the merge and release rules are installed with the Enterprise module only, and the checker fails an Enterprise project without them; `gh pr review` asks in every tier.* CODEOWNERS and protected-branch settings are expected and named in the profile.
- **Machine-generated evidence.** CI runs `check_package.py --verify release --receipt` and keeps the receipt as a build artifact. Release records link CI runs instead of restating results.
- **Supply chain.** Release gates in the command inventory for a dependency audit, an SBOM (format set in the profile) and a license check. Missing tools are gaps, as for any gate.
- **Pluggable registers.** OPEN_WORK, release records and ADRs may live in an external tracker; the profile names where, and OPEN_WORK.md then holds only a pointer.

## Mechanics
- **Manifest.** Each file in `PACKAGE_MANIFEST.json` gets a `module`. The manifest lists which modules each tier requires and which features add.
- **Install.** `check_package.py --install DIR --tier internal --features ui` copies the core plus those modules. `--add-module` adds one later, for example when a project gains a UI or moves up a tier. *As built: there is no `--add-module`; rerunning `--install` with a higher `--tier` or more `--features` adds the modules and keeps the project's files, and version 4 adds `--plan-upgrade` for package upgrades.* Bootstrap proposes the tier and features and asks the owner, as today.
- **Generated routing table.** AGENTS.md keeps its rules, but its routing table is generated at install time from the installed modules, so agents never see rows for documents that are not there. This also keeps AGENTS.md small at the lower tiers.
- **Checker.** Project mode knows the installed tier and modules: it no longer reports absent modules as missing, flags a module that the tier requires but is absent, and enforces each tier's mechanical rules (document budget everywhere; ticket IDs, CODEOWNERS and a CI receipt at Enterprise).
- **Tier table.** PROJECT_PROFILE.md's tier table gains the Enterprise column and states, per gate, whether it runs per change or at release.

## Friction budgets
What a routine change (S2, S6 or S10) may touch, besides code and tests:

| Tier | Documents a routine change may edit | Report |
|---|---|---|
| Prototype | README usage only | Two to five lines with the `Verification:` line |
| Internal | Plus OPEN_WORK when something is left open | Same |
| Production service | Plus the VERIFICATION_MATRIX row for a changed requirement | Same |
| Enterprise | Plus the ticket reference in the commit or PR | Same, plus the ticket ID |

## Testing
- **Per-tier friction scenarios.** Run S2, S6 and S7 under prototype, internal, production and enterprise fixtures (`policy-internal`, and `policy-internal-tasks` where a scenario needs per-work-item commits). Score files touched, reply length and whether the tier's gates fired, against the budgets above.
- **Enterprise scenarios.** A change without a ticket ID; an agent asked to approve and merge its own PR; a dependency with a known vulnerability; a release without CI evidence.
- **Install scenarios.** A prototype install contains no release or UI documents; `--add-module ui` adds them and updates the routing table.
- **Adoption cleanup scenario.** A fixture shaped like a real bloated project with dated profile sections, a long OPEN_WORK, one-shot scripts and a rules-bearing `copilot-instructions.md`.
- **Regression.** S1–S12 must not fall below today's results for Flash, Haiku and Opus (19/20, 19/20, 18/20 on the core criteria).

## Phases
1. **Manifest modules and tier-aware install and checker**, with the current files unchanged. Prove with install scenarios. *Checkpoint: owner reviews what each tier installs.*
2. **Generated routing table and a slimmer core AGENTS.md.** Rerun S1–S12 on Flash, Haiku and Opus. *Checkpoint: no regression.*
3. **Enterprise module and scenarios.** *Checkpoint: owner reviews the enterprise rules.*
4. **Friction scenarios and budgets**, tuning the guidance until each tier meets its budget. Routine changes first (S2, S6 and S10 under each tier), then S7, then a **COTS test scenario** (owner, 2026-11-04): a repository of tests against an off-the-shelf tool with one deliberately failing vendor behavior, measuring how many gates bootstrap must exclude and whether agents report the failure or weaken the test. *Done (DOC-031 to DOC-038): routine changes, S7 and the COTS scenarios meet their budgets, and the largest AGENTS.md is back under 10 KB.*
5. **Upgrade procedure and adoption cleanup** for existing projects, tested on that fixture, then on the real project with the owner. *Fixture and scenario S18 done (DOC-039): 5/6 on the current procedure. The real project was then migrated with the owner (findings 48 and 49).*

## Owner decisions, 2026-11-03
1. **Module boundaries: as proposed.** DOMAIN_RULES stays in the design module; RELEASE_NOTES installs with operations.
2. **Merge Internal tool and Self-hosted personal into one tier, Internal:** trusted users or a single owner, data that matters, no external users or uptime commitments. It takes the stricter Self-hosted gates at release: migration and isolated restore tests, off-host backup and disaster recovery, runbooks R1–R3 and R5. This reverses the separate Self-hosted personal tier added in DOC-009; existing profiles naming either old tier map to Internal.
3. **Enterprise specifics: the maintainer's judgment, to revisit with user feedback.**
   - Ticket IDs are **reported, not enforced**: the profile records the ID pattern (a regular expression) and the tracker's location, and the checker reports commits and PRs without one. Any tracker works.
   - The SBOM format defaults to **CycloneDX**, with SPDX allowed as a profile choice.
   - Dependency audit, SBOM generation and license check are **Release gates** in the command inventory; a missing tool is a gap.
   - Separation of duties is enforced by the guardrails, which ask before merge and approval commands (for example `gh pr merge`, `gh pr review --approve`); roles are recorded in the profile.
4. **Generate only the routing table** in AGENTS.md from the installed modules; the rest of AGENTS.md stays hand-written and shared by every tier.
5. **Existing projects stay on 2.x** until they choose to run the upgrade procedure. The restructure is version 3.0 of the package and manifest.
