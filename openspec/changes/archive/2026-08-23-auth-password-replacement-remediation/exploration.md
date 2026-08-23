## Exploration: auth-password-replacement-remediation

### Current State
Authentication owns credentials, account state, and sessions; Access Control remains downstream. `ChangeRequiredPassword` accepts `current_password`, rejects only when it equals `new_password`, then calls the administrative `IdentityProviderPort.update_password(subject, new_password)`. The adapter implements that operation with service-role `auth.admin.update_user_by_id`, which has no current-password input and therefore cannot enforce the submitted secret. Activation, version persistence, and the success audit occur after that provider call.

The provider error mapper is message-based. Its weak-password predicate recognizes `weak` or `password` plus `short`, but the installed SDK-shaped GoTrue message `Password should be at least 6 characters.` is classified as `ProviderUnavailable`. The local provider configuration has an eight-character minimum and `secure_password_change = false`; neither setting proves a safe self-service replacement capability.

The retained red characterizations are executable starting evidence, not regressions: F-1 proves the representative weak-password error maps to 503 instead of `WeakPassword`/422; F-2 proves wrong-current-password acceptance with credential-update invocation, activation, version change, and success audit; the guarded provider proof shows the available authenticated `update_user` operation accepts the wrong `current_password`. F-3 browser evidence establishes that the original session is unavailable after replacement and `/auth/me` returns 401, while the account becomes Active; the PRD requires the original eight-hour timebox to continue. F-4 is excluded.

### Affected Areas
- `backend/src/auth/application/change_required_password.py` — replace the unsafe administrative self-service path and preserve provider-first/no-side-effects ordering.
- `backend/src/auth/ports/identity_provider.py` — define a provider-neutral self-service replacement capability, distinct from administrative reset/update operations; retain session/timebox semantics in the contract.
- `backend/src/auth/adapters/identity_provider/admin_client.py` — implement the selected provider capability and typed error mapping without exposing SDK types, secrets, or raw provider messages.
- `backend/src/auth/adapters/http/models.py`, `backend/src/auth/adapters/http/user_router.py`, and `backend/src/bootstrap/auth_dependency.py` — adjust only if the selected provider flow needs authenticated user-context/session data; preserve the canonical 204 response unless design proves otherwise.
- `backend/tests/auth/application/test_auth_application.py` — turn the F-2 characterization into rejection/no-mutation/no-audit coverage and add successful replacement ordering coverage.
- `backend/tests/auth/adapters/test_auth_adapter_provider.py` — prove F-1 mapping against the SDK-shaped error and the selected provider operation's request/response translation.
- `backend/integration_tests/test_provider_session_persistence.py` and related lifecycle tests — guarded disposable-identity proof for current-password rejection, old-password failure, new-password success, original session usability, and unchanged eight-hour expiration.
- `supabase/config.toml` / deployment configuration — verify provider capability and secure-password-change settings; do not change configuration speculatively or commit secrets.
- `docs/prd/auth.md` — normative constraints are already present: rules 14–16, 25–26, 33–34 and acceptance criteria 8, 12–14. No PRD change is justified by this exploration.

### Confirmed Constraints and Provider Options
The provider options must be tested with generated credentials only and no secret/token logging:

1. **Current administrative update** (`admin.update_user_by_id`) — confirmed available, but unsuitable: it cannot verify `current_password` and may alter session state in a way that violates F-3.
2. **Authenticated `update_user` with `current_password` / reauthentication** — documented as the intended user-context capability, but rejected by the current guarded local provider when `secure_password_change` is false. It remains a candidate only after capability/configuration verification in the target deployment; enabling the setting is a deliberate provider/configuration decision, not an assumed fix.
3. **Reauthenticate/sign in with the current password, then perform a user-context update** — potentially available as a composed provider flow, but must prove that the original session remains usable, the eight-hour origin is not restarted, and the old credential fails. It also introduces session/race/error-handling complexity and must not persist or log the temporary verification session.
4. **Backend-controlled password verification or direct provider database manipulation** — not acceptable as the default direction: it would couple application policy to provider internals, risk secret exposure, and undermine the provider's password hashing/session invariants. Consider only if official provider capabilities cannot satisfy the contract and security review explicitly authorizes it.

### Approaches
1. **Provider-native authenticated self-service replacement** — add a distinct port operation that verifies the current credential in user context and changes the password without creating a replacement session; configure/verify the provider's secure-password-change behavior where required.
   - Pros: honors the trust boundary, keeps provider password/session policy authoritative, directly addresses F-2 and F-3, preserves hexagonal dependency direction.
   - Cons: local configuration currently disables the relevant protection; exact SDK/provider behavior and session continuity require guarded integration proof; may require a deployment setting change.
   - Effort: Medium

2. **Reauthentication followed by a controlled user-context update** — verify current credentials through a provider login/reauthentication operation, then update using the authenticated context while retaining the original application session contract.
   - Pros: may work when a single current-password update endpoint is ineffective; uses public provider operations rather than admin SQL.
   - Cons: session identity and timebox continuity are difficult to guarantee; creates a multi-step failure/race surface; must never substitute a fresh session for the original one.
   - Effort: High

3. **Keep administrative update and remove current-password verification from the contract** — treat the endpoint as an administrative reset-like operation.
   - Pros: smallest code change.
   - Cons: contradicts the existing UI/PRD contract, weakens security, and does not remediate F-2/F-3. Not viable without an explicit product/security decision to change scope.
   - Effort: Low, but unacceptable for this change

### Recommendation
Proceed to proposal/design with Approach 1 as the target, but make implementation conditional on a narrow capability gate: prove the exact provider operation in the local and target-equivalent configuration before selecting it. If the native operation cannot both reject a wrong current password and preserve the original session/timebox, evaluate Approach 2; do not fall back to the administrative update or manufacture a replacement session. Keep administrative reset/enable flows separate from self-service mandatory replacement.

Include F-1 in the same change as a small, evidence-backed adapter mapping correction. Prefer structured SDK/provider category or code mapping; retain only a narrow safe message fallback if the installed SDK exposes no stable category. F-4 remains out of scope.

### Test Strategy
- Preserve the existing intentional red tests until each behavior is implemented; do not weaken or delete assertions.
- Unit: weak-password category/message mapping; wrong-current-password rejection; no provider mutation, account activation, version change, or success audit on rejection; provider-first ordering and typed safe errors.
- API: wrong current password returns the domain's validation/authentication response, leaves the account awaiting replacement, and never returns success; successful replacement keeps 204 and the existing revalidation contract unless deliberately redesigned.
- Guarded integration: disposable identity only; prove wrong current rejection, old-password failure, replacement-password success, original session remains usable, and expiry remains anchored to the original login. Record only classifications and booleans, never credentials/tokens.
- Regression: run focused auth unit/API suites, then the full backend unit suite and guarded integration suite when the local provider is available. Frontend behavior remains unchanged and is not the authority for these rules.

### Delivery Slices
The forecast crosses multiple boundaries (application policy, port, provider adapter/configuration, HTTP composition, and integration evidence), so use chained work units under the 400-line review budget:

1. F-1 typed/structured error mapping plus focused adapter characterization turned green.
2. Self-service provider port/adapter capability and focused unit/API rejection/no-side-effects behavior.
3. Provider configuration/capability integration proof and session/timebox-preserving implementation.
4. Final regression evidence and concise contract/design updates, if needed.

Keep tests with the behavior they verify. Each slice should be independently reviewable, rollback-safe, and record its focused test and runtime-harness result.

### Risks
- The local provider's `secure_password_change = false` may hide or invalidate the documented current-password behavior; changing it can affect other local tests and must be explicit.
- A provider password update may revoke or rotate sessions implicitly; a successful credential change is not sufficient without proving original-session continuity and unchanged expiry.
- Reauthentication composition can accidentally create a new session, leak session material, or restart the timebox.
- Error-message matching is brittle across GoTrue/Supabase versions; structured classification should be preferred and tested against the installed SDK.
- Provider and application operations are not one transaction; provider success followed by local persistence failure needs a bounded recovery/idempotency design.
- Secrets must stay out of logs, audits, fixtures, snapshots, and Engram artifacts.

### Ready for Proposal
Yes. The proposal should define a backend Authentication-only remediation for F-1/F-2/F-3, explicitly exclude F-4, retain the red characterizations as gates, and require provider capability/session-timebox proof before implementation. The design phase must settle the exact native provider operation and whether a safe provider configuration change is necessary; no production behavior is authorized by this exploration alone.

### Skill Resolution
- `supabase` — applied; provider documentation/configuration claims are separated from guarded local evidence, with no secrets exposed.
- `arch-hexagonal-ddd` — applied; the recommendation preserves Authentication ownership and keeps provider details behind a cohesive port while separating administrative and self-service operations.
- `cognitive-doc-design` — applied; the artifact leads with current state and decision gates, then uses concise options, tests, slices, and risks.
- `work-unit-commits` — applied; the scope is forecast for chained, behavior-centered slices under the 400-line review budget.
