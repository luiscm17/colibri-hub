# Apply Progress: Access Authorization Spine

**Mode:** Standard (`strict_tdd: false`)
**Delivery:** `auto-chain`, `feature-branch-chain`
**PR #3 provenance:** branch `back/access-auth-spine-http` was created from merged tracker `origin/back/access-auth-spine` at `d83eb17` (`d83eb173cc70a351904b0a6112aa8aacada09425`); its PR targets `back/access-auth-spine`.
**Artifact continuity correction:** This document consolidates the earlier blocked planning attempt, approved replan, PR #1 completion, initial PR #2 blocker, and the maintainer-authorized PR #2 correction. No implementation or verification was performed by this artifact-only update.

## Cumulative Status

- [x] 1.1 Access domain models and policy tests
- [x] 1.2 Application behavior, bootstrap, mutations, and audit tests
- [x] 1.3 Mutation authorization, audit contract, and serialized invariant tests
- [x] 2.1 SQLAlchemy persistence and registry
- [x] 2.2 Migration safeguards
- [x] 2.3 PostgreSQL persistence proof
- [x] 3.1–3.4 HTTP, composition, and Warehouse integration
- [x] 4.1 Final chain verification

**Task total:** 11/11 complete. All phases are complete.

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

PR #1 and PR #2 retain High 400-line review risk but remain within the approved 800-line slice budget. Each completed slice targets tracker `back/access-auth-spine` after its predecessor has merged there; no child targets `main` directly.

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
## Completed PR #3: HTTP, Composition, and Warehouse Gate
**Branch/scope:** `back/access-auth-spine-http`, created from merged tracker `origin/back/access-auth-spine` at `d83eb17` (`d83eb173cc70a351904b0a6112aa8aacada09425`) and targeting `back/access-auth-spine`; Access self HTTP, Access-to-Warehouse adapter, fail-closed identity seam, CORS header, and only the bale-registration authorization gate. No Authentication provider, migration, package, frontend, other route protection, commit, push, PR, review, or native-attempt operation was performed.
**Deployment constraint — Critical, known and intentional:** production HTTP fails closed with `401` until a future Authentication adapter supplies validated trusted identities. This is not an implementation failure; deployment cannot provide protected access before that successor capability exists.
| Evidence | Recorded result |
|---|---|
| Focused HTTP/composition tests | `uv run --locked --package backend python -m unittest backend.tests.api.test_access_http_authorization backend.tests.api.test_registration_endpoint backend.tests.api.test_openapi backend.tests.runtime.test_composition -v` — exit 0; 14 passed. |
| Runtime harness | The focused TestClient suite proved production `create_app` returns `401` without an identity resolver, accepts deterministic injected identities, returns ordinary/global `/access/me` snapshots, returns specific missing/inactive self outcomes, returns generic `403 access_denied` before invalid request mapping or mutation, and accepts the CORS `Authorization` request header. No server process was started. |
| Full unit suite | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 43 passed. The only output was the existing FastAPI/Starlette TestClient deprecation warning. |
| Guarded PostgreSQL integration suite | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v` — exit 0; 14 passed. No reset or schema change was needed. |
| Diff hygiene | `git diff --check -- backend/src/access backend/src/bootstrap backend/src/warehouse backend/tests/api` — exit 0. |
| Cleanup/process evidence | TestClient was in-process; no server was started. `pgrep -af 'python.*(unittest|fastapi|uvicorn)'` reported only the checking shell process after verification. |
| Rollback boundary | Revert only PR #3 `backend/src/access/adapters/{http_router,warehouse_authorization}.py`, `backend/src/warehouse/bales/ports/authorization.py`, the listed bootstrap/Warehouse HTTP files, and API/composition tests; retain PR #1–2 domain/persistence/migration work. |
## Completed Phase 4: Chain Verification

- **Base and merged boundaries:** `origin/back/access-auth-spine` resolves to `d83eb173cc70a351904b0a6112aa8aacada09425`; PR #37 merged core into that tracker at `de57496`, and PR #38 merged persistence at `d83eb17`. The HTTP worktree is based directly on that merged tracker, so no PR #1/PR #2 paths replay in the intended PR #3 set.
- **Intended path boundary and count:** only the HTTP/composition/Warehouse source paths, their API/runtime tests, and these two SDD artifacts are included. They measure **466 implementation/test + 50 SDD artifact = 516 additions plus deletions**; **496** and **503** remain historical intermediate counts only.
- **Explicit preservation/exclusion:** unstaged unrelated `main.py`, root `pyproject.toml`, and `uv.lock` remain preserved and excluded; they are not PR #3 pollution because manual delivery MUST selectively stage only the intended paths.
- **Focused evidence:** read-only Git/GitHub checks confirmed PR #37/#38 merged bases, the direct `d83eb17` base, intended-path-only source/test accounting, and absence of PR #1/PR #2 replay. No tests, installs, database reset, commit, push, PR, review, or native-attempt action ran.
- **Runtime harness:** N/A for this final read-only chain-verification unit; the persisted PR #3 TestClient runtime evidence remains the applicable runtime proof.
- **Rollback boundary:** revert only the intended PR #3 HTTP/composition/Warehouse source and API/runtime test paths plus `openspec/changes/access-auth-spine/{tasks,apply-progress}.md`; retain PR #1/PR #2 and all explicitly excluded unrelated paths.
