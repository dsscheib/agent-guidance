# Specialist agent team

Kind: Policy. It applies as written; changing it needs an owner decision. It governs work that one agent delegates to another, using the specialist roles in `docs/roles/`. Every specialist follows [AGENTS.md](../AGENTS.md) like any other agent; this document adds only what delegation needs. How each tool loads the specialists is in [AGENT_TOOLS](AGENT_TOOLS.md#specialist-agents).

## When to delegate
Delegate a bounded task that matches one role's responsibilities and can be checked on its own: a server-side change with its tests, an independent review, a regression run. Do the work yourself when it is small, when it spans several roles' files at once, or when splitting it would cost more coordination than it saves. Delegation is optional; no change requires it.

## Rules for delegated work
1. **The delegating agent stays responsible.** It states the task, the files the specialist may change and the acceptance check, then reviews the specialist's result before accepting it. Specialist output is evidence to check, not a verified result, and the delegating agent's report to the user follows AGENTS.md rule 13. *Why: the user sees one reply, and an unchecked hand-off is how a wrong claim reaches it.*
2. **One owner per file at a time.** Never let two agents edit the same file concurrently. Name each specialist's files when work runs in parallel. *Why: concurrent edits overwrite each other silently.*
3. **Specialists report in their reply, not in files.** The reply to the delegating agent holds the summary, what was verified and how, what is assumed rather than observed, file paths with line numbers where they apply, open issues and the recommended next step. Anything unresolved goes to [OPEN_WORK](OPEN_WORK.md) through the delegating agent, like any other open item. *Why: a report file per task breaks the [document budget](DOCUMENTATION.md#document-budget).*
4. **Authorization does not pass down.** A specialist may do only what the user authorized the delegating agent to do, within the task it was given. *Example: a user's "push when done" lets the delegating agent push after review; it does not let a specialist push.*

## Role kinds
Each role declares a kind that sets what its generated agent files allow. Enforcement differs by tool and is best-effort ([AGENT_TOOLS](AGENT_TOOLS.md#specialist-agents)); the role's instructions state the limit in every tool.

| Kind | Edits files | Runs commands | Use for |
|---|---|---|---|
| implementer | Yes | Yes | Changes and their focused tests |
| tester | Yes | Yes | Test code and test runs; never product code outside the task |
| inspector | No | Yes | Running and measuring: browsers, profilers, test suites |
| reviewer | No | No | Independent reading and judgment |

## Roles
A role is installed when the project has the `team` feature and the module it requires. The installed set is whatever is in the project's `docs/roles/`.

| Role | Kind | Requires |
|---|---|---|
| [backend](roles/backend.md) | implementer | |
| [documentation](roles/documentation.md) | implementer | |
| [integration-tester](roles/integration-tester.md) | tester | |
| [auditor-advisor](roles/auditor-advisor.md) | reviewer | |
| [database](roles/database.md) | implementer | `data` |
| [devops](roles/devops.md) | implementer | `operations` |
| [security](roles/security.md) | reviewer | `operations` |
| [performance](roles/performance.md) | inspector | `production-ops` |
| [frontend](roles/frontend.md) | implementer | `ui` |
| [frontend-tester](roles/frontend-tester.md) | inspector | `ui` |
| [ux-designer](roles/ux-designer.md) | reviewer | `ui` |

## Changing the team
- **Change a role** by editing its file in `docs/roles/`, then run `python3 check_package.py --sync-adapters`. The checker fails while the generated agent files are stale. Never edit the generated files.
- **Pin a model** with a per-tool key in the role file's frontmatter; [AGENT_TOOLS](AGENT_TOOLS.md#specialist-agents) lists the keys and each tool's model without a pin. Model names are time-sensitive vendor claims, so record where each pin's model name came from in the same frontmatter, as `model-source: <vendor page> (checked YYYY-MM-DD)`; the sync leaves it out of the generated files.
- **Add a role** by adding `docs/roles/<name>.md` with `name`, `description`, `title` and `kind` in its frontmatter, then sync. **Remove a role** by deleting its file and syncing; the generated files go with it. Adding or removing a role is an owner decision; record it in PROJECT_PROFILE.md's Excluded guidance row when a packaged role is dropped.
