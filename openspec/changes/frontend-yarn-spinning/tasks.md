# Tasks: Complete Frontend Yarn Spinning

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 1,400–2,100 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 → PR 6 → PR 7 |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Boundary/routes/seam | PR 1 | `pnpm vitest run` | Protected route → unavailable | exports, routes, seam |
| 2 | Sections/Progress/Skeining | PR 2 | `pnpm vitest run` | Change Progress identity | `sections/**` |
| 3 | Quality | PR 3 | `pnpm vitest run` | Draft with unavailable profile | `quality/**` |
| 4 | Waste | PR 4 | `pnpm vitest run` | Unavailable capture/review | `waste/**` |
| 5 | Reporting/records | PR 5 | `pnpm vitest run` | Filters and empty/unavailable | `reporting/**` |
| 6 | Corrections/recovery | PR 6 | `pnpm vitest run` | Conflict then explicit refresh | `corrections/**` |
| 7 | Accessibility/docs | PR 7 | `pnpm vitest run && pnpm lint && pnpm build` | Keyboard/narrow viewport | tests and docs |

## Phase 1: Foundation, Routes, and Unavailable Seam (PR 1)

All capability paths below are under `frontend/src/features/spinning/`.

- [x] 1.1 Create `{index.ts,routes.tsx}`; compose exports in `frontend/src/app/routes/{index.tsx,lazy-pages.ts}` inside `ProtectedRoute`.
- [x] 1.2 Create `integration/{contracts.ts,unavailableGateway.ts}` and `components/IntegrationState.tsx`; no HTTP, calculation, record, or access decision.
- [x] 1.3 RED/GREEN: test route identity/unavailable status without fabricated success; then delete `pages/SpinningPage.tsx`.

## Phase 2: Sections, Progress, and Skeining (PR 2)

- [ ] 2.1 RED: test five routes retain date/shift/drafts; Skeining identifies Yarn Spinning and excludes Lot Processing.
- [ ] 2.2 Create `sections/**` section-close workspaces with one production/applicable-Progress intent and unavailable reads/submits.
- [ ] 2.3 RED/GREEN: test continuity unavailable retains draft and an older request-key response cannot replace changed Progress identity.

## Phase 3: Quality and Waste (PR 3–4)

- [ ] 3.1 RED/GREEN: create `quality/**`; unavailable profiles invent no fields/results; recoverable failure retains draft/context.
- [ ] 3.2 RED/GREEN: create `waste/**` by machine group/shift; unavailable state confirms no calculated or fabricated waste.

## Phase 4: Reporting, Records, Corrections, and Recovery (PR 5–6)

- [ ] 4.1 RED/GREEN: create `reporting/**`; retain URL filters and distinguish unavailable/loading/empty/stale/failure/populated without zero substitution.
- [ ] 4.2 RED/GREEN: create `corrections/**`; retain draft, require explicit refresh, and prohibit automatic retry/downstream change.

## Phase 5: Accessibility, Responsive Verification, and Documentation (PR 7)

- [ ] 5.1 RED/GREEN: add keyboard/focus and `aria-live` tests for unavailable, retry, review, and conflict states.
- [ ] 5.2 Test narrow viewport stacking and labelled controlled overflow keep context/actions reachable; run `pnpm vitest run`, `pnpm lint`, and `pnpm build` in `frontend/`.
- [ ] 5.3 Update `frontend/docs/features/yarn-spinning.md` with the boundary, unavailable-only integration, rollback, and manual smoke evidence.
