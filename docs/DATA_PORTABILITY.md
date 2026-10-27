# Data portability and exchange

Kind: Policy with template fields. Applies only if the project imports or exports data; otherwise record an exclusion in PROJECT_PROFILE.md.

## Scope and formats
{{SHIPPED_FORMATS_VERSIONS_AND_INCLUSION_EXCLUSION}}
Distinguish human-editable exchange, logical full-fidelity transfer and operational backup. An export is not automatically a recoverable backup. Do not advertise full recovery while omitting relationships, history, required assets or configuration. Exclude secrets and reusable sessions from ordinary portable exports; define account inclusion explicitly.

## Identity and fidelity
Use stable identities and explicit referenced IDs; display names are not foreign keys. Specify format version, application/schema compatibility, scope, units, timestamps, encoding, null/unknown meaning and exact representations. Publish bounded synthetic examples of actual shipped schemas. Reject unsupported versions with clear errors; never silently reinterpret them.

## Import workflow
1. Select explicit intent and target scope; enforce permission.
2. Parse bounded input into isolated staging without persistent mutation.
3. Validate types, limits, identities, relationships, duplicates and conflict rules.
4. Preview create/update/skip/rejected counts, field clearing and consequential effects.
5. Confirm the disclosed operation, then commit under the adopted atomicity/idempotency contract.
6. Return sanitized row errors and a truthful summary with retry provenance.

Do not hold transactions while waiting for confirmation. All-or-nothing versus chunked/partial behavior is a product decision; declare it before commit and implement durable progress/retry protection when chunking. Re-import is not implicitly an additive operation. Occupied-target merge/remapping and empty-target restore are separate contracts.

## Security and consistency
Bound upload size, expansion, member count and parsing work. Reject archive traversal, absolute paths, unsafe symlinks and executable content; authorize downloads and use appropriate headers. Defend spreadsheet-oriented outputs against formula injection using an adopted escaping strategy. Lossy spreadsheet escaping must not be advertised as exact machine round-trip fidelity.

Capture a consistent declared scope and matching assets; avoid indefinite read transactions or unbounded memory. Validate manifests/checksums and source/target compatibility before changes. Export failure must leave the source intact. Test Unicode, special characters, missing/empty values, relationships, assets, versions, retries and conflicts against the promised fidelity.

## Acceptance
Document actual commands/UI steps, inclusion/exclusion and supported tools. Demonstrate an isolated round trip and relationship/invariant checks. Record implementation gaps without inventing planned interfaces or deferring adopted scope silently.
