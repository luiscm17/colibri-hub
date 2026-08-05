# Design: auth-hexagonal-audit

## Technical Approach

Mechanical, layer-by-layer refactor of the `auth` bounded context to match the proven `access` pattern. Zero behavior change: identical URL paths, response shapes, status codes, and error handling. Work proceeds bottom-up so each phase is independently revertible: import redirects → shared infra → typed container + factory extraction → router split + response typing. The `access` module (`containers.py`, `access_admin_dependency.py`, split routers) is the reference template.

## Architecture Decisions

| Decision | Choice | Rejected | Rationale |
|----------|--------|----------|-----------|
| Cross-context import source | `shared.identity` | keep `warehouse.bales.ports.authorization` | `shared.identity` is the canonical kernel; removes hidden auth→warehouse dependency (PRD rule 10) |
| Use-case container | frozen `@dataclass(slots=True) AuthUseCases` in `auth/application/containers.py` | keep `dict[str,Any]` | compile-time safety, IDE discoverability, mirrors `AdminUseCases` |
| Shared clock/identity placement | `infra/clock.py`, `infra/identity.py` | duplicate private classes; `shared/` | `infra` owns technical adapters; `shared/` is value-object kernel only |
| Shared adapter coupling | structural (Protocol) compliance, no import of auth/access ports | import a port for `isinstance` | auth & access `ClockPort`/`IdentityPort` are structurally identical; keeps `infra` dependency-free (inward rule) |
| `AuthUseCaseProvider` alias home | `auth/application/containers.py` | duplicate in each router; keep in deleted `router.py` | single source of truth; avoids router→router coupling after split |
| Factory shape | move whole `_compose_auth` into `bootstrap/auth_dependency.py` as `compose_auth(settings, session_provider) -> tuple[IdentityResolver, AuthUseCaseProvider]` | split resolver/factory into two | preserves exact session-sharing + access-provisioning wiring (PRD rule 9) |
| Orphan `TransactionPort` | delete `auth/ports/transaction.py` | keep | never imported; auth commits via session, access has its own port |
| Router organization | `user_router.py` (self) + `admin_router.py` (accounts/audits), both `prefix="/auth"` | one file; distinct prefixes | mirrors access; keeps identical URL paths |

## Data Flow (unchanged at runtime)

```
create_app ──> compose_auth(settings, session_provider)
                   │ returns (identity_resolver, auth_use_case_provider)
                   v
create_api_router ──> create_auth_user_router(resolver, provider)
                 └──> create_auth_admin_router(resolver, provider)
                          │ Depends(provider) per request
                          v
                   AuthUseCases (built from session-scoped adapters +
                   AccessProvisioningAdapter sharing the SAME session)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `auth/application/containers.py` | Create | `AuthUseCases` dataclass (10 use cases) + `AuthUseCaseProvider = Callable[..., AuthUseCases]` |
| `bootstrap/auth_dependency.py` | Create | Extracted `compose_auth`; builds typed container, uses shared infra, preserves access provisioning + session sharing |
| `auth/adapters/http/user_router.py` | Create | `create_auth_user_router`: `GET /auth/me`, `POST /auth/password-change`, `DELETE /auth/session` |
| `auth/adapters/http/admin_router.py` | Create | `create_auth_admin_router`: `/auth/accounts` (GET,POST), `/auth/accounts/{id}` (GET), `password-reset`, `disable`, `enable`, `GET /auth/audits` |
| `infra/clock.py` | Create | `SystemClock.now() -> datetime` (UTC) |
| `infra/identity.py` | Create | `SystemIdentity.generate_id()/generate_operation_id()` |
| `auth/adapters/http/models.py` | Modify | Add `AuditEntryResponse`; typed audit endpoint |
| `auth/adapters/http/router.py` | Delete | Replaced by user/admin routers |
| `auth/ports/transaction.py` | Delete | Orphan port |
| `auth/adapters/identity_provider/jwt_validator.py` | Modify | Import `AuthenticatedIdentity` from `shared.identity` |
| `auth/adapters/identity_provider/request_pipeline.py` | Modify | Import `AuthenticatedIdentity` from `shared.identity` |
| `bootstrap/http_application.py` | Modify | Remove inline `_compose_auth`; call `compose_auth`; drop `_Fake*` classes |
| `bootstrap/access_admin_dependency.py` | Modify | Use `SystemClock`/`SystemIdentity` from infra; drop `_Simple*` classes |
| `bootstrap/api_router.py` | Modify | Import `AuthUseCaseProvider` from containers; include both auth sub-routers |

## Interfaces / Contracts

```python
# auth/application/containers.py
@dataclass(frozen=True, slots=True)
class AuthUseCases:
    get_current_authentication: GetCurrentAuthentication
    change_required_password: ChangeRequiredPassword
    record_logout: RecordLogout
    provision_account: ProvisionAccount
    reset_password: ResetPassword
    disable_account: DisableAccount
    enable_account: EnableAccount
    get_account: GetAccount
    list_accounts: ListAccounts
    list_audits: ListAudits

AuthUseCaseProvider = Callable[..., AuthUseCases]
```

```python
# auth/adapters/http/models.py (new)
class AuditEntryResponse(_AuthModel):
    audit_id: str
    operation_id: str
    event_type: str
    outcome: str
    affected_account_id: str | None
    occurred_at: str  # keep serialized shape identical to current dict
```

Router handlers switch from `use_cases["key"]` to `use_cases.attr`; all commands/DTOs and response models are unchanged.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `SystemClock`/`SystemIdentity` satisfy port contracts; `AuthUseCases` construction | stdlib `unittest` |
| Unit | Router handlers resolve via typed container; audit response shape unchanged | update existing auth router tests to typed container |
| Integration | All `/api/v1/auth/*` paths return identical status/body; session sharing intact | existing FastAPI TestClient suite, no path/response changes |
| Regression | Grep tests for `_FakeClock`/`_FakeIdentity`/`_SimpleClock`/`_SimpleIdentity` and dict-key access | update references before deleting old symbols |

## Threat Matrix

N/A — no shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. The router "split" is mechanical reorganization: identical URL paths, identical `identity_resolver` guards, error handlers stay app-level. No new routing behavior or authorization surface is introduced.

## Migration / Rollout

No migration required. No schema, config, or API changes. Each phase is a standalone `git revert`; `shared.identity` re-exports keep old import paths working during transition. Single PR within the 400-line budget (~300 net lines).

## Open Questions

None — all decisions confirmed in the proposal.
