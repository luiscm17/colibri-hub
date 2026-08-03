# Apply Progress: Access Authorization Spine

**Mode:** Standard (`strict_tdd: false`)
**Delivery:** `auto-chain`, `feature-branch-chain`
**Current recorded boundary:** PR #2 `back/access-auth-spine-persistence` targets `back/access-auth-spine` after PR #1 merged.
**Artifact continuity correction:** This document consolidates the earlier blocked planning attempt, approved replan, PR #1 completion, initial PR #2 blocker, and the maintainer-authorized PR #2 correction. No implementation or verification was performed by this artifact-only update.

## Cumulative Status

- [x] 1.1 Access domain models and policy tests
- [x] 1.2 Application behavior, bootstrap, mutations, and audit tests
- [x] 1.3 Mutation authorization, audit contract, and serialized invariant tests
- [x] 2.1 SQLAlchemy persistence and registry
- [x] 2.2 Migration safeguards
- [x] 2.3 PostgreSQL persistence proof
- [ ] 3.1–3.4 HTTP, composition, and Warehouse integration
- [ ] 4.1 Final chain verification

**Task total:** 6/11 complete. Phase 3 and Phase 4 remain pending.

## History: Original Blocked Forecast and Approved Replan

The original pre-write apply attempt stopped before source changes because the former PR #1 forecast was approximately 1,340 additions plus deletions, beyond a reviewable slice.

| Original required surface | Estimated additions + deletions |
|---|---:|
| Domain models and policy rules | 150 |
| Application ports, use cases, audit, and mutation invariant | 260 |
| SQLAlchemy records, mappings, repositories, registry, package discovery | 300 |
| Imperative migration with constraints, RLS/ACL, indexes, and safeguards | 250 |
| Unit and PostgreSQL concurrency/atomicity proof | 380 |
| **Original blocked forecast** | **1,340** |

The maintainer-approved replan changed delivery to three `feature-branch-chain` slices accumulating into tracker branch `back/access-auth-spine`:

1. PR #1: domain/application and unit proof, estimated ~620 lines.
2. PR #2: persistence, migration, safeguards, and PostgreSQL proof, estimated ~720 lines.
3. PR #3: HTTP/composition/Warehouse integration, estimated ~360 lines.

PR #1 and PR #2 retain High 400-line review risk but remain within the approved 800-line slice budget. In this chain, each child targets its immediate parent; no child targets `main` directly.

## Completed PR #1: Domain and Application

**Branch/scope:** `back/access-auth-spine-core` targeting tracker `back/access-auth-spine`; framework-free Access domain/application only, without ORM, HTTP, or Warehouse behavior changes.

| Evidence | Recorded result |
|---|---|
| Focused Access unit tests | `uv run --locked --package backend python -m unittest backend.tests.test_access_spine -v` — exit 0; 7 passed. |
| Full unit suite | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 39 passed. |
| Runtime harness | N/A: deterministic store doubles prove the framework-free domain/application seam. |
| Diff hygiene | `git diff --check -- backend/src/access backend/tests/test_access_spine.py openspec/changes/access-auth-spine` — exit 0. |
| Rollback boundary | Remove PR #1 `backend/src/access/` domain/application/ports work and `backend/tests/test_access_spine.py`; do not alter existing persistence, HTTP, or Warehouse behavior. |

PR #1 core/test changes were recorded as 354 additions and 0 deletions before planning-artifact updates.

## PR #2: Initial Blocked Persistence Result

PR #2 added Access SQLAlchemy persistence, record registration, package discovery, migration `20260803015250_create_access_authorization_spine.sql`, and guarded PostgreSQL proof on `back/access-auth-spine-persistence` targeting `back/access-auth-spine` after PR #1 merged.

Focused Access evidence passed, but the initial full guarded integration suite ran **14 tests: 12 passed and 2 failed**. The failures were stale Warehouse expectations in `test_postgres_schema_security` and `test_postgres_types`, which expected `raw_material_batches.received_at` to remain `timestamptz` and omitted `raw_material_bales.delivery_date`. Those expectations contradicted authoritative migrations `20260730074124_alter_received_at_to_date.sql` and `20260730074125_add_delivery_date_and_indexes.sql`. Tasks 2.1–2.3 remained unchecked until a maintainer authorized correction.

## PR #2: Maintainer-Authorized Correction and Final Result

The maintainer authorized only stale expectation alignment and the Access services warning correction. The correction retained test intent: current schema shape plus PostgreSQL `date` and `Decimal` behavior.

- `test_postgres_schema_security.py` now asserts `received_at` as `date`, `delivery_date`, its state-date constraint, and current migration indexes.
- `test_postgres_types.py` now asserts `date` plus `Decimal` round trips.
- `access/application/services.py` expanded compact `class …: pass` declarations to standard multiline declarations. The repository has no configured Python lint/type-check command; the source matched E701-style static-editor diagnostics. Exception behavior and types did not change.

| Evidence | Final recorded result |
|---|---|
| Focused stale Warehouse tests | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest backend.integration_tests.test_postgres_schema_security backend.integration_tests.test_postgres_types -v` — exit 0; 4 passed. |
| Focused Access PostgreSQL tests | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest backend.integration_tests.test_access_postgres -v` — exit 0; 3 passed. |
| Full unit suite | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 39 passed. The only output was the pre-existing FastAPI/Starlette TestClient deprecation warning. |
| Full guarded integration suite | After a clean reset, `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v` — exit 0; 14 passed. |
| Reset and migration state | `pnpm supabase db reset --local --no-seed` — exit 0; applied migrations `20260722130455`, `20260730074124`, `20260730074125`, and `20260803015250`. `pnpm supabase migration list --local` reported local/remote alignment for all four. |
| Diff hygiene | `git diff --check` on tracked intended paths plus `git diff --no-index --check /dev/null` for each intended untracked file — exit 0. |
| Cleanup/process evidence | A final local reset completed successfully; test sessions closed, engines disposed in tear-down, and no `python.*unittest` process remained. |

**Final intended PR #2 boundary:** 350 additions plus deletions, below the maintainer-authorized 800-line maximum.

**PR #2 rollback boundary:** Revert only `backend/src/access/adapters/`, `backend/src/infra/persistence/record_registry.py`, `backend/pyproject.toml`, `supabase/migrations/20260803015250_create_access_authorization_spine.sql`, `backend/integration_tests/test_access_postgres.py`, corrected Warehouse integration tests, `backend/src/access/application/services.py`, and PR #2 task/progress artifacts. Retain PR #1 core and all Phase 3/4 work.

## Preserved Boundaries

No HTTP, FastAPI, CORS, Warehouse authorization port, Authentication/Supabase Auth, frontend, or Phase 3/4 behavior was implemented in PR #2. No packages were installed and no commit, push, PR, review-lifecycle, or native-attempt-state operation was performed.
