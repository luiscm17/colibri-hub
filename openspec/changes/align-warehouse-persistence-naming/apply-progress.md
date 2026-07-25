# Apply Progress: Align Warehouse Persistence Naming

> **Final status:** All 11 tasks across PR1-PR4 are complete. Evidence below is
> retained as executed verification and manual rollback/commit boundaries.
> Native review authority was corrupted/invalidated; this record does not claim
> review-gate or receipt success.

## PR1 — Atomic DB Contract

### Completed Tasks

- [x] 1.1 RED tests updated for canonical physical names, named keys/index, lifecycle CHECK metadata, and PostgreSQL status diagnostics.
- [x] 1.2 GREEN migration, ORM records, mapper, diagnostics, database support, and persistence references aligned.
- [x] 1.3 GO/NO-GO reset record completed.
- [x] 1.4 Reset and PostgreSQL integration verification completed.

### Reset Authorization Record

| Field | Value |
|---|---|
| Target URL/fingerprint | `postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres` (local guarded integration target) |
| Owner | Maintainer, as authorized in the interactive request |
| Disposable/data-free authorization | Confirmed in the interactive request |
| Reset window | Current interactive PR1 resume session |
| Prior commit | `da4797d92514dcf2a1086268057810fa7c6777f1` |
| Applied migration SHA-256 | `269b0280a5aed6e3aca507a7c64b4456e789270c229724c86dac4b3e86722e6f` |
| Migration-list snapshot | Local and remote both report `20260722130455` at `2026-07-22 13:04:55 UTC` |

### Work Unit Evidence

The initial apply attempt was blocked after checking a nonexistent global CLI. The maintainer clarified that this repository invokes the already-running local service through `pnpm supabase`; this resumed run used that wrapper.

| Evidence | Result |
|---|---|
| RED focused unit test | `uv run --locked python -m unittest backend.tests.test_warehouse.adapters.persistence.test_persistence_schema backend.tests.test_warehouse.adapters.persistence.test_bale_repository backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction -v` → expected failure: 7 errors before production alignment |
| GREEN focused unit test | Same command → exit 0, 17 tests passed |
| Full backend unit suite | `uv run --locked python -m unittest discover -s backend/tests -v` → exit 0, 176 tests passed |
| Supabase status | `pnpm supabase status` → exit 0; local database available at `postgresql://postgres:postgres@127.0.0.1:54322/postgres` |
| Reset and migration list | `pnpm supabase db reset --local --no-seed && pnpm supabase migration list --local` → exit 0; baseline reset and migration snapshot recorded |
| Focused PostgreSQL integration | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest backend.integration_tests.test_migrated_warehouse_schema backend.integration_tests.test_warehouse_transaction backend.integration_tests.test_register_bale_reception -v` → exit 0, 12 passed |
| Full PostgreSQL integration | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest discover -s backend/integration_tests -v` → exit 0, 12 passed |
| Rollback boundary | Revert the PR1 migration, persistence records/mapper/diagnostics, database support, and named persistence/integration tests together; reset only an authorized disposable target once the CLI is available. |

### Diff Budget

Scoped runtime/test/migration diff: **161 additions + 60 deletions = 221 changed lines** (cap: 399).

### Status

PR1 implementation and PostgreSQL proof are complete within the authored-diff cap. PR2–PR4 remain untouched.

## PR2 — Role-Based Adapter Cutover

### Completed Tasks

- [x] 2.1 Renamed concrete adapters to `TransactionAdapter`, `RawMaterialBatchRepositoryAdapter`, and `BaleRepositoryAdapter`; retained `Uuid4IdentityGenerator`.
- [x] 2.2 Updated bootstrap composition, canonical exports/imports, focused tests, and integration fixtures.
- [x] 2.3 Confirmed concrete names do not expose the SQLAlchemy framework; rollback is isolated to PR2 adapter/composition/test files.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| RED focused tests | Focused adapter/bootstrap suite → expected failure: 3 import errors before the renamed classes existed |
| GREEN focused tests | `uv run --locked python -m unittest backend.tests.test_warehouse.adapters.identity.test_identity_generator backend.tests.test_warehouse.adapters.persistence.test_bale_repository backend.tests.test_warehouse.adapters.persistence.test_warehouse_transaction backend.tests.test_bootstrap.test_warehouse_bale_dependency backend.tests.test_warehouse.bales.application.test_register_raw_material_batch -v` → exit 0, 31 passed |
| Full backend unit suite | `uv run --locked python -m unittest discover -s backend/tests -v` → exit 0, 176 passed |
| Runtime harness | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest backend.integration_tests.test_warehouse_transaction backend.integration_tests.test_register_bale_reception -v` → exit 0, 4 passed; full integration discovery → exit 0, 12 passed |
| Rollback boundary | Revert the PR2 identity/persistence adapter names, bootstrap composition, and affected unit/integration tests together. No schema, public result, or HTTP behavior changes are included. |

### Diff Budget

PR2 scoped runtime/test diff from `a7f6017`: **46 additions + 46 deletions = 92 changed lines** (cap: 399).

### Status

PR1 and PR2 are complete. PR3–PR4 remain untouched.

## PR3 — Public Result Hard Rename

### Completed Tasks

- [x] 3.1 Renamed the application result and HTTP response field to `raw_material_batch_id` with no compatibility alias.
- [x] 3.2 Proved the unchanged route returns 201 with `raw_material_batch_id`, and OpenAPI exposes it while omitting `reception_id`.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| RED focused tests | Expected failure: 13 errors and one 500 response while result/response constructors still accepted only `reception_id` |
| GREEN focused tests | `uv run --locked python -m unittest backend.tests.test_warehouse.bales.application.test_register_raw_material_batch backend.tests.test_warehouse.adapters.http.raw_material.test_bale_reception_http_models backend.tests.test_warehouse.adapters.http.raw_material.test_bale_router backend.tests.test_warehouse.bales.adapters.http.test_canonical_http_adapter backend.tests.test_bootstrap.test_http_application -v` → exit 0, 47 passed |
| Full backend unit suite | `uv run --locked python -m unittest discover -s backend/tests -v` → exit 0, 176 passed |
| Runtime harness | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest backend.integration_tests.test_register_bale_reception -v` → exit 0, 2 passed; full integration discovery → exit 0, 12 passed |
| Rollback boundary | Revert the application result, HTTP response/mapping, and their application/HTTP/integration tests together. No physical schema, adapter-role, frontend, route, or lifecycle change is included. |

### Diff Budget

PR3 scoped runtime/test diff from `b3df7f2`: **31 additions + 19 deletions = 50 changed lines** (cap: 399).

### Status

PR1–PR3 are complete. PR4 remains untouched.

## PR4 — Guidance and Safe Housekeeping

### Completed Tasks

- [x] 4.1 Aligned the tracked canonical Warehouse guidance with the implemented batch/bale schema, role-based adapters, lifecycle, RLS posture, and public identifier.
- [x] 4.2 Removed ignored backend Python caches and confirmed no tracked cache files or runtime changes.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Documentation verification | Current code/migration facts were read through CodeGraph; targeted documentation no longer claims obsolete physical names, old concrete adapter names, or `IN_PRODUCTION` as the current Bale state. The `reception_id` occurrence in the dictionary explicitly documents its absence from the public response. |
| Scoped diff check | `git diff --check -- AGENTS.md docs/architecture/ARCHITECTURE.md docs/architecture/backend.md docs/architecture/backend/persistence-decisions.md docs/db/warehouse-dictionary.md docs/domain/warehouse.md` → exit 0 |
| Runtime harness | N/A — documentation and ignored-cache-only work; no runtime, test, schema, or dependency file was touched. |
| Cache cleanup | Removed only ignored `backend/**/__pycache__/` and `backend/**/*.pyc`; subsequent `git status --ignored --short --untracked-files=all -- backend` listed no Python cache entries and `git ls-files` found no tracked cache paths. |
| Rollback boundary | Revert the six tracked guidance files; cache cleanup has no repository diff and is recreated safely by Python if needed. |

### Diff Budget

PR4 scoped documentation diff from `80c9be3`: **47 additions + 44 deletions = 91 changed lines** (cap: 399).

### Status

All 11 tasks across PR1–PR4 are complete.
