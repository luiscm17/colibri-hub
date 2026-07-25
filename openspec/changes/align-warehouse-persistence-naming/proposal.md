# Proposal: Align Warehouse Persistence Naming

> **Status: implemented; traceability artifact.** All tasks are complete. This
> directory records planning and execution evidence, not independent proof of
> the current runtime. Current code, migration, and tests are the implementation
> authority. Native review authority was corrupted/invalidated, so no review or
> receipt success is claimed; the apply progress preserves the available
> verification evidence and manual commit boundaries.

## Intent

Replace obsolete Reception persistence vocabulary with the established Warehouse batch-and-bale model. The new disposable-database baseline must align physical storage, adapters, and the public result with `RawMaterialBatch` and independently addressable `Bale` entities.

## Scope

### In Scope
- Rewrite the resettable Warehouse baseline with `raw_material_batches`, `raw_material_bales`, `raw_material_batch_id`, and aligned PK/FK/unique/index names.
- Add named `ck_raw_material_bales_status`, allowing exactly `in_warehouse` and `delivered`. This baseline invariant enforces the existing lifecycle and rejects deprecated `in_production` or arbitrary bypass writes; it adds no state or operation.
- Align ORM records, mappers, diagnostics, role-based adapters (`TransactionAdapter`, repository adapters), composition, and `Uuid4IdentityGenerator`.
- Hard-rename the result/HTTP field to `raw_material_batch_id`, retaining `POST /api/v1/warehouse/bales`, validation, errors, and behavior.
- Plan Warehouse-only tests, PostgreSQL verification, and terminology updates for manual implementation.

### Out of Scope
- Other contexts, endpoints, actors, timestamps, states, lifecycle redesign, compatibility bridges, or data/schema preservation.
- Forward/down/rename migrations, new policies, grants, triggers, or `IN_PRODUCTION`.

## Capabilities

### New Capabilities
- `warehouse-bale-persistence`: Canonical Warehouse batch/bale baseline, enforced Bale status values, and returned batch identifier.

### Modified Capabilities
- None; no baseline OpenSpec capabilities exist.

## Approach

Replace `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql` in place. An authorized owner must attest each target is disposable, has no retained data, and may reset; otherwise it is no-go. Deploy matching code and baseline, then reset—never rename in place. Preserve RawMaterialBatch 1:N Bale, UUIDs, types, nullability, uniqueness, restricted FK, RLS, zero policies, and revoked public roles.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql` | Modified | Canonical reset baseline and named status CHECK |
| `backend/src/warehouse/bales/adapters/` | Modified | Records, mappers, constraints, role-based adapters |
| `backend/src/warehouse/bales/application/`, `backend/src/bootstrap/` | Modified | Renamed result and composition |
| `backend/tests/`, `backend/integration_tests/`, `docs/` | Modified | Manual implementation proof and terminology |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Unapproved or non-disposable target | Medium | Written reset authorization and inventory; no-go otherwise |
| Old `reception_id` consumers | High | Coordinate intentional hard cutover |
| ORM/DDL drift | Medium | Assert exact PostgreSQL metadata, including CHECK |

## Rollback Plan

Restore the prior migration and matching code from version control, then reset only authorized disposable databases. No data-preserving rollback or old-schema compatibility applies.

## Success Criteria

- [x] Schema/ORM expose only target names and `ck_raw_material_bales_status` permits exactly `in_warehouse` and `delivered`.
- [x] One batch persists independent Bales; uniqueness and restricted FK remain intact.
- [x] HTTP/OpenAPI returns `raw_material_batch_id`, never `reception_id`.
- [x] PostgreSQL verifies names, CHECK, RLS, zero policies, revokes, and reset-only baseline behavior.

## Work-Unit Strategy

Force-chained, stacked-to-main: schema/ORM plus tests; adapters/composition plus tests; HTTP/integration/docs. Manual implementation only. Every work unit must be strictly below 400 changed lines; split before reaching 400.

## Proposal Question Round

The maintainer resolved reset authority, lifecycle enforcement, compatibility, and scope; no product decision blocks correction.
