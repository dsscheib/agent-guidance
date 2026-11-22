---
name: ui-design
description: Design or substantially improve a user interface, visual direction, layout, theme, or interactive workflow. Use when building a new app UI, establishing a design direction, creating or redesigning screens and components, or polishing visual hierarchy, responsiveness, and interaction states. Do not use for backend-only work, API-only changes, or minor copy edits.
---
# UI and interaction design

Goal: produce interfaces with intentional visual craft, clear hierarchy, and responsive, truthful interactions—never generic framework defaults—while holding accessibility and semantics as a non-negotiable floor.

## 1. Inspect project context first
Read [docs/UI.md](../UI.md), the existing stylesheets/tokens, and the screens around your change. Never invent a competing design system when one already exists.

Choose the mode that matches the repository:
- **No visual direction yet (greenfield or unstyled):** Do not ship a stock component-library theme or generic SaaS boilerplate. Propose **2–3 genuinely distinct aesthetic directions** tailored to the product's domain and users—varying typography, palette/surfaces, density, layout rhythm, and tone—and show them as small runnable prototypes or live previews where practical. Ask the user to pick one (with your recommendation), then record the chosen direction, tokens, and component conventions in [docs/UI.md](../UI.md).
- **Design direction already exists:** Extend it confidently within its voice. Reuse its tokens, type scale, spacing, and components, and invest craft in layout composition, visual hierarchy, scannability, state transitions, and responsive ergonomics rather than introducing foreign colors or a second component library.

## 2. Design craft
Treat a component library (such as DaisyUI, Radix, or shadcn) as structural primitives—override its theme tokens so the application has its own identity.

- **Typography & hierarchy:** Make deliberate choices for display, UI/body, and monospace fonts. Use clear size/weight/contrast separation so the eye immediately finds the primary content and primary action. Use tabular numerals (`tabular-nums`) for tables, counts, timestamps, and measurements.
- **Color, surfaces & restraint:** Build around 1–2 dominant surface layers, crisp border/elevation contrast, one intentional accent color, and distinct semantic status colors—never encoding status by color alone. Verify every supported theme (light, dark, high contrast).
- **Spatial composition & density:** Match information density to the task (tight, scannable layouts for operator/data tools; generous breathing room for editorial or onboarding flows). Avoid "card soup" (wrapping every list item or metric in identical nested shadowed boxes); use alignment, whitespace, hairline dividers, and intentional grids.
- **Interaction & truthful states:** Design every real state with care—helpful first-run empty states (clear next action), filtered no-results states (with one-click reset), bounded loading/skeleton states (never spinning forever), inline validation that preserves user input, explicit conflict/error recovery, and confirmed success only after the authoritative save completes. Use restrained, purposeful motion and honor `prefers-reduced-motion`.
- **Avoid generic AI clichés:** Do not default to purple-blue neon gradients on dark cards, decorative pill badges above every heading, emoji bullets in place of icons, repetitive 3-column icon grids, or critical actions hidden behind hover.

## 3. Non-negotiable floor
Creative choices never override the accessibility, native-semantics, keyboard, reflow, and truthful-state requirements in [docs/UI.md](../UI.md) (including any project-specific accessibility target recorded in [PROJECT_PROFILE.md](../../PROJECT_PROFILE.md)) or any adopted stack profile (such as valid partial-swap DOM and plain-form fallback in server-rendered apps). For narrow viewports, put wide data tables in labelled scrolling regions or switch to a task-appropriate summary, and never hide critical workflows behind hover.

## 4. Team execution & verification
- **Delegation (when specialist roles are installed):** Consult any installed UX design specialist to sharpen flows, hierarchy, and acceptance criteria on substantial changes; delegate UI implementation to an installed frontend specialist (escalating per [AGENTS.md](../../AGENTS.md) for complex async or state logic); run live browser, responsive, and accessibility checks with an installed browser-testing specialist when available.
- **Verification & UAT handoff:** Follow the browser-verification and gap-recording rules in [docs/UI.md](../UI.md) (quoting `python3 scripts/verify.py --verify`) and the local UAT and batched-deployment rules in [AGENTS.md](../../AGENTS.md), naming the key journeys, states, viewports, and themes to inspect.
