# Requirements review template

Scope/revision/reviewer/date: {{REVIEW_CONTEXT}}
Kind: Template. Status: Advisory assessment; findings require revalidation and adoption in authoritative guides.

| Finding ID / severity | Concrete contradiction or missing contract | References / observed behavior | User/operational consequence | Recommendation / decision | Work ID |
|---|---|---|---|---|---|
| {{FINDING_ID}} | {{FINDING}} | {{EVIDENCE}} | {{IMPACT}} | Proposed; {{RECOMMENDATION}} | {{WORK_ID}} |

Review domain identities/types/invariants, lifecycle/retries/stale writes, schema and public interfaces, import/export fidelity, semantic accessible UI, security boundaries, supported platforms, coherent recovery, deployment failures and complete test/qualification coverage. Distinguish requirements from inspected code and executed evidence. Do not accept unbounded guarantees or indexes/configuration knobs as proof of latency, durability or capacity.

For each recommendation record adopted/rejected/deferred/blocked status, decision authority, changed authoritative home, actual tests and remaining limits. This review never authorizes production operations or substitutes for readiness evidence.
