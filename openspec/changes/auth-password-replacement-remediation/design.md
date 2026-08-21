# Design: Remediate Mandatory Password Replacement

## Technical Approach

Use a narrow self-service port instead of administrative `update_password`. Select an implementation only after a disposable-identity harness proves it locally and in target-equivalent configuration. Activate and audit only after provider success. Preserve the client sequence: empty 204 from `POST /api/v1/auth/password-change`, then same-bearer `GET /api/v1/auth/me` returning `next_step: "load_access"`. This covers F-1/F-2/F-3 without frontend changes and excludes F-4, administration, and Access.

## Provider Capability Gate and Remedy Selection

No candidate is approved today: the local `update_user(... current_password=...)` characterization accepted a wrong password. Documentation examples are not runtime proof.

1. Evaluate native authenticated update first; composed reauthentication second.
2. Record safe pre-state: account status/version, success-audit count, and original provider-session identity/continuity evidence. The provider-configured bounded maximum duration begins with the originating login; never independently calculate or configure it, and never persist secrets.
3. Prove weak-new and wrong-current attempts leave credential, account, audit, and original provider session unchanged.
4. Prove one valid replacement makes old login fail and new login succeed while use continues only within the original provider session's remaining duration; do not restart, extend, rotate, or substitute it.
5. Repeat target-equivalently. Any failed, skipped, unavailable, or unobservable assertion blocks selection. Never consider admin update, recovery, auth-schema writes, or replacement sessions.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Add `PasswordReplacementPort` | Adds one boundary but prevents admin capability leakage | Selected; consumer-owned and provider-neutral |
| Reuse `IdentityProviderPort.update_password` | Small diff, but cannot express current-password/session invariants | Rejected |
| Native vs composed provider flow | Native is simpler; either may vary by provider configuration | Gate both in order; select none without proof |
| Map provider messages | Brittle and may leak details | Use stable SDK status/code fields; narrowly recognize policy/current-password classes, default to `ProviderUnavailable` |
| Preserve 204 then `/auth/me` revalidation | Returning a session/body or requiring a new token would break the current client flow | Keep the empty 204 and prove immediate `/auth/me` success with the original bearer |

## Data Flow and Responsibilities

    POST password-change → use case → replacement port → selected adapter
                                  └─ activate + audit ← success only
    empty 204 → existing client revalidate → GET /auth/me (same bearer)
                                      └──────→ 200, next_step: load_access

- **Port**: `replace_required_password(subject, session_id, current_password, new_password) -> None`; guarantees verified current credential and preservation of the supplied original provider session within its remaining duration; exposes only typed application errors.
- **Application**: validates state and differing passwords, calls the port first, and saves/audits only on success. It never retries another mechanism.
- **Adapter**: binds the selected, gate-proven provider operation to the authenticated original session; emits no session/token result and does not independently calculate, configure, restart, extend, rotate, or substitute its provider-configured duration; maps stable provider classifications and redacts raw payloads.
- **HTTP**: keep `WeakPassword` at 422; add safe `CurrentPasswordRejected` at 401; unknown failures remain `ProviderUnavailable` at 503. Success stays bodyless 204 and returns/installs no session, preserving same-bearer `/auth/me` revalidation. Responses and logs remain secret-safe.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/src/auth/ports/password_replacement.py` | Create | Narrow self-service contract |
| `backend/src/auth/adapters/identity_provider/password_replacement.py` | Create | Gate-selected adapter and typed mapping |
| `backend/src/auth/application/change_required_password.py` | Modify | Provider-first call; success-only activation/audit |
| `backend/src/auth/domain/errors.py` | Modify | Add current-password rejection |
| `backend/src/auth/adapters/http/error_handlers.py` | Modify | Safe 401 mapping |
| `backend/src/auth/adapters/http/user_router.py` | Verify | Preserve bodyless 204 and existing `/auth/me` contract; no response-model change |
| `backend/src/bootstrap/auth_dependency.py` | Modify | Wire selected adapter only after gate approval |
| `backend/tests/auth/{application,adapters,api}/` | Modify | F-1/F-2, no-side-effect, and 204→same-bearer `/auth/me` contract tests |
| `backend/integration_tests/test_provider_password_replacement.py` | Create | Credential-safe local/target capability gate |
| `backend/integration_tests/test_auth_lifecycle_local_supabase.py` | Modify | API success, immediate `/auth/me` revalidation, and original-session continuity |

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Typed policy/current rejection; unknown errors; no save/audit/version/status change | Fakes plus SDK-shaped errors; retain RED characterizations until each slice turns green |
| API | 422 weak, 401 wrong current, 503 unknown; success is empty 204 followed by same-client `GET /auth/me` returning 200 and `next_step: load_access` | Extend the existing FastAPI `unittest` endpoint test; assert no replacement token/session is returned or required |
| Integration | Gate, lifecycle, and revalidation compatibility | With a disposable identity, assert original-bearer POST yields empty 204, then `/api/v1/auth/me` yields 200 active/load-access before proving continuity only within the original provider session's remaining duration from the originating login; record safe evidence locally and target-equivalently |

## Chained Work Units and Rollback

Under auto-chain and the 400-line budget: (1) F-1 mapping/tests; (2) port and rejection semantics/tests; (3) safe gate harness/evidence; (4) selected adapter, wiring, 204→`/auth/me` and lifecycle proof. Each slice is tested and independently revertible. Slice 4 requires a selection from slice 3. Roll back slice 4 wiring/adapter together, retain RED gates, and do not change frontend/provider configuration. No migration or RLS change is required.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is changed.

## Open Questions

- [ ] Which candidate, if any, passes every local and target-equivalent gate assertion?
