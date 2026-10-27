# Optional server-rendered web technology profile

Kind: Profile. Status: Not selected. Adopt explicitly in PROJECT_PROFILE.md before treating these technology boundaries as binding. Other approved architectures may use the neutral core guides.

## Stack and responsibilities
- Go: authoritative use cases, validation, authorization and persistent state.
- Templ: escaped semantic HTML from explicit view models.
- HTMX: server requests and rendered fragments, with documented target/swap/error/expiry contracts.
- Alpine.js: temporary local interaction state, not canonical business truth.
- Tailwind CSS: layout/responsiveness and approved tokens.
- DaisyUI: baseline components/themes; styling alone does not establish accessibility.
- Storage driver/database: {{APPROVED_STORAGE_CHOICE}}. Do not assume a specific database or persistence model.

## Contracts this profile adds to the core guides
- Public interfaces in DESIGN_DOC.md document direct navigation, full-document and fragment variants, HTMX target/swap contracts, validation, authentication expiry and retry behavior.
- Critical workflows keep a plain form or navigable no-script fallback where feasible; direct and HTMX submissions share authoritative validation and effects.
- Fragments fit the target element's native content model; verify the DOM after every swap, not only the initial page.

## Further rules
URL parameters represent shareable search/filter/sort/page state where applicable. Verify HTMX swaps preserve valid HTML, labels, landmarks, focus and Alpine lifecycle. Use capabilities of the approved stack before bespoke JavaScript. Preserve the adopted security/content policy, including compliant expression registration when a constrained Alpine build is selected.

Do not introduce a SPA framework/router, alternate CSS component system or database without authorization. Pin tooling/dependencies, document generation order and inspect actual repository layout; language conventions do not justify restructuring a working application. Keep UI/native semantic requirements in UX_DESIGN_SPEC.md and component contracts in UI_PATTERNS.md.
