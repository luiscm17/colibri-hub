# Design: Fix Auth Disable Account

## Technical Approach

Replace the invalid `admin.sign_out(uuid, "global")` call with a direct `auth.sessions` table deletion via the service-role client, which is the same mechanism already used by `get_session`. Add adapter and endpoint tests to cover the disable/enable/reset paths.

## Architecture Decisions

| Decision | Choice | Alternative | Rationale |
|----------|--------|-------------|-----------|
| Session revocation mechanism | Delete from `auth.sessions` via service-role schema query | Find user's active JWT and pass to `sign_out` | No admin API exists in supabase-py 2.31 to revoke sessions by user ID; direct table deletion is already proven in `get_session`; ban prevents new logins regardless |
| Revocation remains best-effort | Keep try/except + warning (no re-raise) | Make revocation mandatory (raise on failure) | Spec §13 defines safe ordering: local denial + Access deactivation happen BEFORE provider ops. Ban alone prevents new sessions. Revocation is defense-in-depth for existing tokens. |
| Test approach | Unit tests with fake adapter + API tests with mocked provider | Integration tests against local Supabase | Unit tests validate contract and orchestration; integration tests are out of scope for this fix (documented in coverage gap analysis §4.3) |

## Data Flow

```
DisableAccount.execute
    │
    ├─ 1. account.disable(now)    → local state = disabled
    ├─ 2. accounts.save(account)  → flush to DB
    ├─ 3. access.deactivate_profile → Access user inactive
    ├─ 4. provider.ban_user       → update_user_by_id(uuid, {ban_duration})  ✓
    ├─ 5. provider.revoke_sessions → DELETE auth.sessions WHERE user_id = uuid  ← FIX
    └─ 6. audits.append           → audit record
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modify | Replace `sign_out(subject, "global")` with `schema("auth").from_("sessions").delete().eq("user_id", subject).execute()` |
| `backend/tests/test_auth_adapter_provider.py` | Create | Unit tests for `IdentityProviderAdapter`: ban_user, unban_user, revoke_sessions, error translation |
| `backend/tests/api/test_auth_admin_endpoints.py` | Create | HTTP endpoint tests for disable (204), enable (204), reset (204), and their error paths |

## Interfaces / Contracts

No new ports or interfaces. The `IdentityProviderPort.revoke_sessions` signature remains:

```python
def revoke_sessions(self, *, subject: str) -> None:
    """Revoke all active provider sessions for this identity (best-effort)."""
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (adapter) | `revoke_sessions` calls correct Supabase method; `ban_user`/`unban_user` pass valid args; errors map to domain types | Mock `SupabaseClient` and assert calls |
| Unit (application) | `DisableAccount` orchestration with failing provider | Existing fakes in `test_auth_application.py`, verify safe ordering |
| API | Disable/enable/reset return correct status codes and handle errors | TestClient with mocked use cases |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Pure adapter code fix + new test files.

## Open Questions

None — all technical decisions resolved from exploration evidence.
