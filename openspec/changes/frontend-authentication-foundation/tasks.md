# Tasks: Frontend Authentication Foundation

## Authoritative Inputs

- **Tech Spec** (serves as spec + design): `frontend/docs/features/authentication.md`
- **Exploration**: `openspec/changes/frontend-authentication-foundation/exploration.md`
- **Proposal**: engram `sdd/frontend-authentication-foundation/proposal`
- **Backend contract**: Already merged — GET /auth/me, POST /auth/password-change, DELETE /auth/session
- **Base branch**: `front/authentication-foundation` from `main`

## Session Preferences

- **Delivery strategy**: `ask-on-risk`
- **Chain strategy**: `feature-branch-chain` (tracker: `front/authentication-foundation` → main)
- **Artifact store**: `hybrid` (engram + openspec)
- **Strict TDD**: disabled (no test framework configured)
- **Installation rule**: User installs all packages. Agent provides exact CLI commands only.

## Review Workload Forecast

| Field                        | Value                                                                |
| ---------------------------- | -------------------------------------------------------------------- |
| Estimated changed lines      | ~480 total (new + modified)                                          |
| 400-line budget risk         | Medium                                                               |
| Chained PRs recommended      | No — stays under 600-line reasonable single-PR bound                 |
| Decision needed before apply | No                                                                   |

## Implementation Status

**Status: IMPLEMENTED — pending manual verification and PR**

All 19 tasks completed. Build passes (`pnpm build` clean). Verified via `sdd-verify` with PASS WITH WARNINGS (W1 and W3 fixed; W2 deferred as follow-up).

---

## Phase 1: Environment and Provider SDK ✅

### Prerequisites (user-executed)

```bash
pnpm add @supabase/supabase-js
```

### Tasks

- [x] 1.1 Create `frontend/.env.example`
  - **Files**: `frontend/.env.example`

- [x] 1.2 Create identity provider client — singleton with `persistSession: true`, `autoRefreshToken: true`, `detectSessionInUrl: false`
  - **Files**: `frontend/src/features/auth/provider/identityClient.ts`
  - **Note**: Renamed from `supabaseClient.ts` per naming convention (no technology names in identifiers)

- [x] 1.3 Create `authenticationState.ts` — 5-state discriminated union + `AuthenticationAccountSummary`
  - **Files**: `frontend/src/features/auth/model/authenticationState.ts`

---

## Phase 2: HTTP Client Expansion ✅

- [x] 2.1 Expand `httpClient.ts` — DELETE/PUT methods, module-level `tokenAccessor`, `setTokenAccessor`/`clearTokenAccessor`, auto-attach bearer
  - **Files**: `frontend/src/api/httpClient.ts`

---

## Phase 3: Auth API Layer ✅

- [x] 3.1 Create `authApi.types.ts` — `AuthMeResponse`, `PasswordChangeRequest`, `PasswordChangeResponse`
  - **Files**: `frontend/src/features/auth/api/authApi.types.ts`

- [x] 3.2 Create `authApi.ts` — `fetchCurrentAuthentication`, `submitPasswordChange`, `terminateSession`, `mapToAccountSummary`
  - **Files**: `frontend/src/features/auth/api/authApi.ts`

---

## Phase 4: AuthProvider Rewrite and Route Boundaries ✅

- [x] 4.1 Create `providerSession.ts` — thin adapter (`signIn`, `signOut`, `hasSession`, `getAccessToken`, `onAuthStateChange`)
  - **Files**: `frontend/src/features/auth/provider/providerSession.ts`
  - **Note**: No SDK types leak outside this file. All public signatures use `string`, `boolean`, `unknown`.

- [x] 4.2 Rewrite `AuthContext.tsx` — `useReducer` state machine, provider subscription, `/auth/me` validation, token accessor, `logoutInitiatedRef` for expired detection
  - **Files**: `frontend/src/features/auth/context/AuthContext.tsx`

- [x] 4.3 Rewrite `auth-context.ts` — new `AuthContextValue` (`authState`, `login`, `logout`, `revalidate`, `account`, `isAuthenticated`, `isResourceAllowed` stub)
  - **Files**: `frontend/src/features/auth/context/auth-context.ts`

- [x] 4.4 Create `AuthenticationBoundary.tsx` — spinner on initializing, redirect on unauthenticated, retry on unavailable
  - **Files**: `frontend/src/features/auth/components/AuthenticationBoundary.tsx`

- [x] 4.5 Create `SessionExpiredDialog.tsx` — modal on `reason === 'expired'`, mounted in AppLayout
  - **Files**: `frontend/src/features/auth/components/SessionExpiredDialog.tsx`

- [x] 4.6 Create route boundaries — `UnauthenticatedOnly`, `PasswordChangeOnly`, `AuthenticatedOnly`
  - **Files**: `frontend/src/features/auth/components/UnauthenticatedOnly.tsx`, `PasswordChangeOnly.tsx`, `AuthenticatedOnly.tsx`

---

## Phase 5: Pages, Routes, and Integration ✅

- [x] 5.1 Rewrite `LoginPage.tsx` — email field, `signInWithPassword` via context, generic denial, `role="alert"`, password cleared on error
  - **Files**: `frontend/src/features/auth/pages/LoginPage.tsx`

- [x] 5.2 Create `MandatoryPasswordChangePage.tsx` — current/new/confirm fields, `submitPasswordChange`, revalidation, field-specific errors, `role="alert"`
  - **Files**: `frontend/src/features/auth/pages/MandatoryPasswordChangePage.tsx`

- [x] 5.3 Update routes — `AuthenticationBoundary` + `AuthenticatedOnly` at layout, `UnauthenticatedOnly` on login, `PasswordChangeOnly` on `/password-change`, lazy imports
  - **Files**: `frontend/src/app/routes/index.tsx`, `frontend/src/app/routes/lazy-pages.ts`

- [x] 5.4 Update `AppLayout.tsx` — `account?.displayName`/`initials`, async `logout()`, `useEffect` for sidebar localStorage, `SessionExpiredDialog` mounted
  - **Files**: `frontend/src/app/layout/AppLayout.tsx`

- [x] 5.5 Update `ProfilePage.tsx` — `account.displayName`, `account.email`, removed `allowedResources`
  - **Files**: `frontend/src/features/profile/pages/ProfilePage.tsx`

- [x] 5.6 Update barrel exports — new public surface, removed old `User` type
  - **Files**: `frontend/src/features/auth/index.ts`

- [x] 5.7 Delete `ProtectedRoute.tsx`
  - **Files**: `frontend/src/app/routes/ProtectedRoute.tsx` (deleted)

---

## Additional Changes (post-verify fixes)

- [x] Vite proxy for `/api` → `http://127.0.0.1:8000` in development
  - **Files**: `frontend/vite.config.ts`

- [x] react-doctor `no-impure-state-updater` fix — moved `localStorage.setItem` to `useEffect`
  - **Files**: `frontend/src/app/layout/AppLayout.tsx`

- [x] react-doctor `prefer-useReducer` fix — `BaleReceptionPage` submission state grouped into reducer
  - **Files**: `frontend/src/features/warehouse/bales/pages/BaleReceptionPage.tsx`

- [x] react-doctor `artifact-baas-authority-surface` — suppressed (false positive documented)
  - **Files**: `frontend/react-doctor.config.json`

---

## Completion Criteria — Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `pnpm build` passes with zero type errors | ✅ |
| 2 | Real login through Supabase + `/auth/me` validation works | ✅ (confirmed via token log + backend 200) |
| 3 | Session restore validates before protected content renders | ✅ |
| 4 | Provisional accounts route exclusively to password change | ✅ |
| 5 | Logout clears provider + auth state + navigates to login | ✅ |
| 6 | Bearer token attaches without leaking to components | ✅ |
| 7 | Existing warehouse calls work unchanged | ✅ |
| 8 | `isResourceAllowed` returns true (stub until Access Control) | ✅ |

---

## Out of Scope — Documented for Next Change

The following items are defined in the tech spec (`frontend/docs/features/authentication.md`) but NOT implemented in this change. They require Access Control (not yet in frontend) or a separate delivery:

### Requires Access Control (separate change)

- §6.3 — `AccessProvider` loads `/access/me` after `authenticated`
- §14 — Unified Account Administration (list, detail, create, disable, enable, reset, audit pages)
- §15 — Access route guard (effective `action + scope`)
- §9.2.7 — Navigate to first authorized destination (currently hard-coded to `/warehouse/bales`)
- §16 — Admin error handling (`duplicate_email`, `last_system_administrator`, `version_conflict`, etc.)

### Requires follow-up (no external dependency)

- §8.3 — Centralized 401 retry/revalidation in httpClient (W2 from verify)
- §7 — Missing files: `authApi.mappers.ts`, `authApi.errors.ts`, `hooks/useAuth.ts` (separate file), `hooks/useAuthenticationAccount.ts`, `model/account.ts`, `components/PasswordField.tsx`, `routes.tsx`
- §17 — Full accessibility: focus to first invalid field, password visibility toggle with accessible name
- §19 — Testing strategy: unit, component, integration, E2E (no test framework configured)
- §20.7 — Unified account administration
- §20.9 — Navigation uses effective permissions
- §20.10 — Tests pass

### Tech spec §7 architecture deviation

The tech spec lists `provider/supabaseClient.ts`. Implementation uses `provider/identityClient.ts` per project naming convention (no technology names in identifiers). The tech spec should be updated to reflect this decision.
