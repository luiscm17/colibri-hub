# Tasks: Frontend Access Control Compliance
## Review Workload Forecast
3,300–3,600 total; U1–U9 ≤400; auto-chain.
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High
#81 umbrella; #82 U1–U2; #83 U3–U5; #84 U6–U8; #78 separate; #85 follow-up.
|U|Goal; branch; base|Test; runtime; rollback|
|-|-|-|
|U1|routes; `front/access-route-matrix`; `front/access-auth-foundation` tracker|`pnpm --dir frontend exec vitest run src/features/access-control/administration/operations.test.ts`; backend S1–2; matrix/routes|
|U2|recovery; `front/access-origin-recovery`; `front/access-route-matrix`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/route-state.test.ts`; backend S3–4; shell/state|
|U3|RBAC; `front/access-rbac-matrix`; `front/access-origin-recovery`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/forms/matrix.test.ts`; backend S5; forms|
|U4|presets; `front/access-preset-flows`; `front/access-rbac-matrix`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/presets/presets.test.ts`; backend S6; presets|
|U5|scopes/history; `front/access-scope-history`; `front/access-preset-flows`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/scopes/history.test.ts`; backend S6; scopes/history|
|U6|user gate; `front/access-user-gate`; `front/access-scope-history`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/user-role-gate.test.ts`; backend S7; user gate|
|U7|role gate; `front/access-role-gate`; `front/access-user-gate`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/shared-role-gate.test.ts`; backend S8; role gate|
|U8|safe dialogs; `front/access-safe-dialogs`; `front/access-role-gate`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/accessibility.test.tsx`; backend S9; dialog|
|U9|closure; `front/access-evidence-ledger`; `front/access-safe-dialogs`|`pnpm --dir frontend exec vitest run src/features/access-control/administration/evidence-completeness.test.ts`; backend S10; ledger/docs|
Paths: current `AdministrationPage.tsx`, `GovernancePanel.tsx`, `governance.ts`, `frontend/src/app/routes/index.tsx`; planned `operations.ts`, `route-state.ts`, `AdministrationShell.tsx`, `{forms,presets,scopes,history,mutations}/`.

## Phase U1: #82 routes
- [ ] RED: `operations.test.ts` Direct entry/Prohibited state; `pnpm --dir frontend exec vitest run src/features/access-control/administration/operations.test.ts`.
- [ ] IMPLEMENT: `operations.ts`, page/routes: matrix/no request.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/operations.test.ts`.
- [ ] EVIDENCE: refresh/prohibited; `openspec/changes/frontend-access-control-compliance/evidence/U1.md`.
- [ ] DELIVERY: matrix/routes; `feat(access): constrain administration routes`; STOP.
## Phase U2: #82 recovery
- [ ] RED: `route-state.test.ts` Origin and discard/Recovery; `pnpm --dir frontend exec vitest run src/features/access-control/administration/route-state.test.ts`.
- [ ] IMPLEMENT: `route-state.ts`/`AdministrationShell.tsx`: restore/clear.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/route-state.test.ts`.
- [ ] EVIDENCE: discard/stale; `openspec/changes/frontend-access-control-compliance/evidence/U2.md`.
- [ ] DELIVERY: shell/state; `feat(access): recover administration navigation`; STOP.
## Phase U3: #83 matrix
- [ ] RED: `forms/matrix.test.ts`: additive active-role union; inactive excluded; wrong action/right scope deny; right action/wrong scope deny; label rename independence; catalog growth without evaluator change; no hierarchy/direct grants/deny/ABAC/ReBAC/bundles/instance/org namespace; `pnpm --dir frontend exec vitest run src/features/access-control/administration/forms/matrix.test.ts`.
- [ ] IMPLEMENT: `forms/matrix.ts`: active IDs; inactive removable.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/forms/matrix.test.ts`.
- [ ] EVIDENCE: Matrix; `openspec/changes/frontend-access-control-compliance/evidence/U3.md`.
- [ ] DELIVERY: forms/matrix; `feat(access): constrain permission selection`; STOP.
## Phase U4: #83 presets
- [ ] RED: `presets/presets.test.ts` Preset independence; `pnpm --dir frontend exec vitest run src/features/access-control/administration/presets/presets.test.ts`.
- [ ] IMPLEMENT: `presets/`: copies never synchronize.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/presets/presets.test.ts`.
- [ ] EVIDENCE: copies; `openspec/changes/frontend-access-control-compliance/evidence/U4.md`.
- [ ] DELIVERY: presets; `feat(access): separate preset flows`; STOP.
## Phase U5: #83 scopes-history
- [ ] RED: `scopes/history.test.ts` Matrix/Preset limits; `pnpm --dir frontend exec vitest run src/features/access-control/administration/scopes/history.test.ts`.
- [ ] IMPLEMENT: `scopes/`/`history/`: recognized/four filters.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/scopes/history.test.ts`.
- [ ] EVIDENCE: scope/History; `openspec/changes/frontend-access-control-compliance/evidence/U5.md`.
- [ ] DELIVERY: scopes/history; `feat(access): constrain governance history`; STOP.
## Phase U6: #84 user gate
- [ ] RED: `mutations/user-role-gate.test.ts` Fresh replacement; `pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/user-role-gate.test.ts`.
- [ ] IMPLEMENT: `mutations/user-role-gate.ts`: non-zero preview/version once.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/user-role-gate.test.ts`.
- [ ] EVIDENCE: preview/apply; `openspec/changes/frontend-access-control-compliance/evidence/U6.md`.
- [ ] DELIVERY: user gate; `feat(access): gate user role replacement`; STOP.
## Phase U7: #84 shared-role gate
- [ ] RED: `mutations/shared-role-gate.test.ts` fingerprint/version, non-zero, apply-once, optional `reason: ""`, edit/session/conflict invalidation, no replay, affected impact != membership, Invalidated replacement; `pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/shared-role-gate.test.ts`.
- [ ] IMPLEMENT: `mutations/shared-role-gate.ts`: invalidate; separate impact.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/shared-role-gate.test.ts`.
- [ ] EVIDENCE: conflict/session; `openspec/changes/frontend-access-control-compliance/evidence/U7.md`.
- [ ] DELIVERY: shared-role gate; `feat(access): gate shared role replacement`; STOP.
## Phase U8: #84 safe delivery
- [ ] RED: `mutations/accessibility.test.tsx` Accessible safe delivery; `pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/accessibility.test.tsx`.
- [ ] IMPLEMENT: `mutations/ConfirmationDialog.tsx`: impact/focus/announcements/clearing.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/mutations/accessibility.test.tsx`.
- [ ] EVIDENCE: keyboard/narrow; `openspec/changes/frontend-access-control-compliance/evidence/U8.md`.
- [ ] DELIVERY: dialog; `feat(access): make access confirmation safe`; STOP.
## Phase U9: #81 closure
- [ ] RED: `evidence-completeness.test.ts` Evidence S1–S9; `pnpm --dir frontend exec vitest run src/features/access-control/administration/evidence-completeness.test.ts` failing.
- [ ] IMPLEMENT: only `evidence/ledger.md`, docs, fixtures; inspect receipts.
- [ ] GREEN: `pnpm --dir frontend exec vitest run src/features/access-control/administration/evidence-completeness.test.ts`, `pnpm --dir frontend exec vitest run`, `pnpm --dir frontend build`, `pnpm --dir frontend lint`.
- [ ] EVIDENCE: inspect U1–U8/ledger; `openspec/changes/frontend-access-control-compliance/evidence/U9.md`.
- [ ] DELIVERY: ledger/docs/fixtures; `test(access): close compliance evidence`; STOP.
