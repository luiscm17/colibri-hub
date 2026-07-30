# Design: Frontend Bale Management

## Technical Approach

Keep the final specifications unchanged and deliver Reception as three sequential child PRs, each targeting `front/bale-management` after its predecessor merges. PR3A builds reusable local state and spreadsheet UI without registering `/warehouse/bales/reception`; PR3B composes the real page and performs the route/navigation cutover; PR3C removes only the now-unreferenced legacy Reception prototype.

## Architecture Decisions

| Option | Tradeoff | Decision and rationale |
|---|---|---|
| Three Reception PRs | PR3A exceeds the default review budget | Accept PR3A's explicit PR-only `size:exception` because the cohesive controller/grid slice is estimated at 530–750 changed lines; keep PR3B and PR3C at ≤400 each. |
| Route only with the real page | PR3A has no canonical browser entry | Do not commit a placeholder or route. Verify PR3A through pure behavior checks and, when browser rendering is needed, a non-committed local harness removed before review. |
| Cut over before cleanup | Legacy files survive one merged PR | PR3B removes the legacy route and navigation reference; PR3C then deletes exactly eight unreferenced Reception-only files. This separates behavior change from mechanical deletion. |
| Preserve shared placeholder page | Leaves unrelated scaffolding in place | Keep `frontend/src/features/warehouse/pages/WarehousePage.tsx`; current unrelated Warehouse routes still depend on it. |

## Data Flow

```text
PR3A: local harness/pure proof → controller → header/grid/summary (no route, no API submit)
PR3B: landing/nav → /warehouse/bales/reception → page → controller → registerBatch → API
                                            └→ confirm → submitting/error/success feedback
PR3C: delete unreferenced legacy prototype only
```

The controller owns immutable row IDs/order, 1–100-row atomic paste, string decimals, derived net weight, validation, draft preservation, and local reset. PR3B adds confirmed `Guardar`/`Limpiar`, request lifecycle, indexed field-error mapping, notifications, and successful-batch feedback.

## File Changes and Sequencing

| Slice | Forecast | File actions |
|---|---:|---|
| PR3A | 530–750; `size:exception` | Create `bales/hooks/useBaleReception.ts` and `bales/components/{ReceptionHeader,ReceptionGrid,ReceptionSummary}.tsx`. No route, page, placeholder, navigation, or legacy-file change. |
| PR3B | ≤400 | Create `bales/pages/BaleReceptionPage.tsx`; complete lifecycle integration in `useBaleReception.ts`; modify `app/routes/{index.tsx,lazy-pages.ts}` and `app/navigation-data.tsx`. Register the canonical route, retain the landing card's canonical target, remove `/warehouse/reception` and its nav item with no redirect. |
| PR3C | ≤400 | Delete exactly the eight files listed below; no route or behavior changes. |

Reception remains estimated at 1,150–1,500 changed lines. The corrected overall action forecast is 28 new, 4 modified, and 8 deleted files. All three child PRs target `front/bale-management` and merge sequentially; no child stacks on another child branch.

PR3C deletes exactly:

1. `frontend/src/features/warehouse/api/receptionApi.ts`
2. `frontend/src/features/warehouse/components/BaleDataGrid.tsx`
3. `frontend/src/features/warehouse/components/ReceptionForm.tsx`
4. `frontend/src/features/warehouse/components/reception-columns.ts`
5. `frontend/src/features/warehouse/hooks/useBaleGrid.ts`
6. `frontend/src/features/warehouse/hooks/useReceptionSubmit.ts`
7. `frontend/src/features/warehouse/pages/ReceptionPage.tsx`
8. `frontend/src/features/warehouse/types/reception-types.ts`

## Interfaces / Contracts

Existing `ReceptionHeader`, `ReceptionGridRow`, `RegisterBatchInput`, `RegisteredBatch`, `registerBatch`, mapper, and `BaleApiError` contracts remain authoritative. DTO decimals stay snake_case strings; local models remain camelCase. No backend, persistence, Supabase, or RLS change is introduced.

## Phase 5: Delivery Design

Delivery uses a local 1–50 row grid for manual typing or two-column paste of shipment and bale identities. Each row receives a frontend-only `rowId` for React state and grid identity; there is no available-bales endpoint or selectable bale list.

Submission validates a delivery date and unique normalized composite identities, then sends one batch request containing only `delivery_date` and normalized `shipment_number`/`bale_number` values. `rowId` is never serialized. The documented response envelope contains `delivery_date`, delivered and failed counts, and per-identity results with shipment number, bale number, status, and optional error; it contains no local `rowId`.

For each result, the client normalizes the returned shipment+bale composite identity, resolves the matching local row, and updates that row while preserving its frontend-local `rowId`. Delivered rows are locked. Not-found, already-delivered, validation, transport, and server-failure rows retain their draft values so the operator can correct or retry them. Clear resets local state only.

### Phase 5 Verification Provenance

`openspec/` is untracked in this checkout, so this design section and the Phase 5 task evidence are the verification record rather than a Git-isolated evidence diff. The production implementation remains attributable through these 11 frontend delivery paths and their current diff against HEAD/base:

1. `frontend/src/app/navigation-data.tsx`
2. `frontend/src/app/routes/index.tsx`
3. `frontend/src/app/routes/lazy-pages.ts`
4. `frontend/src/features/warehouse/bales/api/baleApi.dto.ts`
5. `frontend/src/features/warehouse/bales/api/baleApi.mappers.ts`
6. `frontend/src/features/warehouse/bales/api/baleApi.ts`
7. `frontend/src/features/warehouse/bales/model/delivery.ts`
8. `frontend/src/features/warehouse/bales/components/delivery/DeliveryGrid.tsx`
9. `frontend/src/features/warehouse/bales/hooks/useBaleDelivery.ts`
10. `frontend/src/features/warehouse/bales/model/deliveryGrid.ts`
11. `frontend/src/features/warehouse/bales/pages/BaleDeliveryPage.tsx`

## Testing Strategy

| Layer | Approach |
|---|---|
| Every PR | Run `pnpm lint` and `pnpm build` from `frontend/`; inspect the committed diff and changed-line count. |
| PR3A | Prove row continuation, paste atomicity, decimal/net calculations, duplicates, summary, keyboard/focus, and themes through pure checks and an optional non-committed harness. Confirm canonical remains Not Found and legacy remains available. |
| PR3B | Browser-prove confirmations, submit/error/success preservation, indexed errors, local-only clear, canonical route/navigation, and legacy Not Found without redirect. |
| PR3C | Build/lint and prove no stale imports; canonical Reception and unrelated `WarehousePage` routes still render. |

No frontend automated test runner is configured.

## Threat Matrix

| Boundary | Applicability | Safe/failure behavior and planned RED proof |
|---|---|---|
| Browser route resolution | Applicable | PR3A leaves canonical Not Found and legacy available. PR3B serves only the real canonical page and makes legacy Not Found without alias/redirect. RED proof checks both states and fails on any committed placeholder or premature route. |
| Documentation-like paths | N/A — no executable classification | No execution boundary or RED task. |
| Git repository selection | N/A — no VCS automation | No repository selector or RED task. |
| Commit state | N/A — no commit automation | No index semantics or RED task. |
| Push state | N/A — no push automation | No ref resolution or RED task. |
| PR commands | N/A — sequencing is documented, not automated | No command composition or RED task. |

## Migration / Rollout

No migration required. Merge PR3A → PR3B → PR3C into `front/bale-management`. Roll back PR3A independently. Rolling back PR3B restores the legacy route/nav and removes canonical composition while the eight files still exist. After PR3C, roll back PR3C first, then PR3B. Never introduce a redirect.

## Open Questions

None.
