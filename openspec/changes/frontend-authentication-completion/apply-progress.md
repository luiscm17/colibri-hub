# Apply Progress: Frontend Authentication Completion

## Completed Tasks

- [x] 1.1 RED provider-event and Access handoff tests
- [x] 1.2 Current-only provider validation, semantic handoff identity, and serialized local clearing
- [x] 1.3 One eligible Access handoff and protected-route withholding
- [x] 2.1 RED return-intent validation tests
- [x] 2.2 Safe return intent, latest-only generic login denial, secret clearing, and focus
- [x] 2.3 RED replacement validation and dirty-discard tests
- [x] 2.4 Restricted route recovery and shared failure-safe termination behavior
- [x] 3.1 RED administration mutation, conflict, and recovery tests
- [x] 3.2 Authentication-only account mutation recovery and renewed confirmation
- [x] 3.3 RED History cursor, duplicate, retry, refresh, and stale-result tests
- [x] 3.4 Opaque cursor-chain deduplication and accessible History states

## Work Unit Evidence

| Evidence | Exact result |
|---|---|
| WU1 RED test command | `pnpm vitest run src/features/auth/context/AuthContext.test.tsx --reporter=verbose` exited 1: new latest-provider-session test expected two `/auth/me` calls and received zero. |
| WU1 focused test command | `pnpm vitest run src/features/auth/context/AuthContext.test.tsx src/features/access-control/AccessProvider.test.tsx src/features/access-control/access-controller.test.ts --reporter=verbose` exited 0: 3 files, 13 tests passed. |
| WU1 runtime harness | The same command rendered the AuthProvider → AccessProvider integration path in jsdom; two provider events resolved out of order, publishing one current account and one `/access/me` bootstrap. Exit 0, 13 tests passed. |
| WU1 quality commands | `pnpm lint` exited 0. `pnpm build` exited 0; Vite emitted its existing chunk-size warning for `index-Btd_SGxg.js` at 664.80 kB. |
| WU1 rollback boundary | Revert `frontend/src/features/auth/context/AuthContext.tsx`, `frontend/src/features/auth/provider/providerSession.ts`, and the focused AuthContext test. This removes event-epoch validation, stable handoffs, and serialized local logout without touching later work units. |
| WU2 RED test command | `pnpm vitest run src/features/auth/pages/LoginPage.test.tsx src/features/auth/pages/MandatoryPasswordChangePage.test.tsx --reporter=verbose` exited 1: safe intent helper was absent; malformed intent, equal replacement secret, and dirty-discard cases failed. |
| WU2 focused test command | `pnpm vitest run src/features/auth/pages/LoginPage.test.tsx src/features/auth/pages/MandatoryPasswordChangePage.test.tsx src/features/auth/context/AuthContext.test.tsx --reporter=verbose` exited 0: 3 files, 17 tests passed. |
| WU2 runtime harness | The focused Vitest jsdom harness submitted overlapping login attempts, discarded a dirty replacement draft, and exercised replacement success through the shared logout mock. Exit 0, 17 tests passed. |
| WU2 quality commands | `pnpm lint` exited 0. `pnpm build` exited 0; Vite emitted its existing chunk-size warning for `index-BxdFqHdG.js` at 664.89 kB. |
| WU2 rollback boundary | Revert `frontend/src/features/auth/pages/returnIntent.ts`, `LoginPage.tsx`, `LoginPage.test.tsx`, `MandatoryPasswordChangePage.tsx`, `MandatoryPasswordChangePage.test.tsx`, and `AuthenticationBoundary.tsx`. This removes only entry/replacement behavior, leaving WU1 session handoff intact. |
| WU3 RED test command | `pnpm vitest run src/features/auth/pages/AuthenticationAccountsPage.test.tsx src/features/auth/pages/AuthenticationHistoryPage.test.tsx --reporter=verbose` exited 1: 2 files, 16 passed and 2 failed. The new assertions proved duplicate audit rows and retained disable confirmation after `409` conflict. |
| WU3 focused test command | `pnpm vitest run src/features/auth/pages/AuthenticationAccountsPage.test.tsx src/features/auth/pages/AuthenticationHistoryPage.test.tsx --reporter=verbose` exited 0: 2 files, 18 tests passed. The existing missing-detail test emitted a React Router mock-exhaustion stderr trace after safe back navigation, but the command passed. |
| WU3 runtime harness | The same focused Vitest jsdom command exercised reset/disable mutation recovery, conflict reload with renewed confirmation, opaque cursor continuation, retry, refresh, and stale-continuation rejection. Exit 0, 2 files and 18 tests passed. |
| WU3 quality commands | `pnpm lint` exited 0. `pnpm build` exited 0; Vite emitted its existing chunk-size warning for `index-DIdCAsJb.js` at 664.89 kB. |
| WU3 rollback boundary | Revert `frontend/src/features/auth/pages/AuthenticationAccountsPage.tsx`, `AuthenticationAccountsPage.test.tsx`, `AuthenticationHistoryPage.tsx`, and `AuthenticationHistoryPage.test.tsx`. This removes only conflict reconfirmation and History duplicate filtering, retaining WU1/WU2 session and entry behavior. |

## Delivery Boundary

- Strategy: `auto-chain`, `feature-branch-chain`.
- Completed slices: Work Unit 1 / child PR #1 and Work Unit 2 / child PR #2, both merged into tracker `front/auth-spec-completion`.
- Current slice: Work Unit 3 / final child PR targeting `front/auth-spec-completion`.
- WU3 authored frontend diff: 35 additions + 1 deletion, under the 400-line limit.
- WU1 runtime attempt: `sha256:df04fc62ea7e16ae6943559a15b0586efb2665006fdfe16519594506bb181e44` used once.
- WU2 runtime attempt: `sha256:b8ac17b80389a7bdaf54a84106b46e7332cc923f393ff33533b9c8ca3343475b` used once.
- Reconciliation runtime attempt: `sha256:4ae610ce83eda2bc6d77b28765b913b8e317efbc0614892791cc204c6925d691` used once.
- WU3 runtime attempt: `sha256:626c8b953fc073c609bdf6c8360003e54117c5549634cb1461fb4ea0384f354b` used once.

## Remaining Tasks

- [ ] 4.1–4.2 Full verification
