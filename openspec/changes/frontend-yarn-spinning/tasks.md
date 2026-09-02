# Tasks: Complete Frontend Yarn Spinning

## Review Workload Forecast
Estimate: 1,800–2,600. Strategy: auto-chain. Split: PR 1 → PR 10.
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal / base | Test | Harness | Rollback |
|---|---|---|---|---|---|
| 1 | Boundary/tracker | `pnpm vitest run` | protected → unavailable | exports/routes |
| 2 | Corrective discharge, PR1 | `pnpm vitest run routes.test.tsx` | repeated FIN event | `sections/**`/tests |
| 3 | Progress, PR2 | `pnpm vitest run` | change pending identity | progress grid |
| 4 | Skeining, PR3 | `pnpm vitest run` | Skeining-only | Skeining grid |
| 5 | Quality/PR4 | `pnpm vitest run` | unavailable profile | `quality/**` |
| 6 | Sample grid, PR5 | `pnpm vitest run` | ordered rows | Sample grid |
| 7 | Waste, PR6 | `pnpm vitest run` | edit weighed row | `waste/**` |
| 8 | Reporting, PR7 | `pnpm vitest run` | filters/empty | `reporting/**` |
| 9 | Corrections, PR8 | `pnpm vitest run` | conflict/refresh | `corrections/**` |
| 10 | A11y/handoff, PR9 | `pnpm vitest run && pnpm lint && pnpm build` | keyboard/narrow | a11y tests |

## Phase 1: Foundation (PR 1)
- [x] 1.1 Establish `features/spinning/{index,routes,integration}/**`; retain protected composition and RBAC.

## Phase 2: Corrective Production Discharge (PR 2)
- [x] 2.1 RED: prove repeated events/invalid paste stay separate; required catalog-backed machine/yarn-count, gross kg, operative spindle count, spindle tare g, cart kg, optional roving/observations, and unavailable selections behave correctly; direct net-weight input is absent.
- [x] 2.2 GREEN: use `configuration`, `dischargeModel`, `ProductionDischargeGrid`, `SectionWorkspace`, and a capability-local read-only catalog gateway without frontend FIN policy; retain raw drafts and render net weight only as unavailable pending server confirmation.

Corrective scope for the already discharged tasks 2.1/2.2: the optional roving-title input is rendered only when the read-only catalog authorizes it for an applicable discharge machine; no section identifier determines that policy. The section capture context visibly identifies the operational supervisor without fabricating an identity or submission outcome, and its shift selector uses `A`, `B`, and `C`. This does not complete any future phase.

## Phase 3: Applicable Progress (PR 3)
- [x] 3.1 RED/GREEN: add `progressModel`/`ProgressGrid` unique machine+yarn-count rows only for PSJ/Ring/Twisting; reject stale reads and aggregation.

## Phase 4: Skeining (PR 4)
- [x] 4.1 RED/GREEN: create `SkeiningGrid` as independent production; assert no Progress or Lot Processing controls.

## Phase 5: Quality Profiles (PR 5)
- [x] 5.1 RED/GREEN: create `quality/**` configuration/capture; unavailable profiles invent no fields/results and retain drafts.

## Phase 6: Quality Sample Grid (PR 6)
- [x] 6.1 RED/GREEN: render 10–15 ordered Sample measurements in React Data Grid with units, validation, readonly results, tolerance status.

## Phase 7: Waste (PR 7)
- [x] 7.1 RED/GREEN: create independent `waste/**` weighed machine-group/shift grid; prohibit production/Progress coupling and calculated waste.

## Phase 8: Reporting (PR 8)
- [x] 8.1 RED/GREEN: create `reporting/**`; retain URL filters and distinguish loading/empty/populated/stale/failure/unavailable without zero substitution.

## Phase 9: Corrections (PR 9)
- [ ] 9.1 RED/GREEN: create `corrections/**`; retain conflict drafts, require current-record read, and prohibit automatic retry.

## Phase 10: Accessibility/Handoff (PR 10)
- [ ] 10.1 RED/GREEN: test keyboard editing, focus, live status, narrow overflow.
- [ ] 10.2 User-run handoff (not assistant-run): start frontend and authenticated backend; use an account permitted by existing routes; visit `/spinning/preparation`, `/ring-spinning`, `/twisting`, `/bobbin-winding`, `/skeining`, `/quality`, `/waste`, `/consolidated`. Enter/paste repeated rows, tab controls, narrow viewport, attempt unavailable submit. Expect distinct discharges; Progress only PSJ/Ring/Twisting; independent Skeining/Waste; ordered Sample; focus/status; retained draft/no success. On failure capture URL, screenshot, console/network response, entered values. Backend continuity/submits/tolerance/records/corrections/authorization need APIs; unproven.
