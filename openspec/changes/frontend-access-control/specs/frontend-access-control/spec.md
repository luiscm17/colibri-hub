# Frontend Access Control Specification

## Requirements

### Requirement: Access State and Handoff
Access MUST have exactly `waiting-for-authentication`, `loading`, `ready`, `blocked`, and `unavailable`. Only Authentication `authenticated + next_step=load_access` SHALL load; unresolved, ended/unauthenticated, and password-change-required clear Access; unavailable enters unavailable. `profile_not_found`/`profile_inactive` block; eligible retry reloads. Duplicate handoff MUST not duplicate bootstrap; refresh atomically replaces; stale bootstrap MUST NOT publish.

#### Scenario: Handoff
- GIVEN every Authentication condition
- WHEN its handoff arrives
- THEN only eligible Access loads; all other conditions expose no protected content
- Evidence: integration

#### Scenario: Stale bootstrap
- GIVEN duplicate handoff or newer refresh
- WHEN an earlier request resolves last
- THEN only the current atomic snapshot publishes
- Evidence: focused logic

### Requirement: Fail-Closed Decisions
The adapter MUST accept only complete ordinary/global variants and fail closed otherwise. Ordinary allows exact action/scope; global allows only supplied actions in any scope. Actions are independent; absence denies. `anyOf` requires one match; `allOf` every match.

#### Scenario: Decision
- GIVEN malformed, prefix-similar, wrong-action, global, and positive/negative compound grants
- WHEN decisions are evaluated
- THEN only declared exact/global Boolean outcomes allow
- Evidence: focused logic

### Requirement: Protected Capability Boundaries
Navigation, routes, history, and actions MUST share exact default-deny requirements; denied leaves and empty groups SHALL be omitted. The system SHALL preserve Frontend Access §4.3 mappings: Warehouse `raw_materials|finished_products|production_supplies`; Yarn sections plus `process_quality|waste`; Lot `lot_processing|stage.*`; transversal `consolidated_dashboard`. Scopes are independent; filters/shifts are neutral; `edit` differs from `edit_outside_window`; actions hide or disable consistently.

#### Scenario: Revocation
- GIVEN a direct/history destination or visible action with partial/revoked authority
- WHEN requirements are reevaluated or `403` occurs
- THEN protected content is withheld; safe input remains; one refresh occurs; no mutation replays
- Evidence: workflow; manual real-backend

### Requirement: Addressable Administration
Administrators MUST reach paginated Users, Roles, Presets, Scopes, and History collections, details, and create/edit without a mounted row. Dirty Back/Cancel SHALL confirm discard then restore origin criteria/page. Stale/missing subjects SHALL clear to nearest permitted fallback; refresh is latest-only and reconciles invalid/empty pages.

#### Scenario: Recovery
- GIVEN direct refresh, dirty Back, stale subject, or emptied page
- WHEN resolution completes
- THEN origin/page restore or permitted fallback is correct
- Evidence: integration; manual real-backend

### Requirement: Governance and History
Access MUST govern profile lifecycle, complete role replacement/reasons, inactive read-only assignments, matrices, and presets; profile creation/accounts remain Authentication-owned. Exact-copy and adjustable presets MUST create independent roles. Scopes MUST use recognized definitions, loaded versions/reasons/lifecycle, and grant no ordinary access. History SHALL use only `subject_type`, `change_kind`, `date_from`, `date_to`.

#### Scenario: Governance
- GIVEN inactive/reserved selection, preset flow, or unrecognized scope
- WHEN submitted
- THEN invalid configuration is unavailable and valid configuration is independent and traceable
- Evidence: interaction

### Requirement: Mutation and Concurrency
Role/assignment replacement MUST use fresh preview/confirmation/reasons and affected-user evidence. Preset/scope use loaded versions without preview; profile status has no conflict. Edit, `409`, or authority/session change MUST invalidate confirmation, preserve isolated safe drafts, reconcile success, reject last-administrator failure, and NEVER replay.

#### Scenario: Conflict
- GIVEN previewed role or assignment change
- WHEN edited or conflicted
- THEN current state loads separately and a fresh preview is required
- Evidence: integration; manual real-backend

### Requirement: Accessible, Safe, and Evidenced Delivery
Only latest results MAY publish; abandoned requests are silent, old subjects SHALL not flash, and duplicates MUST be blocked. Selectors SHALL announce loading/results/no-match/selection; History relationships and preview-return focus MUST be semantic. Unauthorized administration code/content SHALL defer; denied/session-end clears drafts without disclosure; responsive views retain critical content/actions. Each risk MUST use the narrowest focused-logic, interaction, integration, workflow, or manual evidence. Recorded real-backend manual evidence after user startup MUST cover handoff, `403`, pagination, mutations/conflicts, route recovery, responsive behavior, and assistive technology; mocks MUST NOT replace it.

#### Scenario: Evidence
- GIVEN switch, preview return, narrow viewport, session end, and evidence review
- WHEN each completes
- THEN safe content, announcements, focus, parity, clearing, and record exist
- Evidence: interaction; manual real-backend and assistive-technology
