# Design: Rebuild Backend Test Suite

## Technical Approach

Commit `5730050` is the approved exceptional deletion-only baseline: 36 files and 2,746 lines removed from `backend/tests/`, with zero additions and no green-suite evidence. Commit `00ce2db` is the accepted Slice-5 measurement parent: five legacy integration files and 616 lines removed as a prerequisite `size:exception`, not a fresh slice or green evidence. Build six fresh `unittest` slices from current runtime and migration contracts; never recover legacy assertions.

## Architecture Decisions

| Decision | Rejected | Rationale |
|---|---|---|
| Representative partitions, `subTest`, and small capability builders | Every validation permutation; fixture god-module | Covers high-value boundaries without duplicate assertions or budget pressure. |
| Session fakes/spies for persistence units | SQLite as PostgreSQL evidence | Slice 2 proves mapper/repository/transaction orchestration only; PostgreSQL alone proves driver diagnostics, constraints, types, and security. |
| Injected `TestClient` contracts | Live server; duplicated mapper/handler tests | Exercises the exact ASGI route and observable envelopes without network or infrastructure. |
| Behavioral dependency seams only | Custom AST dependency checker or new tool | Existing injection and port seams provide useful architecture evidence without maintaining a parser. No `backend/tests/architecture/` package is planned. |

## Data Flow

    deterministic command → RegisterRawMaterialBatch → ports/fakes
                                              └──────→ adapters → guarded PostgreSQL
    HTTP payload → injected FastAPI app → use-case stub → response/error envelope

## Files and Delivery Slices

Changed-line forecasts include additions, modifications, renames, and deletions, but no invented production-fix reserve.

| # | Files / contract ownership | Forecast |
|---|---|---:|
| 1 | Create `backend/tests/__init__.py`, `support/{__init__.py,values.py,builders.py,doubles.py}`, `domain/{__init__.py,test_core_contracts.py}`, `application/{__init__.py,test_registration.py}`. Prove representative canonicalization/invalid partitions, weight/date boundaries, Bale transition, batch identity/uniqueness, and registration success/order/result plus canonical duplicate, known conflicts, and unknown failure. | 318 |
| 2 | Create `persistence/{__init__.py,test_mappers.py,test_repositories.py,test_transaction.py}`. Prove field round-trips, ordered adds, commit/rollback, and synthetic named/unknown `IntegrityError` handling; make no PostgreSQL claim. | 276 |
| 3 | Create `support/http_payloads.py`, `api/{__init__.py,test_registration_endpoint.py,test_openapi.py}`. Prove the single exact POST/201 contract, shipment 409, bale/domain/request 422, unexpected 500, and nonduplicated OpenAPI responses/route. | 292 |
| 4 | Create `runtime/{__init__.py,test_settings.py,test_database_resources.py,test_composition.py}`. Prove settings precedence/redaction/isolation, lazy engine creation, session lifetime, and injected composition bypass. | 284 |
| 5 | Retain `backend/integration_tests/__init__.py`; revalidate `database_test_support.py`; rewrite schema coverage as `test_postgres_schema_security.py`; add `test_postgres_types.py`. Prove guarded URL, exact schema/FK/constraints/index, RLS/ACL/policies, aware-time and `Decimal` round-trips, with safe FK-aware cleanup. | 326 |
| 6 | Rewrite transaction/registration coverage as `test_postgres_transaction.py` and `test_postgres_registration.py`. Prove real constraint diagnostics, unknown failure propagation, rollback, atomic registration, duplicate shipment and per-batch bale behavior, and isolation hardening. | 348 |

Discovery markers are exactly `backend/tests/__init__.py`, `backend/tests/support/__init__.py`, `backend/tests/domain/__init__.py`, `backend/tests/application/__init__.py`, `backend/tests/persistence/__init__.py`, `backend/tests/api/__init__.py`, `backend/tests/runtime/__init__.py`, and retained `backend/integration_tests/__init__.py`; namespace recursion is not assumed. Helpers remain capability-scoped and immutable.

## Interfaces / Contracts

`validated_test_database_url()` reads only `TEST_DATABASE_URL` and rejects before engine creation unless the URL is `postgresql+psycopg`, loopback, port `54322`, database `postgres`. Current HTTP authority governs the conflict distinction: duplicate shipment is `409`; duplicate bale is `422`.

## Testing and Acceptance

Slice 1 is measured against parent `5730050`; each later slice is measured against its immediate accepted parent. Slice 5 is measured from `00ce2db`, excluding SDD artifacts and unrelated working-tree changes. A slice is independently green when its focused modules and all fresh `backend/tests` introduced through that slice pass at its tip. Slice 5 additionally runs its focused fresh integration modules and full integration discovery as regression evidence; transaction/registration modules are not all fresh until slice 6. Slice 6 makes full guarded integration discovery fresh acceptance evidence. Absolute changed-line maximum is 399. Any evidence-backed production fix counts at actual size; if it threatens the cap or broadens behavior, stop and re-slice before editing.

Apply must start from the stated parent, preserve unrelated working-tree modifications in `backend/pyproject.toml` and `uv.lock`, and exclude them from every slice. No install, staging, commit, or PR action is automatic.

## Threat Matrix

N/A — no routing dispatcher, shell/subprocess, VCS/PR automation, executable classification, or process-integration boundary is introduced. The database-target guard is specified above.

## Migration / Rollout

No migration required. Revert fresh slices from newest to oldest. Restoring the legacy tests after fresh slices land would create competing suites and therefore requires maintainer coordination; do not treat baseline rollback as an isolated revert.

## Open Questions

None.
