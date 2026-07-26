# Apply Progress: Rebuild Backend Test Suite

## Slice 1 — Domain/Application

**Status:** complete  
**Mode:** Standard (`strict_tdd` configuration is absent; a unittest runner exists)  
**Delivery:** force-chained, `stacked-to-main`; base `5730050`; current boundary is Slice 1 only.

### Completed Tasks

- [x] 1.1 Fresh discovery markers and deterministic, capability-scoped support.
- [x] 1.2 Fresh domain contracts for representative value-object partitions, Bale lifecycle, and RawMaterialBatch invariants.
- [x] 1.3 Fresh registration orchestration contracts using behavior-focused port doubles.
- [x] 1.4 Focused/full fresh discovery, diff check, and line-budget checkpoint.

### Fresh-Contract Evidence

All tests were derived from current production source through CodeGraph and current PRD, architecture, OpenSpec proposal/spec/design/tasks, and repository guides. They deliberately do not use legacy tests, Git history, `.kiro`, failed-refactor artifacts, or current integration assertions. Current behavior satisfied every fresh contract, so no artificial RED or production change was warranted.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `uv run --locked python -m unittest backend.tests.domain.test_core_contracts backend.tests.application.test_registration -v` — PASS, 7 tests, 0.002s. |
| Full fresh discovery | `uv run --locked python -m unittest discover -s backend/tests -v` — PASS, 7 tests, 0.001s. No integration discovery, database, network, or secrets invoked. |
| Static diff check | `git diff --check` — PASS. |
| Runtime harness | N/A — this slice has no runtime boundary; behavior-focused port doubles exercised the application transaction path without persistence, HTTP, bootstrap, settings, database, or network. |
| Rollback boundary | Revert only `backend/tests/` Slice-1 markers, support, domain, and application files; no production behavior or later-slice work is removed. |
| Immediate-parent budget | `git diff --no-index --numstat /dev/null` for the nine new Slice-1 test/support files: 257 additions, 0 deletions; `257 <= 399`. SDD artifact churn and unrelated dirty files excluded. |

### Production Changes

None. Initial test-authoring mistakes (a non-exported convenience import and overlength sample shipment strings) were corrected in test fixtures before green verification; they did not prove a production-contract defect.

### Remaining Slices

Slices 2–6 remain pending and were not started.

## Slice 2 — Persistence

**Status:** complete  
**Mode:** Standard (`strict_tdd` configuration is absent; a unittest runner exists)  
**Delivery:** force-chained, `stacked-to-main`; immediate accepted parent `c72c92e`; current boundary is Slice 2 only.

### Completed Tasks

- [x] 2.1 Fresh persistence mapper, repository, and transaction contracts using record metadata and small session spies.
- [x] 2.2 Focused/full verification, dialect-limit declaration, and immediate-parent line-budget checkpoint.

### Fresh-Contract Evidence

Tests derive from current production source through CodeGraph and current PRD, architecture, OpenSpec proposal/spec/design/tasks, and repository guides. They do not use deleted tests, Git/history content, `.kiro`, failed-refactor artifacts/memories, or current integration assertions as authority. Mapper metadata proves only table/column/type/default intent; transaction diagnostics are synthetic unit seams. SQLite and this slice do not prove PostgreSQL constraint names or diagnostics, migrations, RLS/ACL, FK actions, timezone/`Decimal` database round-trips, or real database behavior; Slices 5–6 own those claims.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `uv run --locked python -m unittest backend.tests.persistence -v` — PASS, 9 tests, 0.002s. |
| Full fresh discovery | `uv run --locked python -m unittest discover -s backend/tests -v` — PASS, 16 tests, 0.004s; Slice 1's 7 tests remain green. No integration discovery, database, network, or secrets invoked. |
| Static diff check | `git diff --check` — PASS. |
| Runtime harness | N/A — this unit exercises dialect-neutral mapper/repository/session seams with record metadata, session spies, and synthetic `IntegrityError` diagnostics; no runtime boundary can establish PostgreSQL behavior. |
| Rollback boundary | Revert only `backend/tests/persistence/{__init__.py,test_mappers.py,test_repositories.py,test_transaction.py}`; Slice 1 and production behavior remain intact. |
| Immediate-parent budget | New Slice-2 files measured against `c72c92e` with `git diff --no-index --numstat /dev/null`: 10 + 94 + 81 + 78 additions, 0 deletions = **263 changed lines**; `263 <= 399`. SDD artifact churn and unrelated dirty `backend/pyproject.toml`, `uv.lock`, root, and untracked files are excluded. |

### Production Changes

None. The initial mapper expectation used the wrong fixture value and was corrected before green verification; it did not prove a production-contract defect.

### Remaining Slices

Slices 3–6 remain pending and were not started.

## Slice 3 — HTTP/OpenAPI

**Status:** complete  
**Mode:** Standard (`strict_tdd` configuration is absent; a unittest runner exists)  
**Delivery:** force-chained, `stacked-to-main`; immediate accepted parent `8b73723`; current boundary is Slice 3 only.

### Completed Tasks

- [x] 3.1 Fresh ASGI request/response, mapping, route, and focused OpenAPI contracts.
- [x] 3.2 Fresh error-envelope contracts, full discovery, and immediate-parent line-budget checkpoint.

### Fresh-Contract Evidence

Tests derive only from current production through CodeGraph, current PRD/architecture, corrected OpenSpec artifacts, and repository guides. They do not use deleted tests, Git/history content, `.kiro`, failed-refactor artifacts/memories, or current integration assertions as authority. Injected ASGI assembly uses the current API router and registered exception handlers without a database, settings, network, or PostgreSQL claim. `TestClient` is compatible with the locked FastAPI 0.138.1, Starlette 1.3.1, and httpx 0.28.1 dependencies; no deprecation warnings occurred. The tests live in `backend/tests/api/`, which avoids shadowing Python's standard-library `http` package; an explicit `import http.cookies` resolves to the Python 3.13 standard-library module.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `uv run --locked python -m unittest backend.tests.api.test_registration_endpoint backend.tests.api.test_openapi -v` — PASS, 6 tests, 0.117s. |
| Full fresh discovery | `uv run --locked python -m unittest discover -s backend/tests -v` — PASS, 22 tests, 0.127s; Slices 1–2 remain green. No PostgreSQL, database, network, or secrets invoked. |
| No-shadow proof | `uv run --locked python -c "import http.cookies; print(http.cookies.__file__)"` — PASS; resolved `/home/luis-cm/.local/share/uv/python/cpython-3.13.13-linux-x86_64-gnu/lib/python3.13/http/cookies.py`. |
| Runtime harness | Injected FastAPI ASGI router plus registered exception handlers through `TestClient` — PASS; exact POST, redirect-only trailing slash, and OpenAPI generation exercised without a live server. |
| Static diff check | `git diff --check` — PASS. |
| Rollback boundary | Revert only `backend/tests/support/http_payloads.py` and `backend/tests/api/`; Slices 1–2 and production behavior remain intact. |
| Immediate-parent budget | New Slice-3 files measured from `8b73723` with `git diff --no-index --numstat /dev/null`: 21 + 1 + 168 + 35 additions, 0 deletions = **225 changed lines**; `225 <= 399`. SDD artifact churn and unrelated dirty `backend/pyproject.toml`, `uv.lock`, root, and untracked files are excluded. |

### Production Changes

None. Fresh evidence identified no production defect. The Slice-3 package was renamed from `http` to `api`; no standard-library proxying, `load_tests`, or source/path manipulation remains.

### Remaining Slices

Slices 4–6 remain pending and were not started.

## Slice 4 — Infrastructure/Bootstrap/Settings

**Status:** complete  
**Mode:** Standard  
**Delivery:** force-chained, `stacked-to-main`; immediate accepted parent `e135667`; current boundary is Slice 4 only.

### Completed Tasks

- [x] 4.1 Fresh settings, explicit-entrypoint handoff, database resource, request-session lifecycle, and application-composition contracts in `backend/tests/runtime/`.
- [x] 4.2 Behavioral seams only; focused/canonical full discovery, no-shadow proof, diff check, and immediate-parent checkpoint.

### Fresh-Contract Evidence

Tests derive only from current production through CodeGraph and current OpenSpec/repository guidance. The non-colliding `runtime` package preserves canonical unittest discovery without changing production imports or test-runner configuration. Typed session doubles use the current `SessionFactory` callable contract and exact context-manager exit parameters; no broad forwarding wrappers are used.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `uv run --locked python -m unittest backend.tests.runtime.test_settings backend.tests.runtime.test_database_resources backend.tests.runtime.test_composition -v` — PASS, 10 tests, 0.070s. |
| Full fresh discovery | `uv run --locked python -m unittest discover -s backend/tests -v` — PASS, 32 tests, 0.173s; Slices 1–3 remain green. |
| No-shadow proof | `uv run --locked python -c 'import bootstrap; print(bootstrap.__file__)'` — PASS; resolved `backend/src/bootstrap/__init__.py`. |
| Runtime harness | Injected composition, temporary dotenv paths, isolated environment/CWD, patched entrypoint handoff, and SQLAlchemy connect-event observation — PASS; no live server, network, database session, or real dotenv read. |
| Static diff check | `git diff --check` — PASS. |
| Rollback boundary | Revert only `backend/tests/runtime/`; prior slices and production behavior remain intact. |
| Immediate-parent budget | New Slice-4 runtime files measured against `e135667`: 213 additions, 0 deletions; `213 <= 399`. SDD artifact churn and unrelated dirty files excluded. |

### Production Changes

None.

### Remaining Slices

Slices 5–6 remain pending and were not started.

## Slice 5 — PostgreSQL Schema/Security/Types

**Status:** complete  
**Mode:** Standard  
**Delivery:** force-chained, `stacked-to-main`; immediate accepted parent `00ce2db`; current boundary is Slice 5 only. The parent is the accepted deletion-only prerequisite (five files, 616 lines), excluded from fresh evidence and this slice's budget.

### Completed Tasks

- [x] 5.1 Guarded support plus current migration-derived schema, security, and type contracts.
- [x] 5.2 Focused evidence, Supabase runtime harness, full integration regression, and checkpoint without a Slice-6 claim.

### Fresh-Contract Evidence

Tests derive from the current migration, Warehouse dictionary, production ORM records, corrected SDD artifacts, and the guarded local PostgreSQL runtime. They use no `DATABASE_URL` fallback, current or deleted test assertions, Git/history, `.kiro`, or failed-refactor artifacts/memories. The suite owns only guard, cleanup, schema/security, and type round trips; it makes no transaction-diagnostic, rollback, or registration claim reserved for Slice 6.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest backend.integration_tests.test_postgres_schema_security backend.integration_tests.test_postgres_types -v` — PASS, 4 tests, 0.128s. |
| Canonical unit discovery | `uv run --locked python -m unittest discover -s backend/tests -v` — PASS, 32 tests, 0.211s. |
| Runtime harness | `pnpm supabase status` — PASS; the migrated local PostgreSQL target is `127.0.0.1:54322/postgres`. Full guarded integration discovery — PASS, 4 tests, 0.135s. |
| Security/type evidence | Both tables have RLS enabled, zero policies, and no SELECT/INSERT/UPDATE/DELETE privileges for `anon`, `authenticated`, or `service_role`; schema introspection verifies named PK/FK/unique/CHECK/index and FK `ON DELETE RESTRICT`; aware `timestamptz` and `numeric` values round trip as `datetime` with UTC and `Decimal`. |
| Immediate-parent budget | Fresh Slice-5 integration files measured from `00ce2db`, excluding the deletion baseline, SDD artifacts, and unrelated dirt: 1 + 38 + 69 + 34 additions = **142 changed lines**; `142 <= 399`. |
| Static diff check | `git diff --check` — PASS. |
| Rollback boundary | Revert only `backend/integration_tests/{__init__.py,database_test_support.py,test_postgres_schema_security.py,test_postgres_types.py}`; no production, schema, migration, or Slice-6 behavior is removed. |

### Production Changes

None.

### Remaining Slices

Superseded by the completed Slice 6 record below.

## Slice 6 — PostgreSQL Transactions/Registration

**Status:** complete  
**Mode:** Standard  
**Delivery:** force-chained, `stacked-to-main`; immediate accepted parent `89d1f10`; committed slice `bed637a test(backend): rebuild PostgreSQL transaction coverage`; current boundary is Slice 6 only.

### Completed Tasks

- [x] 6.1 Guarded real-PostgreSQL transaction diagnostics, unknown propagation, rollback, atomic registration, duplicate shipment, and per-batch Bale-uniqueness contracts.
- [x] 6.2 Focused/guarded integration/full discovery, immediate-parent line-budget checkpoint, and Slice-6 rollback boundary.

### Fresh-Contract Evidence

Tests derive from current production contracts, current OpenSpec artifacts, and the guarded local PostgreSQL runtime. They cover only the transactions/registration scope reserved for Slice 6: named diagnostic translation, unknown integrity propagation, rollback semantics, atomic registration, and uniqueness behavior. No production, schema, migration, manifest, lockfile, or other runtime behavior was changed.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest backend.integration_tests.test_postgres_transaction backend.integration_tests.test_postgres_registration -v` — PASS, 7 tests. |
| Full unit discovery | `uv run --locked python -m unittest discover -s backend/tests -v` — PASS, 32 tests. |
| Runtime harness | `pnpm supabase status` — PASS; guarded full integration discovery (`TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest discover -s backend/integration_tests -v`) — PASS, 11 tests. |
| Static diff check | `git diff --check` — PASS. |
| Rollback boundary | Revert only `backend/integration_tests/{database_test_support.py,test_postgres_transaction.py,test_postgres_registration.py}` from `bed637a`; no prior slice, production, schema, or migration behavior is removed. |
| Immediate-parent budget | `bed637a` from parent `89d1f10`: `database_test_support.py` (+13), `test_postgres_transaction.py` (+105), and `test_postgres_registration.py` (+110) = **228 changed lines**; `228 <= 399`. SDD artifact churn and unrelated worktree changes are excluded. |

### Production Changes

None. Slice 6 changes only `backend/integration_tests/database_test_support.py`, `backend/integration_tests/test_postgres_transaction.py`, and `backend/integration_tests/test_postgres_registration.py`.

### Completion and Review Authority

All 16 tasks are complete. Native review authority remains corrupted and is manually excepted; no valid native review receipt is claimed. This apply-progress reconciliation does not modify the verification report or authorize review, archive, or any authority operation.
