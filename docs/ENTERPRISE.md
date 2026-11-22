# Enterprise controls

Applies at the Enterprise tier in addition to Production tier rules. `scripts/verify.py` reads the ticket ID pattern from the table below.

## Settings
| Setting | Value |
|---|---|
| Ticket ID pattern (a regular expression, in backticks) | {{TICKET_ID_PATTERN}} |
| Tracker for tickets, open work and decisions | {{TRACKER_LOCATION}} |
| Software bill of materials format | {{SBOM_FORMAT: CycloneDX (default) or SPDX}} |
| CODEOWNERS file and protected default branch | {{CODEOWNERS_AND_BRANCH_PROTECTION}} |

## Roles and separation of duties
| Role | Who | Decides |
|---|---|---|
| Product owner | {{PRODUCT_OWNER}} | Scope, priorities and business rules |
| Approver | {{APPROVERS}} | Code review approval and merging to the default branch |
| Release manager | {{RELEASE_MANAGER}} | Release acceptance for an identified candidate and environment |

- **An agent never approves, merges, or accepts work (its own or anyone else's).** Prepare the change and evidence, then stop; the tool guardrails ask before `gh pr merge`, `gh pr review`, and `gh release create`, and `scripts/verify.py` fails if those rules are removed.
- When asked to approve, merge, or accept, name which role decides and what evidence they need, and stop there.
- Keep `CODEOWNERS` and branch protection enforced on the hosting service; `scripts/verify.py` reports if `CODEOWNERS` is missing.

## Traceability
- **Every change names a ticket.** Put the ticket ID in each commit message and pull request description. If none was given, ask for it; never invent one. Scope outside the ticket needs its own ticket.
- `scripts/verify.py` reports recent commits lacking a ticket ID.

## Evidence from CI
- CI runs `python3 scripts/verify.py --verify release --receipt verification.json` on each candidate and stores the receipt as a build artifact.
- Link the CI run in PRs and release records and quote the `Verification:` line verbatim instead of rewriting results.

## Supply chain
- The command inventory includes three Release gates: dependency audit, SBOM (format above), and license check. Missing tools are gaps; while the dependency audit is a gap, `--verify release` names dependency manifests to inspect by hand.
- Never add or upgrade a dependency to fix an audit finding without normal review.

## External trackers
If the tracker above holds open work, ADRs, or release records, keep [docs/OPEN_WORK.md](OPEN_WORK.md), ADRs, and [docs/RELEASE_NOTES.md](RELEASE_NOTES.md) as one-line pointers to it.
