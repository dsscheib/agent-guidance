# Server-rendered web profile (Go)

Adopt explicitly in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md) before treating these rules as binding.

## Stack and contracts
- **Go:** Authoritative use cases, validation, authorization, and persistence.
- **Templ:** Escaped semantic HTML from explicit view models.
- **HTMX + Alpine.js:** Document full-document vs. fragment endpoints, `HX-*` target/swap/error/session-expiry behavior, and keep a plain-form fallback for critical flows sharing the same authoritative handler. Alpine holds temporary UI interaction state only.
- **Tailwind CSS + DaisyUI:** Override theme tokens so the app has its own visual identity rather than stock defaults; verify valid HTML nesting and focus/Alpine lifecycle after every HTMX swap.
- **Storage:** Use the approved choice in `PROJECT_PROFILE.md` without assuming one.
- Keep shareable filter/search/sort/page state in URL parameters; do not introduce a SPA router, alternate CSS system, or unapproved database; inspect existing layout before restructuring.
