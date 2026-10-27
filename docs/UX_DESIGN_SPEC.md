# UX and accessibility specification

Kind: Policy. It applies as written; changing it needs an owner decision. The product-context field is a template. Applies only to projects with a UI.

## Adopted product context
{{USERS_PRIMARY_JOURNEYS_NAVIGATION_DENSITY_AND_SUPPORTED_DEVICES}}
Preserve existing presentation defaults until an authorized decision changes them. Density, navigation shell and presentation mode are distinct choices. Show only supported actions and model-backed values; distinguish identities, units, unknown and zero.

## Native HTML semantics
Choose elements by content/behavior before styling. Prefer native semantics over generic nested containers; a styling framework does not justify discarding meaning.

| Meaning | Structure |
|---|---|
| Document landmarks | header, labelled navigation, one visible main, footer where appropriate |
| Headings | Logical explicit h1–h6 hierarchy, independent of styling |
| Thematic / independent / complementary content | section with heading / article / aside only when their meaning fits |
| Repeated items or ordered steps | ul/ol with li |
| Name/value metadata | dl with dt/dd |
| Tabular comparison | table with caption/name, associated headers and cells |
| Navigation / action | a with href / button with deliberate type |
| Data entry | form, explicit label/control associations, native inputs |
| Related controls | fieldset and legend where the grouping is real |
| Disclosure / modal | details/summary or dialog when behavior fits |
| Captioned media / machine-readable time | figure/figcaption / time with datetime |
| Layout-only or inline styling | div/span where no suitable semantic element exists |

Do not mechanically replace wrappers with section/article, set numeric div limits or recreate native controls with ARIA. Use ARIA only for missing information/behavior, not to override correct native roles. Label distinct landmarks without making every panel a landmark. Preserve valid list/table/form nesting and meaningful reading order.

Full documents own landmarks. Partial updates must fit their targets without duplicate main elements, nested forms or invalid children. Preserve IDs, labels, focus, fallback behavior and authoritative-state contracts after each update. Semantics do not authorize indexing private content.

## Interaction and state
Use approved tokens/components and test supported themes. Provide persistent input labels, visible keyboard focus, non-color-only status, accessible control names and logical tab order. Provide any no-script or plain-form fallback the adopted stack profile requires. Confirmation is selective for irreversible destruction; undo requires a real reversal contract.

Preserve submitted values on validation/network errors. Show field errors and an accessible summary; distinguish empty first use, no matching results, unavailable data, loading, success, conflict and permission failure. Do not claim success before authoritative persistence or leave indefinite loading states. Modal focus placement, containment, dismissal and return must be verified.

## Responsive and accessible behavior
Adopt the target and matrix in PROJECT_PROFILE.md; for web projects consider WCAG 2.2 AA as the baseline target unless another requirement governs. Test narrow-screen overflow, configured breakpoints, text resizing/zoom, contrast, reduced motion, keyboard and focus-not-obscured behavior. Isolate deliberate wide-table scrolling in a labelled usable region. Prefer summaries on narrow screens when the task permits; preserve tabular comparison where needed.

Record manual touch, assistive-technology, forced-colors and environmental checks separately from automated checks. A framework class or zero automated accessibility violations is not complete conformance evidence.

## Visual design direction

When creating or substantially redesigning an interface, establish a coherent visual direction appropriate to the application's purpose, audience, and workflows.

- Define or reuse the application's visual identity, including typography, color palette, spacing, information density, component styling, and motion.
- Prefer existing design tokens, components, and visual conventions over introducing new ones.
- When no visual direction exists, propose one before implementing significant UI changes.
- Design skills or tools available to your agent may assist with visual exploration and refinement but must not override adopted project requirements.
- Visual distinctiveness must not compromise accessibility, semantic HTML, usability, consistency, or established interaction patterns.
- Follow the verification requirements in [UX_ACCEPTANCE_CHECKLIST.md](UX_ACCEPTANCE_CHECKLIST.md). A design tool's self-review does not replace project acceptance criteria.

## Search and performance
For supported searchable collections, expose active filters, result counts and clear actions. Represent shareable state in coherent navigable URLs where applicable; preserve Back/Forward behavior. Live search needs bounded debounce and stale-response protection plus usable direct submission. Announce meaningful changes politely, not every keystroke. Use pagination/bounded data access according to the adopted contract.

## Done
All affected required journeys, states, semantic composition, supported viewports/themes/engines, focus/input and fallback behaviors must have evidence. Documentation updates follow the routing table in [AGENTS.md](../AGENTS.md).
