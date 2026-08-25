## Exploration: frontend-authentication-completion

### Current State
The frontend already has the principal Authentication surfaces: provider-backed sign-in, `/auth/me` validation, mandatory password replacement, serialized-looking backend logout intent, Accounts/detail reset and disable interactions, and cursor-based Authentication History. The implementation also has useful local stale-response guards in account detail and History, plus safe clearing of administrative reset secrets.

Comparison with `frontend/docs/features/authentication.md` shows that the remaining work is broader than the prior 40–55% estimate in some areas. The central `AuthProvider` currently validates by an epoch but does not bind a response to a concrete provider session identity or latest login attempt, does not subscribe to the full provider event lifecycle, and can publish `authenticated` for any non-`change_password` response without explicitly enforcing `load_access`. The authentication boundary redirects to a fixed `/login`, losing validated return intent, and the observed route/auth composition does not yet demonstrate Access-aware destination resolution or exactly-once semantic handoff/navigation.

Mandatory replacement clears fields and calls the shared logout path after `204`, but lacks explicit dirty-leave confirmation, safe password-policy feedback, distinct replacement-versus-session-ending recovery, focus recovery, and coverage for provider invalidation or stale submissions. Login has basic required-field and generic denial behavior, but lacks observable latest-submission abandonment, return-intent handling, and focus assertions.

Account administration implements the defined Accounts/detail/reset/disable/History transport surfaces and several confirmation, version, refresh, and conflict-recovery behaviors. The implementation still needs verification against the complete contract for collection invalidation, stale collection/detail publication, nearest-valid navigation and origin restoration, explicit conflict draft separation, last-administrator outcomes, dirty non-secret departure, focus recovery, and account links from History. Existing CodeGraph evidence shows no covering tests for the Authentication context, login, mandatory replacement, or History, while account administration has focused tests.

The scope is limited to the observable Authentication requirements in the frontend specification and its normative Authentication and Access PRDs. Frontend provisioning, re-enablement, and Access account-review flows are explicitly excluded because the current Authentication frontend contract does not define complete frontend obligations for them.

### Affected Areas
- `frontend/src/features/auth/context/AuthContext.tsx` — provider event normalization, session identity/attempt races, `/auth/me` transition publication, logout serialization, and semantic handoff.
- `frontend/src/features/auth/context/auth-context.ts` — Authentication-to-Access semantic contract and any return-intent/session lifecycle contract additions.
- `frontend/src/features/auth/provider/providerSession*` — provider event subscription, restoration, refresh, sign-in, and local sign-out boundary.
- `frontend/src/features/auth/components/AuthenticationBoundary.tsx` and `frontend/src/features/auth/components/AuthenticatedOnly.tsx` — unavailable preservation, mandatory replacement isolation, addressable sign-in, and return-intent-safe routing.
- `frontend/src/app/routes/index.tsx` and `frontend/src/app/layout/AppLayout.tsx` — Access-aware destination resolution, navigation consequences, protected route composition, and logout behavior.
- `frontend/src/features/auth/pages/LoginPage.tsx` — validated return intent, latest-submission handling, draft lifecycle, focus, and generic denial accessibility.
- `frontend/src/features/auth/pages/MandatoryPasswordChangePage.tsx` — restricted experience, policy validation, dirty-leave confirmation, safe failure/recovery, provider invalidation, and focus.
- `frontend/src/features/auth/pages/AuthenticationAccountsPage.tsx` — collection/detail lifecycle, mutation invalidation, confirmations, conflict recovery, navigation, safe drafts, and focus.
- `frontend/src/features/auth/pages/AuthenticationHistoryPage.tsx` — account relationship/navigation and complete cursor-chain state and stale-response coverage.
- `frontend/src/features/auth/api/authApi.ts` and `frontend/src/features/auth/api/authApi.types.ts` — strict response/error normalization and the currently present but out-of-scope provisioning/re-enable declarations that must not be expanded.
- `frontend/src/features/auth/**/*.test.tsx` — missing coverage for session races, handoff, intent, replacement, logout, History, and cross-cutting draft/accessibility contracts.
- `frontend/docs/features/authentication.md` — authoritative observable requirements; no product source or test changes are made during exploration.

### Approaches
1. **Capability-centered completion in bounded work units** — complete the Authentication provider/session contract first, then entry/replacement/logout, then account administration and verification, preserving Access as a semantic consumer rather than importing its internals.
   - Pros: follows existing capability ownership, reduces race and navigation risk before dependent UI work, keeps the Authentication→Access boundary explicit, and fits the 400-line review guard through auto-chained slices.
   - Cons: requires coordinated route and context changes and may expose pre-existing Access integration assumptions.
   - Effort: High

2. **Page-by-page patching** — finish each visible page independently and defer provider/session and navigation semantics.
   - Pros: small local edits and quick visual progress.
   - Cons: cannot reliably satisfy global stale-session, exactly-once handoff, logout, return-intent, or cross-page draft guarantees; risks parallel state authorities and regressions.
   - Effort: High

### Recommendation
Proceed with Approach 1. Treat `AuthProvider` plus the provider boundary as the single session authority, publish only the exact semantic handoff conditions, and make navigation a consequence of published Authentication/Access state. Sequence implementation into auto-chained reviewable slices: session/races and handoff; sign-in/intent/logout; mandatory replacement; Accounts/detail lifecycle; History and cross-cutting verification. Preserve the spec’s `unavailable` behavior, permitted return-intent rule, confirmation/conflict recovery, and secret/draft safety rules. Do not add provisioning, re-enablement, or Access account-review behavior.

### Risks
- Provider SDK event semantics and session identity availability may constrain exact race handling; the adapter must expose only a centralized asynchronous boundary without leaking tokens.
- Access route/destination contracts may be incomplete or distributed, so Authentication must not invent destination policy or bypass Access authorization.
- Logout and password replacement involve backend notification plus provider-local termination; browser JWT expiry limitations must remain accurately represented.
- Account mutation conflict and stale-response behavior can lose safe drafts or show another account if invalidation is not ordered before refresh publication.
- The repository OpenSpec configuration reports frontend tests as unavailable even though frontend Vitest files exist; verification capability must be confirmed before planning claims coverage.

### Ready for Proposal
Yes — the scope, exclusions, architectural boundary, and major implementation slices are clear. The proposal should explicitly state that this is an Authentication frontend contract-completion change, not provisioning or Access account-review work, and should forecast chained delivery under the 400-line review budget.
