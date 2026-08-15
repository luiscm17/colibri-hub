# Tasks: Access Sensitive Mutation Preview

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 620–800 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 user gate/flow → PR 2 canonical shared-role flow; tracker `front/access-auth-foundation` |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Canonical gate and user replacement | `front/access-sensitive-mutation-preview` PR → `front/access-auth-foundation` tracker | `pnpm vitest run src/features/access-control/administration/mutations/user-role-gate.test.ts src/features/access-control/administration/mutations/accessibility.test.tsx` | Browser: preview, confirm once, edit reason, confirm blocked | Gate, user panel, and their tests |
| 2 | #83 role authority migration and evidence | Child PR base → `front/access-sensitive-mutation-preview`; rebase/retarget to tracker after PR 1 | `pnpm vitest run src/features/access-control/administration/roles/RoleWorkflow.test.tsx src/features/access-control/administration/AdministrationPage.test.tsx` | Real shared-role revoked-authority `403`: one preview POST, one PUT `403`, one `/access/me` refresh, protected-state clearing, no replay, safe persistent recovery feedback | Role workflow, deleted parallel panel, docs, and tests |

## Phase 1: Canonical Gate and User Flow (PR 1)

- [x] 1.1 RED: add `sensitive-mutation-gate.test.ts` for normalized fingerprint, semantic no-op, reason/metadata invalidation, late/aborted preview, one apply, no replay, and 401/403/conflict safe clearing.
- [x] 1.2 Create `mutations/sensitive-mutation-gate.ts`; implement generation, abort/latest-only publishing, explicit confirmation, synchronous apply lock, and protected-state transitions.
- [x] 1.3 Modify `mutations/user-role-gate.ts` and `UserRoleReplacementPanel.tsx` to use the policy; verify exact preview/version before one PUT, reconciliation, live status, and focus.
- [x] 1.4 Extend `mutations/accessibility.test.tsx` for user count-first impact, accessible complete disclosure, non-color diff, narrow layout, and #82 dirty-departure preservation.

## Phase 2: Sole Shared-Role Authority (PR 2)

- [x] 2.1 RED: extend `roles/RoleWorkflow.test.tsx` for metadata-only confirmation, full no-op block, stale/reason invalidation, rejection recovery, and no duplicate/shared-role PUT.
- [x] 2.2 Modify `roles/RoleWorkflow.tsx` and `mutations/shared-role-gate.ts` to own preview/confirm/apply, retain the #83 matrix and #82 dirty contract, and preserve existing reason wire semantics.
- [x] 2.3 Modify `mutations/ImpactPreview.tsx` for count-first `aria-expanded` disclosure of all identities and separate labeled metadata diff; delete `mutations/SharedRolePermissionPanel.tsx`.
- [x] 2.4 Extend `AdministrationPage.test.tsx` with a no-bypass proof: only `RoleWorkflow` can emit shared-role PUT; verify success reconciliation, focus, denial/session clearing, and private diagnostics.

## Phase 3: Documentation and Evidence Plan

- [x] 3.1 Update `frontend/docs/features/access-control.md` with canonical ownership, lifecycle, privacy, #85 boundary, rollback, and explicit exclusions (#78, #86, backend contracts, broad #82/#83 work).
- [x] 3.2 Run each unit’s focused Vitest command plus `pnpm lint` and `pnpm build` from `frontend/`; record request-count assertions and outcomes with its work unit.
- [x] 3.3 Retain automated and code-level evidence for focus, `role=status`/live announcement, accessible expand/collapse state, keyboard operation, non-color distinction, and responsive visibility; plan only the maintainer-controlled real shared-role revoked-authority `403` closure scenario, with redacted metadata and no replay.
- [x] 3.4 Align scope: real VoiceOver/NVDA or other manual screen-reader execution is not a closure gate; the manual guide contains only the remaining shared-role revoked-authority `403` scenario.
