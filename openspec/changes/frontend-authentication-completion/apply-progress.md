# Apply Progress: Frontend Authentication Completion

## Completed Tasks

- [x] 1.1 RED provider-event and Access handoff tests
- [x] 1.2 Current-only provider validation, semantic handoff identity, and serialized local clearing
- [x] 1.3 One eligible Access handoff and protected-route withholding
- [x] 2.1 RED return-intent validation tests
- [x] 2.2 Safe return intent, latest-only generic login denial, secret clearing, and focus
- [x] 2.3 RED replacement validation and dirty-discard tests
- [x] 2.4 Restricted route recovery and shared failure-safe termination behavior

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

## Delivery Boundary

- Strategy: `auto-chain`, `feature-branch-chain`.
- Completed slice: Work Unit 1 / child PR #1 targeting `front/auth-spec-completion`.
- Current slice: Work Unit 2 / child PR #2 targeting `front/auth-session-handoff`.
- WU2 authored frontend diff: 111 additions + deletions, under the 400-line limit.
- WU1 runtime attempt: `sha256:df04fc62ea7e16ae6943559a15b0586efb2665006fdfe16519594506bb181e44` used once.
- WU2 runtime attempt: `sha256:b8ac17b80389a7bdaf54a84106b46e7332cc923f393ff33533b9c8ca3343475b` used once.
- Reconciliation runtime attempt: `sha256:4ae610ce83eda2bc6d77b28765b913b8e317efbc0614892791cc204c6925d691` used once.

## Remaining Tasks

- [ ] 3.1–3.4 Authentication administration and History
- [ ] 4.1–4.2 Full verification
