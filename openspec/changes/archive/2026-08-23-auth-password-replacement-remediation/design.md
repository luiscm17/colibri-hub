# Design: Remediate Mandatory Password Replacement

## Technical Approach

Use a narrow self-service port instead of administrative `update_password`. Select an implementation only after a disposable-identity harness proves it against locally controlled Supabase Auth development. Activate and audit only after provider success. A successful replacement terminates the provider session; the client must clear its authentication state, direct the user to sign in, and resolve Access only after that subsequent authentication. This covers F-1/F-2/F-3 and requires the minimum frontend lifecycle change; it excludes F-4 and administration. No remote or target-equivalent provider configuration is required.

## Provider Capability Gate and Remedy Selection

No candidate is approved today: the local `update_user(... current_password=...)` characterization accepted a wrong password. Documentation examples are not runtime proof.

1. Evaluate native authenticated update first; composed reauthentication second.
2. Record safe pre-state: account status/version and success-audit count; never persist credentials, tokens, or session identifiers.
3. Prove weak-new and wrong-current attempts leave credential, account, audit, and current provider session unchanged.
4. Prove one valid replacement makes old login fail, terminates the replacement session, and permits new-password login; prove no Access Control resolution occurs before that fresh authentication.
5. Run every assertion against locally controlled Supabase Auth development. Any failed, skipped, unavailable, or unobservable assertion blocks selection. Never consider admin update, recovery, or auth-schema writes.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Add `PasswordReplacementPort` | Adds one boundary but prevents admin capability leakage | Selected; consumer-owned and provider-neutral |
| Reuse `IdentityProviderPort.update_password` | Small diff, but cannot express current-password and lifecycle invariants | Rejected |
| Native vs composed provider flow | Native is simpler; either may vary by provider configuration | Gate both in order; select none without proof |
| Map provider messages | Brittle and may leak details | Use stable SDK status/code fields; narrowly recognize policy/current-password classes, default to `ProviderUnavailable` |
| Terminate session then sign in again | Requires an explicit client transition but matches the provider lifecycle contract | Keep bodyless 204; clear client auth state, redirect to sign-in, and resolve Access only after fresh authentication |

## Data Flow and Responsibilities

    POST password-change → use case → replacement port → selected adapter
                                  └─ activate + audit ← success only
    empty 204 → clear client auth state → sign-in with established password
                                      └──────→ GET /auth/me → 200, next_step: load_access

- **Port**: `replace_required_password(subject, session_id, current_password, new_password) -> None`; guarantees verified current credential and session termination after provider-confirmed replacement; exposes only typed application errors.
- **Application**: validates state and differing passwords, calls the port first, and saves/audits only on success. It never retries another mechanism.
- **Adapter**: binds the selected, gate-proven provider operation to the authenticated session, terminates it after provider-confirmed replacement, emits no session/token result, maps stable provider classifications, and redacts raw payloads.
- **HTTP and frontend**: keep `WeakPassword` at 422; add safe `CurrentPasswordRejected` at 401; unknown failures remain `ProviderUnavailable` at 503. Success stays bodyless 204 and returns/installs no session. The frontend clears authentication state and directs the user to sign in. Responses and logs remain secret-safe.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/src/auth/ports/password_replacement.py` | Create | Narrow self-service contract |
| `backend/src/auth/adapters/identity_provider/password_replacement.py` | Create | Gate-selected adapter and typed mapping |
| `backend/src/auth/application/change_required_password.py` | Modify | Provider-first call; success-only activation/audit |
| `backend/src/auth/domain/errors.py` | Modify | Add current-password rejection |
| `backend/src/auth/adapters/http/error_handlers.py` | Modify | Safe 401 mapping |
| `backend/src/auth/adapters/http/user_router.py` | Verify | Preserve bodyless 204 with no session/token response; no response-model change |
| `backend/src/bootstrap/auth_dependency.py` | Modify | Wire selected adapter only after gate approval |
| `backend/tests/auth/{application,adapters,api}/` | Modify | F-1/F-2, no-side-effect, account-activation-after-provider-success, and 204→signed-out contract tests |
| `backend/integration_tests/test_provider_password_replacement.py` | Create | Credential-safe capability gate against locally controlled Supabase Auth development |
| `backend/integration_tests/test_auth_lifecycle_local_supabase.py` | Modify | API success, terminated-session rejection, fresh login, and post-login Access resolution |
| `frontend/src/features/auth/` | Modify | Clear client authentication state and route to sign-in after successful replacement |

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Typed policy/current rejection; unknown errors; no save/audit/version/status change | Fakes plus SDK-shaped errors; retain RED characterizations until each slice turns green |
| API | 422 weak, 401 wrong current, 503 unknown; success is empty 204, activation follows provider success, and the prior bearer is rejected | Extend the existing FastAPI `unittest` endpoint test; assert no replacement token/session is returned or required |
| Integration | Gate, lifecycle, fresh-login, and Access-resolution compatibility | With a disposable identity in locally controlled Supabase Auth development, assert the replacement-session bearer yields empty 204 then is rejected; assert a fresh new-password login yields `/api/v1/auth/me` 200 with active/load-access; record credential-free evidence |

## Chained Work Units and Rollback

Under auto-chain and the 400-line budget: (1) F-1 mapping/tests; (2) port and rejection semantics/tests; (3) safe gate harness/evidence; (4) selected adapter, frontend sign-out transition, wiring, fresh-login, and lifecycle proof. Each slice is tested and independently revertible. Slice 4 requires a selection from slice 3. Roll back slice 4 wiring/adapter/frontend transition together, retain RED gates, and do not change provider configuration. No migration or RLS change is required.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is changed.

## Open Questions

- [ ] Which candidate, if any, passes every locally controlled Supabase Auth gate assertion?
