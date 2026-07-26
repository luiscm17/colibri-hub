# Design: Align Warehouse Persistence Naming

## Technical Approach

Replace the disposable Warehouse baseline in place and align ORM, adapters, diagnostics, tests, and the existing HTTP result with `RawMaterialBatch` 1:N independently lifecycle-owned `Bale`. Preserve `IN_WAREHOUSE -> DELIVERED`; add no endpoint, state, actor, timestamp, compatibility alias, or other bounded context.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Baseline rewrite vs rename migration | Destructive; no retained-data path | Rewrite `20260722130455_create_raw_material_reception_storage.sql`; reset only after per-target owner attestation. |
| Domain-only vs layered lifecycle enforcement | Duplicated invariant prevents bypass writes | DDL and ORM define the named row CHECK allowing exactly `in_warehouse` and `delivered`. |
| Framework-named vs role-named adapters | Renames concrete imports | Use `TransactionAdapter`, `RawMaterialBatchRepositoryAdapter`, `BaleRepositoryAdapter`, and retain `Uuid4IdentityGenerator`. |
| Compatibility field vs hard cutover | Existing consumers must coordinate | Return only `raw_material_batch_id`. |

## Data Flow

`POST /api/v1/warehouse/bales -> RegisterRawMaterialBatch -> batch add/flush -> Bale add_all -> TransactionAdapter.commit -> PostgreSQL -> raw_material_batch_id`

## Interfaces / Contracts

Exact DDL inside `raw_material_bales`:

```sql
constraint ck_raw_material_bales_status
    check (status in ('in_warehouse', 'delivered'))
```

`BaleRecord.__table_args__` must include `CheckConstraint("status IN ('in_warehouse', 'delivered')", name="ck_raw_material_bales_status")`, explicit `PrimaryKeyConstraint`, `ForeignKeyConstraint(..., name="fk_raw_material_bales_raw_material_batch_id", ondelete="RESTRICT")`, `UniqueConstraint`, and `Index` matching the spec. The FK attribute is `raw_material_batch_id`; no implicit/generated constraint name is acceptable. PostgreSQL invalid-write tests must assert `IntegrityError.orig.diag.constraint_name == "ck_raw_material_bales_status"` for `in_production` and an arbitrary value; direct writes of both accepted values must commit.

## Exact Blast Radius and Stacked Slices

| Slice (stacked to `main`) | Forecast | Independently valid boundary |
|---|---:|---|
| PR1 atomic DB contract | 350–395 | Migration; persistence `raw_material_batch_record.py`, `bale_record.py`, `bale_mapper.py`, `transaction.py` diagnostic constants; unit `test_persistence_schema.py`, `test_bale_repository.py`, `test_warehouse_transaction.py`; PostgreSQL `database_test_support.py`, `test_migrated_warehouse_schema.py`, `test_warehouse_transaction.py`, `test_register_bale_reception.py`. Keep DDL/ORM, both unique diagnostic constants, exact CHECK diagnostics, and focused PostgreSQL conflict tests together. |
| PR2 adapter roles | 170–260 | Persistence/identity `__init__.py`, `bale_repository.py`, `raw_material_batch_repository.py`, `transaction.py`, `identity_generator.py`; `bootstrap/warehouse_bale_dependency.py`; `application/register_raw_material_batch.py`; focused identity, transaction, dependency, registration tests. |
| PR3 public result | 160–250 | `register_raw_material_batch.py`, `register_raw_material_batch_result.py`, HTTP mapping/response; application, router/model, canonical-adapter, and `test_http_application.py` ASGI/OpenAPI tests. |
| PR4 truthful guidance | 90–220 | `AGENTS.md`, `backend/docs/warehouse-bale-endpoint-architecture-review.md`, `docs/architecture/{ARCHITECTURE.md,backend.md}`, `docs/architecture/backend/persistence-decisions.md`, `docs/db/warehouse-dictionary.md`, `docs/domain/warehouse.md`. |

Each slice is capped at 399 additions plus deletions, starts from its predecessor, must have a slice-only diff, passing checks, and independent rollback. PR1 has no honest smaller passing boundary; stop before apply if its measured forecast exceeds 399 and request a delivery decision rather than silently splitting the atomic contract.

`frontend/src/features/warehouse/api/receptionApi.ts` and `types/reception-types.ts` are excluded: they target `/api/warehouse/receptions` with a contract-incompatible payload. Follow-up must align endpoint, payload, and response together; a field-only rename is forbidden.

## Verification / Implementation Guide

Delegated `sdd-apply` may begin only after ALL of: (1) disposable/data-free reset attestation and authorization; (2) a completed SDD tasks artifact; (3) explicit approval of the tasks and workload forecast through the Review Workload Guard; and (4) explicit interactive approval to apply. It may then implement with checkpoints, but must not create commits or open PRs automatically; either action requires a request.

```bash
uv run --locked python -m unittest backend.tests.test_warehouse.adapters.persistence.test_persistence_schema backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction -v
uv run --locked python -m unittest discover -s backend/tests -v
supabase db reset --local --no-seed
supabase migration list --local
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest backend.integration_tests.test_migrated_warehouse_schema backend.integration_tests.test_warehouse_transaction backend.integration_tests.test_register_bale_reception -v
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest discover -s backend/integration_tests -v
uv run --locked python -m unittest backend.tests.test_warehouse.adapters.http.raw_material.test_bale_router backend.tests.test_warehouse.bales.adapters.http.test_canonical_http_adapter backend.tests.test_bootstrap.test_http_application -v
```

## Migration / Rollout

GO requires each target’s ref/URL fingerprint, owner, written disposable/data-free attestation, reset authorization, window, and migration-list snapshot. Otherwise NO-GO. Record prior commit, migration checksum, and matching artifact; stop old code, reset, prove PR1, deploy matching code, then verify 201 JSON/OpenAPI. On failure restore migration and code together and reset only authorized targets; never run mixed versions or attempt data preservation.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation implementation, executable classification, or process-integration boundary changes.

## Open Questions

None; the conditional PR1 size checkpoint is an apply gate, not an unresolved design choice.
