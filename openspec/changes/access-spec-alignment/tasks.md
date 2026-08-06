# Tasks: Access Spec Alignment

## Review Workload Forecast

| Field | Value |
| ----- | ----- |
| Estimated changed lines | 900–1200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 → PR2 → PR3 → PR4 → PR5 |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
| ---- | ---- | --------- | -------------------- | --------------- | ----------------- |
| 1 | Namespace split: dto→commands+results, router→two routers, delete shims | PR1 `back/fix-59-01-namespace-split` | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A — mechanical refactor, no new behavior | Revert branch; no downstream PR depends on it yet |
| 2 | Domain hardening + /access/me contract fix | PR2 `back/fix-59-02-domain-and-me` | `uv run --locked --package backend python -m unittest backend.tests.domain.test_roles -v` | N/A — domain unit test only | Revert branch; PR3 depends on this |
| 3 | Role & scope lifecycle use cases + endpoints | PR3 `back/fix-59-03-role-scope-lifecycle` | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A — application unit tests with fakes | Revert branch; PR5 depends on this |
| 4 | User detail + status endpoints | PR4 `back/fix-59-04-user-detail-status` | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A — application unit tests with fakes | Revert branch; PR5 depends on this |
| 5 | Pagination envelope + audit filters | PR5 `back/fix-59-05-pagination-audit` | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A — unit tests with in-memory repos | Revert branch; terminal slice |

## Phase 1: Namespace Split (PR1 — `back/fix-59-01-namespace-split`)

Base: `back/fix-59-access-spec-alignment` (tracker)

- [x] 1.1 Create `access/application/commands.py` — move all `*Command` + `PermissionInput` from `dto.py`
- [x] 1.2 Create `access/application/results.py` — move all `*Result` dataclasses from `dto.py`
- [x] 1.3 Repoint all application use-case imports from `dto` → `commands`/`results` (12 files under `access/application/`)
- [x] 1.4 Repoint `access/ports/repositories.py` importers (12 use-case files) → specific port modules (`access.ports.users`, `.roles`, `.scopes`, `.audit`)
- [x] 1.5 Repoint `access/adapters/persistence/repositories.py` importers (4 bootstrap files) → specific adapter modules
- [x] 1.6 Delete `access/application/dto.py`, `access/ports/repositories.py`, `access/adapters/persistence/repositories.py`
- [x] 1.7 Create `access/adapters/http/self_access_router.py` — extract `create_self_access_router` from `router.py`
- [x] 1.8 Create `access/adapters/http/admin_router.py` — extract `create_admin_router` + `_resolve_user_id` from `router.py`
- [x] 1.9 Delete `access/adapters/http/router.py`; update `bootstrap/api_router.py` imports to new router files
- [x] 1.10 Run full test suite — verify green; fix any remaining import references in tests

## Phase 2: Domain Hardening + /access/me (PR2 — `back/fix-59-02-domain-and-me`)

Base: PR1 branch

- [x] 2.1 Add `PRIVILEGED_ACTIONS` set and `Role.set_permissions(permissions)` to `access/domain/roles.py`; raise `PrivilegedActionRequiresSystemAdministrator` for non-sys-admin roles
- [x] 2.2 Write unit test: `Role.set_permissions` rejects privileged action on ordinary role, accepts on sys-admin
- [x] 2.3 Add `RoleSummaryResult` to `access/application/results.py`; add `roles: list[RoleSummaryResult]` to `CurrentAccessResult`
- [x] 2.4 Update `get_current_access.py` to populate `roles[]` from user assignments
- [x] 2.5 Rename `AuthorizationResponse.global_access` → `is_global` (spec uses `global`; Python reserved word → `is_global` field name)
- [x] 2.6 Add `RoleSummaryResponse` to `models.py`; add `roles[]` to `CurrentAccessResponse`
- [x] 2.7 Update `self_access_router.py` to map `roles[]` into the response
- [x] 2.8 Write/update tests: `/access/me` returns `roles[]` and uses `is_global` field name

## Phase 3: Role & Scope Lifecycle (PR3 — `back/fix-59-03-role-scope-lifecycle`)

Base: PR2 branch

- [x] 3.1 Create `access/application/update_role.py` — `UpdateRole` use case (calls `Role.set_permissions`, audit, version check)
- [x] 3.2 Create `access/application/activate_role.py` — `ActivateRole` use case
- [x] 3.3 Create `access/application/deactivate_role.py` — `DeactivateRole` use case
- [x] 3.4 Create `access/application/activate_scope.py` — `ActivateScope` use case
- [x] 3.5 Create `access/application/deactivate_scope.py` — `DeactivateScope` use case
- [x] 3.6 Extend `AdminUseCases` container + `access_admin_dependency.py` — wire all 5 new use cases
- [x] 3.7 Add `GET /roles/{id}`, `PUT /roles/{id}`, `PATCH /roles/{id}/status`, `PATCH /scopes/{id}/status` to `admin_router.py`
- [x] 3.8 Write unit tests: update role (version conflict, privileged reject, happy path); activate/deactivate role/scope (not found, version conflict, audit written)

## Phase 4: User Detail + Status (PR4 — `back/fix-59-04-user-detail-status`)

Base: PR1 branch

- [x] 4.1 Create `access/application/get_access_user.py` — `GetAccessUser` use case (returns user + assignments + permissions)
- [x] 4.2 Extend `AdminUseCases` + `access_admin_dependency.py` — wire `GetAccessUser` + `ActivateAccessUser` + `DeactivateAccessUser`
- [x] 4.3 Add `GET /users/{id}`, `PATCH /users/{id}/status` to `admin_router.py`
- [x] 4.4 Write unit tests: get user (not found, happy path with assignments); activate/deactivate user status (version conflict, audit)

## Phase 5: Pagination + Audit Filters (PR5 — `back/fix-59-05-pagination-audit`)

Base: PR4 branch (after PR3 + PR4 merge into tracker)

- [x] 5.1 Create `PaginatedResponse[T]` generic model in `access/adapters/http/models.py`
- [x] 5.2 Add `limit`/`offset` params + `count()` to port protocols: `users.py`, `roles.py`, `scopes.py`, `audit.py`
- [x] 5.3 Implement `limit`/`offset`/`count` in persistence adapters: `user_repository.py`, `role_repository.py`, `scope_repository.py`, `audit_repository.py`
- [x] 5.4 Add `page`/`page_size` query params to all list endpoints in `admin_router.py`; return `PaginatedResponse`
- [x] 5.5 Add audit filter query params (`subject_type`, `change_kind`, `date_from`, `date_to`) to `GET /audits`
- [x] 5.6 Update list use cases to accept and forward pagination params
- [x] 5.7 Write unit tests: pagination total-preserving (total==full count, len(items)<=page_size); audit filters
