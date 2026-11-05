# Acceptance requirements for csvsum 4.2

Source: the finance team's adoption criteria and the vendor manual (`vendor/csvsum/MANUAL.md`).

| ID | Requirement | Source |
|---|---|---|
| REQ-1 | `--column NAME` prints the sum of that column | Manual §2 |
| REQ-2 | The header row is not summed | Manual §2 |
| REQ-3 | Quoted values with thousands separators, such as `"1,234"`, count as 1234 | Manual §3; finance exports use them |
