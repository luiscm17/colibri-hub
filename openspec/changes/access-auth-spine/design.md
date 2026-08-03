# Design: Access Authorization Spine

## Technical Approach

Add an `access` bounded context alongside `warehouse`: pure domain/application/ports; SQLAlchemy/FastAPI adapters outside. Warehouse owns its required authorization port; an Access adapter implements it at composition. This implements both delta specs without Authentication, provider SDKs, or client authority.

```
trusted resolver -> Warehouse AuthorizationPort -> Access adapter -> Access application
                         |                                              |
                         +---- Warehouse register after allow -----------+-> PostgreSQL policy/audit
```

## Architecture Decisions

| Decision | Options/trade-off | Choice and rationale |
|---|---|---|
| Context dependencies | Warehouse reads Access records; or consumer-owned port | `warehouse.bales` owns `AuthorizationPort`; `access` implements it from an outer adapter. `bootstrap` wires them. Warehouse imports neither Access contracts nor persistence. |
| Policy ownership | Anemic evaluator service; rich model | `AccessProfile`, `Role`, `RoleAssignment`, `Permission`, and `Scope` own active/exact/global rules. Application use cases load, invoke behavior, transact, and audit. |
| Identity | Header/dev subject; provider-neutral seam | Frozen `AuthenticatedIdentity(subject, session_id=None)` is supplied only by a resolver. Production resolver raises unauthenticated; test/future Authentication adapters inject it. |
| Bootstrap scopes | Migration seeds scopes; or bootstrap establishes them | Migration creates only schema, constraints, and a singleton bootstrap lock row. `BootstrapAccess` atomically creates the two canonical scopes with the profile, role, assignment, and audit; this satisfies retry/partial-state semantics. |
| Administrator invariant | Application count alone; serialized mutation gate | Lock the reserved-role row first, then current assignments and profiles in stable ID order; re-count operational coverage in the same transaction. This serializes every coverage-removing command. |

## Data Flow

`POST /warehouse/bales`: identity dependency resolves first (`401` if absent); route derives `write` + `warehouse.raw_materials` itself; its consumer-owned port returns allow or generic `403 access_denied`; only then request mapping, Warehouse validation, and its existing transaction run. The composed Access adapter delegates to `AuthorizeAction`. Roles/scopes/body/header values never influence the decision. Other Warehouse routes remain unchanged.

`GET /access/me` maps authenticated subject to an ordinary permission snapshot or `{global: true}`; it alone returns specific missing/inactive-profile outcomes.

## Domain and Interfaces

`Action` is the fixed action enum. `ScopeCode` is immutable. Ordinary active roles contribute only deduplicated exact active `(action, scope)` permissions; missing/inactive profile, assignment, role, or scope denies. The reserved active `system_administrator` role has an explicit global branch for every recognized scope, never a wildcard row.

```python
@dataclass(frozen=True)
class AuthenticatedIdentity: subject: str; session_id: str | None = None

class AuthorizationPort(Protocol):  # warehouse.bales.ports.authorization
    def require(self, identity: AuthenticatedIdentity, *, action: str, scope: str) -> None: ...
```

`backend/src/warehouse/bales/ports/authorization.py` owns this contract and opaque identity type; its strings are server constants, not client data. `access/adapters/warehouse_authorization.py` implements it and maps them to Access `Action`/`ScopeCode` before delegating to Access application use cases; Access has no dependency from Warehouse back into its policy or records. Application driver ports: `AuthorizeAction`, `GetCurrentAccess`, `BootstrapAccess`, `SetProfileActive`, `SetRoleActive`, `CreateCurrentAssignment`, `RemoveCurrentAssignment`, and `SetAssignmentActive`. Mutation commands include actor, target, required reason, and operation ID; first authorize actor for `write/access_control`, then lock, mutate, append audit, and commit. Rejection rolls back unchanged. Bootstrap is an internal trusted driver port: it locks the singleton, creates all initial state or returns the same complete result (profile, role, both scopes, assignment, audit); any pre-existing partial/incompatible identifiers fail closed without repair.

## Persistence and Rollout

One forward-only imperative migration creates `access_profiles` (immutable unique subject/code), `access_roles`, `access_scopes`, `access_role_permissions`, historical `access_role_assignments` (one current pair), `access_change_audit`, and a singleton bootstrap-lock table/row. It does **not** seed role or scope policy rows. Bootstrap holds that row `FOR UPDATE` and atomically creates the reserved role, exactly `access_control` and `warehouse.raw_materials`, profile, assignment, and audit, or returns the stored complete operation result. Named PK/FK/check/unique constraints, restrictive FKs, partial indexes for active subject resolution/current assignments/operational administrators, and unique role-permission/scope/operation identifiers reject duplicates and incompatible partial state. Audit has redacted JSON before/after, actor nullable only for `initial_bootstrap`, and no application delete/update path; history is retained.

Enable RLS on every Access table and revoke table privileges from `anon`, `authenticated`, and `service_role`, matching Warehouse; backend application authorization remains primary. Do not use `SECURITY DEFINER`, client JWT metadata, secrets, tokens, or raw claims. Reset local drift before PostgreSQL evidence: `pnpm supabase db reset --local --no-seed`; inspect with `pnpm supabase migration list --local`. Rollback is an approved forward compensating migration plus dependent composition removal, never a down migration or silent unprotection.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/src/access/{domain,application,ports,adapters}/` | Create | Policy model/use cases, SQLAlchemy records/repositories, `/access/me`, and Warehouse-port adapter. |
| `backend/src/warehouse/bales/ports/authorization.py` | Create | Consumer-owned opaque identity and authorization requirement contract. |
| `backend/src/bootstrap/{http_application,api_router,warehouse_bale_dependency}.py` | Modify | Compose Access adapter behind the Warehouse port, identity seam/router; permit `Authorization` CORS header. |
| `backend/src/warehouse/bales/adapters/http/router.py` | Modify | Consume its port before DTO mapping; document 401/403. |
| `backend/src/infra/persistence/record_registry.py`, `backend/pyproject.toml` | Modify | Register records; include `access*` package discovery. |
| `supabase/migrations/<generated>_create_access_authorization_spine.sql` | Create | Forward-only schema, bootstrap lock, indexes, RLS/ACL; no policy seeds. |
| `backend/tests/{domain,application,api,runtime}/`, `backend/integration_tests/` | Create/Modify | Policy, composition/HTTP, and PostgreSQL proof. |

## Testing Strategy

| Layer | Proof | Approach |
|---|---|---|
| Unit/application | exact/additive/inactive/global policy; every final-admin removal path; idempotent/conflicting bootstrap | `unittest` Access objects/use cases plus Warehouse-owned-port doubles; assert rejected mutation/audit leave state unchanged. |
| HTTP/composition | fail-closed 401, generic Warehouse 403 before mapper/use case, ignored client roles/scopes, `/me` contracts, CORS/router discovery | Inject deterministic resolver and an implementation of the Warehouse port into `create_app`. |
| PostgreSQL | named constraints/indexes, RLS/ACL, immutable/history behavior, bootstrap retry/conflict, concurrent final-admin mutations | Verify bootstrap creates all two scope rows and complete result in one transaction; pre-existing partial scope/role state rejects without repair; separate sessions/threads prove only one competing removal commits after reset. |

Commands: `uv run --locked --package backend python -m unittest discover -s backend/tests -v`; then `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v`. No E2E framework exists. No dependency is expected; if one becomes necessary, the user—not an agent—must run its install command.

## Threat Matrix

| Boundary | Applicability | Response / RED test |
|---|---|---|
| Documentation-like paths | N/A | No executable classification. |
| Git repository selection | N/A | No VCS operation. |
| Commit state | N/A | No commit operation. |
| Push state | N/A | No push operation. |
| PR commands | N/A | Review boundaries are planning only. |

## Review Boundaries and Open Questions

Forecast supports two coherent units: (1) Access domain/application, migration, PostgreSQL proof; (2) HTTP/composition, Warehouse gate, contract proof. Keep the chain strategy explicitly unresolved until tasks/apply; each targets the 800-line user budget and must also report the repository 400-line guard.

- [ ] Confirm mutation driver ports remain internal until a later administrative HTTP contract is approved.
- [ ] Select chained versus approved-size delivery before apply.
