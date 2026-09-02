## Exploration: Complete frontend Yarn Spinning implementation

### Current State
The Yarn Spinning capability is currently a single `SpinningPage` stub that renders only a title. Eight protected destinations already exist for Preparation, Ring Spinning, Bobbin Winding, Twisting, Skeining, Process Quality, Waste, and Consolidated reporting; navigation exposes the same destinations and filters them through the existing effective-access snapshot. `ProtectedRoute` already owns loading, unavailable, blocked, and denied route outcomes. `httpJson` provides the existing authenticated transport boundary and recoverable access-denied handling.

The frontend specification requires one capability to present five productive section workspaces (including Skeining), independent Quality and Waste capture, section/consolidated read-only dashboards, correction review and history, profile-driven Quality configuration/capture, Progress continuity preparation, and resilient accessible interaction states. The backend specification defines the eventual endpoints, payloads, server-derived values, optimistic versions, cursor reads, error codes, and current-state semantics. The frontend must not reproduce business or authorization policy.

### Affected Areas
- `frontend/src/features/spinning/pages/SpinningPage.tsx` — replace the stub with route-aware section workspace, transversal capture, dashboard, and correction composition.
- `frontend/src/features/spinning/` — establish the Yarn Spinning capability's public presentation/interaction boundary, transport adapters, models, draft state, validation feedback, and focused tests; keep Quality, Waste, Skeining, dashboards, and corrections as distinct responsibility areas.
- `frontend/src/app/routes/index.tsx` and `frontend/src/app/routes/lazy-pages.ts` — preserve protected destinations while selecting the correct spinning experience/context for each route; no new authorization policy.
- `frontend/src/app/navigation-data.tsx` — likely only labels/route grouping adjustments if the final UX needs separate capture, records, or correction entry points; consume existing protected routes/outcomes.
- `frontend/src/api/httpClient.ts` and spinning adapters — consume the backend `/api/v1/spinning` contract, map transport errors to stable presentation outcomes, cancel obsolete requests, and reject stale responses.
- `frontend/docs/features/yarn-spinning.md` — current explanatory specification is the complete UI scope and should remain the implementation authority for interaction behavior.
- `backend/docs/features/yarn-spinning.md` — integration dependency: routes and exact response/error contracts for profiles, captures, records, corrections, metrics, and Progress prefill.
- Frontend test/build configuration — current OpenSpec configuration records no configured frontend test runner; implementation can still add focused behavior tests only if the repository's actual tooling is introduced/available, while `pnpm build` and `pnpm lint` remain quality gates.

### Approaches
1. **Capability-first route composition** — retain the existing app shell and protected routes, add a narrow spinning public surface with route-specific page compositions and explicit adapters for each backend contract.
   - Pros: preserves current boundaries, isolates transport from presentation, supports chained PR slices, and keeps section/Quality/Waste/dashboard lifecycles independent.
   - Cons: requires several focused models and draft/recovery state paths rather than one generic form.
   - Effort: High

2. **Single generic operational form/page** — make `SpinningPage` infer all route behavior and render shared dynamic fields from one broad configuration object.
   - Pros: initially fewer files and fast route coverage.
   - Cons: couples independent submission semantics, risks leaking business rules into configuration, makes correction/draft/accessibility behavior harder to reason about, and creates a large review unit.
   - Effort: High

### Recommendation
Use capability-first route composition. Keep five section workspaces as one coherent section-capture contract, with shared context and atomic production/progress submission, while keeping Quality, Waste, dashboards, and corrections independent because their server contracts, lifecycles, authorization outcomes, and recovery rules differ. Expose only semantic public entry points from the spinning capability; application routes compose them. Deliver as chained slices under the 400-line review budget: foundation/contracts and section workspace; Progress continuity and Skeining; Quality capture/profile configuration; Waste; dashboards/records; corrections/history/recovery; then accessibility/responsive hardening and integration verification. Do not add local RBAC, roles, scopes, or permission evaluation.

### Risks
- Backend endpoints and exact response variants do not yet exist, so adapters, fixtures, and integration wiring must be contract-driven and may need a compatibility seam until backend work lands.
- The backend contract has distinct server-owned/calculated fields, decimal strings, profile versions, cursor pagination, and `409` flows; browser-side duplication or optimistic calculations could create false authority.
- A single route currently serves every spinning destination; route/context parsing and navigation changes can accidentally merge independent experiences or bypass protected-route handling.
- Draft preservation, obsolete-request rejection, profile invalidation, concurrency rebase, and correction evidence require explicit state ownership and are easy to lose in a monolithic page.
- Dense grids and operational forms need deliberate keyboard/focus, announcements, controlled overflow, and non-color-only status treatment; build/lint alone will not prove these.
- Existing repository metadata says frontend tests are unavailable even though the strategy describes focused Vitest coverage for some frontend work; verification tooling must be confirmed before committing to automated test slices.

### Ready for Proposal
Yes. The proposal should define the chained implementation slices, explicitly mark backend-dependent integration as a later seam, and state that authorization is consumed only through existing protected routes and server outcomes. It should not define Access-Control policy.
