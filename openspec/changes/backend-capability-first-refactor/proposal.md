# Proposal: Backend Capability-First Refactor

> **Status: completed historical P0 capability-cutover evidence.** This entire
> change directory records the decisions and verification boundaries that were
> valid during the P0 cutover. Later persistence, public identifier, and concrete
> adapter naming decisions are superseded by
> `../align-warehouse-persistence-naming/`: canonical physical batch names,
> public `raw_material_batch_id`, role-based adapters, and the reset baseline now
> govern. Historical `reception_id`, old schema, and `SqlAlchemyTransaction`
> references below remain time-scoped evidence, not current requirements.

## Intent

Make `warehouse.bales` the canonical vertical boundary for the existing raw-material receiving capability. This P0 removes structural ambiguity without adding product behavior.

## Problem and Goals

The current layer-first `raw_material` namespace obscures ownership and models a receiving action as a domain concept. Establish clear capability ownership, canonical domain vocabulary, and composable routing before further Warehouse endpoints.

## Scope

### In Scope
- Move the complete receiving slice to `warehouse.bales.{domain,application,ports,adapters}`.
- Canonically name the use case `RegisterRawMaterialBatch`; atomically register one complete `RawMaterialBatch` and one-or-more `Bale` aggregates.
- Compose routers as `/api/v1` → `/warehouse` → `/bales`.
- Preserve the existing public `POST /api/v1/warehouse/bales` contract.

### Out of Scope
- Correction workflows; future corrections, including omitted Bales, MUST be explicit and audited.
- Delivery, `IN_PRODUCTION`, `delivered_at`, delivery actors, and multi-Bale delivery semantics.
- Migrations, schema changes, RLS/privilege changes, and product/API behavior changes.

## Capabilities

### New Capabilities
- `warehouse-bales`: Register complete raw-material batches and their Bales through the canonical Warehouse capability boundary.

### Modified Capabilities
- None. No existing main OpenSpec capability covers this behavior.

## Approach and Compatibility Guarantees

Use a direct move—not a new-to-old wrapper—with old FQNs allowed only as temporary, named old-to-new aliases. Keep `RawMaterialBatch` and `Bale` canonical internally; retain transport/persistence compatibility names such as `reception_id`. Preserve request/response fields, validation, status/error semantics, slash behavior, collective result, one request-scoped session, header-before-detail insertion, atomic commit/rollback, known-constraint translation, and unknown-integrity propagation.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/src/warehouse/` | Modified | Capability-owned domain, application, ports, HTTP, and persistence. |
| `backend/src/bootstrap/` | Modified | Hierarchical router and dependency composition. |
| `backend/tests/`, `backend/integration_tests/` | Modified | Preserve contract and architecture coverage. |
| `supabase/migrations/` | Unchanged | Verification evidence only. |

## Database Policy and Verification

No migration is required. Historical tables, columns, constraints, index, RLS, privileges, and migration history remain unchanged. Later verification MUST cover package discovery, ASGI/OpenAPI route uniqueness, unit tests, and PostgreSQL integration after `supabase db reset --local --no-seed`; no Supabase command runs during planning.

## Chained Delivery Intent

Deliver four successive stacked-to-`main` slices: router seam; domain/application; ports/persistence/DI; cleanup and full verification. Keep each practical authored diff at or below 400 changed lines, with its tests and rollback boundary.

## Risks and Rollback

| Risk | Mitigation |
|---|---|
| Rename changes route or payload | Assert exact route, OpenAPI, and HTTP contract. |
| ORM move breaks mappings | Preserve schema names and verify PostgreSQL constraints. |
| Protected workspace changes are touched | Limit edits to planned files; never clean or format broadly. |

Revert an individual stacked slice and its tests without altering migrations or protected unrelated workspace changes; remove temporary aliases only after consumers move.

## Open Design Questions

- Which old FQNs, if any, require a temporary alias and removal criterion?
- Where should non-capability router composition modules live?
- Which aggregate repository operations are genuinely needed?

## Success Criteria

- [x] `warehouse.bales` became the sole canonical implementation owner for this P0 cutover.
- [x] `RegisterRawMaterialBatch` preserved complete-batch, one-or-more-Bale atomic registration.
- [x] This P0 cutover introduced no observable HTTP or persistence behavior change at that phase.
- [x] This P0 cutover introduced no delivery/correction behavior, migration, or schema change.
