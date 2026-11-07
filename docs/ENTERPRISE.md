# Enterprise controls

Kind: Policy with template fields. Applies at the Enterprise tier, in addition to everything Production service requires. Fill in the fields during bootstrap; the checker reads the ticket ID pattern from the table below. These controls are a first version, to be revisited with feedback from teams using them.

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

- **An agent never approves, merges or accepts its own work, or anyone's.** It prepares the change and its evidence; a person in the named role decides. The guardrails ask before `gh pr merge`, `gh pr review` and `gh release create`; the merge and release rules come with this module, and the checker fails if they are removed.
- When asked to approve, merge or accept, say which role decides and what evidence they need, and stop there.
- CODEOWNERS and branch protection enforce review on the hosting service. The checker reports when no CODEOWNERS file exists.

## Traceability
- **Every change names a ticket.** Put the ticket ID in each commit message and pull request description. If the request gives none, ask for it; never invent one. Work the ticket does not cover needs its own ticket.
- The checker reports recent commits on the current branch whose message lacks a ticket ID. It reports; it does not block.

## Evidence from CI
- CI runs `python3 check_package.py --verify release --receipt verification.json` on every candidate and keeps the receipt as a build artifact.
- Release records and pull requests link the CI run instead of restating its results. An agent quotes the `Verification:` line; it does not rewrite the evidence.
- The checker reports when no CI workflow runs `check_package.py --verify`.

## Supply chain
- The command inventory has three Release gates: a dependency audit, an SBOM in the format above, and a license check. A gate without a command is a gap, like any other. While the dependency audit is a gap, `--verify` names the dependency files to read by hand.
- Never add or upgrade a dependency to fix an audit finding without the change going through review like any other change.

## Registers
If the tracker above holds open work, ADRs or release records, the repository copies (OPEN_WORK.md, ADRs, RELEASE_NOTES.md) hold one line pointing to it instead of a second list.
