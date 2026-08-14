# Proposal: Frontend Access Control Compliance

## Intent

Correct the completed `frontend-access-control` UI where visible administration workflows do not yet meet Access and Authentication PRDs. Preserve backend-authoritative, exact action/scope, default-deny authorization; do not rewrite the closed baseline.

## Scope

### In Scope
- Add only matrix-supported, addressable Access administration states with origin recovery and dirty-discard protection (#82).
- Deliver role/preset/scope governance and constrained History UI: two independent preset flows, recognized scopes, inactive-reference handling, and four existing History filters (#83).
- Gate user-role and shared-role permission replacements with fresh backend previews, one final confirmation, optional form-level reason, zero-delta blocking, and safe invalidation (#84).

### Out of Scope
- Scope or History detail, user creation owned by Access, role-members discovery, direct user permissions, audit before/after transport, and #78.
- Backend/API reason-policy alignment (#85), new preview/reservation/idempotency endpoints, or authorization redesign.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `frontend-access-control`: Correct administration, governance, and the two supported preview-confirmation workflows against the existing Access contract. (No `openspec/specs/` baseline is currently present; use the completed change's capability spec as the historical reference.)

## Approach

Use a contract-first, capability-owned delta. Encode the operation matrix: Users collection/detail/assignment-status only; Roles and Presets support collection/detail/create/edit/lifecycle; Scopes collection/recognized-definition registration/lifecycle only; History collection only with `subject_type`, `change_kind`, `date_from`, and `date_to`. Chain #82 → #83 → #84; keep #78 separate. Label preview users as proposed-change impact, show total plus six with accessible expansion, and distinguish local role metadata summary from backend-computed impact.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/features/access-control/administration/` | Modified | Supported routes, forms, matrix, history, previews. |
| `frontend/src/app/routes/index.tsx` | Modified | Matrix-constrained administration routing. |
| `openspec/changes/frontend-access-control/` | Reference | Historical baseline only; unchanged. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Unsupported detail/API expansion | High | Enforce operation matrix and no speculative requests. |
| Stale preview confirms mutation | High | Fingerprint/version binding; invalidate; never replay. |
| Dense work exceeds review budget | High | Auto-chain work units; split PR8/PR9 under 800 lines. |

## Rollback Plan

Revert the affected chained slice, clear protected drafts/previews, and retain the prior backend-authorized UI. Never replay mutations or alter the closed baseline.

## Dependencies

- #82 → #83 → #84; #78 remains independent.
- #85 owns durable optional-versus-required reason policy; omitted optional reasons may remain `reason: ""` for current wire compatibility and must never be fabricated.

## Success Criteria

- [ ] System Administrators alone can complete every matrix-supported workflow without speculative operations.
- [ ] Both previewed mutations block zero delta and apply only a fresh, explicitly confirmed, backend-authorized draft.
- [ ] Preset independence, constrained history, invalidation, accessibility, and no-replay behavior are proven per chained work unit.
