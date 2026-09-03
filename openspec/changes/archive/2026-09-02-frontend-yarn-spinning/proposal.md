# Proposal: Complete Frontend Yarn Spinning

## Intent

Replace the title-only page with accessible operational capture, review, correction, and reporting grids. Server results, calculations, and authorization remain authoritative; unavailable integrations remain explicit.

## Scope

### In Scope
- Repeatable spreadsheet-style Production Discharge grids for applicable sections; every row is a distinct event.
- A separate unique per-machine-and-yarn-count Progress summary grid only for Preparation PSJ, Ring Spinning, and Twisting, with server-derived continuity. Bobbin Winding and Skeining have no Progress.
- Separate Skeining production, independent Waste, and ordered Quality Sample React Data Grids.
- Independent Quality configuration/capture, Waste review, dashboards, records, corrections, recovery, responsive layouts, and WCAG 2.1 AA states.
- Chained frontend slices targeting 400 changed lines where practical.

### Out of Scope
- Backend implementation, persistence, API changes, client calculation/aggregation, or fabricated outcomes.
- RBAC/Access-Control policy, roles, scopes, or evaluation.
- Skeining Lot Processing behavior, reference-data administration, charts, planning, and deferred dashboard metrics.

## Capabilities

### New Capabilities
- `frontend-yarn-spinning`: Route-composed Yarn Spinning capture, Quality, Waste, reporting, corrections, recovery, accessibility, and responsive behavior.

### Modified Capabilities
None.

## Approach

Create a capability-first `spinning` public boundary. Compose section workspaces from applicable grids, never a generic form: repeatable discharge events, distinct applicable Progress summaries, and Skeining-only production. Keep Quality, Waste, dashboards/records, and corrections independent. Routes consume protected outcomes; typed `httpJson` adapters retain drafts, reject obsolete reads, and render backend-confirmed values only. Slice delivery by grid foundation/sections, Progress/Skeining, Quality, Waste, dashboards/records, corrections/recovery, then accessibility/responsiveness.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/features/spinning/` | Modified | Capability boundary, grid composition, state, adapters, and UI. |
| `frontend/src/app/routes/` | Modified | Compose destinations without changing protection. |
| `frontend/docs/features/yarn-spinning.md` | Dependency | Authoritative interaction contract; no change proposed. |
| Backend Yarn Spinning APIs | Dependency | Future contract consumed without API changes. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Backend contract evolves | High | Isolated adapters and unavailable states. |
| Grids blur server-owned semantics | Medium | Distinct event/summary models; render confirmed results only. |
| Dense capture excludes users | Medium | Keyboard, focus, status, and overflow checks. |

## Rollback Plan

Revert the affected chained slice; remove its route composition or adapter while retaining the verified fallback.

## Dependencies

- Planned backend Yarn Spinning API and authorized reference-data reads.
- Existing authentication, protected routes, and server authorization outcomes.

## Success Criteria

- [ ] Applicable sections provide repeatable discharge grids; only Preparation PSJ, Ring Spinning, and Twisting provide Progress grids.
- [ ] Skeining, Waste, and Quality Sample use independent required grids, with no Skeining Lot Processing behavior.
- [ ] No client policy, aggregation, or calculation is introduced.
