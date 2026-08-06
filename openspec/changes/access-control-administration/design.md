# Design: Access Control Administration

## Overview

Restructure the Access spine into the full administrative layer defined by tech spec §6-18, mirroring the `auth/` module exactly: one class per use case, per-aggregate repository ports injected via `__init__`, a `TransactionPort` for atomic boundaries, and composition in `bootstrap/http_application.py`. Namespaces communicate technology (`adapters/persistence`, `adapters/http`); classes describe role (`AccessUserRepositoryAdapter`, not `SqlAlchemy…`). Clean-break migration drops the spine and recreates the spec schema. Presets and previews are deferred (proposal Out of Scope). Delivered as 4 chained PRs.

## Architecture

### Decisions

| Decision | Choice | Alternatives rejected | Rationale |
|----------|--------|-----------------------|-----------|
| Application shape | One file/class per use case (`create_role.py`…) | Keep monolithic `AccessApplication`; group by aggregate (spec §8.1) | User constraint: mirror `auth/`. Deterministic auditing, single responsibility |
| Ports | Per-aggregate protocols in `ports/` package | Keep monolithic `AccessStore` load/commit | Repository-per-aggregate; matches `auth.ports` |
| Transaction | `TransactionPort.atomic()` ctx-mgr wrapping one session | `store.serialized()` | Same session shared with Auth for coordinated provisioning (§12) |
| Last-admin invariant | Command locks reserved role + current assignments (`SELECT…FOR UPDATE`) inside `atomic()`, then asserts ≥1 active admin | DB trigger only | Cross-record invariant → app transaction (§12, obj 4.2) |
| Scope-definition catalog | New immutable `access_scope_definitions` table seeded with 19 rows; `ScopeDefinitionRegistryAdapter` reads it; `access_scopes.definition_key` FK to it | Code-only constant (not queryable); free-form scopes | Satisfies seed + `ListScopeDefinitions` + immutability (RLS). **Single addition beyond §11 table list — flagged in Open Questions** |
| HTTP routers | Split `create_self_access_router` (`/access/me`) + `create_admin_router`; admin guarded by `require_manage_access` dependency; commands re-verify inside txn | One router; per-route inline checks | Clear surface; defense-in-depth (§12 step 2) |
| Auth integration | Real `AccessProvisioningAdapter(session)` implements existing `auth.ports.access_provisioning.AccessProvisioningPort`, delegating to `CreateAccessUser`/`ActivateAccessUser`/`DeactivateAccessUser` + admin-count query | Publish `POST /access/users` | §7/§10.6 internal contract; shares session for one transaction |
| Versioning | `version` (profile admin optimistic lock) + `authorization_version` (bumped for affected users on role/scope/assignment change) | Single version | §11.1, §12 |

### Data Flow

Coordinated provisioning (Auth → Access, one transaction):

```
ProvisionAccount ──create provider id──▶ IdentityProvider
      │
      ▼ (session txn.atomic)
  AccountRepo.save ──▶ AccessProvisioningAdapter.provision_profile
                              │
                              ▼
                        CreateAccessUser ──▶ AccessUserRepo.save
                                          ──▶ AssignmentRepo (roles)
                                          ──▶ AccessAuditRepo.append (operation_id)
      commit ◀────────────────────────────┘   (rollback compensates provider id)
```

Admin mutation (e.g. ReplaceUserRoles):

```
HTTP ▶ require_manage_access ▶ UseCase.execute
   txn.atomic: verify version → lock admin set → mutate assignments
             → bump authorization_version(affected) → append audit → commit
```

## Components and Interfaces

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `access/domain/{actions,users,roles,scopes,errors}.py` | Create | 5 actions; `AccessUser` (UUID/version/authorization_version/timestamps); `Role`(name/description/`is_system_administrator`)/`Permission`; `Scope`/`ScopeCode`/`ScopeDefinition`; typed errors |
| `access/domain/models.py` | Delete | Replaced by split modules |
| `access/ports/{repositories,transaction,identity,clock}.py` | Create | `AccessUserRepository`, `RoleRepository`, `ScopeRepository`, `ScopeDefinitionRegistry`, `AccessAuditRepository`, `TransactionPort`, `IdentityPort`, `ClockPort` |
| `access/ports.py` | Delete | Replaced by `ports/` package |
| `access/application/*.py` | Create | One class per use case (proposal list): commands + queries + `AuthorizeAction`, `GetCurrentAccess`; `dto.py` |
| `access/application/services.py` | Delete | Monolith removed |
| `access/adapters/persistence/{records,repositories,transaction,authorization}.py` | Create/Replace | Spec-schema records; per-aggregate adapters; `TransactionAdapter`; authorization query adapter |
| `access/adapters/http/{models,router,error_handlers}.py` | Create | Pydantic models (strict/extra-forbid); self+admin routers; error→envelope map (§14) |
| `access/adapters/http_router.py` | Delete | Replaced by `adapters/http/` |
| `access/adapters/access_provisioning.py` | Create | `AccessProvisioningAdapter` implementing Auth port |
| `access/adapters/warehouse_authorization.py` | Modify | Point to `AuthorizeAction`; string-based `Action` unaffected |
| `bootstrap/http_application.py` | Modify | `_compose_access`; build provisioning adapter inside `auth_use_case_factory(session)`; remove `_FakeAccessProvisioning` |
| `bootstrap/warehouse_bale_dependency.py` | Modify | Replace `AccessStoreAdapter`/`AccessApplication` wiring with new repos + `AuthorizeAction` |
| `supabase/migrations/…_access_control_administration.sql` | Create | Clean-break: drop spine; create tables + `access_scope_definitions`; RLS/revokes; partial unique indexes; reserved-role/append-only triggers; seed 19 definitions |
| `backend/tests/**`, `backend/integration_tests/**` | Rewrite | Unit + real-Supabase integration |

### Interfaces / Contracts

```python
class AccessUserRepository(Protocol):
    def find_by_subject(self, subject: str) -> AccessUser | None: ...
    def save(self, user: AccessUser) -> None: ...          # optimistic version
    def count_active_administrators(self, *, exclude_user_id: str | None = None,
                                    for_update: bool = False) -> int: ...

class ScopeDefinitionRegistry(Protocol):
    def all(self) -> list[ScopeDefinition]: ...
    def get(self, definition_key: str) -> ScopeDefinition | None: ...  # supported_actions

class TransactionPort(Protocol):
    @contextmanager
    def atomic(self): ...
```

Admin commands take `expected_version` + `reason`. HTTP routers split into self-access (`/access/me`) and admin (`~15` endpoints, all behind `require_manage_access`). The `AccessProvisioningAdapter` implements the existing `auth.ports.access_provisioning.AccessProvisioningPort` unchanged — the exact contract that replaces `_FakeAccessProvisioning`.

## Data Models

Tables per tech spec §11 (physical schema authority; SQLAlchemy records mirror named constraints):

| Table | Key columns / constraints |
|-------|---------------------------|
| `access_users` | `user_id` PK; unique immutable `identity_subject`, `user_code`; `is_active`; `authorization_version`, `version`; timestamps |
| `access_roles` | `role_id` PK; unique `role_code`; `role_name`, `description`; `is_system_administrator` (partial unique index ≤1 true); `is_active`; `version` |
| `access_user_role_assignments` | `assignment_id` PK; FKs user/role; `assigned_by`/`assigned_at`; nullable `revoked_by`/`revoked_at`/`revoke_reason`; partial unique current `(user_id, role_id)` where `revoked_at IS NULL` |
| `access_scopes` | `scope_id` PK; unique immutable `definition_key` (FK→definitions) + `scope_code`; catalog metadata; `is_active`; `version` |
| `access_role_permissions` | `role_permission_id` PK; FKs role/scope; `action`; unique `(role_id, scope_id, action)`; rejects privileged actions on ordinary roles |
| `access_change_audits` | `access_change_audit_id` PK; `operation_id`; `change_kind`; `subject_type`/`subject_id`; nullable `performed_by`; `reason`; `before_values`/`after_values` JSONB; append-only |
| `access_scope_definitions` **(added)** | `definition_key` PK; `scope_code`, `scope_name`, `owning_context`, `description`, `supported_actions`; seeded with 19 rows; immutable (no API write path) |

Preset tables (`access_role_presets`, `access_role_preset_permissions`) deferred — not created this change.

## Correctness Properties

> Requirement numbers below reference the authoritative tech spec `backend/docs/features/access-control.md` sections; the sdd-spec phase will assign matching `X.Y` acceptance-criteria IDs.

### Property 1: Default-deny
Authorization is allowed only when an exact active `(action, scope)` exists in an active assigned active role, for an active user; every other request is denied.
**Validates: Requirements 6.4, 6.6**

### Property 2: Exact-match
Dot-separated scope codes carry no inheritance; a prefix match never authorizes a sibling or child scope.
**Validates: Requirements 6.2**

### Property 3: Union
Effective permissions equal the distinct union across all active assignments and active roles.
**Validates: Requirements 6.4**

### Property 4: System Administrator global access
An active admin gets all 5 actions in every active scope via a policy branch, not permission rows; the reserved role cannot be deactivated or demoted.
**Validates: Requirements 6.5**

### Property 5: Last-admin preserved
No committed mutation may leave zero active operational System Administrators (enforced under row locks).
**Validates: Requirements 6.5, 12.1**

### Property 6: Optimistic concurrency
A mismatched `expected_version` aborts with `access_version_conflict` before any mutation.
**Validates: Requirements 12.1**

### Property 7: Atomic audit
Every successful mutation appends exactly one audit row in the same transaction; failure rolls back both configuration and audit.
**Validates: Requirements 12.1, 15.1**

### Property 8: Immediate effect
Role/scope/assignment changes bump `authorization_version` for affected users and take effect on the next request (no cache).
**Validates: Requirements 12.1**

## Error Handling

Access domain errors map to the shared envelope (`access/adapters/http/error_handlers.py`, mirroring `auth`), per §14:

| HTTP | Codes |
|------|-------|
| 403 | `access_denied`, `access_user_inactive`, `access_profile_not_found` |
| 404 | `access_user_not_found`, `access_role_not_found`, `access_scope_not_found` |
| 409 | `duplicate_access_identity`/`_user_code`/`_role_code`/`_scope_code`, `access_version_conflict`, `last_system_administrator_required`, `inactive_access_role`, `inactive_access_scope` |
| 422 | `invalid_access_action`, `unsupported_action_for_scope`, `unrecognized_scope_definition`, `privileged_action_requires_system_administrator`, `duplicate_role_permission`, `access_change_reason_required`, `reserved_role_mutation_forbidden` |

Unnamed integrity errors are not translated to known conflicts; SQL, stack traces, and audit snapshots are never exposed.

## Testing Strategy

| Layer | What to test | Approach |
|-------|-------------|----------|
| Unit (domain) | 5 actions, ordinary-role rejects privileged actions, dup permissions, reserved-role invariants | stdlib `unittest`, no DB |
| Unit (application) | union permissions, inactive user/role/scope deny, exact-match no inheritance, version conflict, last-admin, audit-per-mutation | fake repos/clock/identity |
| API | 401/403 contract, `/access/me` ordinary+global shapes, admin rejects ordinary user, strict validation, envelope | FastAPI test client, injected session |
| Integration | named constraints, current-vs-historical assignment, atomic mutation+audit rollback, concurrent last-admin, immediate deactivation, append-only audit, RLS/revokes | real local Supabase (`TEST_DATABASE_URL`, port 54322) |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. Authorization is in-process policy.

## Migration / Rollout

Single clean-break migration (pre-launch, no data): drop spine tables/functions/triggers → create spec schema → RLS + revoke from `anon`/`authenticated`/`service_role` → partial unique indexes (one `is_system_administrator`, one current assignment per `(user,role)`) → reserved-role + append-only audit triggers → seed 19 `access_scope_definitions`. SQLAlchemy records mirror named constraints. Bootstrap (reserved role, `access_control` scope, initial admin) is a coordinated Auth-initialization transaction (§13), not real-secret migration data.

**Delivery — 4 chained PRs (<800 lines each):** 1) domain + ports; 2) persistence + migration + records; 3) application use cases; 4) HTTP + composition + Auth wiring (removes `_FakeAccessProvisioning`). Tests land with each PR touching that layer.

## Open Questions

- [ ] `access_scope_definitions` reference table is the one addition beyond §11's explicit table list (§11 keeps the catalog conceptual). Confirm the table is acceptable vs a code-only registry — chosen for queryability, seed requirement, and FK immutability.
- [ ] Confirm presets/previews stay deferred (tables and endpoints omitted this change).
