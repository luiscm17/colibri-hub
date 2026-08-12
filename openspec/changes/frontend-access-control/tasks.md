# Tasks: Frontend Access Control

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | PR1 includes ~726 generated lockfile additions plus authored tooling/foundation changes; PR2 350; PR3 330; PR4 395; PR5 395; PR6 320 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 → PR2 → PR3 → PR4 → PR5 → PR6 |
| Delivery strategy | exception-ok for PR1; auto-chain afterward |
| Chain strategy | size-exception for PR1; feature-branch-chain afterward |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

This is an OpenSpec-only portable handoff. All 30 tasks are pending and the prior local attempt was fully reverted. The maintainer approves `size:exception` for PR1, including a generated `frontend/pnpm-lock.yaml` update estimated at ~726 additions and a total PR above 800 changed lines when structurally justified. Use the new session's finite preflight review budget as the operational guard; do not reacquire a stale 400-line cap. Every unit includes its RED tests and GREEN production completion in the same work-unit commit/PR. PR1 base = `feature/frontend-access-control`; PR2 base = PR1; PR3 base = PR2; PR4 base = PR3; PR5 base = PR4; PR6 base = PR5; only the tracker merges to `main`. Git, branches, commits, pushes, and GitHub operations remain manual. Check every child diff for base pollution.

## Phase 1: PR1 — Foundation and handoff (base: tracker)

- [x] 1.1 Add Vitest, `@testing-library/react`, `@testing-library/user-event`, and `jsdom` to `frontend/package.json`/lockfile; configure `frontend/vitest.config.ts` and test discovery under `frontend/src/**/*.test.{ts,tsx}`.
- [x] 1.2 RED→GREEN in the same unit: test and implement Authentication semantic eligibility/session-end input, five Access states, retry, clear, and no protected content for unresolved/password-change/ended/unavailable; STOP and notify user before any live-backend check.
- [x] 1.3 RED→GREEN: test and implement strict `/api/v1/access/me` ordinary/global mapping, exact action/scope, `anyOf`/`allOf`, malformed fail-closed behavior, and normalized `profile_not_found`, `profile_inactive`, 403, 401, network/service, and invalid responses.
- [x] 1.4 RED→GREEN: test and implement identity `(accountId,handoffId,load_access)`, duplicate suppression, generation/correlation, AbortController, stale-result silence, atomic replacement, and narrow snapshot/check/refresh/clear exports; modify Auth only at the semantic boundary and retire no seam.
- [x] 1.5 Verify from `frontend/`: `pnpm vitest run src/features/access-control --reporter=verbose && pnpm build && pnpm lint`; after user starts/provisions the backend, record handoff/session-end evidence in `evidence/pr1.md`. Rollback `frontend/src/features/access-control/` and the semantic handoff adapter only; leave Auth shell behavior intact.

## Phase 2: PR2 — Protected catalog, shell, and routes (base: PR1)

- [x] 2.1 RED→GREEN: test and implement exact catalog requirements for Warehouse, five Yarn sections, quality/waste, Lot dashboard/queue/detail plus five stages, and transversal dashboard; keep filters/shifts neutral and distinguish `edit` from `edit_outside_window`.
- [x] 2.2 RED→GREEN: test and implement default-deny navigation in `frontend/src/app/navigation-data.tsx` and `frontend/src/app/layout/{AppLayout,Sidebar}.tsx`, omitting denied leaves and empty groups without role/label/prefix inference.
- [x] 2.3 RED→GREEN: test and implement direct/history route denial, blocked/unavailable outcomes, lazy admin protection, and exact requirements in `frontend/src/app/routes/{index,lazy-pages}.tsx`; migrate all consumers and remove `isResourceAllowed` one-way.
- [x] 2.4 Verify `pnpm vitest run src/app --reporter=verbose && pnpm build && pnpm lint`; STOP until user starts backend, then record direct URL/history denial and permitted fallback in `evidence/pr2.md`. Rollback catalog, route, and layout changes while retaining PR1’s public contract.

## Phase 3: PR3 — Protected operations and 403 recovery (base: PR2)

- [x] 3.1 RED→GREEN: test and implement read/write/edit/edit-outside-window checks and malformed/safe input handling in `frontend/src/features/warehouse/bales/` and affected protected feature consumers. Current applicable scope closed by maintainer decision: reusable exact action/scope contracts and the implemented Bale read/write operation are covered; no absent Bale correction operation was invented.
- [x] 3.2 RED→GREEN: test and implement shared denial/revalidation through `frontend/src/api/{httpClient,httpError}.ts`: unexpected 403 refreshes once, rechecks, preserves safe input, never replays a mutation, and clears on denial/session end.
- [x] 3.3 RED→GREEN: test and implement exact Warehouse, Yarn, quality/waste, Lot-stage, and transversal consumers with consistent hide/disable behavior and latest-only/abort guarantees. Current applicable scope closed by maintainer decision: reusable exact requirements and shared recovery are implemented; absent owner-domain operation surfaces remain intentionally unimplemented.
- [x] 3.4 Verify `pnpm vitest run src/features/warehouse src/api --reporter=verbose && pnpm build && pnpm lint`; STOP for user backend startup, then record permitted, revoked-403, retry, and no-replay counts in `evidence/pr3.md`. Rollback operation adapters/pages only.

## Phase 4: PR4 — Addressable administration families (base: PR3)

- [x] 4.1 RED→GREEN: test and implement Users/profiles collection, detail, and addressable recovery in `frontend/src/features/access-control/administration/`; cover origin/page restoration, dirty Back/Cancel, stale/missing/denied fallback, pagination, latest-only subjects, empty-page reconciliation, loading/refresh retention, selection, and focus.
- [x] 4.2 RED→GREEN: test and implement Roles collection/detail addressability with the same pagination, stale-result, fallback, loading, no-match, selection, and focus contracts.
- [x] 4.3 RED→GREEN: test and implement Presets collection/detail addressability with the same recovery and semantic loading/no-match contracts.
- [x] 4.4 RED→GREEN: test and implement Scopes paginated addressable collection with selected context derived from loaded rows/definitions; do not call or invent `/scopes/{id}`.
- [x] 4.5 RED→GREEN: test and implement History filtered paginated collection only, using exactly `subject_type`, `change_kind`, `date_from`, and `date_to`; no detail route/endpoint is implied.
- [x] 4.6 RED→GREEN: test and implement `frontend/src/app/routes/lazy-pages.tsx` administration entry points, responsive Mantine tables/cards, keyboard/focus and screen-reader semantics, including inactive profiles as read-only and no unauthorized disclosure.
- [x] 4.7 Verify `pnpm vitest run src/features/access-control/administration --reporter=verbose && pnpm build && pnpm lint`; STOP for user backend provisioning, then record all five families, pagination, direct recovery, responsive, keyboard, and screen-reader evidence in `evidence/pr4.md`. Rollback administration surfaces/routes only.

## Phase 5: PR5 — Governance, forms, previews, and conflicts (base: PR4)

- [ ] 5.1 RED→GREEN: test and implement profile status lifecycle, assignment replacement/reasons, inactive read-only behavior, and Authentication-owned profile creation under `frontend/src/features/access-control/administration/profiles/`.
- [ ] 5.2 RED→GREEN: test and implement role matrices, supported permission pairs, role create/edit/lifecycle reasons, and exact-copy versus adjustable independent preset flows under `roles/` and `presets/`.
- [ ] 5.3 RED→GREEN: test and implement recognized scope registration/lifecycle, loaded versions/reasons, and no free-form or automatic grants under `scopes/`.
- [ ] 5.4 RED→GREEN: test and implement collection/detail/create/edit transitions, Mantine `useForm`/Combobox where needed, loaded-version semantics, preview distinction, and safe isolated drafts.
- [ ] 5.5 RED→GREEN: test and implement mutation fingerprints, fresh-preview invalidation after edit/conflict/authority change, 409 reconciliation, auth/session invalidation, last-administrator rejection, affected-user evidence, no replay, and success/departure clearing.
- [ ] 5.6 Verify `pnpm vitest run src/features/access-control --reporter=verbose && pnpm build && pnpm lint`; STOP for user backend provisioning, then record mutation, 409, last-admin, route recovery, post-success refresh, duplicate/replay, and focus evidence in `evidence/pr5.md`. Rollback governance modules/forms only; never backend data.

## Phase 6: PR6 — Hardening, accessibility, and evidence (base: PR5)

- [ ] 6.1 RED→GREEN: run the complete spec matrix for handoff, latest-only/abort, disclosure, route recovery, session clearing, responsive critical actions, keyboard tab/focus, and screen-reader announcements; close only observed gaps without adding requirements.
- [ ] 6.2 RED→GREEN: remove the retired authorization seam, complete remaining Access exports and fixtures, and preserve capability ownership/backend-authority boundaries.
- [ ] 6.3 Update `frontend/docs/testing/strategy.md`, `frontend/docs/features/access-control.md`, and `evidence/index.md` with commands, screenshots/observations, pass/fail status, and the unresolved external Authentication dependency.
- [ ] 6.4 Verify `pnpm vitest run --reporter=verbose`, `pnpm build`, `pnpm lint`, `git diff --stat`, and each child base; STOP, notify user, and await backend startup before recording handoff, 403, pagination, mutations/conflicts, recovery, responsive, and assistive real-backend evidence. Rollback docs, fixtures, and hardening only.

After a fresh session completes mandatory preflight/init/status guards, `sdd-apply` is authorized for PR1 only under its selected finite review budget and the approved `size:exception`. These implementation tasks remain unchecked. OpenSpec is the only portable handoff authority; do not retrieve an old runtime ledger. The user alone starts or provisions the backend, and only after an explicit checkpoint request. Git and GitHub operations remain manual.
