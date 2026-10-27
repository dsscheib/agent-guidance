# UX acceptance checklist

Kind: Template, copied per candidate or UI scope.

Candidate: {{CANDIDATE}}. Scope: {{UI_SCOPE}}. Required matrix: {{BROWSERS_VIEWPORTS_THEMES_INPUTS}}. All boxes begin unverified; attach actual evidence.

- [ ] Adopted primary journeys work with authoritative persisted outcomes.
- [ ] Identity, units, unknown/zero and state labels are truthful.
- [ ] Initial DOM and partial updates preserve native landmarks, heading hierarchy, lists, metadata, table headers/captions and valid nesting.
- [ ] Links/buttons/native controls fit their meaning; no clickable generic wrappers when a native control fits.
- [ ] Labels, descriptions, errors, names and unique IDs remain associated after updates.
- [ ] Keyboard, focus visibility/order, modal containment/return and skip navigation work.
- [ ] Direct navigation (deep links), session expiry and any fallback required by the adopted stack profile are usable.
- [ ] Loading, success, empty, no-results, network/error, validation and stale/conflict states are exercised; input is preserved.
- [ ] Search/filter/history and stale-response handling follow the contract.
- [ ] Required viewport, zoom/reflow, theme/contrast and reduced-motion checks have evidence.
- [ ] Touch targets, real devices, screen-reader announcements, forced colors and relevant use environments have the required manual evidence.
- [ ] Automated accessibility and browser results are recorded separately from manual coverage.
- [ ] Routing-table documents updated (AGENTS.md rule 14); unverified criteria remain open in OPEN_WORK.md.

A passing automated scan cannot close unperformed manual checks. Avoid an unrelated whole-template rewrite solely to reduce wrapper counts.
