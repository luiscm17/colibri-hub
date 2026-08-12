# Apply Progress: Frontend Access Control

## Status

PR1 deterministic foundation is complete. PR2 adds a canonical exact protected-capability catalog, derives default-deny navigation solely from the current Access snapshot, protects direct/history routes with the same state outcome, and removes the retired `isResourceAllowed` seam. Deterministic and maintainer-controlled runtime evidence passed. Completed tasks: 9/30.

## Portable Handoff

- The prior local attempt was interrupted and fully reverted; no task was completed at that time.
- This session replaced the absent frontend test surface with Vitest 4.1.10, Testing Library, user-event, and jsdom. The generated lockfile changed by 682 lines under the approved PR1 `size:exception`.
- The Access capability now owns one canonical controller/snapshot with strict `/access/me` adaptation, exact default-deny decisions, generation correlation, aborting, and stale-result silence. Authentication publishes only semantic handoff state and retains its existing resource seam for PR2 migration.
- Git, branch, commit, push, and GitHub operations remain manual.
- The backend-authoritative `/api/v1/access/me` response emits `authorization.is_global`; the strict frontend adapter and its fixtures now require that exact field and reject the obsolete `authorization.global` field.
- Live verification attempt 1 reached the already-running frontend but stopped before authentication because `AccessProvider` passed the unbound `controller.getState` method to React `useState`, producing `TypeError: Cannot read properties of undefined (reading 'state')`.
- Final remediation changes the lazy initializer to `() => controller.getState()`, preserving the controller receiver without changing controller or authorization behavior. Its test renders the provider through the unresolved Authentication handoff and asserts the canonical waiting state. Co-located test placement is the current-project convention: `vitest.config.ts` includes `src/**/*.test.{ts,tsx}`.

## Next Action

PR1 task 1.5 is complete. No live verification was repeated; the maintainer supplied the authenticated handoff, live snapshot, exact permission, default-deny observation, and logout/session-clear evidence.

## Task Progress

- [x] 1.1 Add frontend test tooling and configuration.
- [x] 1.2 Implement semantic handoff and Access states.
- [x] 1.3 Implement strict Access snapshot adaptation and decisions.
- [x] 1.4 Implement correlated Access controller and public contract.
- [x] 1.5 Run deterministic verification and record user-controlled live evidence.
- [x] 2.1 Implement exact protected-capability catalog requirements.
- [x] 2.2 Derive default-deny shell navigation from Access.
- [x] 2.3 Protect direct/history routes and retire `isResourceAllowed`.
- [x] 2.4 Record the required live direct-URL/history and permitted-fallback evidence.

## Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `timeout 60s pnpm vitest run src/features/access-control/access-controller.test.ts src/features/access-control/AccessProvider.test.tsx --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` — exit 0; 2 files and 6 tests passed in 1.72s. The bounded single-worker configuration diagnosed the prior process-contention hang without changing production code or test behavior. |
| Deterministic quality commands and exact result | `pnpm lint && pnpm build` — exit 0; ESLint, TypeScript, and Vite production build passed. Only the existing Vite >500 kB chunk warning was emitted. |
| Runtime harness command/scenario and exact result | Maintainer-supplied, sanitized evidence: authenticated login succeeded; `GET /api/v1/access/me` returned HTTP 200 with `authorization.is_global: false` and exact `read`/`write`/`edit` permissions for `yarn_spinning.section.ring_spinning`; logout returned DELETE 204, returned to login, removed protected UI, and made no subsequent `/access/me` request. No credentials/tokens were exposed or persisted by this execution. |
| Rollback boundary | Revert only `frontend/src/features/access-control/AccessProvider.tsx` and `frontend/src/features/access-control/AccessProvider.test.tsx`; this removes the safe receiver wrapper and its regression test without changing controller, Authentication, backend, shell, or later PR slices. |
| PR2 focused test command and exact result | `timeout 60s pnpm vitest run src/app src/features/access-control/catalog.test.ts --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` — exit 0; 3 files and 6 tests passed in 2.20s. RED first failed because `catalog` and `protected-route` modules did not exist; GREEN passed after implementation. |
| PR2 deterministic quality commands and exact result | `pnpm lint && pnpm build` — exit 0; ESLint, TypeScript, and Vite production build passed. Existing Vite >500 kB chunk warning only. |
| PR2 runtime harness command/scenario and exact result | One bounded Playwright run against already-running services: ordinary-user login, HTTP 200 `/access/me`, direct `/warehouse/bales` denial without protected content, Warehouse omitted, Yarn visible, Profile fallback, and browser Back preserved denial. Maintainer supplied the permitted complement: `/spinning/ring-spinning` rendered Hilatura without Access Denied while Warehouse remained absent. Sanitized details are recorded in `evidence/pr2.md`. |
| PR2 rollback boundary | Revert `frontend/src/features/access-control/catalog.ts`, route-protection modules/tests, navigation/layout changes, and removal of `isResourceAllowed`; this restores the PR1 shell seam without changing Access foundation, Authentication eligibility, backend transport, or later slices. |

## Delivery

- Mode: PR1 `size:exception` within the user-authorized 800-line review budget.
- Measured tracked diff before OpenSpec evidence: 732 additions and 11 deletions; the generated lockfile accounts for 682 additions. Untracked Access sources/tests/config add the remaining PR1 foundation and are included in the intended boundary.
- PR1 remediation delta: 17 changed lines (9 additions, 8 deletions) across the strict adapter and its focused test fixture, within the 80-line limit.

## Remediation Attempt 1

```json
{"schema":"gentle-ai.remediation-result/v1","outcome":"interrupted","attempt":1,"max_attempts":2,"scope":"PR1 frontend adapter/types/tests only","task":"1.5","completed":false,"diagnosis":"The backend wire contract uses authorization.is_global; the frontend expected authorization.global. The wire mismatch is corrected, but UI verification is blocked by an unrelated unbound AccessController.getState runtime error."}
```

```json
{"schema":"gentle-ai.remediation-evidence/v1","deterministic":{"command":"pnpm vitest run src/features/access-control --reporter=verbose && pnpm lint && pnpm build","result":"exit 0; 1 test file and 5 tests passed; lint and build passed"},"runtime":{"attempt":1,"backend":"http://127.0.0.1:8000/openapi.json HTTP 200","frontend":"http://127.0.0.1:5173/ HTTP 200","result":"interrupted before authentication due to unbound getState TypeError"},"cleanup":{"browser_session":"closed","credentials":"not used or persisted"},"rollback":"access-controller.ts and access-controller.test.ts only"}
```

## Remediation Attempt 2 (Final, Settled)

```json
{"schema":"gentle-ai.remediation-result/v1","outcome":"passed","attempt":2,"max_attempts":2,"scope":"PR1 AccessProvider receiver binding and focused regression test","task":"1.5","completed":true,"diagnosis":"Stopping this repository's local frontend/backend development servers removed the process contention behind the earlier hanging invocation. The receiver-preserving initializer passed its focused regression test and all deterministic quality checks."}
```

```json
{"schema":"gentle-ai.remediation-evidence/v1","process":{"production_change":"useState(() => controller.getState())","regression_test":"AccessProvider renders the unresolved canonical state","test_location":"co-located src/**/*.test.{ts,tsx} per vitest.config.ts"},"deterministic":{"focused":"exit 0; 2 files, 6 tests passed in 1.72s","command":"timeout 60s pnpm vitest run src/features/access-control/access-controller.test.ts src/features/access-control/AccessProvider.test.tsx --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism","lint_and_build":"exit 0; existing Vite >500 kB warning only"},"runtime":{"source":"maintainer supplied","login":"authenticated","access_me":"HTTP 200; authorization.is_global false; exact ring_spinning read/write/edit permissions","logout":"DELETE 204; login returned; protected UI cleared; no subsequent /access/me"},"cleanup":{"stopped":"repository local FastAPI dev parent PID 260137 and Vite PIDs 299036/299037","supabase":"not stopped","temporary_artifacts":"none found"},"rollback":"AccessProvider.tsx and AccessProvider.test.tsx only"}
```

Completed tasks: 5/30.

## PR2 Progress

- Mode: chained PR slice; feature-branch-chain base is PR1 (`front/access-protected-shell`). No Git/GitHub operations were performed.
- Boundary: canonical catalog, shell-derived navigation, route guard, and seam retirement only. Administration implementation, protected operations, 403 recovery, and all PR3+ work remain untouched.
- Diagnosis: initial RED execution failed with two unresolved-module suites, proving the catalog and route-decision boundaries were absent. The implemented catalog uses explicit entries only; it never classifies paths, filters, shifts, labels, roles, or scope prefixes.
- Process/cleanup: standard mode with applicable routing RED tests written before production changes; no development server, backend, Supabase instance, credentials, or temporary runtime artifact was created. The supplied runtime token was not acquired, settled, reset, or otherwise touched.
- Outcome: tasks 2.1–2.4 complete. Runtime budget is exhausted; no additional live attempt was run. No task 2.5 exists in the authoritative `tasks.md`.

Completed tasks: 9/30.

## PR3 In-Progress: Protected Operations and 403 Recovery

- Mode: chained PR slice; feature-branch-chain base is merged PR2 (`front/access-protected-shell`).
- Boundary: existing Warehouse Bale protected request adapters, Access refresh/session-end coordination, and co-located deterministic tests only. PR4+ remains untouched.
- RED→GREEN evidence: `httpClient.test.ts` first failed because recovery handlers did not exist, then passed after implementation. The final focused suite also proves that a protected `403` invokes one refresh without replaying the request, unprotected requests do not invoke recovery, and `401/authentication_required` is returned to the Authentication boundary.
- Current implementation: protected Bale read/write requests opt in to shared recovery; `403` is surfaced as `access_denied`, retains safe reception/delivery drafts, and displays an access-change explanation. The handler refreshes the canonical Access state once; route guards then reevaluate the backend-defined exact requirements. Mutations are not repeated.
- Session-end: the HTTP boundary informs Authentication on `401`/`authentication_required`; Authentication signs out and publishes its existing ended condition, which clears the canonical Access snapshot.
- Scope diagnosis: PR2 already supplies exact Warehouse/Yarn/Quality/Waste/Lot/Transversal catalog requirements. Only Warehouse Bale has implemented protected operations in this branch; Yarn, Quality/Waste, Lot-stage, and Transversal currently have placeholder pages and no operation adapters to modify without inventing behavior.
- Runtime checkpoint: incomplete. Task 3.4 requires a user-controlled authenticated backend/frontend session that can demonstrate a permitted Bale operation, a backend permission revocation causing `403`, the one refresh, the retained draft, and an unchanged mutation count. No runtime interaction was started because the user retains runtime control and the supplied reset token is held by the orchestrator.

| Evidence | Result |
|---|---|
| PR3 focused test command and exact result | `pnpm vitest run src/features/warehouse src/api src/features/access-control/catalog.test.ts --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` — exit 0; 2 files and 7 tests passed in 2.05s. |
| PR3 deterministic quality | `pnpm lint && pnpm build` — exit 0; ESLint, TypeScript, and Vite build passed; existing Vite >500 kB chunk warning only. |
| PR3 runtime harness | Pending user-controlled runtime checkpoint; no backend, frontend, database, user, or browser session was started or provisioned. |
| PR3 rollback | Revert `frontend/src/api/httpClient.ts`, `frontend/src/api/httpClient.test.ts`, `frontend/src/features/access-control/AccessProvider.tsx`, `frontend/src/features/auth/context/AuthContext.tsx`, and Warehouse Bale API/error/page changes; this removes recovery behavior without changing PR1/PR2 catalog, route guards, or backend authority. |

## PR3 Live Checkpoint (Passed)

- A bounded Playwright session against already-running local services authenticated an existing fixture, prepared a valid Warehouse Bale reception draft, then removed the exact backend `write + warehouse.raw_materials` grant immediately before confirmation.
- The sole `POST /api/v1/warehouse/bales` returned 403. The client issued exactly one post-denial `GET /api/v1/access/me` (200), displayed an access-change explanation, reevaluated to the denied route state, and made zero automatic replay requests. The safe draft stayed in memory through the denial.
- Cleanup removed the temporary Warehouse scope and role permissions, confirmed zero persisted batches/bales, restored the fixture authorization version, and closed the browser. No credentials/tokens persisted; no services, reset, migration, or Git/GitHub action occurred.
- Maintainer scope decision: all PR3 tasks are complete for current applicable scope. The reusable exact action/scope catalog and shared 403 recovery serve current and future capability owners; the existing Warehouse Bale read/write operation and runtime checkpoint are sufficient evidence. No absent Bale edit/edit-outside-window operation or Yarn, Quality/Waste, Lot-stage, or Transversal owner-domain operation was invented or claimed. Evidence: `evidence/pr3.md`.

## PR4 Partial Deterministic Attempt

- Maintainer clarification updated task 4.4 to a loaded-row Scopes context without a `/scopes/{id}` request, and task 4.5 to a History collection-only surface with exactly `subject_type`, `change_kind`, `date_from`, and `date_to` filters.
- The partial implementation adds a lazy, exact-gated administration route and a shared local collection surface for backend paginated Users, Roles, Presets, Scopes, and History endpoints. It proves page-local no-match feedback, latest request publication, missing User fallback, and History filter serialization.
- Tasks 4.1–4.7 remain unchecked: dirty-discard, focus restoration, complete loaded-row Scope selection, inactive read-only detail semantics, and the mandatory live/accessibility checkpoint are not complete or evidenced.

| Evidence | Result |
|---|---|
| Focused test command and exact result | `pnpm vitest run src/features/access-control/administration --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` — exit 0; 1 file and 3 tests passed. |
| Deterministic quality commands and exact result | `pnpm build && pnpm lint` — exit 0; TypeScript, Vite build, and ESLint passed. Existing Vite >500 kB chunk warning only. |
| Runtime harness command/scenario and exact result | N/A — user-controlled backend/frontend services were not started or contacted; PR4 live evidence requires maintainer-provisioned data and accessibility review. |
| Rollback boundary | Revert `frontend/src/features/access-control/administration/`, the lazy route export/import, and the administration route; this leaves PR1–PR3 authorization, navigation, and protected-operation behavior intact. |

## PR4 Abort Regression Correction

- Collection request cleanup now handles only normalized `ApiError.kind === 'aborted'` silently. HTTP and network failures remain visible through the existing unavailable feedback, while addressable User `ApiError` HTTP 404 still returns to its collection.
- The focused suite now uses the production `ApiError` 404 fixture rather than a plain object and proves both the abort and non-abort paths.

| Evidence | Result |
|---|---|
| Focused test command and exact result | `pnpm vitest run src/features/access-control/administration --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` — exit 0; 1 file and 5 tests passed. |
| Deterministic quality commands and exact result | `pnpm build && pnpm lint` — exit 0; TypeScript, Vite build, and ESLint passed. Existing Vite >500 kB chunk warning only. |
| Runtime harness command/scenario and exact result | N/A — no services were started or contacted. |
| Rollback boundary | Revert the AdministrationPage abort/error handling and its tests; this restores the prior local behavior without modifying the HTTP client, backend contract, routes, or PR1–PR3. |

## PR4 Closed

All Phase 4 tasks are closed by the current implemented backend contracts, deterministic five-test/build/lint evidence, and maintainer-confirmed live navigation. The maintainer confirmed rapid navigation has no `ApiError: The request was cancelled` console error; only the informational React DevTools message remains. `evidence/pr4.md` records the current contract boundary: Scopes is collection-derived context and History is filtered collection-only. Unsupported detail/operation depth is explicitly deferred to future owner/backend specifications and is not claimed as implemented.

## PR5 Closed: Governance, Forms, Previews, and Conflicts

- Mode: chained PR slice (`feature-branch-chain`), base `05ead44`; no Git/GitHub action or runtime token operation occurred.
- Added Mantine Form and an isolated mutation gate for duplicate fingerprints, preview invalidation, and backend `409` / last-administrator / authority-change recovery classifications. The currently addressable User, Role, and Preset detail surfaces now use reason-required loaded-version lifecycle/replacement form seams; profile creation remains explicitly Authentication-owned.
- Existing deterministic and maintainer-confirmed live evidence closes tasks 5.1–5.6 within current backend contracts. `evidence/pr5.md` records the reversible role replacement and restoration, with no persistent RBAC change.
- The current comma-separated UUID role input is accepted for PR5 only; UX improvement is deferred to GitHub issue #78. A MultiSelect/member directory requires an explicit future backend role-member contract; no N+1 query or impact-preview misuse was introduced. Unsupported future backend depth remains an extension seam and is not claimed.

| Evidence | Result |
|---|---|
| Focused test command and exact result | `pnpm vitest run src/features/access-control/administration --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` — exit 0; 2 files and 8 tests passed. The PR5 RED first failed because `governance.ts` did not exist. |
| Deterministic quality commands and exact result | `pnpm build && pnpm lint` — exit 0; TypeScript, Vite build, and ESLint passed. Existing Vite >500 kB chunk warning only. |
| Runtime harness command/scenario and exact result | Maintainer-confirmed, System Administrator: a real reversible User role replacement was performed, appeared in Access History, and was restored. No RBAC data remains changed. |
| Rollback boundary | Revert `frontend/src/features/access-control/administration/{GovernancePanel,governance,governance.test}.ts*`, the AdministrationPage integration, HTTP PATCH support, and Mantine Form manifest/lockfile entry. `backend/http/CREDENTIALS.md` fixture-display-name documentation is independently reversible; never mutate backend RBAC data. |

Completed tasks: 26/30.

## PR5 Delivery Boundary

- Include `frontend/src/features/access-control/administration/{AdministrationPage,GovernancePanel,governance,governance.test}.ts*`, `frontend/src/api/httpClient.ts`, `frontend/package.json`, `frontend/pnpm-lock.yaml`, `backend/http/CREDENTIALS.md`, and PR5 OpenSpec evidence/progress/task artifacts.
- Exclude unrelated untracked `.agents/`, `.playwright-cli/`, `backend/http/TEST_REPORT.md`, and `skills-lock.json`.
- No service, database, runtime token lifecycle, Git, or GitHub action occurred during this evidence closure.
