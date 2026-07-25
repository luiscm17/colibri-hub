# Tasks: Backend Capability-First Refactor v2

> **Status: complete historical task ledger.** All P0 tasks are complete. Naming
> constraints recorded here were valid for their work units and are superseded,
> where applicable, by `../align-warehouse-persistence-naming/`.

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | PR1 180; PR2 679; PR3 395; PR4 395; PR5A 280; PR5B 680; PR6 300; total about 2,909 |
| 400-line budget risk | High; PR2, PR3, and PR5B have bounded maintainer-approved exceptions; PR5A has none unless actual exceeds 400 |
| Chained PRs recommended | Yes |
| Suggested split | PR1 → PR2 → PR3 → PR4 → PR5A → PR5B → PR6; `size:exception` applies only to PR2, PR3, and bounded PR5B |
| Delivery strategy | exception-ok |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal / dependency | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| PR1 ≤180 | Router hierarchy; base main. | `uv run --locked python -m unittest backend.tests.test_bootstrap.test_http_application -v` | ASGI route/slash/OpenAPI | Router/bootstrap files and focused tests. |
| PR2 679 + corrections | Correct implemented domain slice after PR1; no PR3+ scope; approved `size:exception`. | `uv run --locked python -m unittest backend.tests.test_warehouse.bales.domain.test_raw_material_batch backend.tests.test_warehouse.domain.test_bale backend.tests.test_warehouse.domain.test_bale_reception backend.tests.test_warehouse.domain.test_value_objects -v`; full `uv run --locked python -m unittest discover -s backend/tests -v` | N/A—pure domain and aliases | `backend/src/warehouse/bales/domain/`, `backend/src/warehouse/bales/__init__.py`, `backend/src/warehouse/domain/raw_material/`, and focused domain tests. |
| PR3 ≤395 | Application/ports canonical move after PR2. | Application unittest module | N/A—framework-free | Application/ports and tests. |
| PR4 ≤395 | Persistence move after PR3; unchanged schema literals. | Persistence unittest modules | SQLite only | Persistence adapters/shims and tests. |
| PR5A ~280 | Canonical identity and transaction adapters after PR4; independently runnable. | `uv run --locked python -m unittest backend.tests.test_warehouse.adapters.identity.test_identity_generator backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction -v`; then full suite | N/A—no HTTP/DI cutover; adapter protocols and SQLite transaction tests are the runtime boundary | Revert canonical identity/transaction, old→new aliases, and PR5A tests only. |
| PR5B ~680 | Canonical HTTP plus DI/bootstrap cutover after PR5A; bounded `size:exception`. | `uv run --locked python -m unittest backend.tests.test_warehouse.adapters.http.test_bale_router backend.tests.test_warehouse.adapters.http.test_bale_reception_http_models backend.tests.test_warehouse.adapters.http.test_error_handlers backend.tests.test_warehouse.adapters.http.test_error_mapping backend.tests.test_bootstrap.test_warehouse_bale_dependency backend.tests.test_bootstrap.test_http_error_handlers backend.tests.test_bootstrap.test_http_application -v`; then full suite | TestClient: POST, slash 307, OpenAPI, 201/409/422/500, and one shared session across both repositories/transaction | Revert canonical HTTP modules, old→new aliases, bootstrap cutover, and PR5B tests; restore runnable PR5A. |
| PR6 ~300 | Remove shims/tree and final verification after PR5B. | Full unit, integration, Supabase, and ASGI commands below | PostgreSQL/Supabase/ASGI | Cleanup-only paths and verification artifacts. |

Chain: `PR1 → PR2 → PR3 → PR4 → 📍 PR5A → PR5B → PR6`; PR5B cannot start before PR5A passes.

## Phase 1: Stacked PR 1 — Router hierarchy

- [x] 1.1 RED then GREEN: preserve `POST /api/v1/warehouse/bales`, slash behavior, OpenAPI uniqueness, and one-session DI through `/api/v1` → `/warehouse` → `/bales`; rollback PR1 paths; ≤180.

## Phase 2: Stacked PRs 2–3 — Domain, application, and ports

- [x] 2.1 Correct the implemented-but-not-accepted PR2: `RawMaterialBatchId` is canonical technical identity; immutable globally unique `ShipmentNumber` is business identity; Bale stores `RawMaterialBatchId` and not `ShipmentNumber`; `BaleReceptionId` exists only as old-FQN alias to `RawMaterialBatchId`. RED/GREEN tests must prove tuple storage before empty/duplicate validation, caller-list mutation safety, distinct identities, old/new alias identity, and unchanged P0 Bale behavior. Use the exact focused/full commands above; runtime N/A; do not mark complete until apply finishes; approved `size:exception` covers existing 679 lines plus narrow corrections.
- [x] 3.1 Move application/errors/results and ports to canonical `warehouse/bales/{application,ports}`; preserve old→new exports, order, conflicts, unknown propagation, and no correction/delivery; maintainer-approved `size:exception`; runtime N/A.

## Phase 3: Stacked PRs 4–5 — Adapters and wiring

- [x] 4.1 Move persistence adapters to `warehouse/bales/adapters/persistence`; preserve `reception_id`, mapping, order, rollback, and schema identity; ≤395.
- [x] 5.1 PR5A: create `warehouse.bales.adapters.identity.identity_generator.UuidIdentityGenerator` and `warehouse.bales.adapters.persistence.transaction.SqlAlchemyTransaction`; alias old FQNs `warehouse.adapters.identity.uuid_identity_generator.UuidIdentityGenerator` and `warehouse.adapters.persistence.warehouse_transaction.WarehouseTransaction`; canonical imports use only `warehouse.bales.ports.{identity_generator,transaction,transaction_errors}`. Acceptance: canonical/legacy identity, UUID, protocol, commit/rollback failure, exact constraint translation, unknown-integrity propagation, and shared-session tests pass; focused + full commands above; runtime N/A. Forecast ~280, no exception unless actual >400; rollback those adapters/aliases/tests; audit no schema/migration/API/unrelated files and technology appears once per canonical FQN.
- [x] 5.2 PR5B (depends on PR5A): create canonical `warehouse.bales.adapters.http.{router,bale_reception_mapping,bale_reception_request,bale_reception_response,error_handlers,error_mapping,error_response}`; alias every `warehouse.adapters.http.raw_material.*`; cut over `bootstrap.warehouse_bale_dependency`, `bootstrap.http_error_handlers`, and required `bootstrap.http_application`, retaining `/warehouse` ownership. Acceptance: exact `reception_id` payload, decimal/datetime validation, 201/409/422/500 envelopes, one route/OpenAPI operation, slash 307, canonical imports, and one request-scoped shared session; focused + full commands and TestClient runtime above. Forecast ~680, bounded maintainer-approved `size:exception`; rollback canonical HTTP/aliases/bootstrap/tests; audit no schema/migration/P1/public API/unrelated files and technology-once FQNs.

## Phase 4: Stacked PR 6 — Cleanup and verification

- [x] 6.1 Removed old tree/shims; audited canonical dependencies, package discovery, authored lines, and protected exact paths. Focused suite passed 137 tests; full unit suite passed 176; Supabase status/reset/migration-list passed with `20260722130455` applied; loopback PostgreSQL integration passed 11; ASGI/OpenAPI exact-route/slash/error behavior passed. Approved fallback-readability correction removed dead canonical fallback attributes and moved tests to Bales ownership; its focused suite passed 33, full suite passed 176, and integration passed 11. Final cleanup removed the obsolete empty total-net-weight test; its canonical application suite passed 17 and full suite passed 175. PR6-only `size:exception` accepted the final 1,810-line backend cleanup diff, including 424 untracked canonical-test additions. Schema, migrations, P1/public API, and unrelated files remain unchanged; rollback cleanup seams only.

No delivery, lifecycle, correction, schema, migration, or API redesign; commits optional.
