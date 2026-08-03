# Tasks: Access Authorization Spine

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | PR 1: ~620; PR 2: ~720; PR 3: ~360; total: ~1,700 additions+deletions |
| 400-line budget risk | High for PR 1/2; Low for PR 3 |
| 800-line budget risk | Low for every slice |
| Chained PRs recommended | Yes |
| Suggested split | Domain/application → persistence/migration/PostgreSQL → HTTP/composition |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Start / finish and boundary | PR/base and dependency | Focused evidence | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Start on `back/access-auth-spine-core`; finish abstract Access policy/use cases and unit proof, without ORM/HTTP. | PR #1 targets tracker `back/access-auth-spine`; no dependency. | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` (focused Access modules first). | N/A: pure domain/application; deterministic doubles are the runtime seam. | Revert `backend/src/access/{domain,application,ports}/` and unit tests only. |
| 2 | Start from merged PR #1 tracker state; finish SQLAlchemy, migration, safeguards, audit persistence, and PostgreSQL proof. | `back/access-auth-spine-persistence` targets tracker `back/access-auth-spine` after PR #1 merged. | Focused persistence tests, then guarded integration suite. | User runs `pnpm supabase db reset --local --no-seed`; then `TEST_DATABASE_URL=... uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v`. | Revert Access persistence, registry, migration, and integration tests; retain abstract core. |
| 3 | Start from merged PR #1–2 tracker state; finish HTTP/composition, `/me`, CORS, and only the bale write gate. | `back/access-auth-spine-http` was created from merged tracker `origin/back/access-auth-spine` at `d83eb17` (`d83eb173cc70a351904b0a6112aa8aacada09425`) and its PR targets `back/access-auth-spine`. | Focused API/runtime tests, then backend unit suite. | Inject resolver/port into `create_app`; no installation or production identity provider. | Revert HTTP/bootstrap/Warehouse adapter changes and API tests; retain PR #1–2. |

## Phase 1: Domain and Application (PR #1)

- [x] 1.1 Create `backend/src/access/domain/` immutable subject/scope, exact additive active-policy, explicit global-admin, and self-snapshot rules; unit-test exact, inactive, global, and ordinary-non-global scenarios.
- [x] 1.2 Create `backend/src/access/application/` driver ports/use cases for authorize, current access, trusted bootstrap, and profile/role/current-assignment mutations; test idempotent/conflicting bootstrap and every final-admin removal path with atomic unchanged rejection.
- [x] 1.3 Keep mutation authorization, actor/reason/operation inputs, audit command contract, and serialized invariant behavior at abstract ports; test accepted mutations and redacted audit events without persistence.

## Phase 2: Persistence and PostgreSQL Proof (PR #2)

- [x] 2.1 Create SQLAlchemy records/repositories under `backend/src/access/adapters/persistence/`; register records in `backend/src/infra/persistence/record_registry.py` and expose `access*` in `backend/pyproject.toml`.
- [x] 2.2 Create `supabase/migrations/<timestamp>_create_access_authorization_spine.sql`: all tables, singleton lock, named constraints/restrictive FKs, active/current/admin indexes, immutable redacted audit, RLS/ACL, and no policy seeds.
- [x] 2.3 Add `backend/integration_tests/` PostgreSQL proof for bootstrap retry/conflict/partial state, constraints, RLS/ACL, immutable history, two scopes, and concurrent final-admin removals; reset is verification-only and user-run.

## Phase 3: HTTP, Composition, and Warehouse Gate (PR #3)

- [x] 3.1 Create `backend/src/warehouse/bales/ports/authorization.py` with opaque `AuthenticatedIdentity` and narrow consumer-owned `AuthorizationPort`; Access must not own this contract.
- [x] 3.2 Create `backend/src/access/adapters/warehouse_authorization.py` and `/api/v1/access/me`; test ordinary/global snapshots and specific missing/inactive self outcomes versus generic business denial.
- [x] 3.3 Modify `backend/src/bootstrap/{http_application,api_router,warehouse_bale_dependency}.py` for composition, deterministic test identity injection, fail-closed `401`, route discovery, and `Authorization` CORS header.
- [x] 3.4 Modify `backend/src/warehouse/bales/adapters/http/router.py` so only `POST /api/v1/warehouse/bales` derives `write + warehouse.raw_materials` and authorizes before mapping/validation/mutation; test allowed, denied, client-authority-ignored, and unaffected endpoints.

## Phase 4: Chain Verification

- [x] 4.1 Verify each child diff against its immediate parent, record focused/runtime evidence, preserve the user-only installation rule, and do not create branches, commits, PRs, or invoke review lifecycle commands.

## Completion Metadata Correction

- PR #3 implementation/test changes are **466 additions plus deletions before task/progress artifacts**, verified against `origin/back/access-auth-spine` at `d83eb17`.
- **496** and **503** are retained only as historical intermediate totals; neither is the current intended PR #3 total.
- The **current intended PR #3 total is 516 additions plus deletions: 466 implementation/test + 50 SDD artifacts**. Preserve and exclude unrelated unstaged `main.py`, root `pyproject.toml`, and `uv.lock`; manual delivery MUST selectively stage only the intended PR #3 paths.
