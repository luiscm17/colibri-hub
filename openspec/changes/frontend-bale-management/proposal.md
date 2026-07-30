# Proposal: Frontend Bale Management

## Intent

Replace the Warehouse reception prototype with frontend-only reception, stock, and delivery workflows against the documented contract.

## Scope

### In Scope
- Spanish `/warehouse/bales` landing page: exactly three accessible cards—Reception, Stock, Delivery—with no backend requests, metrics, or operational data.
- Reception grid: one batch, 1–100 bales, string decimals, calculated weight, continuation rows, keyboard/paste, local validation, and Spanish copy.
- Stock metrics, conjunctive filters, composite lookup, and a 1–50 identity delivery grid with results and retries.
- Typed API boundary, grid primitives, accessible feedback, lazy navigation, and removal of `/warehouse/reception` without redirect. Preserve the three workflow routes.

### Out of Scope
- Backend code, schema, endpoints, CORS, or contract changes.
- Authorization integration (including card visibility), delivery reversal, corrections, audit history, exhaustive listing, and dependencies.

## Capabilities

### New Capabilities
- `bale-management-landing-ui`: Accessible Bale Management landing navigation.
- `bale-reception-ui`: Spreadsheet reception and batch-registration flow.
- `bale-stock-ui`: Filtered stock summary and bale lookup flow.
- `bale-delivery-ui`: Spreadsheet delivery and retry flow.

### Modified Capabilities
None; `openspec/specs/` has no existing capabilities.

## Approach

Create `features/warehouse/bales/` with a static landing page, feature pages/API, and `common/grid/` primitives. The landing has only three Spanish cards; future authorization may govern visibility. Keep state local, decimals as scaled `BigInt`, and Mantine themes. Use notifications and cell errors. Reception has `Guardar` and `Limpiar`; delivery retains locked successes. Add `/warehouse/bales` without changing workflow routes.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/features/warehouse/` | Modified/New | Bale Management module and landing page. |
| `frontend/src/common/grid/` | New | Theme-aware grid editors and cells. |
| `frontend/src/app/routes/`, `navigation-data.tsx` | Modified | Landing route/navigation; preserve workflow routes; remove legacy route. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| API is unavailable | High | Typed boundary; preserve drafts. |
| Scope exceeds 400 lines | High | Forecast slices before apply. |
| Grid/accessibility defects | Med | BigInt model; keyboard, paste, theme validation. |
| Landing becomes a dashboard | Low | Restrict to cards; defer data and authorization. |

## Rollback Plan

Revert the frontend change set. No backend state or API changes; restore the prototype route only by source revert, never redirect.

## Dependencies

- Documented Warehouse Bale API contract; availability is external.
- Existing dependencies.

## Success Criteria

- [ ] `/warehouse/bales` is Spanish and keyboard-accessible, exposes only Reception, Stock, and Delivery cards, and loads no data.
- [ ] The Spanish, accessible workflow pages remain at `/warehouse/bales/reception`, `/stock`, and `/delivery`.
- [ ] Reception/delivery preserve failure drafts; clear is local-only; successes are visible and locked.
- [ ] `pnpm build`, `pnpm lint`, and manual grid, failure, theme, and landing validation pass.
