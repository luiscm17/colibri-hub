# Proposal: Fix Auth Disable Account (Issue #61)

## Intent

`POST /api/v1/auth/accounts/{id}/disable` returns HTTP 500 instead of completing the disable flow. The `revoke_sessions` adapter method passes a UUID to `admin.sign_out(jwt, scope)` which expects a JWT — a confirmed contract mismatch with supabase-auth 2.31.0. Additionally, the actual 500 source needs reproduction to determine whether it's a transaction rollback from an upstream provider failure or the sign_out defect itself. This fix corrects the adapter contract, adds missing test coverage, and ensures partial-failure safety.

## Scope

### In Scope
- Fix `revoke_sessions` to use a valid Supabase admin API mechanism for user-targeted session invalidation.
- Reproduce and identify the actual HTTP 500 source (provider integration or transaction rollback).
- Add unit tests for the adapter's ban/unban/revoke contract.
- Add API-level tests for disable, enable, and password-reset admin endpoints.
- Verify partial-failure ordering: local denial persists even if provider operations fail.

### Out of Scope
- Auth admin endpoint authorization guard (C1 from coverage analysis — separate PR).
- Bootstrap command functionality (C2).
- Last-admin locking invariant (C3).
- Role presets, impact previews, authorization_version propagation (D1–D3).
- Frontend changes.

## Capabilities

### New Capabilities
None

### Modified Capabilities
None — this is a bugfix within existing authentication capability boundaries.

## Approach

1. Replace `admin.sign_out(subject, "global")` with a valid admin mechanism. Options:
   - Use `admin.update_user_by_id(subject, {"ban_duration": "876600h"})` (already done by ban) which makes explicit session revocation redundant since banned users cannot refresh tokens.
   - Or query+delete from `auth.sessions` via service-role direct DB access.
2. Given that `ban_user` already prevents new sessions, make `revoke_sessions` use the direct `auth.sessions` deletion approach for immediate invalidation of existing tokens.
3. Add adapter-level unit tests validating correct method calls and error translation.
4. Add HTTP endpoint tests for disable/enable/reset paths.
5. Verify safe ordering: local state saved → access deactivated → provider ban → revoke (best-effort).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modified | Fix `revoke_sessions` contract |
| `backend/tests/test_auth_adapter_provider.py` | New | Adapter contract unit tests |
| `backend/tests/api/test_auth_admin_endpoints.py` | New | HTTP endpoint tests for disable/enable/reset |
| `backend/tests/test_auth_application.py` | Modified | Verify orchestration with updated mock |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Direct `auth.sessions` deletion may not exist on local Supabase | Low | Verified during explore: adapter already uses `schema("auth").from_("sessions")` in `get_session` |
| Ban alone may be insufficient if access tokens haven't expired | Medium | Combine ban (no new sessions) + session deletion (invalidate existing refresh tokens) |
| Transaction rollback on provider failure leaves inconsistent state | Medium | Spec §13 defines safe ordering; tests verify local denial persists regardless of provider outcome |

## Rollback Plan

Revert the branch. The fix is isolated to one adapter method and new test files. No schema migrations, no domain model changes.

## Dependencies

- Local Supabase running for integration verification (`pnpm supabase start`).
- supabase-auth 2.31.0 (already locked).

## Success Criteria

- [ ] `POST /auth/accounts/{id}/disable` returns 204 on a valid active account.
- [ ] Provider sessions are invalidated after disable.
- [ ] `revoke_sessions` no longer passes UUID as JWT.
- [ ] Disable/enable/reset endpoints have automated test coverage.
- [ ] Provider failure in ban/revoke returns 503, not 500.
- [ ] Local account state is disabled even if provider operations fail (safe ordering preserved).
