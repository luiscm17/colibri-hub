# Apply Progress: Remediate Mandatory Password Replacement

## Delivery Context

- Delivery strategy: `auto-chain`
- Chain strategy: `feature-branch-chain`
- Completed work unit: PR 3 — F-2/F-3 capability eligibility proof.
- Current work unit: PR 4 — selected capability, sign-out transition, and lifecycle wiring.
- PR boundary: the gate-selected composed Supabase replacement adapter, bootstrap port wiring, post-204 frontend sign-out, and lifecycle evidence only. Provider configuration and native attempt state remain unchanged.
- Strict TDD mode: No — OpenSpec sets `strict_tdd: false` and `rules.apply.tdd: false`.

## Completed Tasks

- [x] 1.1–1.3 F-1 typed weak-password mapping and verification.
- [x] 2.1–2.3 F-2 self-service rejection boundary and verification.
- [x] 3.1 RED disposable-identity local capability gate.
- [x] 3.2 GREEN credential-safe local gate evidence.
- [x] 3.3 PR 4 eligibility gate.

## Work Unit Evidence

| Evidence | Result |
|---|---|
| PR 1 focused test | `uv run --locked --package backend python -m unittest backend.tests.auth.adapters.test_auth_adapter_provider -v` — exit 0; 21 passed. |
| PR 1 runtime harness | N/A — SDK-shaped adapter classification only. |
| PR 1 rollback boundary | F-1 adapter/error tests and mapping only. |
| PR 2 focused test | `uv run --locked --package backend python -m unittest backend.tests.auth.application.test_auth_application.TestChangeRequiredPassword backend.tests.auth.api.test_auth_endpoints.TestPasswordChangeEndpoint -v` — exit 0; 9 passed. Auth discovery: 135 passed. Full backend discovery: 283 passed. |
| PR 2 runtime harness | N/A — no provider capability was selected before PR 3. |
| PR 2 rollback boundary | Password-replacement port, use case, errors, HTTP mapping, constructors, and PR-2 tests. |
| PR 3 focused test | `set -a; source backend/.env; set +a; uv run --locked --package backend python -m unittest backend.integration_tests.test_provider_password_replacement -v` — exit 0; 1 passed. |
| PR 3 static validation | `uv run --locked --package backend ruff check backend/integration_tests/test_provider_password_replacement.py` — exit 0, `All checks passed!`; `uv run --locked --package backend pyright backend/integration_tests/test_provider_password_replacement.py` — exit 0, 0 errors/warnings/informations; `git diff --check -- backend/integration_tests/test_provider_password_replacement.py` — exit 0. |
| PR 3 runtime harness | Disposable local identity completed wrong-current rejection and no-side-effect preservation; correct-current replacement; old-password rejection; terminated prior bearer; fresh new-password login; and subject-matched access eligibility. Safe summary contained only booleans/classification. |
| PR 3 rollback boundary | Revert only `backend/integration_tests/test_provider_password_replacement.py`; production behavior, provider configuration, native attempt state, and PR 4 remain untouched. |
| PR 4 focused test | `set -a; source backend/.env; set +a; TEST_DATABASE_URL="$TEST_DATABASE_URL" uv run --locked --package backend python -m unittest backend.tests.auth.api.test_auth_endpoints.TestPasswordChangeEndpoint backend.integration_tests.test_auth_lifecycle_local_supabase -v` — exit 0; 7 passed. It proves safe wrong-current rejection, bodyless 204, correct replacement, old-password rejection, terminated prior bearer, fresh login, and `load_access` eligibility. |
| PR 4 unit suite | `uv run --locked --package backend python -m unittest discover -s backend/tests -v` — exit 0; 283 passed. |
| PR 4 frontend validation | `pnpm lint && pnpm build` from `frontend/` — exit 0. |
| PR 4 static validation | Targeted Ruff and Pyright for changed backend files — exit 0; `git diff --check` — exit 0. Repository-wide Ruff remains pre-existing failing (91 unrelated findings). |
| PR 4 runtime harness | The focused guarded local harness passed using `backend/.env` without emitting credentials, tokens, or session IDs. The full guarded integration discovery was run but exit 1 due to unrelated pre-existing state/tests: two Access fixtures and the pre-existing modified `test_provider_session_persistence` RED assertion. |
| PR 4 rollback boundary | Revert `backend/src/auth/adapters/identity_provider/password_replacement.py`, `backend/src/auth/ports/password_replacement.py`, `backend/src/bootstrap/auth_dependency.py`, `backend/integration_tests/test_auth_lifecycle_local_supabase.py`, and `frontend/src/features/auth/pages/MandatoryPasswordChangePage.tsx` together. |
| PR 4 session-persistence characterization | `set -a; source backend/.env; set +a; TEST_DATABASE_URL="$TEST_DATABASE_URL" uv run --locked --package backend python -m unittest backend.integration_tests.test_provider_session_persistence -v` — exit 0; 2 passed. The corrected test proves wrong-current rejection, original-bearer termination after replacement, old-password rejection, and fresh new-password sign-in. |
| PR 4 session-persistence static validation | `uv run --locked --package backend ruff check backend/integration_tests/test_provider_session_persistence.py` — exit 0; `uv run --locked --package backend pyright backend/integration_tests/test_provider_session_persistence.py` — exit 0, 0 errors/warnings/informations; `git diff --check -- backend/integration_tests/test_provider_session_persistence.py` — exit 0. |
| PR 4 session-persistence runtime harness | Full guarded discovery: `TEST_DATABASE_URL="$TEST_DATABASE_URL" uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v` — exit 1; 45 run, 2 errors, both in externally tracked Access fixtures. The corrected provider-session module passed. |
| PR 4 session-persistence rollback boundary | Revert only `backend/integration_tests/test_provider_session_persistence.py`; this restores the prior characterization without changing Auth behavior or external Access fixtures. |

## Gate Result

- Gate-selected capability: locally proven native authenticated update flow for eligibility evidence only; no production selection or wiring was applied.
- Local eligibility: **eligible**. All required assertions passed with `provider_failure_classification=none` and disposable cleanup succeeded.
- PR 4 gate: **unblocked for a separately authorized PR 4 slice**. This correction does not start PR 4 or alter fallback policy.

## Correction Record

- Maintainer authority token: `sha256:0b34b268f82a42681ecc59f0591a3dc949b76e015840240ad679e968fd881a4f`.
- Gate source SHA-256 after correction: `sha256:9c7ad12920f566c4b26f2a418e7576dc75899c3bd72ce1c0dca16f4e32353a6e`.
- Correction: removed the invalid `UserResponse.session` assumption from the `update_user` result. Session termination remains independently proved later through sign-out and rejected prior bearer.
- No credential, token, session identifier, or raw provider payload was emitted. `backend/.env` was sourced only for the gated command.
- At the PR 3 correction, native attempt state was not acquired, settled, reset, or modified; provider configuration and fallback policy remain unchanged. No commit, push, or PR was created.

## PR 4 Attempt Record

- Maintainer authority token: `sha256:52ba05feb75b76a9d1d6a055a795876893049e14a145d94155332335fb3ec960`.
- Gate-selected implementation: a composed disposable reauthentication verifies the submitted current password, performs provider-native replacement, verifies provider termination of the original session, and exposes no administrative password-update fallback.
- The successful HTTP transition remains bodyless 204. The frontend then clears local provider state by invoking `logout`, which routes the user to sign-in; Access becomes eligible only after fresh login.
- Gate source SHA-256 is unchanged: `sha256:9c7ad12920f566c4b26f2a418e7576dc75899c3bd72ce1c0dca16f4e32353a6e`.
- Full guarded integration settlement remains blocked by two externally tracked Access fixture failures; the corrected provider-session characterization now passes. No native configuration/state reset, commit, push, or PR was performed.

## PR 4 Characterization Correction

- Maintainer authority token: `sha256:1352898a72244d909f5c39433f3adcd9c3394186e6283e455ca9aa21f9ce024a`.
- Replaced the stale native `update_user(..., current_password=...)` RED expectation with the selected `SupabasePasswordReplacementAdapter` contract: wrong-current rejection, correct-current replacement, original bearer rejection, old-password rejection, and fresh new-password login.
- The focused module passed 2 tests. Full guarded discovery ran 45 tests and now fails only on the two external Access fixtures; no Access fixture, migration, issue, provider configuration, or native runtime attempt state was changed.
- Tasks 4.1–4.3 remain unchecked until the full guarded integration suite is green.

## Remaining Tasks

- [ ] 4.1–4.3 selected capability and lifecycle wiring — implementation and focused evidence are complete, but the required full guarded integration suite is not green.

## Settlement Recommendation

Settle PR 3 as **passed/eligible** and preserve its credential-safe local evidence. Hold PR 4 as **verification-blocked** until the pre-existing integration failures are settled without changing native state; retain the no-fallback policy.
