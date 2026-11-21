# Server-rendered web profile (Rust)

Adopt explicitly in [PROJECT_PROFILE.md](../PROJECT_PROFILE.md) before treating these rules as binding.

## Stack and contracts
- **Rust + Axum on Tokio:** HTTP extractors call domain use cases; keep business rules out of handlers. Never block Tokio worker threads (run password hashing, image processing, or sync I/O via bounded blocking tasks).
- **Askama:** Compiled escaped semantic HTML. Never mark untrusted or imported strings safe (`|safe`).
- **SQLx:** Parameterized queries (`--locked` builds with pinned `Cargo.lock` and toolchain), short transactions never held across external I/O or confirmations, and offline metadata generated only against isolated synthetic DBs.
- **HTMX + Alpine.js:** Document full-page vs. fragment routes, declare `Vary: HX-Request` whenever responses differ by header, share one handler/use-case with plain-form fallbacks, verify post-swap DOM validity and focus/Alpine re-init, and keep Alpine strictly for temporary local UI state.
- **Tailwind CSS + DaisyUI:** Override theme tokens for a deliberate visual identity rather than stock defaults; document asset-before-Cargo build order.
- Never add `unsafe` code, a SPA router, or an unapproved crate/ORM/database without authorization.
