# Optional server-rendered web technology profile (Rust)

Kind: Profile. Status: Not selected. Adopt explicitly in PROJECT_PROFILE.md before treating these technology boundaries as binding. Other approved architectures may use the neutral core guides.

## Stack and responsibilities
- Rust: authoritative use cases, validation, authorization and persistent state in domain and persistence modules.
- Axum on Tokio: HTTP transport. Handlers extract input, call a use case and render a response; business rules stay out of handlers and extractors.
- Askama: compiled, escaped semantic HTML from explicit view models.
- SQLx: parameterized queries, transactions and explicit migrations. Database: {{APPROVED_STORAGE_CHOICE}}. Do not assume a specific database or persistence model.
- HTMX: server requests and rendered fragments, with documented target/swap/error/expiry contracts.
- Alpine.js: temporary local interaction state, not canonical business truth.
- Tailwind CSS: layout/responsiveness and approved tokens.
- DaisyUI: baseline components/themes; styling alone does not establish accessibility.

## Contracts this profile adds to the core guides
- Public interfaces in DESIGN_DOC.md document direct navigation, full-document and fragment variants, HTMX target/swap contracts, validation, authentication expiry and retry behavior.
- Critical workflows keep a plain form or navigable no-script fallback where feasible; direct and HTMX submissions share one handler path or use case, so validation and effects cannot diverge.
- Fragments fit the target element's native content model; verify the DOM after every swap, not only the initial page.
- Map each domain error to an explicit status and a full-document or fragment response. Responses that differ by the `HX-Request` header declare `Vary: HX-Request`.

## Further rules
URL parameters represent shareable search/filter/sort/page state where applicable. Verify HTMX swaps preserve valid HTML, labels, landmarks, focus and Alpine lifecycle. Use capabilities of the approved stack before bespoke JavaScript. Preserve the adopted security/content policy, including compliant expression registration when the Alpine CSP build is selected.

Never mark untrusted or imported strings safe in Askama (`|safe` or equivalent); only server-built markup from trusted inputs may bypass escaping. Never build SQL by string concatenation; bind every value. Keep transactions short and never hold one across user confirmation, external I/O or unbounded awaits. Do not block Tokio worker threads: run CPU-heavy or blocking work (password hashing, image processing, synchronous file or database calls) through bounded blocking tasks. Generate SQLx offline query metadata, if used, only from isolated synthetic databases; builds never connect to live data.

Do not introduce a SPA framework/router, alternate CSS component system, web framework, template engine, ORM or database without authorization. Do not add `unsafe` code to the application without authorization. Commit `Cargo.lock`, pin the toolchain, build with `--locked`, enable only the crate features in use, and pin frontend tooling and assets; document generation order (assets before the Cargo build that embeds or packages them). Inspect actual repository layout; language conventions do not justify restructuring a working application. Keep UI/native semantic requirements in UX_DESIGN_SPEC.md and component contracts in UI_PATTERNS.md.
