# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| `4.x` | Yes |
| `3.0.x` | Security fixes only |
| `< 3.0` | No |

## Scope and trust boundaries

- **Project-local writes only:** `manage.py --install` writes only inside the target project directory (supports `--dry-run`, preserves customized files without `--force`, and refuses legacy `PACKAGE_MANIFEST.json` layouts unless `--plan-upgrade` or `--force` is used), `--plan-upgrade` writes nothing inside the project (besides an optional patch written outside it), and neither touches your home directory or global CLI configuration.
- **Best-effort agent guardrails:** Tool guardrails (`.claude/settings.json`, `.codex/rules/guidance.rules`, `.github/hooks/guidance.json` + `guidance_guardrail.py`) and read-only role settings vary by AI platform and are defense-in-depth, not a substitute for OS, container, branch-protection, or network sandboxing; bypass flags or shell indirection bypass tool-level checks.
- **Verification runner (`scripts/verify.py`):** `--verify` executes only `## Command inventory` rows in `PROJECT_PROFILE.md` whose **Gate** is `Development`, `Release`, or `Documentation` (never `Manual` or `—`). Review untrusted repositories' `PROJECT_PROFILE.md` commands before running `--verify`.
- **No secrets or external writes:** Packaged scripts use the Python standard library only, make no network calls, and never write secrets or dependency version dumps into verification output or receipts.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Instead, report issues privately using GitHub's **Private Vulnerability Reporting** in this repository's **Security** tab ("Report a vulnerability"), and include:

- The affected file or command
- Reproduction steps or proof of concept
- Potential impact and any suggested mitigation
