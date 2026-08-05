# Proposal: auth-hexagonal-audit

> Architectural audit of `backend/src/auth/` against hexagonal/DDD principles — fix all identified violations to align with the proven `access` module pattern.

## Intent

Bring the **auth** bounded context into full compliance with the project's hexagonal architecture principles. The exploration phase identified 3 critical violations (dependency direction, composition root type safety, shared infra duplication) and 1 medium violation (namespace alignment). All fixes are mechanical refactoring with zero behavior change.

## Business Justification

The auth PRD (rule 10) establishes that "Authentication owns the login account; Access Control owns the profile and roles." The current code violates this boundary by importing types from `warehouse.bales.ports.authorization` — creating a hidden dependency from auth to warehouse. This makes auth non-portable and couples it to warehouse's internal structure.

Additionally, the stringly-typed composition root (`dict` returns, string-key lookups) undermines the zero-suppression type safety policy established across the codebase, making refactoring error-prone and breaking IDE discoverability.

## Scope

### Critical Fixes (must-do)

| # | Violation | Fix | Files |
|---|-----------|-----|-------|
| 1 | Cross-context dependency: auth imports from `warehouse.bales.ports.authorization` | Redirect imports to `shared.identity` (already exists and is correct) | `jwt_validator.py`, `request_pipeline.py`, `router.py` |
| 2 | Composition root type safety: `_compose_auth` returns `dict`, router uses `Callable[..., dict]` | Create typed `AuthUseCases` dataclass container (mirrors `access.application.containers.AdminUseCases`) | New `auth/application/containers.py` + `router.py` + `http_application.py` |
| 3 | Shared infra duplication: `_FakeClock`/`_FakeIdentity` duplicated with `_SimpleClock`/`_SimpleIdentity` | Extract `infra/clock.py` (`SystemClock`) and `infra/identity.py` (`SystemIdentity`) — single shared adapters | New `infra/clock.py`, `infra/identity.py` + `http_application.py` + `access_admin_dependency.py` |

### Medium Fix (in-scope)

| # | Violation | Fix | Files |
|---|-----------|-----|-------|
| 4 | Router exceeds 200 LOC — mixes admin and user endpoints | Split into `user_router.py` (login, password change, current-auth) and `admin_router.py` (accounts, audits, enable/disable) | New files replacing `router.py` |

### Low Fixes (in-scope, minimal effort)

| # | Violation | Fix | Files |
|---|-----------|-----|-------|
| 5 | Orphan `auth/ports/transaction.py` | Delete — defined but never imported, access module has its own working pattern | 1 deleted |
| 6 | Audit endpoint returns bare `list[dict]` | Add typed response model in `auth/adapters/http/models.py` | 1 modified |

### Composition Root Extraction

Extract `_compose_auth` (~180 LOC) from `http_application.py` into `bootstrap/auth_dependency.py` following the established `access_admin_dependency.py` pattern. The factory returns a typed `AuthUseCases` container via FastAPI dependency injection.

## Approach

1. **Bottom-up, layer-by-layer** — fix imports first (no ripple), then types, then structure.
2. **Reference pattern**: `access` module is the template. Copy its container dataclass pattern, its factory file structure, and its router organization.
3. **Zero behavior change** — no new features, no API signature changes, no business logic modifications.
4. **Session-sharing preserved** — `auth_dependency.py` continues to wire access provisioning adapters within the same SQLAlchemy session scope (PRD rule 9: "Provisioning is one administrative flow").

## Execution Order

```text
Phase 1: Import fixes (no dependencies)
  - Redirect 3 files from warehouse.bales.ports.authorization → shared.identity
  - Delete orphan auth/ports/transaction.py

Phase 2: Shared infrastructure
  - Create infra/clock.py (SystemClock) and infra/identity.py (SystemIdentity)
  - Update http_application.py and access_admin_dependency.py to use shared adapters

Phase 3: Typed container + factory extraction
  - Create auth/application/containers.py (AuthUseCases dataclass)
  - Extract bootstrap/auth_dependency.py from _compose_auth
  - Update http_application.py to use the new factory

Phase 4: Router split + response typing
  - Split router.py → user_router.py + admin_router.py
  - Add typed audit response model
  - Update bootstrap/api_router.py to include both sub-routers
```

## Affected Modules

| Module | Change Type |
|--------|-------------|
| `backend/src/auth/adapters/http/router.py` | Split → 2 files, fix imports |
| `backend/src/auth/adapters/identity_provider/jwt_validator.py` | Fix import |
| `backend/src/auth/adapters/identity_provider/request_pipeline.py` | Fix import |
| `backend/src/auth/ports/transaction.py` | Delete |
| `backend/src/auth/adapters/http/models.py` | Add audit response model |
| `backend/src/bootstrap/http_application.py` | Extract factory, use shared infra |
| `backend/src/bootstrap/access_admin_dependency.py` | Use shared infra |
| `backend/src/bootstrap/api_router.py` | Update router includes |
| New: `backend/src/auth/application/containers.py` | Typed `AuthUseCases` container |
| New: `backend/src/bootstrap/auth_dependency.py` | Extracted factory |
| New: `backend/src/auth/adapters/http/user_router.py` | User-facing endpoints |
| New: `backend/src/auth/adapters/http/admin_router.py` | Admin endpoints |
| New: `backend/src/infra/clock.py` | `SystemClock` adapter |
| New: `backend/src/infra/identity.py` | `SystemIdentity` adapter |

## Estimate

- **Net new/changed lines**: ~300 (within 400-line single-PR budget)
- **Files touched**: ~12 modified + 6 new - 2 deleted = ~16 total
- **Risk level**: Low — mechanical refactoring, proven reference pattern exists

## Rollback Plan

Every change is independently revertible:
1. Import redirects are a single `git revert` — `shared.identity` re-exports remain.
2. Shared infra extraction keeps both old and new working until old references are removed.
3. Factory extraction is one file move — revert restores inline `_compose_auth`.
4. Router split can be reverted by restoring the original `router.py`.

Full rollback: `git revert` the merge commit. No data migration, no schema change, no configuration change.

## Non-Goals

- No new features or API endpoints
- No business logic changes
- No auth domain model modifications (domain layer is already STRONG)
- No test framework changes
- No frontend changes
- No database schema changes
- No changes to the warehouse or access domain layers
- No `shared.identity` module modifications (it's already correct)

## Risks

| Risk | Mitigation |
|------|-----------|
| Router split may affect error handler registration | Auth error handlers register at app level, not per-router — verified safe |
| Tests using dict-key access to use cases | Update test factories to return typed container — search for string-key patterns |
| Session-sharing between auth and access factories | Preserve existing session-scope pattern in extracted factory |
| Renamed `_FakeClock`/`_FakeIdentity` may break test references | Grep all test files for these names before removing |

## Decisions Made

1. **Shared adapters live in `infra/`** — not in `shared/` (which is only for kernel types, not implementations).
2. **Names: `SystemClock` and `SystemIdentity`** — descriptive, match production reality (not "fake" or "simple").
3. **Router split follows PRD actor model** — "System User" endpoints in `user_router.py`, "System Administrator" endpoints in `admin_router.py`.
4. **`AuthUseCases` container in `auth/application/`** — mirrors access module's `containers.py` placement.
5. **Orphan `TransactionPort` deleted** — auth uses its own transaction handling through the session; the port was never imported.
6. **Factory file named `auth_dependency.py`** — consistent with `access_admin_dependency.py` naming convention.
