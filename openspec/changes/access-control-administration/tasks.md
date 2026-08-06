# Tasks: Access Control Administration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 2800–3400 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Domain entities + ports protocols + unit tests | PR 1 → `back/access-control-administration` | `uv run --locked --package backend python -m unittest backend.tests.access.domain -v` | N/A — pure domain, no DB | Revert PR 1 branch from tracker |
| 2 | Persistence records + migration + scope-definition seed + integration tests | PR 2 → PR 1 branch | `TEST_DATABASE_URL=... uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v` | `pnpm supabase db reset --local --no-seed` before run | Revert PR 2 branch; migration is additive |
| 3 | Application use cases (commands + queries) + unit tests | PR 3 → PR 2 branch | `uv run --locked --package backend python -m unittest backend.tests.access.application -v` | N/A — fake repos | Revert PR 3 branch |
| 4 | HTTP routers + composition wiring + auth adapter + API tests + cleanup | PR 4 → PR 3 branch | `uv run --locked --package backend python -m unittest backend.tests.api.test_access -v` | Full app via `create_app` test client | Revert PR 4 branch |

---

## Phase 1: Domain + Ports (PR 1)

- [ ] 1.1 Create `access/domain/actions.py` — `Action` StrEnum with 5 values (`read`, `write`, `edit`, `edit_outside_window`, `manage_access`), `Permission` frozen dataclass
- [ ] 1.2 Create `access/domain/scopes.py` — `ScopeCode` value object, `Scope` entity (UUID, `definition_key`, `scope_code`, metadata, `is_active`, `version`), `ScopeDefinition` immutable dataclass (`definition_key`, `scope_code`, `scope_name`, `owning_context`, `description`, `supported_actions`)
- [ ] 1.3 Create `access/domain/roles.py` — `Role` entity (UUID, `role_code`, `role_name`, `description`, `is_system_administrator`, `is_active`, `version`, permissions set), `Assignment` entity (UUID, FKs, `assigned_by`/`assigned_at`, nullable revocation fields)
- [ ] 1.4 Create `access/domain/users.py` — `AccessUser` entity (UUID, `identity_subject`, `user_code`, `display_name`, `is_active`, `authorization_version`, `version`, timestamps)
- [ ] 1.5 Create `access/domain/errors.py` — typed exceptions per §14: `AccessDenied`, `AccessUserNotFound`, `AccessRoleNotFound`, `AccessScopeNotFound`, `DuplicateAccessIdentity`, `DuplicateUserCode`, `DuplicateRoleCode`, `DuplicateScopeCode`, `AccessVersionConflict`, `LastSystemAdministratorRequired`, `InactiveAccessRole`, `InactiveAccessScope`, `InvalidAccessAction`, `UnsupportedActionForScope`, `UnrecognizedScopeDefinition`, `PrivilegedActionRequiresSystemAdministrator`, `DuplicateRolePermission`, `AccessChangeReasonRequired`, `ReservedRoleMutationForbidden`, `AccessUserInactive`, `AccessProfileNotFound`
- [ ] 1.6 Create `access/domain/__init__.py` — re-export public API
- [ ] 1.7 Create `access/ports/__init__.py`, `access/ports/repositories.py` — `AccessUserRepository`, `RoleRepository`, `ScopeRepository`, `ScopeDefinitionRegistry`, `AccessAuditRepository` protocols
- [ ] 1.8 Create `access/ports/transaction.py` — `TransactionPort` protocol with `atomic()` context manager
- [ ] 1.9 Create `access/ports/identity.py` — `IdentityPort` protocol (`generate_id`, `generate_operation_id`)
- [ ] 1.10 Create `access/ports/clock.py` — `ClockPort` protocol (`now() -> datetime`)
- [ ] 1.11 Delete `access/domain/models.py` and `access/ports.py` — replaced by new packages
- [ ] 1.12 Write unit tests for domain entities: action validation, permission set ops, reserved-role invariants, scope-code normalization, user activation/deactivation
- [ ] 1.13 Write unit tests for `snapshot_for` / `allows` equivalents confirming default-deny, exact-match, union, global admin access

## Phase 2: Persistence + Migration (PR 2)

- [ ] 2.1 Create clean-break migration SQL: DROP all spine tables/functions/triggers → CREATE `access_users`, `access_roles`, `access_user_role_assignments`, `access_scopes`, `access_role_permissions`, `access_change_audits`, `access_scope_definitions` with named constraints → RLS + revokes → partial unique indexes → reserved-role/append-only triggers → seed 19 scope definitions
- [ ] 2.2 Create `access/adapters/persistence/records.py` — new SQLAlchemy records matching spec schema (replace existing records entirely)
- [ ] 2.3 Create `access/adapters/persistence/repositories.py` — `AccessUserRepositoryAdapter`, `RoleRepositoryAdapter`, `ScopeRepositoryAdapter`, `ScopeDefinitionRegistryAdapter`, `AccessAuditRepositoryAdapter`
- [ ] 2.4 Create `access/adapters/persistence/transaction.py` — `TransactionAdapter` wrapping SQLAlchemy session with `atomic()` context manager
- [ ] 2.5 Create `access/adapters/persistence/__init__.py` — re-export adapters
- [ ] 2.6 Write integration tests: named constraint enforcement, current-vs-historical assignment partial unique, atomic mutation+audit rollback, append-only audit trigger, RLS/revokes, scope-definition seed verification (19 rows)

## Phase 3: Application Use Cases (PR 3)

- [ ] 3.1 Create `access/application/dto.py` — command/query data structures for all use cases
- [ ] 3.2 Create command use cases (one file each): `create_access_user.py`, `activate_access_user.py`, `deactivate_access_user.py`, `create_role.py`, `update_role.py`, `activate_role.py`, `deactivate_role.py`, `replace_user_roles.py`, `register_recognized_scope.py`, `activate_scope.py`, `deactivate_scope.py`
- [ ] 3.3 Create query use cases (one file each): `authorize_action.py`, `get_current_access.py`, `list_access_users.py`, `get_access_user.py`, `list_roles.py`, `get_role.py`, `list_scopes.py`, `list_scope_definitions.py`, `list_access_audits.py`
- [ ] 3.4 Create `access/application/__init__.py` — re-export use case classes
- [ ] 3.5 Delete `access/application/services.py` — monolith replaced
- [ ] 3.6 Write unit tests with fake repos: default-deny, union permissions, inactive user/role/scope deny, exact-match no inheritance, version conflict rejection, last-admin enforcement, audit-per-mutation, `authorization_version` bump on role/scope/assignment change

## Phase 4: HTTP + Composition + Auth Wiring (PR 4)

- [ ] 4.1 Create `access/adapters/http/models.py` — Pydantic request/response models (strict, extra-forbid)
- [ ] 4.2 Create `access/adapters/http/router.py` — `create_self_access_router` (`/access/me`) + `create_admin_router` (~15 admin endpoints) with `require_manage_access` dependency
- [ ] 4.3 Create `access/adapters/http/error_handlers.py` — domain error → HTTP envelope mapping per §14 table
- [ ] 4.4 Create `access/adapters/access_provisioning.py` — `AccessProvisioningAdapter` implementing `auth.ports.access_provisioning.AccessProvisioningPort`
- [ ] 4.5 Modify `access/adapters/warehouse_authorization.py` — point to new `AuthorizeAction` use case
- [ ] 4.6 Modify `bootstrap/http_application.py` — `_compose_access` wiring; build provisioning adapter inside `auth_use_case_factory(session)`; remove `_FakeAccessProvisioning`
- [ ] 4.7 Modify `bootstrap/warehouse_bale_dependency.py` — replace `AccessStoreAdapter`/`AccessApplication` wiring with new repos + `AuthorizeAction`
- [ ] 4.8 Delete `access/adapters/http_router.py` — replaced by `adapters/http/` package
- [ ] 4.9 Delete `access/adapters/persistence/store.py` — old monolithic store
- [ ] 4.10 Write API tests: 401/403 contract, `/access/me` ordinary+global shapes, admin rejects ordinary user, strict validation, error envelope format, provisioning integration
