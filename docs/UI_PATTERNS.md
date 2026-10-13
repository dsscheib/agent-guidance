# Reusable interaction patterns

Status: Pattern contracts to adopt for applicable interfaces; no application routes or components are implied.

## Page and fragments
A full web document owns one visible main landmark, meaningful headings and applicable header/navigation/footer. Include a usable skip link when appropriate. Fragments fit the target's native content model and must not introduce nested forms, duplicate IDs/landmarks or broken label associations. Verify both initial DOM and post-replacement DOM. Generic wrappers support layout, not replacements for native meaning.

## Forms
Use native forms/controls and explicit label-for/id associations. Group actual related controls with fieldset/legend. Associate descriptions/errors with controls; indicate invalid states in text and programmatically. Preserve safe submitted values, present an accessible summary and make recovery possible. Direct submission and enhanced submission share authoritative validation and consequential effects.

## Collections and metadata
Use semantic tables for comparison, labelled scrolling when needed, meaningful captions and header scope. Put sorting controls in headers with visible direction and appropriate aria-sort. Use lists for repeated summaries and dl/dt/dd for metadata. Do not fabricate selection/bulk actions or unsupported fields.

## Dialogs and feedback
Use native dialog when suitable; verify focus containment/return, keyboard behavior and appropriate dismissal. Keep failed submissions visible with their input/errors. Close after a confirmed successful result, not every response. Use polite status announcements for ordinary success/results and assertive alerts selectively for meaningful errors. Dismiss buttons require accessible names.

## Navigation and enhancements
Links navigate; buttons act and specify type. Support disclosure controls with native behavior where feasible. Preserve search/filter URLs, browser history and return context. Enhanced requests have documented target/swap, error, expiry and focus contracts. Reinitialize local components after replacement without duplicating listeners or mirroring persistent truth.

## Review record
| Pattern | Adopted implementation | Direct/fallback behavior | Dynamic/error/focus evidence |
|---|---|---|---|
| {{PATTERN}} | {{SOURCE_REFERENCE}} | {{FALLBACK_CONTRACT}} | Not verified |

Use the selected technology profile for concrete framework attributes. Examples must use real inspected interfaces or be explicitly illustrative.
