# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| `4.x` | Yes |
| `3.0.x` | Security fixes only |
| `< 3.0` | No |

## Scope and trust boundaries

- **Project-local writes only:** `manage.py --install` preflights destination paths to reject symlinks pointing outside the target directory, writes only inside that target (supporting `--dry-run` and preserving customized files without `--force`), refuses legacy `PACKAGE_MANIFEST.json` layouts unless migrating via `--plan-upgrade` (`--force` overwrites matching files without removing retired v2/v3 files), `--plan-upgrade` writes nothing inside the project (besides an optional patch written outside it), and neither touches your home directory or global CLI configuration.
- **Best-effort agent guardrails:** Tool guardrails (`.claude/settings.json`, `.codex/rules/guidance.rules`, `.github/hooks/guidance.json` + `guidance_guardrail.py`) and read-only role settings vary by AI platform and are defense-in-depth, not a substitute for OS, container, branch-protection, or network sandboxing; bypass flags or shell indirection bypass tool-level checks.
- **Verification runner (`scripts/verify.py`):** `--verify` executes only `## Command inventory` rows in `PROJECT_PROFILE.md` whose **Gate** is `Development`, `Release`, or `Documentation` (never `Manual` or `—`). Review untrusted repositories' `PROJECT_PROFILE.md` commands before running `--verify`.
- **Output and secret handling:** Packaged scripts use the Python standard library only and make no network calls. The dependency-discovery helper reports manifest filenames only (never file contents or pinned versions), while `--verify` prints up to the last 5 output lines for failed gate commands and records configured gate commands and output tails in `--receipt` files—so inventory commands themselves must never print secrets.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Instead, report issues privately using GitHub's **Private Vulnerability Reporting** in this repository's **Security** tab ("Report a vulnerability"), and include:

- The affected file or command
- Reproduction steps or proof of concept
- Potential impact and any suggested mitigation
