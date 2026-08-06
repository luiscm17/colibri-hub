# Design: Access Module Hexagonal/DDD Audit

## Technical Approach

Inside-out refactor delivered as 4 chained PRs (each < 200 lines): enrich the domain (behavior + invariants), tighten ports and relocate the shared identity type, fix adapters/type-safety, then type the composition root. No behavior changes — use cases keep orchestration and delegate mutation to new entity methods. All 158 unit + 31 integration tests stay green after each PR.

## Architecture Decisions

| Topic | Options | Decision & Rationale |
|-------|---------|----------------------|
| Home for `AuthenticatedIdentity` | (a) keep in `warehouse.bales.ports`; (b) `infra`; (c) new `shared` kernel | **(c) `backend/src/shared/identity.py`.** Provider-neutral identity value object used by both Access and Warehouse. `infra` is technical-only; keeping it in Warehouse forces Access→Warehouse imports. A shared *kernel* is a DDD pattern, not a business context (see Open Questions). |
| Assignment persistence | (a) keep `save_assignment`/`find_assignments_*` on `RoleRepository`; (b) split | **(b) dedicated `AssignmentRepository` port + `AssignmentRepositoryAdapter`.** Assignment is its own lifecycle aggregate; mixing it into `RoleRepository` violates single responsibility and bloats the role contract. |
| Domain richness | (a) keep anemic dataclasses; (b) behavior methods + guards | **(b).** Use cases currently read-decide-write (`user.is_active = False`). Move to `user.deactivate(now)`, `user.activate(now)`, `role.grant_permission(p)`, `assignment.revoke(by, reason, at)` enforcing invariants and version bumps. |
| pydantic-settings `type: ignore[call-arg]` | (a) keep ignores; (b) `@classmethod` factory | **(b) `ApplicationSettings.from_environment(env_file=...)`.** A typed factory calls `BaseSettings` with proper kwargs, isolating the `_env_file` construction so no suppression is needed. |
| Audit read type (`list_recent` returns `list`) | (a) keep untyped + adapter builds `AuditEntryResult` (application DTO); (b) typed domain read model | **(b) `AccessAuditEntry` read model in `access/domain`.** Port returns `list[AccessAuditEntry]`; the application maps it to the DTO. Removes persistence→application coupling and the untyped return. |
| Use-case provider (`Callable[..., dict]`) | (a) keep dict; (b) typed container | **(b) frozen `AdminUseCases` dataclass container.** Replaces stringly-typed dict lookups (`use_cases["create_role"]`) with typed attributes; router depends on the typed container. |

## Data Flow (dependency direction after relocation)

```
        shared/identity.py  (AuthenticatedIdentity, IdentityResolver)
              ▲                         ▲
              │                         │
   access/adapters/http         warehouse/bales/ports
   access/adapters/warehouse_authorization
              ▲
   bootstrap/http_application
```

No module in `access` imports from `warehouse` (or vice versa) after PR2.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/src/shared/__init__.py` | Create | Shared kernel package marker |
| `backend/src/shared/identity.py` | Create | `AuthenticatedIdentity`, `IdentityResolver` new home |
| `backend/src/access/domain/users.py` | Modify | `deactivate()`, `activate()`; tighten guaranteed types |
| `backend/src/access/domain/roles.py` | Modify | `Role.grant_permission()`; extract `Assignment` guards + `revoke()` |
| `backend/src/access/domain/scopes.py` | Modify | `Scope.activate()/deactivate()` behavior |
| `backend/src/access/domain/audit.py` | Create | `AccessAuditEntry` read model |
| `backend/src/access/ports/repositories.py` | Modify | Type `list_recent`; split out `AssignmentRepository` |
| `backend/src/access/ports/assignments.py` | Create | `AssignmentRepository` protocol |
| `backend/src/access/adapters/persistence/repositories.py` | Modify | New `AssignmentRepositoryAdapter`; map to `AccessAuditEntry`; drop app-DTO import |
| `backend/src/access/adapters/http/router.py` | Modify | Import identity from `shared`; use typed `AdminUseCases` |
| `backend/src/access/application/*` | Modify | Call entity behavior; consume `AssignmentRepository`; map audit read model→DTO |
| `backend/src/warehouse/bales/ports/authorization.py` | Modify | Re-export identity from `shared`; remove local definition |
| `backend/src/warehouse/bales/adapters/persistence/bale_repository.py` | Modify | Guard `delivery_date`; type update result — remove 2 ignores |
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modify | Type provider row shape — remove 1 ignore |
| `backend/src/infra/configuration/application_settings.py` | Modify | Factory classmethod — remove 2 ignores |
| `backend/src/bootstrap/access_admin_dependency.py` | Modify | Return typed `AdminUseCases` container |
| `backend/src/bootstrap/http_application.py` | Modify | Import identity from `shared` |

## Interfaces / Contracts

```python
# access/ports/assignments.py
class AssignmentRepository(Protocol):
    def find_for_user(self, user_id: str) -> list[Assignment]: ...
    def find_for_role(self, role_id: str) -> list[Assignment]: ...
    def save(self, assignment: Assignment) -> None: ...

# access/domain/users.py — behavior + invariant
def deactivate(self, *, at: datetime) -> None:
    if not self.is_active:
        return
    self.is_active = False
    self.version += 1
    self.updated_at = at

# infra/configuration/application_settings.py — no suppression
@classmethod
def from_environment(cls, env_file: Path | None = None) -> "ApplicationSettings":
    ...  # constructs nested settings, passes _env_file internally
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Entity behavior + invariant guards (deactivate idempotent, revoke sets fields, grant_permission rejects duplicates) | stdlib `unittest`, no I/O |
| Unit | `AssignmentRepositoryAdapter`, typed audit mapping | SQLite-backed |
| Integration | Role/assignment/audit flows unchanged; settings factory | Postgres `TEST_DATABASE_URL` |
| Type | Zero Pyright errors, zero `# type: ignore` in `backend/src/` | static check |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No data migration. Each PR is independently revertable; the chain keeps earlier slices stable. Test factories updated in the same PR that changes an entity API.

## Open Questions

- [ ] AGENTS.md states "`shared` is not a business context" and lists only `warehouse/access/auth/infra/bootstrap` as top-level packages. Confirm a `shared` kernel package is acceptable, or relocate `AuthenticatedIdentity` under `infra` instead.
