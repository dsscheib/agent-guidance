# UI and visual design

Visual direction, approved components, and accessibility targets for UI work. Keep existing conventions unless an authorized decision changes them. (If the `ui-design` skill is installed, use it when designing or substantially redesigning screens.)

## Visual identity and tokens
{{VISUAL_DIRECTION_AND_TOKENS}}

## Supported matrix
{{UI_MATRIX}}

Target WCAG 2.2 AA contrast, reflow, and reduced motion unless [PROJECT_PROFILE.md](../PROJECT_PROFILE.md) records another target.

## Approved components and patterns
| Pattern | Source reference | Direct / fallback contract | Dynamic / focus / a11y evidence |
|---|---|---|---|
| {{PATTERN}} | {{SOURCE_REFERENCE}} | {{FALLBACK_CONTRACT}} | Not verified |

## Non-negotiable UI rules
- **Native semantics & keyboard:** Use links (`<a href>`) to navigate, `<button type="...">` to act, real labels/forms/tables/dialogs, visible focus, logical tab order, and modal focus containment/return. Don't rely on color alone for status.
- **Truthful states:** Preserve user input on validation or network failure; keep empty, no-results, loading, error, conflict, permission-denied, and confirmed-saved states distinct. Never close a dialog or report success before the authoritative store saves.
- **Real browser verification:** Verify initial and dynamically updated DOM (no duplicate landmarks/IDs or broken labels). Unit or template-render tests do not verify layout, focus, or contrast. Record missing browser tooling in [docs/OPEN_WORK.md](OPEN_WORK.md) and give local UAT steps in your reply (never in `README.md`).
