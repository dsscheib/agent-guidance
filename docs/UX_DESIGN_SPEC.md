# UX and accessibility specification

Kind: Policy. It applies as written; changing it needs an owner decision. The product-context field is a template, filled at bootstrap or by owner decision; a feature change does not edit this document. Applies only to projects with a UI.

## Adopted product context
{{USERS_PRIMARY_JOURNEYS_NAVIGATION_DENSITY_AND_SUPPORTED_DEVICES}}
Keep existing presentation defaults until an authorized decision changes them. Density, navigation shell and presentation mode are separate choices. Show only actions the product supports and values the model actually holds. Keep identities, units, "unknown" and zero visibly distinct.

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
Use approved tokens and components, and test every supported theme. Every interface provides:
- labels that stay visible on inputs,
- visible keyboard focus and a logical tab order,
- status that does not rely on color alone,
- accessible names for every control,
- any no-script or plain-form fallback the adopted stack profile requires.

Ask for confirmation only before irreversible destruction. Offer undo only when there is a real way to reverse the action.

Keep submitted values when validation or the network fails. Show errors next to their fields, plus an accessible summary. Show each of these states distinctly: empty on first use, no matching results, data unavailable, loading, success, conflict and permission denied. Never report success before the authoritative store has saved the change, and never leave a loading state running indefinitely. Verify where a modal places focus, that focus stays inside it, how it is dismissed, and where focus returns.

## Responsive and accessible behavior
Adopt the accessibility target and test matrix in PROJECT_PROFILE.md. For web projects, consider WCAG 2.2 AA the baseline unless another requirement governs. Test:
- overflow on narrow screens and at the configured breakpoints,
- text resizing and zoom,
- contrast and reduced motion,
- keyboard use, including focus that is never hidden behind other content.

When a wide table must scroll, put it in its own labelled scrolling region. On narrow screens, prefer a summary when the task allows it, and keep the table when users need to compare rows.

Record manual checks (touch, assistive technology, forced colors, real use environments) separately from automated ones. A framework class, or a scan with zero violations, is not full conformance evidence.

## Visual design direction

When creating or substantially redesigning an interface, establish a coherent visual direction appropriate to the application's purpose, audience, and workflows.

- Define or reuse the application's visual identity, including typography, color palette, spacing, information density, component styling, and motion.
- Prefer existing design tokens, components, and visual conventions over introducing new ones.
- When no visual direction exists, propose one before implementing significant UI changes.
- Design skills or tools available to your agent may assist with visual exploration and refinement but must not override adopted project requirements.
- Visual distinctiveness must not compromise accessibility, semantic HTML, usability, consistency, or established interaction patterns.
- Follow the verification requirements in [UX_ACCEPTANCE_CHECKLIST.md](UX_ACCEPTANCE_CHECKLIST.md). A design tool's self-review does not replace project acceptance criteria.

## Search and performance
For searchable collections, show the active filters, the result count and a way to clear them. Put shareable state, such as the query, filters and page, in the URL where it applies, and keep Back and Forward working. Live search needs a bounded debounce, protection against stale responses, and a submit action that works on its own. Announce meaningful result changes politely, not on every keystroke. Page or bound data access as the adopted contract says.

## Done
A UI change is done when the affected journeys, states, semantic structure, focus and input behavior, and fallbacks have evidence for the phase you are in: the development gates for each change, and the full viewport, theme and engine matrix at release ([TESTING_SPEC.md](TESTING_SPEC.md#development-and-release-gates)). Documentation updates follow the routing table in [AGENTS.md](../AGENTS.md).
