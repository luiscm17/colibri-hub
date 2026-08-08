# Design: Access Control Backend Completion

## Technical Approach

Three chained PRs on `back/access-control-completion`. PR1 fixes security/correctness gaps (C1–C5) in place, reusing existing patterns. PR2 adds the presets aggregate (tables + domain + use cases + endpoints) and `authorization_version` propagation. PR3 adds read-only preview use cases built on PR2 infrastructure. All work stays hexagonal, package-by-capability, one-class-per-use-case, repository-per-aggregate. Authorization is by the `is_system_administrator` flag (`domain/authorization.py` step 3), not permission rows — this is the pivot for C1/C2.

## Architecture Decisions

### Decision: Auth admin authorization guard (C1)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| New auth-local guard duplicating logic | Divergence risk, re-implements policy | Rejected |
| Reuse Access `AuthorizeAction` via injected `authorize_action_provider` | Auth already composes Access adapters on the shared session (`auth_dependency.py`) | **Chosen** |

Thread `authorize_action_provider` into `create_auth_admin_router`; add a `_require_admin` dependency mirroring the access router that calls `authorize.execute(action="manage_access", scope_code="access_control")`.

### Decision: Bootstrap mechanism (C2)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Seed admin user + role in SQL | Cannot create provider identity; leaks credential | Rejected |
| Seed `system_administrator` role row only; `python -m` CLI creates the user | Role row satisfies flag-based auth (no permission rows, no FK cycle) | **Chosen** |

Seed migration inserts the role with `is_system_administrator=true`. CLI `main()` reads env/args, builds the composition, calls `BootstrapInitialAdministrator.execute`. Self-actor resolves because the user is saved before `_resolve_actor`.

### Decision: Last-admin invariant (C3)

Flip the adapter's `would_remove_last_administrator` to `for_update=True` (locking already implemented in the repo method and used by `ReplaceUserRoles`). Enforce the invariant on `DeactivateAccessUser` and role deactivation/reassignment paths, not only auth disable.

### Decision: Preset aggregate + copy-on-create (D1)

Presets are an independent aggregate (`RolePreset` + embedded `RolePresetPermission`), mirroring `Role`. `CreateRoleFromPreset` **snapshots** preset permissions into a new `Role` — no live link, so later preset edits do not mutate derived roles.

### Decision: Version propagation (D3)

Add a `_propagate_authorization_version` helper and a repository method that bumps `authorization_version` for all users holding an affected role (or scope). Invoked from role update/status, scope status, and assignment mutations. `ReplaceUserRoles` already bumps the single subject.

### Decision: Previews (D2)

Read-only use cases + a preview query port that computes affected users and permission deltas by diffing current vs. proposed effective permissions using existing `domain/authorization.py` functions. No writes, no transaction.

## Data Flow

Bootstrap:

    CLI main() ──→ BootstrapInitialAdministrator ──→ provider.create_user
         │                    │
         │                    └─→ accounts.save ─→ access.provision_profile ─→ CreateAccessUser
         │                                                    │
         └──────────── seed: system_administrator role ───────┘

Preset copy-on-create:

    POST /role-presets/{id}/create-role ─→ CreateRoleFromPreset
         └─→ preset_repo.find ─→ snapshot perms ─→ Role(save) ─→ audit

Preview:

    POST /roles/{id}/preview ─→ PreviewRoleChange ─→ effective_permissions(current)
         └─→ effective_permissions(proposed) ─→ delta + affected users (read-only)

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/src/auth/adapters/http/admin_router.py` | Modify | Add `_require_admin`, accept `authorize_action_provider` (C1) |
| `backend/src/bootstrap/api_router.py` | Modify | Pass `authorize_action_provider` to auth admin router (C1) |
| `backend/src/auth/adapters/bootstrap_command.py` | Modify | Add `main()` CLI entrypoint (C2) |
| `backend/src/auth/ports/access_provisioning.py` | Modify | Add `display_name` param (C4) |
| `backend/src/access/adapters/access_provisioning.py` | Modify | `for_update=True` (C3); pass real `display_name` (C4) |
| `backend/src/access/application/deactivate_access_user.py` | Modify | Enforce last-admin invariant (C3) |
| `backend/src/auth/adapters/persistence/audit_repository.py` | Modify | `login_succeeded`/`login_failed` write path (C5) |
| `supabase/migrations/{ts}_seed_system_administrator_role.sql` | Create | Seed sysadmin role row (C2) |
| `supabase/migrations/{ts}_create_role_presets.sql` | Create | `access_role_presets`, `access_role_preset_permissions` (D1) |
| `backend/src/access/domain/presets.py` | Create | `RolePreset` aggregate (D1) |
| `backend/src/access/ports/presets.py` | Create | `RolePresetRepository` port (D1) |
| `backend/src/access/ports/previews.py` | Create | Preview query port (D2) |
| `backend/src/access/ports/users.py` | Modify | Add version-bump-by-role method (D3) |
| `backend/src/access/application/{create,update,list,get,change_status}_role_preset.py`, `create_role_from_preset.py` | Create | Preset use cases (D1) |
| `backend/src/access/application/{preview_role_change,preview_user_role_replacement}.py` | Create | Preview use cases (D2) |
| `backend/src/access/application/update_role.py` + role/scope/assignment use cases | Modify | `_propagate_authorization_version` (D3) |
| `backend/src/access/adapters/persistence/{records,preset_repository}.py` | Create/Modify | Preset records + repository (D1) |
| `backend/src/access/adapters/http/admin_router.py` + `models.py` | Modify | 8 endpoints (D1:6, D2:2) |
| `backend/src/access/application/containers.py`, `backend/src/bootstrap/access_admin_dependency.py` | Modify | Wire preset/preview use cases |

## Interfaces / Contracts

```python
class RolePresetRepository(Protocol):
    def find_by_id(self, preset_id: str) -> RolePreset | None: ...
    def find_by_code(self, code: str) -> RolePreset | None: ...
    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[RolePreset]: ...
    def count(self) -> int: ...
    def save(self, preset: RolePreset, *, created_by_user_id: str) -> None: ...

class RolePreviewQuery(Protocol):
    def preview_role_change(self, role_id: str, proposed: set[Permission]) -> PreviewResult: ...
    def preview_user_role_replacement(self, user_id: str, role_ids: list[str]) -> PreviewResult: ...

class AccessUserRepository(Protocol):  # added
    def bump_authorization_version_for_role(self, role_id: str, *, at: datetime) -> list[str]: ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Preset copy-on-create snapshot; version-bump fan-out; preview delta math; sysadmin flag auth | stdlib `unittest`, SQLite |
| Integration | C1 403 for non-admin; C3 concurrent last-admin removal under row lock; C4 cross-context rollback; preset unique constraints; C2 bootstrap idempotency | PostgreSQL `TEST_DATABASE_URL` (54322) |
| E2E | N/A — no browser surface (frontend out of scope) | — |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. The bootstrap CLI is a Python module entrypoint (`python -m auth.adapters.bootstrap_command`), not a shell script or subprocess integration.

## Migration / Rollout

Timestamped migrations via Supabase CLI, applied in order: (1) seed `system_administrator` role before any bootstrap run; (2) preset tables in PR2. No production data exists, so preset tables and role seed are additive. `pnpm supabase db reset --local --no-seed` re-applies all. Rollback = revert commit + drop preset tables / role seed row.

## Open Questions

- [ ] C5 scope: confirm login events are written from the token/login adapter as a skeleton only, deferring provider-webhook wiring (proposal marks production wiring deferred).
- [ ] Bootstrap CLI input source: env vars vs. argparse — resolve in tasks.
