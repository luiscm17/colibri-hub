# Tasks: Rebuild Backend Test Suite

## Review Workload Forecast

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

| Slice / parent | Lines | Focused command | Harness / rollback |
|---|---:|---|---|---|
| 1 / `5730050` | 318 | `uv run --locked python -m unittest backend.tests.domain.test_core_contracts backend.tests.application.test_registration -v` | fakes / Slice 1 |
| 2 / 1 | 276 | `uv run --locked python -m unittest backend.tests.persistence -v` | dialect-neutral / Slice 2 |
| 3 / 2 | 292 | `uv run --locked python -m unittest backend.tests.api.test_registration_endpoint backend.tests.api.test_openapi -v` | injected ASGI / Slice 3 |
| 4 / 3 | 284 | `uv run --locked python -m unittest backend.tests.runtime.test_settings backend.tests.runtime.test_database_resources backend.tests.runtime.test_composition -v` | injected seams / Slice 4 |
| 5 / `00ce2db` | 326 | guarded focused integration | `pnpm supabase status` / Slice 5 |
| 6 / 5 | 348 | guarded integration discovery | `pnpm supabase status` / Slice 6 |

Immediate-parent measurement and 399-line cap apply. Slice 5 measures fresh integration additions from `00ce2db`, excluding the baseline deletion, SDD artifacts, and unrelated worktree changes. No installs/sync, unsafe DB/network, staging, commits, or PR automation. Full: `uv run --locked python -m unittest discover -s backend/tests -v`; integration: `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest discover -s backend/integration_tests -v`. Slice 5 excludes Slice 6 coverage.

## Slice 1: Domain/Application — 318
- [x] 1.1 RED first; create `backend/tests/__init__.py` and `support/{__init__.py,values.py,builders.py,doubles.py}` with fixtures.
- [x] 1.2 RED then `backend/tests/domain/{__init__.py,test_core_contracts.py}`: value-object normalization/invalid partitions, weight/date boundaries, Bale delivery, batch trim/nonempty/unique IDs/identity.
- [x] 1.3 RED then `backend/tests/application/{__init__.py,test_registration.py}`: required Bales, canonicalization, batch-before-Bales, result/order, conflicts, unknown propagation; minimal fix after failure only.
- [x] 1.4 Focused/full discovery and 399-line checkpoint; revert 1.

## Slice 2: Persistence — 276
- [x] 2.1 RED then `backend/tests/persistence/{__init__.py,test_mappers.py,test_repositories.py,test_transaction.py}`: fields, ordering, rollback, named/unknown synthetic `IntegrityError` diagnostics.
- [x] 2.2 SQLite cannot prove PostgreSQL diagnostics, constraints, RLS, FK actions, timezone, or Decimal; verify/revert Slice 2.

## Slice 3: HTTP/OpenAPI — 292
- [x] 3.1 RED then `backend/tests/support/http_payloads.py` and `backend/tests/api/{__init__.py,test_registration_endpoint.py,test_openapi.py}`: exact POST/201 contract and documented routes/responses.
- [x] 3.2 Assert shipment `409/duplicate_shipment_number/shipment_number`; Bale `422/duplicate_bale_number/bales[].bale_number`; validation/domain `422`, unexpected `500`; avoid duplicates; verify/revert Slice 3.

## Slice 4: Settings/Bootstrap — 284
- [x] 4.1 RED then `backend/tests/runtime/{__init__.py,test_settings.py,test_database_resources.py,test_composition.py}`: source precedence, `SecretStr`, dotenv isolation, lazy no-connect engine, session lifecycle, composition/load/bypass.
- [x] 4.2 Behavioral seams only—no AST checker/tooling; verify/checkpoint/revert Slice 4.

## Slice 5: PostgreSQL Schema/Security/Types — 326
- [x] 5.1 RED then retain `backend/integration_tests/__init__.py`, rewrite `database_test_support.py`, add `test_postgres_schema_security.py`/`test_postgres_types.py`: fail-fast allowlist, schema/named constraints/index/FK/status CHECK, RLS zero policies/revoked ACL, aware time/Decimal, FK-aware cleanup.
- [x] 5.2 Focused fresh evidence, `pnpm supabase status`, full integration regression; checkpoint/revert without Slice 6 claim.

## Slice 6: PostgreSQL Transactions/Registration — 348
- [x] 6.1 RED then rewrite `backend/integration_tests/test_postgres_transaction.py` and `test_postgres_registration.py`: diagnostics, unknown propagation, rollback, atomic registration, duplicate shipment, per-batch Bale uniqueness, isolation hardening.
- [x] 6.2 Focused + guarded integration + full discovery; final <=399/parent/unrelated-worktree checkpoint; revert Slice 6.

## Global Apply Gate
- [x] G.1 Fresh failing contract evidence precedes fixes; count diff and stop/re-slice before 399; broader behavior needs a decision.
- [x] G.2 No pytest/coverage/lint/type tools, frontend/new behavior, schema changes, or automatic Git actions; preserve unrelated `backend/pyproject.toml`, `uv.lock`, root/untracked.
