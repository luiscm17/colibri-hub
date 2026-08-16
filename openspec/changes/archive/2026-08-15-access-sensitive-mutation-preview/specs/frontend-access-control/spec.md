# Delta for Frontend Access Control

## ADDED Requirements

### Requirement: Canonical Shared-Role Mutation Authority

`RoleWorkflow` MUST be the sole frontend authority that can preview, confirm, and apply a shared-role update. Any parallel shared-role apply authority MUST be retired; consumers SHALL use the canonical workflow contract. This coordinates with #85's reason policy without implementing or redefining it.

#### Scenario: Canonical shared-role update
- GIVEN an administrator edits a shared role
- WHEN preview or apply is requested
- THEN only `RoleWorkflow` owns the mutation lifecycle
- AND no parallel path can emit the shared-role PUT

#### Scenario: Reason-policy boundary
- GIVEN a supplied optional reason
- WHEN the workflow sends a valid mutation
- THEN it preserves the existing wire contract
- AND #85 remains authoritative for reason policy

## MODIFIED Requirements

### Requirement: Mutation and Concurrency

Only complete user-role replacement and complete shared-role update MUST preview. No sensitive PUT MAY be emitted without one explicit confirmation of a fresh, exact matching preview. Correlation SHALL include operation, subject, normalized permissions, name, description, reason, `subject_version`, authority/session, and request generation. The backend-derived permission impact MUST remain distinct from the local metadata diff. A full semantic no-op (unchanged permissions, name, and description) MUST NOT apply; metadata-only changes MUST preview and confirm. Any relevant edit, including reason-only or metadata-only edit, `access_version_conflict`, `last_system_administrator_required`, `401`, `403`, session/authority change, late/aborted response, or failed apply MUST invalidate confirmation. At most one apply MAY be pending; another apply MUST NOT emit a PUT, and automatic replay is forbidden. Omission sends `""`, never fabricated; #85 owns durable reason policy.
(Previously: preview correlation omitted full role metadata/reason lifecycle and did not require the canonical shared-role path.)

#### Scenario: Fresh user-role replacement
- GIVEN a non-no-op complete user-role draft and exact current preview
- WHEN the administrator explicitly confirms
- THEN exactly one user-role PUT uses that preview version

#### Scenario: Metadata-only shared-role update
- GIVEN permissions are unchanged but name or description changes
- WHEN the administrator receives and confirms a fresh preview
- THEN one shared-role PUT is permitted with a separate local metadata diff

#### Scenario: Full semantic no-op
- GIVEN normalized permissions, name, and description are unchanged
- WHEN preview or apply is requested, including after a reason-only edit
- THEN the PUT is blocked

#### Scenario: Invalidation and pending apply
- GIVEN a preview is ready or an apply is pending
- WHEN a correlated value changes or a listed conflict, denial, session, authority, or failure occurs
- THEN confirmation is cleared, protected state clears on access loss, and no replay or second PUT occurs

#### Scenario: Recoverable domain rejection
- GIVEN apply returns `access_version_conflict` or `last_system_administrator_required`
- WHEN the error is handled
- THEN the workflow retains only safe recoverable context, requires a new preview, and never retries automatically

### Requirement: Accessible, Safe, and Evidenced Delivery

Only latest results MAY publish; duplicates MUST be blocked. Preview impact SHALL present the backend total first and offer an accessible expandable disclosure containing the complete affected-user evidence; it MUST NOT call impact membership. Local metadata changes MUST remain separately labeled. Controls SHALL announce changes through a status/live region; after successful apply, the UI MUST reconcile authoritative success, clear local preview/confirmation state, and move focus to a meaningful updated result. Expand/collapse state MUST be programmatically exposed, controls MUST remain keyboard operable, added/removed values MUST not rely on color, and narrow layouts MUST retain impact/actions. Drafts, previews, user evidence, and reasons MUST NOT enter URLs, storage, logs, analytics, or post-session disclosure. Automated and code-level evidence SHALL cover both mutations, conflicts, denials, no replay, large impact, focus, status/live announcements, disclosure state, keyboard operation, non-color distinction, and responsive visibility. The sole manual closure scenario SHALL be a real shared-role revoked-authority `403`; real screen-reader execution is not a closure gate.
(Previously: impact disclosure, success reconciliation, and privacy boundaries were less specific.)

#### Scenario: Count-first impact evidence
- GIVEN a preview affects users
- WHEN it is presented
- THEN the total appears before the disclosure
- AND expansion exposes all affected identities accessibly

#### Scenario: Successful apply
- GIVEN a confirmed sensitive mutation succeeds
- WHEN authoritative results reconcile
- THEN stale local gate state clears and focus reaches the updated result

#### Scenario: Private error and session handling
- GIVEN denial, session loss, or a recorded evidence journey
- WHEN state or diagnostics are produced
- THEN protected details clear and no sensitive draft, preview, reason, or identities are disclosed

#### Scenario: Automated accessibility contract
- GIVEN a preview, disclosure, outcome, and narrow layout are rendered
- WHEN focused automated and component evidence runs
- THEN it proves meaningful focus, status/live announcement semantics, exposed expand/collapse state, keyboard operation, non-color distinction, and responsive visibility

#### Scenario: Manual revoked-authority closure
- GIVEN an administrator has a real shared-role preview and authority is actually revoked before apply
- WHEN the confirmed shared-role PUT returns `403`
- THEN one access refresh occurs, protected state clears, no replay occurs, and only safe persistent recovery feedback remains
- AND real screen-reader execution is not required to close this change

## Unchanged and Out of Scope

#78 selection/membership, #85 implementation, #86, endpoints, backend authorization/calculation/wire contracts, and broad #82/#83 changes remain out of scope. Backend authorization, versions, and invariants remain authoritative.
