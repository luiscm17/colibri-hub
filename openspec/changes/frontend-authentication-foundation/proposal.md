# Proposal: Frontend Authentication Foundation

## Intent

Replace the 100% mock frontend authentication with real Supabase session management and backend account-state validation. The app currently has no identity verification — any user sees all content with a fake 400ms login. This change establishes the session lifecycle (login → restore → refresh → expiry → logout) and the mandatory password-change gate required before Access Control can be layered.

## Scope

### In Scope

- Supabase client initialization with env config
- Email/password login via `signInWithPassword`
- Session restore + `/auth/me` backend validation
- 5-state discriminated-union state machine (`initializing | unauthenticated | password-change-required | authenticated | unavailable`)
- Mandatory password change page and flow
- Logout sequence (DELETE /session → signOut → clear state)
- Bearer token injection via module-level async accessor
- httpClient expansion (DELETE method, auth header)
- Route boundaries: `AuthenticationBoundary`, `UnauthenticatedOnly`, `PasswordChangeOnly`, `AuthenticatedOnly`
- Session expired dialog
- Provider event subscription (refresh/expiry)
- `.env.example` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`

### Out of Scope

- `AccessProvider`, `/access/me`, permission-based navigation
- `isResourceAllowed()` (stub/defer to Access Control change)
- Admin account CRUD pages (list, detail, create, audit)
- Role selection in provisioning
- Test framework setup (no test runner configured)
- Vite proxy configuration (operational concern, not auth logic)

## Capabilities

### New Capabilities

- `frontend-authentication`: Supabase session lifecycle, state machine, route boundaries, and authenticated HTTP client integration

### Modified Capabilities

- None (no existing `openspec/specs/` capabilities defined)

## Approach

Single `AuthProvider` with `useReducer` state machine + module-level token accessor.

1. **Provider layer** — `supabaseClient.ts` initializes the SDK; `providerSession.ts` wraps event subscription
2. **Model** — `authenticationState.ts` defines the 5-state discriminated union
3. **httpClient** — Add DELETE support + async `getAccessToken` accessor injected at module level
4. **API layer** — `authApi.ts` for `/auth/me`, `/auth/password-change`, `/auth/session`
5. **Context** — Rewrite `AuthProvider` with reducer, Supabase events, and `/auth/me` validation
6. **Boundaries** — Four route guard components consuming `authState.status`
7. **Pages** — Rewrite `LoginPage` for real login; add `MandatoryPasswordChangePage`
8. **Integration** — Update routes, `AppLayout`, navigation

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/features/auth/provider/` | New | Supabase client + session adapter |
| `frontend/src/features/auth/model/` | New | State machine types |
| `frontend/src/features/auth/api/` | New | Backend auth API calls |
| `frontend/src/features/auth/context/` | Modified | Rewrite with useReducer state machine |
| `frontend/src/features/auth/components/` | New | Route boundaries + SessionExpiredDialog |
| `frontend/src/features/auth/pages/` | Modified | Rewrite LoginPage + add MandatoryPasswordChangePage |
| `frontend/src/features/auth/hooks/` | New | `useAuth.ts` hook |
| `frontend/src/api/httpClient.ts` | Modified | Add DELETE, auth header injection |
| `frontend/src/app/` | Modified | Route definitions + AppLayout integration |
| `frontend/.env.example` | New | Supabase env vars |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Missing `.env` vars crash at runtime | High | `.env.example` + clear error on missing config |
| httpClient changes break warehouse calls | Medium | Backward-compatible expansion; existing calls unchanged |
| `isResourceAllowed` consumers break | Medium | Stub returning `true` until Access Control change |
| No automated tests verify state machine | High | Manual verification + defer test framework to separate change |
| Session restore shows blank during `/auth/me` | Low | `initializing` state renders loading UI |

## Rollback Plan

Revert the branch (`front/authentication-foundation`). The mock auth still exists in main; Supabase client is a new dependency with no backend migration required. Rollback is a single `git revert` of the squash-merged PR.

## Dependencies

- User must install: `pnpm add @supabase/supabase-js`
- Local Supabase must be running (`pnpm supabase start`)
- Backend auth endpoints already merged to main

## Success Criteria

- [ ] Login with real email/password authenticates through Supabase + backend validation
- [ ] Session restore on refresh validates against `/auth/me` before showing content
- [ ] Provisional accounts are routed exclusively to password change
- [ ] Logout clears provider session, auth state, and bearer token
- [ ] Protected routes are inaccessible without active authentication
- [ ] httpClient attaches bearer token without token leaking to components
- [ ] Existing warehouse API calls continue working unchanged

## Proposal Question Round

Before finalizing scope, the following product questions would strengthen the proposal:

1. **Session expiry UX** — When the session expires mid-work, should we show a dialog with "Session expired, please log in again" and redirect, or attempt a silent re-authentication first? The tech spec says "at most one controlled revalidation attempt" — is that the desired UX for all cases?

2. **Loading state during initialization** — Should the app show a branded splash/loading screen during `initializing` (session restore + /auth/me), or is a simple spinner sufficient? This affects whether we need a dedicated loading component.

3. **`isResourceAllowed` stub behavior** — The current `AppLayout` calls `isResourceAllowed()`. Should the stub always return `true` (show everything until Access Control lands), or should it hide admin-only navigation items by default?

4. **Password change success feedback** — After mandatory password replacement succeeds, should we show a brief success notification before redirecting to the app, or redirect immediately?

5. **Concurrent tab behavior** — If a user logs out in one tab, should other tabs detect this and clear state immediately (via Supabase's cross-tab events), or only on next API call?

### Assumptions (pending user confirmation)

- Session expiry shows a dialog + redirect (no silent retry beyond the single revalidation attempt)
- Simple loading spinner during initialization (no branded splash needed)
- `isResourceAllowed` stub returns `true` — all nav items visible until Access Control
- Immediate redirect after password change (no intermediate success screen)
- Cross-tab logout detection via Supabase provider events is in scope
