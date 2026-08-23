# Apply Progress: Remediate Mandatory Password Replacement

## Delivery Context

- Delivery strategy: `auto-chain`
- Chain strategy: `feature-branch-chain`
- Completed work unit: PR 3 — F-2/F-3 capability eligibility proof.
- PR boundary: controlled local Supabase Auth gate only. No selected capability, production adapter, bootstrap wiring, lifecycle API work, provider configuration, native attempt-state change, or PR 4 work was changed.
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

## Gate Result

- Gate-selected capability: locally proven native authenticated update flow for eligibility evidence only; no production selection or wiring was applied.
- Local eligibility: **eligible**. All required assertions passed with `provider_failure_classification=none` and disposable cleanup succeeded.
- PR 4 gate: **unblocked for a separately authorized PR 4 slice**. This correction does not start PR 4 or alter fallback policy.

## Correction Record

- Maintainer authority token: `sha256:0b34b268f82a42681ecc59f0591a3dc949b76e015840240ad679e968fd881a4f`.
- Gate source SHA-256 after correction: `sha256:9c7ad12920f566c4b26f2a418e7576dc75899c3bd72ce1c0dca16f4e32353a6e`.
- Correction: removed the invalid `UserResponse.session` assumption from the `update_user` result. Session termination remains independently proved later through sign-out and rejected prior bearer.
- No credential, token, session identifier, or raw provider payload was emitted. `backend/.env` was sourced only for the gated command.
- Native attempt state was not acquired, settled, reset, or modified. No provider configuration, production code, fallback policy, PR 4 file, commit, push, or PR changed.

## Remaining Tasks

- [ ] 4.1–4.3 selected capability and lifecycle wiring — now eligible for a separately authorized PR 4 slice.

## Settlement Recommendation

Settle PR 3 as **passed/eligible** and preserve this credential-safe local evidence. Authorize PR 4 only as its independent feature-branch-chain slice; retain the no-fallback policy.
