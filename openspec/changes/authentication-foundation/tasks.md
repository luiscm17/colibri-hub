# Tasks: Authentication Foundation

## Authoritative Inputs

- **PRD**: `docs/prd/auth.md` — normative business rules
- **Tech Spec**: `backend/docs/features/authentication.md` — complete backend design (hexagonal, Supabase Auth, API contract, data model)
- **Exploration**: `openspec/changes/authentication-foundation/exploration.md`
- **Base branch**: `back/authentication-foundation` at `553dea2` (from `origin/back/access-auth-spine`)

## Session Preferences

- **Delivery strategy**: `auto-chain`
- **Chain strategy**: `feature-branch-chain`
- **Artifact store**: `hybrid` (engram + openspec)
- **Strict TDD**: disabled
- **Installation rule**: User installs all packages. Agent provides CLI commands only.

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | PR 1: ~550; PR 2: ~650; PR 3: ~700; PR 4: ~450; total: ~2,350 |
| 400-line budget risk | High for PR 1/2/3; Low for PR 4 |
| 800-line budget risk | Low for every slice |
| Chained PRs recommended | Yes |
| Suggested split | Domain/ports/application → Persistence/migration → Supabase adapters/JWT/pipeline → HTTP/composition/bootstrap-command |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No (pre-approved by user)
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

## Suggested Work Units

| Unit | Start / finish and boundary | PR/base and dependency | Focused evidence | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Start on `back/auth-foundation-core`; finish auth domain, ports, application use cases, and unit proof without ORM/HTTP/Supabase. | PR #1 targets tracker `back/authentication-foundation`; no dependency. | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A: pure domain/application; deterministic doubles are the runtime seam. | Revert `backend/src/auth/{domain,application,ports}/` and unit tests only. |
| 2 | Start from merged PR #1 tracker state; finish SQLAlchemy records, migration, persistence adapters, and PostgreSQL proof. | `back/auth-foundation-persistence` targets tracker `back/authentication-foundation` after PR #1 merged. | Focused persistence tests, then guarded integration suite. | User runs `pnpm supabase db reset --local --no-seed`; then `TEST_DATABASE_URL=... uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v`. | Revert auth persistence, migration, integration tests; retain core. |
| 3 | Start from merged PR #1–2 tracker state; finish Supabase admin adapter, JWT validator, request pipeline, shared error extraction, settings. | `back/auth-foundation-provider` targets tracker `back/authentication-foundation` after PR #2 merged. | Unit + API tests with mock provider doubles. | N/A for integration; mock Supabase responses in unit tests. | Revert provider adapters, JWT validator, settings, shared error extraction; retain core + persistence. |
| 4 | Start from merged PR #1–3 tracker state; finish HTTP router, composition wiring, bootstrap command, full-stack verification. | `back/auth-foundation-http` targets tracker `back/authentication-foundation` after PR #3 merged. | Full unit + integration + TestClient suite. | Full stack with local Supabase. | Revert HTTP router, bootstrap command, composition changes; retain everything else. |

## Phase 1: Domain, Ports, and Application (PR #1)

### Prerequisites (user-executed)
```bash
uv add --package backend PyJWT cryptography
```
Edit `backend/pyproject.toml` → `[tool.setuptools.packages.find].include` → add `"auth*"`.

### Tasks

- [ ] 1.1 Create `backend/src/auth/domain/`: `account_status.py` (StrEnum: awaiting_password_change, active, disabled), `email.py` (NormalizedEmail VO with case-folding + validation), `account.py` (AuthenticationAccount entity with status transitions, version, immutability rules), `errors.py` (typed domain exceptions per tech spec §15).

- [ ] 1.2 Create `backend/src/auth/ports/`: protocol definitions for `AccountRepository`, `AuditRepository`, `IdentityProviderPort`, `AccessProvisioningPort`, `TransactionPort`, `ClockPort`, `IdentityPort` per tech spec §7.3. Keep Supabase-free — only typed abstractions.

- [ ] 1.3 Create `backend/src/auth/application/`: use cases `get_current_authentication.py`, `change_required_password.py`, `record_logout.py`, `provision_account.py`, `reset_password.py`, `disable_account.py`, `enable_account.py`, `list_accounts.py`, `get_account.py`, `list_audits.py`, `dto.py`. Each coordinates ports without framework imports. Safe ordering per tech spec §13.

- [ ] 1.4 Create `backend/tests/test_auth_domain.py` and `backend/tests/test_auth_application.py`: test account transitions, mandatory replacement rejects equal values, provisioning coordinates profile+roles, reset/disable/enable preserve safe denial, last-admin invariant via AccessProvisioningPort, secrets absent from exceptions/audits.

## Phase 2: Persistence and Migration (PR #2)

### Prerequisites (user-executed)
```bash
pnpm supabase migration new create_authentication_tables
```

### Tasks

- [ ] 2.1 Create `backend/src/auth/adapters/persistence/models.py`: SQLAlchemy mapped classes for `authentication_accounts` and `authentication_audits` with named constraints (`pk_`, `uq_`, `ck_`, `ix_`), RLS-ready.

- [ ] 2.2 Create `backend/src/auth/adapters/persistence/repositories.py`: implement `AccountRepository` and `AuditRepository` ports with SQLAlchemy session, optimistic concurrency on version column.

- [ ] 2.3 Write migration SQL in `supabase/migrations/<timestamp>_create_authentication_tables.sql`: tables, named constraints, unique indexes on `identity_subject` + `normalized_email`, check constraint on status enum, `version` default 1, append-only audit (no UPDATE/DELETE grants), RLS enabled, browser roles revoked, `service_role` and `postgres` retain access.

- [ ] 2.4 Register auth records in `backend/src/infra/persistence/record_registry.py` (add `register_auth_records()`).

- [ ] 2.5 Create `backend/integration_tests/test_auth_postgres.py`: email/subject uniqueness constraints, version conflict, status check constraint, audit immutability, RLS blocking browser roles.

## Phase 3: Supabase Provider Adapters and Request Pipeline (PR #3)

### Prerequisites (user-executed)
```bash
uv add --package backend supabase
pnpm supabase status  # verify running
```

### Tasks

- [ ] 3.1 Update `supabase/config.toml`: set `enable_signup = false`, uncomment `[auth.sessions]` and set `timebox = "8h"`, set `minimum_password_length = 8`.

- [ ] 3.2 Create `backend/src/auth/adapters/identity_provider/supabase_auth.py`: implement `IdentityProviderPort` using Supabase admin client (`SUPABASE_SERVICE_ROLE_KEY`). Methods: create_user, update_password, ban_user, unban_user, sign_out (session revocation), get_session_by_id.

- [ ] 3.3 Create `backend/src/auth/adapters/identity_provider/jwt_validator.py`: implement real `IdentityResolver` — validate Bearer token (RS256, issuer, audience, expiration, sub, session_id claim), JWKS caching with bounded TTL and refresh on unknown kid. Return `AuthenticatedIdentity(subject, session_id)`.

- [ ] 3.4 Create request pipeline logic: after JWT validation, resolve account from `identity_subject`, reject disabled, restrict `awaiting_password_change` to permitted endpoints only (GET /auth/me, POST /auth/password-change, DELETE /auth/session), check session age against provider's `auth.sessions` via service-role query, deny at 8h boundary.

- [ ] 3.5 Extract shared error helper: move `error_json_response`, `ErrorResponse`, `ErrorDetailResponse`, `FieldErrorResponse` from `warehouse/bales/adapters/http/` to `backend/src/infra/http/error_envelope.py`. Update imports in warehouse and bootstrap modules.

- [ ] 3.6 Extend `backend/src/infra/configuration.py` `ApplicationSettings`: add `supabase_url`, `supabase_service_role_key`, `supabase_jwt_secret` (or JWKS URL), `supabase_jwt_issuer`, `supabase_jwt_audience`. Fail startup when absent.

- [ ] 3.7 Create `backend/tests/test_auth_jwt_validator.py` and `backend/tests/test_auth_pipeline.py`: test missing/malformed/expired/wrong-issuer/wrong-audience tokens, disabled account rejection, awaiting_password_change restriction, session-age rejection at 8h, provider unavailable mapping.

## Phase 4: HTTP, Composition, and Bootstrap Command (PR #4)

### Tasks

- [ ] 4.1 Create `backend/src/auth/adapters/http/router.py`: user endpoints (GET `/auth/me`, POST `/auth/password-change`, DELETE `/auth/session`) + admin endpoints (GET/POST `/auth/accounts`, GET `/auth/accounts/{id}`, POST `/{id}/password-reset`, POST `/{id}/disable`, POST `/{id}/enable`, GET `/auth/audits`). Request/response models in `models.py`. Error handlers in `error_handlers.py`.

- [ ] 4.2 Wire auth router into `backend/src/bootstrap/api_router.py` (`create_api_router` includes `create_auth_router`). Wire real `identity_resolver` (JWT validator) into `create_app` when Supabase config is present.

- [ ] 4.3 Create initial System Administrator bootstrap command: `backend/src/auth/adapters/bootstrap_command.py` — receives email, provisional_password, user_code, display_name from env/CLI input, creates Supabase identity + Auth account + Access bootstrap, idempotent. NOT a public route.

- [ ] 4.4 Create `backend/tests/api/test_auth_endpoints.py`: TestClient tests for all endpoints — provisioning flow, password change, logout, admin operations, error codes, CORS, credential redaction.

- [ ] 4.5 Verify full stack: unit suite (all), integration suite (auth + access + warehouse), TestClient (auth + warehouse + access endpoints coexist). Document deployment constraint.

## Phase 5: Chain Verification

- [ ] 5.1 Verify each child diff against its immediate parent, record focused/runtime evidence, preserve the user-only installation rule, and do not create branches, commits, PRs, or invoke review lifecycle commands.

## Completion Metadata

- Total estimated: ~2,350 changed lines across 4 PRs
- Each PR targets tracker `back/authentication-foundation`
- All PRs remain within 800-line review budget
- No PR targets `main` directly
- Installation commands provided to user; agent never executes `uv add` or `pnpm install`
