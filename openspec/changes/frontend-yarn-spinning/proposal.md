# Proposal: Complete Frontend Yarn Spinning

## Intent

Replace the Yarn Spinning title-only page with accessible, responsive operational experiences for capture, review, correction, and reporting. Preserve server authority for business outcomes and authorization; until real backend APIs exist, dependent screens show an explicit unavailable integration state.

## Scope

### In Scope
- Five section workspaces, including Skeining, with atomic production/progress capture, draft recovery, and Progress continuity presentation.
- Independent Process Quality profile configuration/capture and Waste capture/review experiences.
- Section and consolidated dashboards, record reads, corrections/history, conflict recovery, responsive layouts, and WCAG 2.1 AA interaction states.
- Chained, reviewable frontend delivery slices with each slice targeting no more than 400 changed lines where practical.

### Out of Scope
- Backend implementation, persistence, calculations, API-contract changes, or fabricated client-side outcomes.
- RBAC/Access-Control roles, scopes, policy, or permission evaluation.
- Lot Processing behavior, reference-data administration, charts, planning, and deferred dashboard metrics.

## Capabilities

### New Capabilities
- `frontend-yarn-spinning`: Route-composed Yarn Spinning capture, Quality, Waste, reporting, records, correction, recovery, accessibility, and responsive behavior.

### Modified Capabilities
None.

## Approach

Create a capability-first `spinning` public boundary. Keep section capture, Quality, Waste, dashboards/records, and corrections as independent responsibility areas; app routes compose them through existing protected-route outcomes. Use typed adapters over `httpJson`, abort obsolete reads, retain drafts on recoverable failures, and never calculate server-owned values. Implement contract-shaped unavailable states now; wire live APIs only when the planned backend contract is delivered. Plan chained slices: foundation/sections; Progress/Skeining; Quality; Waste; dashboards/records; corrections/recovery; accessibility/responsive verification.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/features/spinning/` | Modified | Capability boundary, route compositions, state, adapters, and UI. |
| `frontend/src/app/routes/` | Modified | Compose destinations without replacing protection. |
| `frontend/src/api/httpClient.ts` | Modified | Reuse transport/error seam if required. |
| `frontend/docs/features/yarn-spinning.md` | Modified | Maintain delivery traceability. |
| `backend/docs/features/yarn-spinning.md` | Dependency | Planned integration contract only. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Backend contract is unavailable or evolves | High | Explicit unavailable states and isolated adapters. |
| Monolithic UI loses independent lifecycles | Medium | Capability-first slices and contracts. |
| Dense workflows exclude users | Medium | Keyboard, focus, status, overflow, and responsive acceptance checks. |

## Rollback Plan

Revert the affected chained slice. Existing protected routes remain intact; remove its route composition or adapter while retaining the title-only fallback until a replacement is verified.

## Dependencies

- Planned backend Yarn Spinning API contract and authorized reference-data reads.
- Existing authentication, protected routes, and server authorization outcomes.

## Success Criteria

- [ ] All frontend specification workflows have contract-shaped, accessible UI states.
- [ ] Backend-dependent actions are explicitly unavailable until real APIs exist; no local policy or calculation is introduced.
- [ ] Each delivery slice is independently reversible and planned within the 400-line review budget.
