# Tasks: Align Warehouse Persistence Naming

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | PR1 350–395; PR2 170–260; PR3 160–250; PR4 90–220 |
| 400-line budget risk | High (PR1 may exceed 399) |
| Chained PRs recommended | Yes |
| Suggested split | PR1 → PR2 → PR3 → PR4 |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: Resolved during implementation
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

PR1 has no smaller passing boundary: stop if diff exceeds 399 and request a decision; never split DDL/ORM, diagnostics, and PostgreSQL proof. Every slice is <=399.

### Suggested Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| PR1 | Schema/ORM | Focused unittest | Reset + PostgreSQL | Migration/records/tests |
| PR2 | Adapters | Full unittest | N/A | Adapter/bootstrap/tests |
| PR3 | Result rename | Focused HTTP | ASGI/OpenAPI | Result/HTTP/tests |
| PR4 | Docs/cache | Full unittest | N/A | Docs/backend caches |

## PR1 — Atomic DB Contract

- [x] 1.1 **RED:** update `test_persistence_schema.py`, `test_bale_repository.py`, `test_warehouse_transaction.py`, and PostgreSQL tests for target names, exact keys/index, CHECK diagnostics, and `IN_WAREHOUSE -> DELIVERED`.
- [x] 1.2 **GREEN:** rewrite `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql`; align `raw_material_batch_record.py`, `bale_record.py`, `bale_mapper.py`, `transaction.py` constants, database support, and registration tests.
- [x] 1.3 **GO/NO-GO before reset:** record target fingerprint/URL, owner, disposable/data-free authorization, window, prior commit, checksum, and migration-list snapshot; missing attestation is NO-GO.
- [x] 1.4 Run `supabase db reset --local --no-seed` and `supabase migration list --local`; run guarded PostgreSQL tests, then full integration. Accept metadata, RLS/zero policies/revokes, RESTRICT, scoped uniqueness, statuses, CHECK diagnostics, rollback.

## PR2 — Role-Based Adapter Cutover

- [x] 2.1 **RED/GREEN:** rename adapters in persistence/identity `__init__.py`, `bale_repository.py`, `raw_material_batch_repository.py`, `transaction.py` to `TransactionAdapter`, `RawMaterialBatchRepositoryAdapter`, `BaleRepositoryAdapter`; retain `Uuid4IdentityGenerator` and update tests.
- [x] 2.2 Wire `backend/src/bootstrap/warehouse_bale_dependency.py` and `application/register_raw_material_batch.py`; update tests and run the full root backend suite.
- [x] 2.3 Confirm role names expose no framework/library; rollback only PR2 files.

## PR3 — Public Result Hard Rename

- [x] 3.1 **RED/GREEN:** rename `register_raw_material_batch.py`, `register_raw_material_batch_result.py`, HTTP mapping/response, router/model fixtures, and canonical adapter to expose only `raw_material_batch_id`; preserve route, validation, codes, errors.
- [x] 3.2 Run `uv run --locked python -m unittest backend.tests.test_warehouse.adapters.http.raw_material.test_bale_router backend.tests.test_warehouse.bales.adapters.http.test_canonical_http_adapter backend.tests.test_bootstrap.test_http_application -v`; prove ASGI 201/OpenAPI and rollback PR3 only.

## PR4 — Guidance and Safe Housekeeping

- [x] 4.1 Update `AGENTS.md`, `backend/docs/warehouse-bale-endpoint-architecture-review.md`, `docs/architecture/{ARCHITECTURE.md,backend.md}`, `docs/architecture/backend/persistence-decisions.md`, `docs/db/warehouse-dictionary.md`, and `docs/domain/warehouse.md`.
- [x] 4.2 **RED/GREEN/verify:** remove backend `__pycache__` and `.pyc`; run full root unit and guarded integration suites. Exclude frontend `receptionApi.ts`/`reception-types.ts`; record endpoint/payload/response alignment as follow-up.

Commands: focused persistence unittest; `uv run --locked python -m unittest discover -s backend/tests -v`; `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest backend.integration_tests.test_migrated_warehouse_schema backend.integration_tests.test_warehouse_transaction backend.integration_tests.test_register_bale_reception -v`; same URL with `uv run --locked python -m unittest discover -s backend/integration_tests -v`.

Historical apply gate (satisfied before implementation): no `sdd-apply` until user approves workload and reset authorization/attestation is recorded; interactive apply approval is separate. No new endpoints, actors, timestamps, states, contexts, migrations, policies, grants, aliases, commits, or PRs. Frontend `receptionApi.ts`/`reception-types.ts` is excluded; follow up must align endpoint/payload/response together.
