# Tasks: Frontend Authentication Completion

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 950–1,250 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Session state and one Access handoff | PR #1 (base: feature/tracker branch) | `pnpm vitest run --reporter=verbose` | Provider-event race then one permitted bootstrap | Auth context, provider adapter, Access controller, route tests |
| 2 | Entry, replacement, and logout | PR #2 (base: PR #1 branch) | `pnpm vitest run --reporter=verbose` | Sign in → replacement/logout | Login/replacement pages, routes, layout, tests |
| 3 | Admin/History recovery | PR #3 (base: PR #2 branch) | `pnpm vitest run --reporter=verbose` | Reset/disable conflict and stale History continuation | Accounts/History pages and tests |

## Phase 1: Session and Access Foundation

- [x] 1.1 RED: In `AuthContext.test.tsx` and `AccessProvider.test.tsx`, prove stale/duplicate provider validations cannot publish identity, bootstrap, or navigate twice; unavailable/replacement clears Access without a request.
- [x] 1.2 Update `providerSession.ts`, `auth-context.ts`, and `AuthContext.tsx` with event/session epochs, current-only `/auth/me`, retry, semantic handoff IDs, and serialized local clearing.
- [x] 1.3 Update `access-controller.ts` and `routes/index.tsx` to consume each eligible handoff once; withhold protected routes for unresolved, ended, replacement, or unavailable states.

## Phase 2: Entry, Replacement, and Logout

- [ ] 2.1 RED: Create `LoginPage.test.tsx` route-intent cases for normalized in-app acceptance; absolute, protocol-relative, auth-loop, malformed, and unpermitted rejection; assert one Access fallback navigation.
- [ ] 2.2 Update `LoginPage.tsx` and `routes/index.tsx` with latest-only submission, generic secret-safe denial, password clearing, associated feedback/focus, and validated non-secret return intent.
- [ ] 2.3 RED: Create `MandatoryPasswordChangePage.test.tsx` for mismatch/different-password validation, dirty leave stay/discard, invalidation, bodyless `204` termination, secret clearing, and no Access handoff.
- [ ] 2.4 Update `MandatoryPasswordChangePage.tsx`, `AuthContext.tsx`, and `AppLayout.tsx` for restricted routing, shared idempotent logout, failure-safe local sign-out, draft clearing, and one sign-in navigation.

## Phase 3: Authentication Administration and History

- [ ] 3.1 RED: Extend `AuthenticationAccountsPage.test.tsx` for latest `expected_version`, one pending reset/disable, `204` invalidation/refresh, conflict secret clearing/reload/reconfirmation, and missing-detail nearest-destination recovery.
- [ ] 3.2 Update `AuthenticationAccountsPage.tsx` with Authentication-only detail, reasoned reversible confirmations, safe draft/focus recovery, current-account generations, and no Access review or re-enable behavior.
- [ ] 3.3 RED: Create `AuthenticationHistoryPage.test.tsx` for opaque-cursor-only continuation, duplicate prevention, refresh invalidation, stale-page rejection, retry, and accessible loading/empty/end states.
- [ ] 3.4 Update `AuthenticationHistoryPage.tsx` to preserve cursor-chain generation and accessible, non-fabricated Authentication evidence states.

## Phase 4: Verification

- [ ] 4.1 Run from `frontend/`: `pnpm vitest run --reporter=verbose`, `pnpm lint`, and `pnpm build`; record focused race, route, replacement, mutation, and History results.
- [ ] 4.2 Manually exercise protected direct entry, failed logout, dirty replacement discard, conflict recovery, and stale History response; confirm no secrets enter URLs, storage, or announcements.
