# Proposal: Access Spec Alignment

## Intent

Align the `access` bounded context implementation with the authoritative technical specification (`backend/docs/features/access-control.md`). The module's architecture is sound but ~60% of the admin API surface defined in §9–§10 is missing or incomplete. This PR closes the implementation gap for all non-preset use cases, fixes API contract divergences, adds pagination, and aligns namespace conventions with the established `auth` module pattern.

## Scope

### In Scope
- Implement missing CRUD use cases: update role, activate/deactivate role, activate/deactivate scope, get user detail, activate/deactivate user endpoints
- Fix `/access/me` response: add `roles` array, rename `global_access` → `global` per spec §10.1
- Add `GET /roles/{role_id}` detail endpoint
- Add pagination to all list endpoints (users, roles, scopes, audits)
- Split `dto.py` → `commands.py` + `results.py` (auth convention)
- Split `router.py` → `self_access_router.py` + `admin_router.py` (auth convention)
- Move privileged-action validation (`manage_access`, `edit_outside_window` rejection on ordinary roles) into domain `Role` entity
- Remove dead `repositories.py` if superseded by split repos
- Add missing admin endpoints: `PATCH /roles/{role_id}/status`, `PATCH /scopes/{scope_id}/status`, `PATCH /users/{user_id}/status`
- Audit query filtering (subject_type, change_kind, date range)

### Out of Scope
- Preset tables, domain, ports, adapters, use cases, and endpoints (separate PR)
- Preview endpoints: `POST /roles/{role_id}/preview`, `POST /users/{user_id}/roles/preview` (separate PR with presets)
- Frontend changes — spec is authoritative
- Other contexts (warehouse, yarn-spinning) — reference only for namespace homogeneity
- No new migrations — data model already covers all non-preset tables

## Capabilities

### New Capabilities
- None — this is a spec-alignment refactor within an existing capability

### Modified Capabilities
- `access-control`: completing the API surface and fixing contract divergences as defined by the existing spec

## Approach

1. **Namespace alignment first** (low-risk, high-value): split `dto.py` → `commands.py` + `results.py`, split `router.py` → two routers, clean dead code
2. **Domain hardening**: move privileged-action check into `Role.grant_permission()` / new `Role.set_permissions()` method
3. **Missing use cases**: implement `UpdateRole`, `ActivateRole`, `DeactivateRole`, `ActivateScope`, `DeactivateScope`, `GetAccessUser` use case classes
4. **Missing HTTP endpoints**: wire all status-change and detail endpoints using existing `StatusChangeRequest` model
5. **Response shape fix**: add `roles` to `/access/me`, rename field to `global`
6. **Pagination**: add `PaginatedResponse` wrapper, query params (`page`, `page_size`), apply to all list endpoints
7. **Audit filtering**: add query params for subject_type, change_kind, date range to `GET /audits`

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `access/application/dto.py` | Removed | Split into `commands.py` + `results.py` |
| `access/application/commands.py` | New | All command dataclasses |
| `access/application/results.py` | New | All result dataclasses |
| `access/application/update_role.py` | New | UpdateRole use case |
| `access/application/activate_role.py` | New | ActivateRole use case |
| `access/application/deactivate_role.py` | New | DeactivateRole use case |
| `access/application/activate_scope.py` | New | ActivateScope use case |
| `access/application/deactivate_scope.py` | New | DeactivateScope use case |
| `access/application/get_access_user.py` | New | GetAccessUser use case |
| `access/application/containers.py` | Modified | Register new use cases |
| `access/adapters/http/router.py` | Removed | Split into two routers |
| `access/adapters/http/self_access_router.py` | New | `/access/me` endpoint |
| `access/adapters/http/admin_router.py` | New | All admin endpoints |
| `access/adapters/http/models.py` | Modified | Add pagination, fix `CurrentAccessResponse` |
| `access/domain/roles.py` | Modified | Privileged-action domain validation |
| `access/ports/` | Modified | Add pagination params to list methods |
| `access/adapters/persistence/repositories.py` | Removed | Dead code cleanup |
| `bootstrap/` | Modified | Wire new routers and use cases |
| `backend/tests/` | Modified | Tests for new use cases and endpoints |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking existing tests importing `dto.py` or `router.py` | High | Comprehensive import grep + update all references in same commit |
| `/access/me` field rename breaks integration tests | Med | Update integration tests atomically; no frontend dependency (pre-launch) |
| Pagination changes break existing list endpoint callers | Low | Pre-launch, no real frontend; breaking changes accepted per user decision |
| Large PR exceeding 400-line budget | High | Likely 600–900 lines; chained PRs recommended (namespace first, then CRUD, then pagination) |

## Rollback Plan

Revert the PR branch. No database migration changes are included — the existing schema supports all proposed endpoints. All changes are application-layer only (Python source). Git revert produces a clean rollback with no data-model implications.

## Dependencies

- Existing migration `20260804200832` already provides the required schema
- Auth module namespace convention established and stable (reference implementation)
- No external service dependencies

## Success Criteria

- [ ] All spec §10 endpoints (non-preset, non-preview) return correct response shapes
- [ ] `/access/me` includes `roles` array and uses `global` field name
- [ ] All list endpoints accept pagination params and return paginated responses
- [ ] `access/application/` uses `commands.py` + `results.py` (no `dto.py`)
- [ ] HTTP layer uses split routers (self-access vs admin)
- [ ] Domain `Role` rejects privileged actions without application-layer involvement
- [ ] No dead code (`repositories.py` removed if superseded)
- [ ] All existing tests pass after refactor
- [ ] New unit tests cover added use cases
