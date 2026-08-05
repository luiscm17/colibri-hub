# Tasks: auth-hexagonal-audit

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~300 (additions + deletions) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Full auth hexagonal audit | Single PR | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A — zero behavior change, no new runtime paths | `git revert` merge commit |

## Phase 1: Import Fixes + Orphan Removal

- [x] 1.1 Update `auth/adapters/identity_provider/jwt_validator.py`: change `AuthenticatedIdentity` import from `warehouse.bales.ports.authorization` to `shared.identity`
- [x] 1.2 Update `auth/adapters/identity_provider/request_pipeline.py`: change `AuthenticatedIdentity` import from `warehouse.bales.ports.authorization` to `shared.identity`
- [x] 1.3 Delete `auth/ports/transaction.py` (orphan, never imported)
- [x] 1.4 Run unit tests to confirm no import breakage

## Phase 2: Shared Infrastructure

- [x] 2.1 Create `infra/clock.py` with `SystemClock` class exposing `now() -> datetime` (UTC), structurally satisfying `ClockPort`
- [x] 2.2 Create `infra/identity.py` with `SystemIdentity` class exposing `generate_id()` and `generate_operation_id()`, structurally satisfying `IdentityPort`
- [x] 2.3 Update `bootstrap/access_admin_dependency.py`: replace `_SimpleClock`/`_SimpleIdentity` with `SystemClock`/`SystemIdentity` imports from infra
- [x] 2.4 Update `bootstrap/http_application.py`: replace `_FakeClock`/`_FakeIdentity` with `SystemClock`/`SystemIdentity` imports from infra
- [x] 2.5 Run unit tests to confirm shared infra wiring is correct

## Phase 3: Typed Container + Factory Extraction

- [x] 3.1 Create `auth/application/containers.py` with frozen `AuthUseCases` dataclass (10 fields) and `AuthUseCaseProvider` type alias
- [x] 3.2 Create `bootstrap/auth_dependency.py` with `compose_auth(settings, session_provider) -> tuple[IdentityResolver, AuthUseCaseProvider]`; preserve session-sharing and access-provisioning wiring
- [x] 3.3 Update `bootstrap/http_application.py`: remove inline `_compose_auth` function, call `compose_auth` from `auth_dependency`
- [x] 3.4 Run unit + integration tests to confirm composition root works with typed container

## Phase 4: Router Split + Response Typing

- [x] 4.1 Add `AuditEntryResponse` model to `auth/adapters/http/models.py`
- [x] 4.2 Create `auth/adapters/http/user_router.py` (`create_auth_user_router`): GET /auth/me, POST /auth/password-change, DELETE /auth/session
- [x] 4.3 Create `auth/adapters/http/admin_router.py` (`create_auth_admin_router`): /auth/accounts CRUD, password-reset, disable, enable, GET /auth/audits
- [x] 4.4 Update `bootstrap/api_router.py`: import `AuthUseCaseProvider` from containers, include both auth sub-routers
- [x] 4.5 Delete `auth/adapters/http/router.py`
- [x] 4.6 Update existing test references: replace dict-key access patterns with typed `AuthUseCases` attribute access; replace `_FakeClock`/`_FakeIdentity`/`_SimpleClock`/`_SimpleIdentity` references
- [x] 4.7 Run full unit + integration test suites to confirm zero behavior change
