# Tasks: Fix Auth Disable Account

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 150–220 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Fix adapter + all tests | Single PR | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` | N/A — unit tests only, no external deps | Revert branch |

## Phase 1: Fix Adapter

- [x] 1.1 Modify `backend/src/auth/adapters/identity_provider/admin_client.py` — replace `self._client.auth.admin.sign_out(subject, "global")` in `revoke_sessions` with `self._client.schema("auth").from_("sessions").delete().eq("user_id", subject).execute()`
- [x] 1.2 Verify existing `get_session` already uses the same `schema("auth").from_("sessions")` pattern for consistency

## Phase 2: Adapter Unit Tests

- [x] 2.1 Create `backend/tests/test_auth_adapter_provider.py` — test `ban_user` calls `update_user_by_id(subject, {"ban_duration": "876600h"})`
- [x] 2.2 Test `unban_user` calls `update_user_by_id(subject, {"ban_duration": "none"})`
- [x] 2.3 Test `revoke_sessions` calls `schema("auth").from_("sessions").delete().eq("user_id", subject).execute()`
- [x] 2.4 Test `revoke_sessions` catches exceptions and does not re-raise (best-effort)
- [x] 2.5 Test `_handle_provider_error` maps exceptions to `ProviderUnavailable`, `DuplicateEmail`, `WeakPassword`

## Phase 3: Admin Endpoint Tests

- [x] 3.1 Create `backend/tests/api/test_auth_admin_endpoints.py` — test `POST /auth/accounts/{id}/disable` returns 204 on success
- [x] 3.2 Test disable returns 404 for non-existent account
- [x] 3.3 Test disable returns 409 for version conflict
- [x] 3.4 Test disable returns 503 when provider is unavailable (ban fails)
- [x] 3.5 Test `POST /auth/accounts/{id}/enable` returns 204 on success
- [x] 3.6 Test `POST /auth/accounts/{id}/password-reset` returns 204 on success

## Phase 4: Verification

- [x] 4.1 Run full unit suite — all pass including new tests
- [x] 4.2 Verify no existing tests regress from the adapter change
