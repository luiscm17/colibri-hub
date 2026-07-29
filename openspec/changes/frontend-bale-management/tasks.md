# Tasks: Frontend Bale Management

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 1,150–1,500; PR3A 530–750, PR3B/PR3C ≤400 |
| Delivery strategy | exception-ok; exception only for PR3A controller/grid |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: tracker-direct-sequential
400-line budget risk: High

### Work Units

| Unit | Goal / base | Focused test command | Runtime harness / rollback boundary |
|---|---|---|---|
| PR3A | State/controller and header/grid/summary; tracker after PR2; no route | `cd frontend && pnpm lint && pnpm build` | Pure checks + non-committed harness; revert four files |
| PR3B | Page, submit/errors, canonical route/nav; tracker after PR3A | `cd frontend && pnpm lint && pnpm build` | Browser/API-mock; revert page, hook, route/nav |
| PR3C | Delete exactly eight legacy files; tracker after PR3B | `cd frontend && pnpm lint && pnpm build` | Canonical + `WarehousePage`; revert eight deletions |

## Phase 0: Completed Prerequisites

- [x] 0.1 Pin TypeScript `6.0.2`, refresh lockfile, and fix `_password` in `AuthContext.tsx`.

## Phase 1: Completed Foundation

- [x] 1.1 Create abortable transport and normalized errors in `frontend/src/api/`.
- [x] 1.2 Create `frontend/src/common/grid/` and scaled `BigInt` arithmetic.
- [x] 1.3 Create bale DTOs, mappers, API errors/APIs, and models.

## Phase 2: Completed Landing / Routing

- [x] 2.1 Capture RED evidence for missing landing and old defaults.
- [x] 2.2 Create Spanish `BaleManagementPage.tsx` with three cards and no requests.
- [x] 2.3 Wire landing, navigation, and root/direct-login defaults; preserve child routes.

## Phase 3: Reception — Three Tracker-Direct PRs

- [x] 3A.1 RED: prove canonical is Not Found and legacy remains available before PR3A routing.
- [x] 3A.2 Create `bales/hooks/useBaleReception.ts` for rows, 1–100 atomic paste, decimals, net weight, validation, drafts, and reset.
- [x] 3A.3 Create `ReceptionHeader.tsx`, `ReceptionGrid.tsx`, and `ReceptionSummary.tsx`; prove keyboard, focus, themes, and pure behavior. PR3A alone uses the approved 530–750-line exception; no route.
- [x] 3B.1 RED: prove only the real canonical page replaces the missing route and legacy becomes Not Found without redirect.
- [x] 3B.2 Create `BaleReceptionPage.tsx`; add confirmation, `Guardar`/`Limpiar`, lifecycle, indexed errors, notifications, and drafts.
- [x] 3B.3 Modify `frontend/src/app/routes/{index.tsx,lazy-pages.ts}` and `app/navigation-data.tsx` to register canonical, remove legacy route/nav, and retain landing target.
- [x] 3B.4 Browser-verify route, confirmation, submit/error/success, clear, accessibility, and no redirect; keep ≤400 lines.
- [x] 3C.1 Verify no legacy imports remain and retain `WarehousePage.tsx`.
- [x] 3C.2 Delete exactly eight: `api/receptionApi.ts`, `components/BaleDataGrid.tsx`, `components/ReceptionForm.tsx`, `components/reception-columns.ts`, `hooks/useBaleGrid.ts`, `hooks/useReceptionSubmit.ts`, `pages/ReceptionPage.tsx`, `types/reception-types.ts`.
- [x] 3C.3 Run lint/build and smoke-test canonical Reception and unrelated `WarehousePage`; keep ≤400 lines.

### PR3C Evidence

| Evidence | Exact result |
|---|---|
| Focused test command | `cd frontend && pnpm lint` — exit 0; `cd frontend && pnpm build` — exit 0. |
| Runtime harness | Vite + Playwright smoke test — canonical `/warehouse/bales/reception` rendered, legacy `/warehouse/reception` stayed Not Found without redirect, and an unrelated `WarehousePage` route rendered. |
| Rollback boundary | Restore only the eight deleted legacy Reception files; no route, navigation, canonical Reception, or unrelated Warehouse prototype changes. |

## Phase 4: Stock / Detail

- [x] 4.1 RED-test missing `/warehouse/bales/stock`; create stock hooks/UI for filters, metrics, zero results, lookup.
- [x] 4.2 Add abort/request-id protection, prior-data retention, retry states, accessibility, and themes.

### Phase 4 Evidence

| Evidence | Exact result |
|---|---|
| RED route proof | Before implementation, authenticated Playwright navigation to `/warehouse/bales/stock` rendered the Spanish 404 page. |
| Focused test command | `pnpm --dir frontend lint && pnpm --dir frontend build` — both exit 0; Vite production build completed. |
| Runtime harness | Vite at `127.0.0.1:5174` + Playwright: verified canonical route, zero summary, date validation, submitted query filters, composite success/not-found/error-retry states, sidebar navigation, and light/dark themes. |
| Rollback boundary | Revert the Stock hook/page and the three route/navigation entries; Reception, Delivery, backend, and legacy Warehouse routes remain independent. |

## Phase 5: Delivery

- [x] 5.1 RED-test missing `/warehouse/bales/delivery`; create the 1–50 identity grid, paste, duplicates, and confirmation.
- [x] 5.2 Correlate each returned normalized shipment+bale identity to its local row, update that frontend-local `rowId`, lock successes, retain failures/drafts, and keep clear local-only.

### Phase 5 Evidence

| Evidence | Exact result |
|---|---|
| Focused test command | `pnpm --dir frontend lint && pnpm --dir frontend build` — both exit 0; Vite production build completed. |
| Runtime harness | Final authorized Vite at `127.0.0.1:5173` + one focused Playwright API-mock run: submitted request-order inputs `  rem-001 ` / ` bale-a `, `REM-002` / `Bale-B`, ` rem-003` / ` bale-c `; the POST serialized normalized identities in that request order with no `rowId`. Mock response order deliberately differed: `REM-003`/`bale-c` `not_found`, `rem-001`/`BALE-A` `delivered`, `REM-002`/`bale-b` `already_delivered`. The grid correlated outcomes by normalized composite identity: row 1 `Entregado`, row 2 `Ya entregado: Ya fue entregado anteriormente.`, row 3 `No encontrado: El fardo no existe en el remito.`; exact status summary was `1 entregado · 2 con error`. Delivered row produced no editable grid input (only the date input remained); failed row produced an editable grid input. Confirmed `Limpiar` reset all populated cells and summary locally, with delivery resource-request count unchanged at 1 before and after clear (zero clear HTTP requests). |
| Rollback boundary | Revert the Delivery page/grid/hook/model, delivery response DTO/API/mapper alignment, and three route/navigation additions; Reception, Stock, backend, and landing remain independent. |
| Provenance | `openspec/` is untracked in this checkout. This table and the Phase 5 design section are the verification record; Git cannot isolate a prior evidence line. The production implementation remains attributable through these 11 frontend delivery paths and their current diff against HEAD/base: `frontend/src/app/navigation-data.tsx`; `frontend/src/app/routes/index.tsx`; `frontend/src/app/routes/lazy-pages.ts`; `frontend/src/features/warehouse/bales/api/baleApi.dto.ts`; `frontend/src/features/warehouse/bales/api/baleApi.mappers.ts`; `frontend/src/features/warehouse/bales/api/baleApi.ts`; `frontend/src/features/warehouse/bales/model/delivery.ts`; `frontend/src/features/warehouse/bales/components/delivery/DeliveryGrid.tsx`; `frontend/src/features/warehouse/bales/hooks/useBaleDelivery.ts`; `frontend/src/features/warehouse/bales/model/deliveryGrid.ts`; `frontend/src/features/warehouse/bales/pages/BaleDeliveryPage.tsx`. |

## Phase 6: Integration

- [x] 6.1 Run lint/build and verify landing requests, accessibility, themes, focus, feedback.

### Phase 6 Evidence

| Evidence | Exact result |
|---|---|
| Focused test command | `cd frontend && pnpm lint && pnpm build` — exit 0; TypeScript build completed with 7,076 transformed modules. |
| Runtime harness | One clean Vite server at `127.0.0.1:5173` plus Playwright API mocks: authenticated root landed on `/warehouse/bales`; exactly three Spanish cards and canonical sidebar/landing routes worked; Reception, Stock, and Delivery each showed a mocked success and retryable 500 failure while preserving drafts; legacy `/warehouse/reception` rendered the stable 404 without redirect. Landing made no API requests, and confirmed local clears made no API request. Cross-navigation reset workflow-local drafts/results. Light and dark rendered, keyboard grid-cell focus was visible, and alerts/status text supplied non-color feedback. |
| Rollback boundary | Revert only this evidence record and `verify-report.md`; no production integration fix was required. |

### Manual Closure Trace

Maintainer-approved manual closure is recorded in `verify-report.md`. All 22 implementation tasks are complete and Phase 6 passed; this trace does not create a native review receipt, `reviewGate: allow`, or SDD archive result.
