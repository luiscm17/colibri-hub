# Exploration: Authentication Foundation

## Context

Authentication Foundation implements the backend identity provider for Colibri Hub, replacing the current fail-closed `401` seam with real Supabase Auth token validation, application-owned account states, mandatory password replacement, session enforcement, and coordinated provisioning with Access Control.

## Authoritative Inputs

- **PRD**: `docs/prd/auth.md` — normative business rules
- **Tech Spec**: `backend/docs/features/authentication.md` — complete hexagonal backend design
- **Access Spine**: already merged in `back/access-auth-spine` (PRs #37, #38, #39)

## Current State

### 1. Identity Seam (Fail-Closed)

`AuthenticatedIdentity` is a frozen dataclass in `warehouse/bales/ports/authorization.py`:
```python
@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    subject: str
    session_id: str | None = None
```

`IdentityResolver = Callable[[], AuthenticatedIdentity]` — injected into `create_app`. Default raises `HTTPException(401, "authentication_required")`. The real JWT validator replaces it at composition time.

### 2. Access Integration Points

`AccessApplication` exposes:
- `bootstrap(subject, profile_code, operation_id)` — initial admin (idempotent)
- `set_profile_active(command, is_active)` — activate/deactivate profiles
- `authorize(subject, action, scope)` — evaluate access
- `current_access(subject)` → `AccessSnapshot | None`
- `create_current_assignment(command, role_code)` — assign roles
- Mutations catch `FinalAdministratorRemoval` for last-admin invariant

**Gap**: No `provision_profile(subject, profile_code, role_ids, operation_id)` method yet. Auth needs a coordinated provisioning service.

### 3. Bootstrap Composition

`create_app` already accepts `identity_resolver: IdentityResolver` parameter. CORS allows `Authorization` header. Route composition via `create_api_router`.

### 4. Persistence Patterns

- Records inherit from `RecordRegistry` (SQLAlchemy DeclarativeBase)
- Named constraints (`pk_`, `uq_`, `fk_`, `ck_`, `ix_`)
- Migrations: imperative SQL in `supabase/migrations/`, timestamped
- RLS enabled, browser roles revoked

### 5. Supabase Auth Configuration Gaps

- `enable_signup = true` → **must be `false`**
- `[auth.sessions]` section commented out → **must set `timebox = "8h"`**
- `minimum_password_length = 6` → **should be `8`**

### 6. Package Dependencies Missing

- `supabase` (admin client)
- `PyJWT` + `cryptography` (server-side JWT RS256 validation)
- `auth*` not in setuptools `packages.find.include`

### 7. Shared Error Helper

`error_json_response` is in `warehouse/bales/adapters/http/error_mapping.py`. Auth needs the same envelope — must extract to shared location.

## Integration Points

1. **Identity injection** — JWT validator replaces `unauthenticated_identity` in `create_app`
2. **Access provisioning** — Auth calls AccessApplication for profile creation and state changes
3. **Shared transaction** — Auth and Access tables share same PostgreSQL session
4. **Error envelope** — Same `{ "error": {...} }` structure
5. **Route composition** — New `create_auth_router(...)` included via `create_api_router`
6. **Record registry** — Auth records registered alongside Access records

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| AccessApplication lacks provision method | Medium | Extend with new coordinated provisioning service in Phase 1 |
| Shared error helper coupling | Low | Extract to `infra/http/` in Phase 3 before auth HTTP |
| Supabase Admin SDK session revocation completeness | Medium | Verify against local Supabase; fallback to direct `auth.sessions` query |
| JWKS caching complexity | Medium | Start with local JWT secret for dev; add JWKS for production |
| Session age requires `auth.sessions` query | Low | Service-role restricted query, not end-user token |

## Conclusion

The codebase is well-prepared. The identity seam is clean, Access spine provides the authorization backbone, hexagonal patterns are established. Implementation follows existing conventions with straightforward module creation.
