# Proposal: Authentication Foundation

## Intent

Establish the first deployable Authentication backend that replaces the current fail-closed `401` with real Supabase Auth identity validation, application-owned account lifecycle, mandatory password replacement, eight-hour session enforcement, and coordinated provisioning with Access Control. This is the prerequisite for every subsequent authenticated capability in Colibri Hub.

## Scope

### In Scope
- Supabase Auth as the identity, credential, token, and session provider.
- Server-side JWT validation with RS256, JWKS caching, and bounded TTL.
- Application-owned `authentication_accounts` table with status transitions: `awaiting_password_change`, `active`, `disabled`.
- Application-owned `authentication_audits` append-only table for redacted evidence.
- Mandatory provisional password replacement before protected access.
- Eight-hour session enforcement via provider timebox configuration plus server-side session-age validation.
- Request pipeline: validate token → check account state → restrict awaiting_password_change → check session age → expose trusted identity.
- User endpoints: `GET /auth/me`, `POST /auth/password-change`, `DELETE /auth/session`.
- Administrative endpoints: provision, list, get, reset, disable, enable accounts; query audits.
- Unified provisioning: create Supabase identity + Auth account + Access profile + initial roles atomically.
- Initial System Administrator bootstrap command (deployment-time, not a public route).
- Coordination with existing Access spine for profile activation/deactivation and last-admin invariant.
- Supabase local configuration: disable signup, set session timebox to 8 hours.

### Out of Scope
- Frontend authentication (separate subsequent phase).
- Access Control administration UI.
- MFA, OAuth, SSO, magic links, self-service recovery.
- Automated email delivery of provisional passwords.
- Configurable session duration.
- Physical account deletion.

## Capabilities

### New Capabilities
- `authentication-foundation`: complete backend Authentication lifecycle per PRD and tech spec.

### Modified Capabilities
- `access-authorization-spine`: extend `AccessApplication` with a provisioning method for coordinated profile+role creation.

## Approach

Create a new `auth/` bounded context following the established hexagonal patterns (domain → ports → application → adapters). Supabase-specific behavior stays behind infrastructure adapters. The existing `IdentityResolver` seam in `create_app` is the injection point for the real JWT validator. Shared error envelope is extracted to `infra/http/` for cross-context reuse.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/src/auth/` | New | Full hexagonal auth module |
| `backend/src/infra/http/` | New | Shared error envelope extraction |
| `backend/src/infra/configuration.py` | Modified | Supabase auth settings |
| `backend/src/infra/persistence/record_registry.py` | Modified | Auth record registration |
| `backend/src/bootstrap/` | Modified | Composition, real identity resolver wiring |
| `backend/src/access/application/services.py` | Modified | Add provisioning method |
| `supabase/config.toml` | Modified | Disable signup, session timebox |
| `supabase/migrations/` | New | Auth tables migration |
| `backend/pyproject.toml` | Modified | Dependencies + package discovery |
| `backend/tests/`, `backend/integration_tests/` | New + Modified | Auth unit, API, and integration tests |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Supabase Admin SDK session revocation API gaps | Medium | Verify locally; fallback to direct `auth.sessions` query via service role |
| Session age validation requires provider table access | Certain | Use service-role restricted query, not end-user token |
| Shared error extraction touches existing imports | Low | Mechanical refactor; run full test suite after |
| Provider creation succeeds but app persistence fails | Low | Safe ordering: keep identity unusable until app commit; compensation removes quarantined identity |
| JWKS key rotation complexity | Medium | Start with local JWT secret; add JWKS caching with bounded TTL |

## Rollback Plan

Each PR slice is independently revertible. Core (domain/ports/application) has zero external coupling. Persistence adds a forward-only migration revertible via compensating migration. Provider adapters and HTTP composition can be removed to restore the fail-closed `401` seam.

## Dependencies

- User-run package installation: `uv add --package backend PyJWT cryptography supabase`
- Local Supabase running (`pnpm supabase start`)
- Access Authorization Spine merged (already done at `553dea2`)
- No frontend dependencies

## Success Criteria

- [ ] Real Supabase JWT validates identity; invalid/expired/missing tokens are denied.
- [ ] Account states enforce mandatory password replacement before protected access.
- [ ] Sessions are denied at exactly eight hours from provider session start.
- [ ] Unified provisioning creates identity + account + profile + roles atomically.
- [ ] Disablement/reset terminate provider sessions and deny access immediately.
- [ ] Initial System Administrator bootstrap is idempotent and controlled.
- [ ] No credential appears in audit, log, error, or response.
- [ ] Unit, API, and integration tests pass for all auth flows.
