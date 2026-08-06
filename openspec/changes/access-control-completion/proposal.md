# Proposal: Access Control Backend Completion

## Intent

Complete the backend implementation per `backend/docs/features/access-control.md`. The core administration layer shipped in PR #47–#50 deliberately deferred presets and impact previews ("separate PR" that was never created). Additionally, 5 critical bugs/divergences were identified post-audit. This change ships all remaining work as three chained PRs: security fixes first, then additive features.

## Scope

### In Scope

- **PR1 — Critical fixes (C1–C5)**:
  - C1: Auth admin route authorization guard (`manage_access` enforcement)
  - C2: Functional bootstrap CLI + `system_administrator` role seed migration
  - C3: Last-admin invariant locking fix (TOCTOU) + enforcement across role/assignment mutations
  - C4: Provisioning `display_name` bug fix + cross-context rollback test
  - C5: Login/security audit event skeleton (`login_succeeded`, `login_failed`)
- **PR2 — Presets + version propagation (D1 + D3)**:
  - D1: Role presets domain (copy semantics), use cases, tables (`access_role_presets`, `access_role_preset_permissions`), 6 endpoints (CRUD + status + create-role-from-preset)
  - D3: `authorization_version` increments on role/scope/assignment mutations for affected users
- **PR3 — Impact previews (D2)**:
  - `POST /roles/{role_id}/preview` — affected users + permission deltas
  - `POST /users/{user_id}/roles/preview` — assignment replacement preview

### Out of Scope

- Frontend access-control UI (under review/refactor; align after backend contract stabilizes)
- Warehouse endpoint authorization guards (separate concern)
- Auth provider session revocation rework (tracked in issue #61)
- Pagination enhancements on existing list endpoints
- Enable-revalidation logic (auth BR 31 — adjacent, not blocking)

## Capabilities

### New Capabilities

- `access-role-presets`: Preset CRUD, lifecycle (active/archived), copy-on-create semantics, 6 HTTP endpoints
- `access-impact-previews`: Preview role and assignment mutations before commit — affected-user lists and permission deltas

### Modified Capabilities

- `access-control-administration`: Authorization-version propagation on indirect mutations; last-admin invariant hardened with row-level locking; login audit events written
- `authentication-foundation`: Auth admin routes protected by `manage_access` authorization; bootstrap command executable via CLI with seed migration

## Approach

Three chained PRs targeting a feature branch `back/access-control-completion`:

1. **PR1 (~450 LOC)**: Security-first. Add `_require_admin` to auth admin router; create bootstrap CLI entrypoint + seed migration; fix `for_update=True` in provisioning adapter; fix `display_name` bug; wire audit events as skeleton.
2. **PR2 (~600 LOC)**: New tables + domain + use cases + endpoints for presets; add `_propagate_authorization_version` helper to role/scope/assignment mutations.
3. **PR3 (~250 LOC)**: Preview use cases consuming the version-propagation and preset infrastructure; 2 new endpoints.

Architecture: hexagonal, package-by-capability, individual use-case classes, repository-per-aggregate — consistent with existing patterns.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/src/auth/adapters/http/admin_router.py` | Modified | Add authorization dependency (C1) |
| `backend/src/auth/adapters/bootstrap_command.py` | Modified | Add `main()` CLI entrypoint (C2) |
| `supabase/migrations/` | New | Seed `system_administrator` role (C2); preset tables (D1) |
| `backend/src/access/adapters/access_provisioning.py` | Modified | Locking fix (C3), display_name fix (C4) |
| `backend/src/access/domain/` | New+Modified | Preset entity, copy-semantics value objects (D1) |
| `backend/src/access/application/` | New+Modified | Preset use cases (D1), preview use cases (D2), version propagation (D3) |
| `backend/src/access/ports.py` | Modified | Preset repository port, preview query port |
| `backend/src/access/adapters/http/admin_router.py` | Modified | 8 new endpoints (D1: 6, D2: 2) |
| `backend/src/access/adapters/persistence/` | New | Preset records + repository (D1) |
| `backend/src/auth/adapters/persistence/` | Modified | Login audit event writes (C5) |
| `backend/src/bootstrap/` | Modified | Wire bootstrap CLI, authorization dependency |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| C2 bootstrap chicken-and-egg (role must exist before provisioning) | High | Seed role in same migration as bootstrap CLI; bootstrap skips provisioning for initial user |
| C3 locking scope crosses auth→access boundary | Medium | Verify shared SQLAlchemy session; test concurrent last-admin removal on real PostgreSQL |
| PR2 size approaches 800-line budget | Medium | Strict scope; move integration tests to PR3 if needed |
| C5 login audit incomplete without provider webhook | Low | Ship skeleton (event types + write path); production wiring deferred until login adapter is finalized |
| D2 preview correctness depends on D3 version semantics | Low | PR ordering enforces dependency; D2 cannot merge before D3 |

## Rollback Plan

Each PR is independently revertable on the feature branch. If reverting after merge to main:
- PR3: Revert commit — no schema changes, just code removal.
- PR2: Revert commit + drop preset tables migration (no production data yet).
- PR1: Revert commit + revert seed migration. Auth admin routes return to unguarded (known pre-existing state).

## Dependencies

- Local Supabase for integration tests
- `backend/docs/features/access-control.md` §5.1–§18 as implementation authority
- PR ordering: PR1 → PR2 → PR3 (each depends on predecessor)

## Success Criteria

- [ ] Auth admin endpoints return 403 for non-administrators
- [ ] `uv run --package backend python -m auth.adapters.bootstrap_command` creates initial System Administrator
- [ ] Concurrent last-admin removal is rejected under PostgreSQL row locking
- [ ] Provisioning uses correct `display_name` and proves cross-context rollback
- [ ] Login audit events are persisted on authentication success/failure
- [ ] Preset CRUD endpoints operational with copy-on-create semantics
- [ ] `authorization_version` increments on all indirect mutations (role/scope/assignment changes)
- [ ] Preview endpoints return affected users + permission deltas
- [ ] All unit + integration tests pass
