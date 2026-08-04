# Exploration: Frontend Authentication Foundation

## Current State

The frontend auth is entirely mocked:
- `AuthContext.tsx` uses `setTimeout(400ms)` to fake login; stores a hardcoded `User` in state
- `auth-context.ts` defines context shape: `user | null`, `isAuthenticated`, `login(username, password)`, `logout()`, `isResourceAllowed()`
- `ProtectedRoute.tsx` checks `isAuthenticated` boolean, redirects to `/login`
- `LoginPage.tsx` collects username/password, calls mock `login()`, navigates on success
- No `@supabase/supabase-js` installed; no env vars defined; no `.env` file in frontend
- `httpClient.ts` supports only GET/POST (no DELETE/PUT/PATCH), no auth header injection, uses relative `/api/v1` prefix
- No Vite proxy configured — frontend relies on same-origin or external reverse proxy for API routing
- `AppLayout.tsx` and `ProfilePage.tsx` consume `useAuth()` for user display and logout
- No state machine — binary authenticated/unauthenticated only

## Key Decisions

**D1: httpClient token injection** — Module-level async accessor; centralized bearer without leaking tokens to components.

**D2: httpClient method expansion** — Current client only supports GET/POST. Must add DELETE (logout) and generic method support.

**D3: AuthProvider architecture** — Single context with `useReducer` state machine (5 discriminated-union states). No external state library.

**D4: Route boundaries** — Replace single `ProtectedRoute` with: AuthenticationBoundary, UnauthenticatedOnly, PasswordChangeOnly, AuthenticatedOnly.

**D5: Environment** — Need `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in new `frontend/.env.example`.

## Scope Boundary

### In Scope (this change)

- Supabase client initialization
- Login with `signInWithPassword`
- Session restore + `/auth/me` validation
- State machine (5 states: initializing, unauthenticated, password-change-required, authenticated, unavailable)
- Mandatory password change flow
- Logout (DELETE /session + signOut + state clear)
- Bearer token injection in httpClient
- Route boundaries (AuthenticationBoundary, UnauthenticatedOnly, PasswordChangeOnly, AuthenticatedOnly)
- Session expiry handling
- Environment setup (.env.example)

### Out of Scope (Access Control — separate change)

- `AccessProvider` and `/access/me` bootstrap
- Permission-based route visibility
- `isResourceAllowed()` logic (currently in AuthContext — will be moved)
- Admin account CRUD pages (AccountListPage, AccountDetailPage, etc.)
- Role selection in provisioning
- Navigation driven by effective permissions
- `AuthenticationAuditPage`

## Approaches Considered

### AuthProvider Architecture

| Approach | Pros | Cons | Complexity |
|----------|------|------|------------|
| **Single context + useReducer state machine** | Simple model; one subscription; matches spec; one re-render tree | Larger provider file; all consumers re-render on any change | Medium |
| **Split state/actions contexts** | Granular re-render; stable action refs | More complexity; premature optimization; two contexts to test | Medium-High |
| **External state machine (XState)** | Formal guarantees; devtools | New dep; breaks convention; overkill for 5 states | High |

### httpClient Token Strategy

| Approach | Pros | Cons | Complexity |
|----------|------|------|------------|
| **Module-level accessor ref** | Zero dep; simple; matches spec's "narrow async accessor" | Module-level mutable (acceptable singleton) | Low |
| **Factory/class wrapper** | Testable with DI; no globals | Breaks current call-site ergonomics; over-engineered | Medium |

## Recommendation

**Single AuthContext with `useReducer` state machine + module-level token accessor.**

1. App follows "hooks + React context only" — no external state libraries
2. Five states is trivial with a discriminated union + `useReducer`
3. Module-level accessor is simplest path satisfying "centralized bearer without token in components"
4. Consumer surface is small (4 components) — re-render concerns negligible
5. Route boundaries are pure consumers of `authState.status`

## Implementation Sequence

1. Install `@supabase/supabase-js`, create `.env.example`
2. Create `provider/supabaseClient.ts` + `model/authenticationState.ts`
3. Expand httpClient (DELETE method + token accessor)
4. Create `api/authApi.ts` (me, password-change, session)
5. Rewrite `AuthProvider` with state machine + Supabase events
6. Create route boundaries
7. Rewrite `LoginPage` for email + Supabase
8. Create `MandatoryPasswordChangePage`
9. Update routes, AppLayout, ProfilePage

## Risks

- No frontend `.env` exists — missing vars = runtime crash at Supabase client init
- Vite proxy not configured for `/api/v1` in dev — may need `server.proxy` config
- httpClient expansion must stay backward-compatible for existing warehouse calls
- No test framework — state machine ships without automated verification
- Session restoration UX — if `/auth/me` is slow, users see blank; needs loading state
- `isResourceAllowed` coupling — currently in AuthContext, consumed by AppLayout; must stub or defer to Access Control

## Ready for Proposal

Yes — the tech spec is authoritative, scope boundary is clear, and the recommended approach is well-defined.
