# Tasks: Remediate Mandatory Password Replacement

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 760–980 |
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
|---|---|---|---|---|---|
| 1 | F-1 typed weak-password mapping | PR 1 | `uv run --locked --package backend python -m unittest backend.tests.auth.adapters.test_auth_adapter_provider -v` | N/A: fake SDK-shaped errors prove mapping | F-1 adapter/error tests |
| 2 | F-2 port and no-side-effect rejection | PR 2 | `uv run --locked --package backend python -m unittest backend.tests.auth -v` | N/A: application/API fakes isolate rejection | port, use case, error handler, tests |
| 3 | F-2/F-3 capability eligibility proof | PR 3 | `TEST_DATABASE_URL=... uv run --locked --package backend python -m unittest backend.integration_tests.test_provider_password_replacement -v` | Disposable identities in locally controlled Supabase Auth development; credential-free session-termination and fresh-login evidence | gate harness and evidence only |
| 4 | Selected capability, sign-out transition, and lifecycle wiring | PR 4 | `TEST_DATABASE_URL=... uv run --locked --package backend python -m unittest backend.integration_tests.test_auth_lifecycle_local_supabase -v` | Empty 204 → terminated bearer → fresh sign-in → `/auth/me`; Access resolves only after fresh authentication | selected adapter, frontend transition, bootstrap wiring, lifecycle tests |

## Phase 1: F-1 Typed Policy Rejection (PR 1)

- [x] 1.1 RED: In `backend/tests/auth/adapters/test_auth_adapter_provider.py`, preserve/add SDK-shaped weak-policy and non-policy failure characterizations: 422 `WeakPassword`, no activation, and no 204.
- [x] 1.2 GREEN: In `backend/src/auth/adapters/identity_provider/admin_client.py` and `backend/src/auth/domain/errors.py`, classify only stable policy code/status as `WeakPassword`; redact raw provider payloads and map unknown failures to `ProviderUnavailable`.
- [x] 1.3 Verify the focused adapter tests, then the full backend unit suite; retain F-2/F-3 RED characterizations.

## Phase 2: F-2 Self-Service Rejection Boundary (PR 2)

- [x] 2.1 RED: In `backend/tests/auth/application/` and `backend/tests/auth/api/test_auth_endpoints.py`, assert wrong-current returns safe 401 with unchanged credential, status, version, success audit, and no session/token response.
- [x] 2.2 GREEN: Create `backend/src/auth/ports/password_replacement.py`; update `change_required_password.py` to call it before activation/audit and never retry or use admin/recovery/auth-schema/session fallback.
- [x] 2.3 GREEN: Add `CurrentPasswordRejected` in `backend/src/auth/domain/errors.py` and its safe 401 mapping in `backend/src/auth/adapters/http/error_handlers.py`; verify `user_router.py` remains bodyless 204.

## Phase 3: Required Capability Gate (PR 3)

- [x] 3.1 RED: Retain `backend/integration_tests/test_provider_password_replacement.py` as the disposable-identity gate; revise its required assertions to fail eligibility for skipped, unavailable, or failed wrong-current rejection, no-side-effect preservation, old-login failure, fresh new-login success, replacement-session termination, or deferred Access resolution. Record no credentials, tokens, session IDs, or raw provider payloads.
- [x] 3.2 GREEN: Implement credential-free gate evidence against locally controlled Supabase Auth development; record classifications/booleans only, never secrets, tokens, session IDs, or raw payloads. No remote or target-equivalent provider configuration is required.
- [x] 3.3 Gate PR 4: do not apply slice 4 unless every locally controlled Supabase Auth assertion passes; otherwise leave replacement unselected with no prohibited fallback.

## Phase 4: F-2/F-3 Selected Capability and Lifecycle (PR 4)

- [ ] 4.1 RED: Extend `backend/integration_tests/test_auth_lifecycle_local_supabase.py` for correct-current success, old-password failure, replacement-session termination, new-password fresh-login success, account activation only after provider success, and Access resolution only after subsequent authentication.
- [ ] 4.2 GREEN: Create `backend/src/auth/adapters/identity_provider/password_replacement.py` only for the gate-selected capability, wire it in `backend/src/bootstrap/auth_dependency.py`, and update the frontend to clear authentication state and route to sign-in after successful replacement.
- [ ] 4.3 Verify `POST /api/v1/auth/password-change` stays empty 204, the prior bearer is rejected, and a fresh new-password sign-in followed by `GET /api/v1/auth/me` returns 200 with `next_step: "load_access"`; run full units and guarded integrations.
