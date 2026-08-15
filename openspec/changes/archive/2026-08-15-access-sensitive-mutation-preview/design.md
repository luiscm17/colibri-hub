# Design: Access Sensitive Mutation Preview

## Technical Approach

Use one lifecycle—`draft -> previewing -> ready -> applying -> reconcile`—for both replacements. `UserRoleReplacementPanel` owns the user operation; `RoleWorkflow` owns the shared-role operation and #83 permission matrix. Shared primitives normalize/correlate requests and render impact, but never own another role workflow. #82 routing and dirty-departure remain unchanged.

## Architecture Decisions

| Option | Tradeoff | Decision and rationale |
|---|---|---|
| Shared workflow provider/reducer | Centralizes both capabilities but obscures subject ownership | Reject; each owning workflow holds local ephemeral state. |
| Reusable correlation/gate policy | Small duplication-free safety seam without parallel UI authority | Choose; extend the existing gates around a normalized fingerprint. |
| Keep `SharedRolePermissionPanel` | Lower migration effort but preserves two PUT authorities | Delete; `RoleWorkflow` must be the sole role preview/confirm/apply owner. |
| Auto-retry after refresh | Convenient but may replay stale intent | Reject; refresh authority/detail only, then require a fresh preview and confirmation. |

## State, Correlation, and Flow

Each owner holds draft, reason, preview/impact, confirmation, message, request generation, preview `AbortController`, apply lock, and focus targets. Access owns authority/session; the loaded entity owns baseline/version.

`fingerprint = JSON.stringify([operation, subjectId, subjectVersion, authorityGeneration, normalizedPermissions, normalizedName, normalizedDescription, reason, requestGeneration])`. Permissions are trimmed, deduplicated, and sorted by `action + scopeId`; name is trimmed; description maps trimmed empty to `null`; omitted reason maps to `""` (no #85 policy inference). Any correlated edit aborts preview and clears preview/confirmation. Only the latest matching, non-aborted generation publishes. Apply captures the accepted fingerprint/version, uses a synchronous lock, emits one PUT, and never replays.

    draft -> POST preview -> exact ready -> explicit confirm -> one PUT
      ^          X stale/abort            |                 |
      +----- edit/error/new preview -------+        GET authoritative detail

A full semantic no-op compares permissions, name, and description and blocks preview/apply even when reason changed. Metadata-only change is valid: preview backend permission impact, display a separately labeled local metadata diff, then confirm the complete update.

## Outcome Transitions

| Outcome | State handling | Recovery |
|---|---|---|
| `401` / session end | Abort; clear draft, reason, identities, preview, confirmation, locks | Authentication handoff; no replay |
| `403` / authority change | Clear protected state; refresh Access once | Reevaluate route/action; fresh preview only |
| `access_version_conflict` | Keep safe proposed draft/reason; clear gate; fetch current detail | Compare, edit, preview again |
| `last_system_administrator_required` | Keep safe draft; clear confirmation/preview | Explain invariant; preview again after edit |
| invalid response/invariant | Clear gate and protected preview evidence | Generic safe failure; authoritative refresh |
| network/server | Keep safe draft/reason; clear gate | Explicit retry starts preview, never PUT |
| abort/late response | Publish nothing | Latest request governs |
| success | Clear gate/draft reason; reconcile detail and Access if affected | Focus updated result; announce success |

## Interfaces and File Changes

| File | Action | Description |
|---|---|---|
| `frontend/src/features/access-control/administration/mutations/sensitive-mutation-gate.ts` | Create | Generic fingerprint, generation, abort/latest-only, confirmation, and apply-lock policy. |
| `.../mutations/user-role-gate.ts` | Modify | Adapt user request/body to canonical policy. |
| `.../mutations/shared-role-gate.ts` | Modify | Adapt full role draft, metadata, reason, and preview version for `RoleWorkflow`. |
| `.../mutations/UserRoleReplacementPanel.tsx` | Modify | Canonical flow, protected clearing, reconciliation callback, focus/live status. |
| `.../roles/RoleWorkflow.tsx` | Modify | Own role preview/confirm/PUT; retain #83 matrix and report #82 dirty state. |
| `.../mutations/SharedRolePermissionPanel.tsx` | Delete | Remove parallel shared-role authority. |
| `.../mutations/ImpactPreview.tsx` | Modify | Count-first summary; `aria-expanded`/`aria-controls` disclosure with complete identities; separate non-color metadata diff. |
| Gate, panel, workflow, accessibility, and `AdministrationPage.test.tsx` tests | Modify/Create | Reducer/gate seams, mocked `httpJson`, Access-provider transitions, focus and reconciliation. |
| `frontend/docs/features/access-control.md` | Modify | Document canonical ownership, transition table, privacy, evidence, and #85 coordination boundary only. |

The owner contract exposes `edit`, `preview`, `confirm`, `apply`, `invalidate`, and `reconcile`; presentation consumes state/actions/meta rather than transport internals.

## Testing and Evidence

Vitest unit tests cover normalization, no-op/metadata-only, reason invalidation, late/abort rejection, duplicate apply, every transition above, and no replay. Component tests prove both operations, sole role PUT authority, #82 dirty departure, #83 matrix behavior, count-first expansion, `role=status`/live announcements, focus after preview/error/success, accessible expand/collapse state, keyboard operation, non-color distinction, narrow-layout visibility, and protected clearing. Evidence records focused Vitest, build/lint, and mocked request counts. The sole remaining manual closure scenario is a maintainer-controlled real shared-role revoked-authority `403`; a real screen-reader journey is not a closure gate. No services run during design.

## Threat Matrix

N/A — this change preserves routes and introduces no shell, subprocess, VCS/PR, executable classification, or process-integration boundary.

## Rollout, Review, and Rollback

No migration or flag. Forecast exceeds 400 authored lines: auto-chain into (1) canonical policy + user flow and (2) `RoleWorkflow` authority migration + deletion + docs/evidence, each with tests and independent rollback. Roll back #84 workflow/policy/UI/docs together; restore prior #83 `RoleWorkflow` behavior, never the deleted parallel authority. #85 may later strengthen reason policy through the same fingerprint/wire seam without changing this lifecycle.

## Open Questions

None.
