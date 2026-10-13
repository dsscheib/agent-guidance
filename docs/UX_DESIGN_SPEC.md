# UX and accessibility specification

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

Full documents own landmarks. Dynamic fragments must fit their targets without duplicate main elements, nested forms or invalid children. Preserve IDs, labels, focus, fallback behavior and authoritative-state contracts after replacement. Semantics do not authorize indexing private content.

## Interaction and state
Use approved tokens/components and test supported themes. Provide persistent input labels, visible keyboard focus, non-color-only status, accessible control names and logical tab order. Keep native forms/navigable fallbacks for critical web tasks where feasible. Confirmation is selective for irreversible destruction; undo requires a real reversal contract.

Preserve submitted values on validation/network errors. Show field errors and an accessible summary; distinguish empty first use, no matching results, unavailable data, loading, success, conflict and permission failure. Do not claim success before authoritative persistence or leave indefinite loading states. Modal focus placement, containment, dismissal and return must be verified.

## Responsive and accessible behavior
Adopt the target and matrix in PROJECT_PROFILE.md; for web projects consider WCAG 2.2 AA as the baseline target unless another requirement governs. Test narrow-screen overflow, configured breakpoints, text resizing/zoom, contrast, reduced motion, keyboard and focus-not-obscured behavior. Isolate deliberate wide-table scrolling in a labelled usable region. Prefer summaries on narrow screens when the task permits; preserve tabular comparison where needed.

Record manual touch, assistive-technology, forced-colors and environmental checks separately from automated checks. A framework class or zero automated accessibility violations is not complete conformance evidence.

## Search and performance
For supported searchable collections, expose active filters, result counts and clear actions. Represent shareable state in coherent navigable URLs where applicable; preserve Back/Forward behavior. Live search needs bounded debounce and stale-response protection plus usable direct submission. Announce meaningful changes politely, not every keystroke. Use pagination/bounded data access according to the adopted contract.

## Done
All affected required journeys, states, semantic composition, supported viewports/themes/engines, focus/input and fallback behaviors must have evidence. Update recurring patterns and the UX acceptance checklist in the same work item.
