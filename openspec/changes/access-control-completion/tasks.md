# Tasks: Access Control Backend Completion

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1300 (450 + 600 + 250) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 (C1–C5) → PR2 (D1+D3) → PR3 (D2) |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Critical fixes C1–C5 | PR1 → `back/access-control-completion` | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` + integration suite | `pnpm supabase start` then `pnpm supabase db reset --local --no-seed` | Revert commit + revert seed migration |
| 2 | Presets + version propagation D1+D3 | PR2 → PR1 branch | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` + integration suite | Same local DB harness | Revert commit + drop preset tables migration |
| 3 | Impact previews D2 | PR3 → PR2 branch | Unit tests only (read-only, no DB mutation) | N/A — pure computation, no infra needed | Revert commit (no schema changes) |

## Phase 1: Critical Fixes — Infrastructure (PR1)

- [x] 1.1 Create `supabase/migrations/{ts}_seed_system_administrator_role.sql` — insert `system_administrator` role row (`is_system_administrator=true`) and ensure `access_control` scope exists
- [x] 1.2 Modify `backend/src/auth/adapters/http/admin_router.py` — add `authorize_action_provider` parameter to `create_auth_admin_router`; create `_require_admin` FastAPI dependency calling `AuthorizeAction.execute(action="manage_access", scope_code="access_control")`
- [x] 1.3 Modify `backend/src/bootstrap/api_router.py` — pass `authorize_action_provider` when constructing the auth admin router

## Phase 2: Critical Fixes — Core Implementation (PR1)

- [x] 2.1 Modify `backend/src/auth/adapters/bootstrap_command.py` — add `main()` CLI entrypoint reading env vars, composing dependencies, calling `BootstrapInitialAdministrator.execute`; wire as `python -m auth.adapters.bootstrap_command`
- [x] 2.2 Modify `backend/src/access/adapters/access_provisioning.py` — set `for_update=True` in `would_remove_last_administrator` call (C3); pass correct `display_name` from command (C4)
- [x] 2.3 Modify `backend/src/access/application/deactivate_access_user.py` — enforce last-admin invariant with locking before deactivation
- [x] 2.4 Modify `backend/src/auth/ports/access_provisioning.py` — add `display_name` parameter to port signature (C4)
- [x] 2.5 Modify `backend/src/auth/adapters/persistence/audit_repository.py` — implement `login_succeeded`/`login_failed` event write path (C5 skeleton)

## Phase 3: Critical Fixes — Testing (PR1)

- [x] 3.1 Unit test: auth admin returns 403 for non-admin user (spec: C1 unauthorized scenario)
- [x] 3.2 Unit test: bootstrap creates initial administrator; idempotent re-run succeeds (spec: C2 scenarios)
- [x] 3.3 Integration test: concurrent last-admin removal rejected under row lock (spec: C3 concurrent scenario)
- [x] 3.4 Unit test: provisioning uses correct `display_name` (spec: C4 scenario)
- [x] 3.5 Integration test: cross-context rollback on provisioning failure (spec: C4 rollback scenario)
- [x] 3.6 Unit test: login audit events persisted with correct `event_type` (spec: C5 scenarios)

## Phase 4: Presets — Infrastructure (PR2)

- [x] 4.1 Create `supabase/migrations/{ts}_create_role_presets.sql` — `access_role_presets` and `access_role_preset_permissions` tables with unique constraints
- [x] 4.2 Create `backend/src/access/domain/presets.py` — `RolePreset` aggregate entity with embedded `RolePresetPermission` value objects
- [x] 4.3 Create `backend/src/access/ports/presets.py` — `RolePresetRepository` protocol (find_by_id, find_by_code, list_all, count, save)
- [x] 4.4 Create `backend/src/access/adapters/persistence/preset_repository.py` + modify `records.py` — SQLAlchemy records and repository implementation

## Phase 5: Presets + Version Propagation — Core (PR2)

- [x] 5.1 Create `backend/src/access/application/create_role_preset.py` — validate no privileged actions, unique code, save
- [x] 5.2 Create `backend/src/access/application/update_role_preset.py` — full permission replace with optimistic concurrency
- [x] 5.3 Create `backend/src/access/application/list_role_presets.py` and `get_role_preset.py` — read use cases
- [x] 5.4 Create `backend/src/access/application/change_role_preset_status.py` — activate/deactivate
- [x] 5.5 Create `backend/src/access/application/create_role_from_preset.py` — copy-on-create snapshot semantics
- [x] 5.6 Modify `backend/src/access/ports/users.py` — add `bump_authorization_version_for_role` method (D3)
- [x] 5.7 Modify `backend/src/access/application/update_role.py` + role/scope/assignment use cases — add `_propagate_authorization_version` helper calls

## Phase 6: Presets — Wiring + Testing (PR2)

- [x] 6.1 Modify `backend/src/access/adapters/http/admin_router.py` + `models.py` — 6 preset endpoints (list, create, get, update, status, create-role-from-preset)
- [x] 6.2 Modify `backend/src/access/application/containers.py` + `backend/src/bootstrap/access_admin_dependency.py` — wire preset use cases
- [x] 6.3 Unit test: preset CRUD lifecycle, reject privileged actions, reject duplicate code (spec: preset lifecycle scenarios)
- [x] 6.4 Unit test: copy-on-create produces independent role; preset change does not propagate (spec: copy semantics scenarios)
- [x] 6.5 Integration test: preset unique constraints; inactive scope rejection (spec: persistence scenarios)
- [x] 6.6 Unit test: `_propagate_authorization_version` bumps all affected users on role/scope/assignment mutations (spec: D3 scenarios)

## Phase 7: Impact Previews (PR3)

- [x] 7.1 Create `backend/src/access/ports/previews.py` — `RolePreviewQuery` protocol with `preview_role_change` and `preview_user_role_replacement`
- [x] 7.2 Create `backend/src/access/application/preview_role_change.py` — read-only delta computation, no locks/audit/version increment
- [x] 7.3 Create `backend/src/access/application/preview_user_role_replacement.py` — replacement preview with last-admin guard
- [x] 7.4 Modify `backend/src/access/adapters/http/admin_router.py` + `models.py` — 2 preview endpoints
- [x] 7.5 Modify `backend/src/access/application/containers.py` + `backend/src/bootstrap/access_admin_dependency.py` — wire preview use cases
- [x] 7.6 Unit test: preview returns correct affected users + permission delta; multi-role overlap handled (spec: D2 scenarios)
- [x] 7.7 Unit test: preview does not mutate state; stale version on confirmation returns 409 (spec: read-only + stale scenarios)
