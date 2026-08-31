# Design: Complete Frontend Yarn Spinning

## Technical Approach

Replace the single title page with a capability-owned route surface under `features/spinning`. The app shell continues to choose destinations and wrap them with existing `ProtectedRoute`; spinning owns workflow composition, drafts, presentation states, and a typed future-integration port. Every server-dependent operation initially resolves to `unavailable`, preserving entered work and never synthesizing records, metrics, calculations, or authorization decisions.

## Architecture Decisions

| Decision | Alternatives considered | Choice and rationale |
|---|---|---|
| Public boundary | Shell imports internal pages; one generic page | Export route components and route descriptors from `features/spinning/index.ts`; this keeps app-to-capability direction explicit and internals replaceable. |
| Responsibility areas | One workflow module; global technical folders | Keep `sections`, `quality`, `waste`, `reporting`, and `corrections` independently owned beneath spinning because their submissions, state, and delivery lifecycles differ. |
| Draft authority | URL/global store/adapter-owned state | Each route workspace owns its draft; child editors receive values/events. URL search parameters own shareable reporting/read filters. Server projections remain adapter results, preventing duplicate authority. |
| Backend seam | Call planned endpoints now; mock successful data | Define a capability-local `SpinningGateway` and discriminated remote states, with an unavailable implementation. Future `httpJson` adapters may implement it without changing UI ownership. |
| Delivery | Single large PR | Use an auto-chained feature branch series because complete scope will exceed 400 authored lines; each slice is independently verifiable and reversible. |

## Data Flow

```text
App routes -> spinning public route component -> responsibility workspace
                                                   |-> local draft
                                                   |-> SpinningGateway -> unavailable outcome
URL search params -> reporting/read filters --------|                    (future httpJson)
```

Changing Progress identity aborts the obsolete gateway request and associates results with an immutable request key. Conflict recovery retains the correction draft, requires an explicit current-record refresh, and never retries automatically.

## File Changes

| File | Action | Description |
|---|---|---|
| `frontend/src/features/spinning/index.ts` | Create | Narrow public route contract. |
| `frontend/src/features/spinning/routes.tsx` | Create | Capability route components and section identity mapping. |
| `frontend/src/features/spinning/{sections,quality,waste,reporting,corrections}/**/*` | Create | Independently owned workspaces, drafts, and presentations. |
| `frontend/src/features/spinning/integration/{contracts,unavailableGateway}.ts` | Create | Stable gateway and explicit unavailable implementation. |
| `frontend/src/features/spinning/components/IntegrationState.tsx` | Create | Accessible loading/empty/stale/failure/unavailable status UI. |
| `frontend/src/app/routes/{index.tsx,lazy-pages.ts}` | Modify | Compose exported pages inside existing route protection. |
| `frontend/src/features/spinning/pages/SpinningPage.tsx` | Delete | Retire title-only authority. |
| `frontend/docs/features/yarn-spinning.md` | Modify | Record delivered boundaries and verification. |

## Interfaces / Contracts

`SpinningGateway` exposes cancellable queries/commands for section context and continuity, Quality profiles/capture, Waste, records/history, metrics, and corrections. Results use `loading | unavailable | failure | empty | populated | stale | conflict`; server payloads remain opaque contract DTOs at the adapter edge. The unavailable gateway performs no HTTP request and returns a reason plus retry capability only when meaningful.

## Accessibility and Responsive Strategy

Semantic headings, labels, field errors, `role="status"`/`aria-live`, visible focus, and focus transfer to outcomes are workspace requirements. Context and primary actions remain reachable on narrow screens; forms stack, tables/grids use labelled controlled overflow, and state is never conveyed by color alone. Keyboard draft, retry, review, and conflict-recovery paths receive component tests.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Draft reducers, request-key stale rejection, state mapping | Vitest pure tests. |
| Component/integration | Route identity, retained drafts/filters, unavailable and conflict states, keyboard/focus, responsive reachability | Testing Library with Mantine/router providers and gateway fakes. |
| E2E | Protected destination smoke paths | Manual acceptance until an E2E runner is configured; run `pnpm vitest run`, `pnpm lint`, and `pnpm build`. |

## Threat Matrix

Routing composition changes, so the required matrix was assessed; no shell/process boundary is introduced.

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths | Executable-looking docs | N/A: routes do not classify files | None | None |
| Git repository selection | Relative/absolute repository selectors | N/A: no VCS execution | None | None |
| Commit state | Staged/index variants | N/A: no commit automation | None | None |
| Push state | Tracking/refspec variants | N/A: no push automation | None | None |
| PR commands | Head/environment/composed commands | N/A: design plans slices but executes no PR commands | None | None |

## Migration / Rollout

Auto-chain order: (1) public boundary, route foundation, unavailable states; (2) sections and Progress/Skeining; (3) Quality; (4) Waste; (5) reporting/records; (6) corrections/recovery; (7) accessibility/responsive hardening and docs. Each targets ≤400 changed lines where practical, includes its tests, depends on its predecessor, and can roll back by restoring the prior route export. No data migration or RBAC change is required.

## Open Questions

None blocking; live gateway implementation waits for backend delivery.
