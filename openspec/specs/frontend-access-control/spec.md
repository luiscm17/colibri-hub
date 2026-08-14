# Delta for Frontend Access Control

## ADDED Requirements

### Requirement: Administration Operation Matrix
Only backend-authorized System Administrators SHALL access administration. Default-deny UI MUST expose Users collection/detail/replacement/lifecycle; Roles/Presets collection/detail/create/edit/lifecycle; Scopes collection/recognized registration/lifecycle; History collection with only `subject_type`, `change_kind`, `date_from`, `date_to`. Scope/History detail, Access user-create, direct permissions, role-members, speculative requests MUST NOT exist. Labels, visibility, prefixes, inactive scopes MUST NOT authorize; reserved actions require System Administrator.

#### Scenario: Direct entry
- GIVEN an authorized supported URL
- WHEN it initializes or refreshes
- THEN it reconstructs without a mounted row

#### Scenario: Prohibited state
- GIVEN a prohibited URL or action
- WHEN requested
- THEN no protected view or request is emitted

## MODIFIED Requirements

### Requirement: Addressable Administration
Administrators MUST reach matrix-supported stable states. Entry captures origin (family, criteria, page, subject); dirty Back/Cancel/departure SHALL confirm discard. Confirm clears/restores; decline preserves URL/draft. Missing, denied, stale, invalid, aborted, empty-page results MUST recover to nearest permitted state. Refresh is latest-only; abandoned requests silent; pages reconcile without loops.
(Previously: all families broadly supported detail/create/edit.)

#### Scenario: Origin and discard
- GIVEN a dirty edit from filtered page two
- WHEN discard is confirmed
- THEN draft clears and exact origin restores

#### Scenario: Recovery
- GIVEN a stale subject or empty page
- WHEN resolution completes
- THEN nearest permitted state publishes without old content

### Requirement: Governance and History
Roles/presets MUST use recognized-scope, supported-action matrices; unsupported/reserved pairs and inactive scopes MUST be unavailable for new grants. Inactive references SHALL be historical/read-only/removable. Exact copy uses its contract; adjustable draft uses role creation; both copy once and MUST NOT synchronize. Scopes MUST register unregistered recognized definitions, use collection version for lifecycle, grant no permissions. History SHALL render actor, time, reason, subject, change kind, four filters only; it MUST NOT fabricate before/after/detail.
(Previously: governance did not distinguish preset flows or constrained History.)

#### Scenario: Matrix
- GIVEN a role draft with an inactive reference
- WHEN permissions are edited
- THEN only supported active pairs are selectable; reference is removable

#### Scenario: Preset independence
- GIVEN either preset flow
- WHEN its role is created
- THEN it is independent of its preset

### Requirement: Mutation and Concurrency
Only complete user-role and shared-role permission replacements MUST preview. Preview MUST bind operation, subject, normalized fingerprint, `subject_version`, authority/session/request generation; edits, `409`, authority/session change, late/aborted responses invalidate it. Apply needs one confirmation, non-zero delta, preview version; duplicate/replay forbidden. Preview MUST label impact—not membership—with total, first six, accessible expansion. Metadata is local summary, distinct from backend impact. One optional final reason applies atomically; omission sends `""`, never fabricated. #85 owns durable policy; only PRD-explicit exceptional interventions require a reason.
(Previously: preview/reason/invalidation covered broader mutation families.)

#### Scenario: Fresh replacement
- GIVEN a non-zero replacement draft
- WHEN its current preview is confirmed
- THEN one apply uses its preview version and labeled impact

#### Scenario: Invalidated replacement
- GIVEN a ready preview
- WHEN `409`, last-admin rejection, `403`, `401`, or session replacement occurs
- THEN confirmation invalidates, no replay occurs, and protected drafts clear on access loss

### Requirement: Accessible, Safe, and Evidenced Delivery
Only latest results MAY publish; duplicates MUST be blocked. Controls SHALL announce changes; focus returns after discard/confirmation. Added/removed values MUST not rely on color; narrow layouts retain impact/actions. Drafts/previews MUST NOT enter URLs, storage, logs, analytics, or post-session disclosure. Real-backend runtime/manual evidence SHALL cover routing/recovery, governance/History, both mutations, conflicts, `403`/`401`, no replay, responsive, assistive technology.
(Previously: evidence did not enumerate corrective workflows.)

#### Scenario: Accessible safe delivery
- GIVEN confirmation, session end, or narrow viewport
- WHEN state changes
- THEN focus, announcements, critical content, and clearing are correct

#### Scenario: Evidence
- GIVEN corrective journeys are reviewed
- WHEN evidence is recorded
- THEN it proves supported workflows without mock substitution

## Unchanged and Out of Scope
Authentication provisioning, authorization redesign, new preview/reservation/idempotency or role-members contracts, Scope/History detail, audit before/after transport, direct permissions, and #78 remain unchanged. Backend authorization remains authoritative.
