# Design: Complete Frontend Yarn Spinning

## Technical Approach

Keep the app shell as route/protection composer and `features/spinning` as capability owner. Replace generic section textareas with controlled `react-data-grid` capture models following the existing Warehouse grid idiom: immutable row IDs, pure row/paste/validation functions, `DataGridShell`, and workspace-owned drafts. Production Discharge, Progress, Skeining, Waste, and Quality Sample remain distinct models and grids. All aggregation, continuity, tolerance, metrics, and outcomes come from the server; until APIs exist, the gateway returns only `unavailable` and drafts remain local.

## Architecture Decisions

| Decision | Alternatives considered | Choice and rationale |
|---|---|---|
| Grid ownership | Generic form/grid schema; global shared model | Capability-local models per business grid; row identity and lifecycle differ, while only the existing technical `DataGridShell` is shared. |
| Section composition | User-selected Progress applicability | Declarative section configuration: Preparation FIN discharge/PSJ Progress, Ring Spinning and Twisting both grids, Bobbin Winding discharge only; prevents client-created applicability. |
| Server authority | Client totals/previews | Store raw strings and row status only; DTOs contain server projections as readonly fields. No browser aggregation or calculation. |
| Integration | Speculative HTTP/mock success | Extend `SpinningGateway` behind cancellable typed operations while `unavailableGateway` implements every seam without HTTP or fabricated data. |
| Delivery | Prior seven broad PRs | Ten narrower feature-chain slices, each targeted below 400 changed lines with its own tests and rollback boundary. |

## Data Flow

```text
Protected route -> spinning workspace -> section configuration -> independent grid models
                                      -> local raw-row drafts -> gateway -> unavailable
Server response (future) -> request-key check -> readonly projection/status -> grid
URL filters -> reporting gateway -> loading/empty/populated/stale/failure/unavailable
```

Repeated discharge rows retain distinct IDs. Progress is keyed uniquely by machine+yarn count; identity changes abort/invalidate continuity reads. Skeining, Waste, and Quality drafts never enter section Production/Progress submission state.

## File Changes

| File | Action | Description |
|---|---|---|
| `frontend/src/features/spinning/sections/{configuration,dischargeModel,progressModel}.ts` | Create | Applicability, raw rows, paste, validation, request keys, snapshots. |
| `frontend/src/features/spinning/sections/{ProductionDischargeGrid,ProgressGrid,SectionWorkspace,SkeiningGrid}.tsx` | Create/Modify | Controlled independent grids; remove textarea and Progress checkbox. |
| `frontend/src/features/spinning/{quality,waste,reporting,corrections}/**/*` | Create | Independent profile/grid, weighed-waste, read, and recovery owners. |
| `frontend/src/features/spinning/integration/{contracts,unavailableGateway}.ts` | Modify | Typed operations and unavailable implementations. |
| `frontend/src/features/spinning/{routes.tsx,routes.test.tsx}` | Modify | Compose and verify workspace-specific grids. |
| `frontend/src/app/routes/{index.tsx,lazy-pages.ts}` | Retain | Existing protected composition; no RBAC change. |
| `frontend/docs/features/yarn-spinning.md` | Retain | Dependency only; replanning does not edit it. |

## Interfaces / Contracts

```ts
type GridRowState = 'pending' | 'invalid' | 'complete' | 'acknowledged-no-production'
type SectionGridConfig = { discharge: 'fin-only' | 'all' | 'none'; progress: boolean; skeining: boolean }
type RemoteState<T> = Loading | Unavailable | Failure | Empty | Populated<T> | Stale<T> | Conflict
```

Discharge snapshots preserve every populated event row. Progress snapshots enforce unique machine+yarn-count identities but never derive values. Sample profiles supply ordered measurement IDs, units, validation metadata, readonly server results, and tolerance statuses. Waste snapshots contain only entered real weighed waste.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Row identity, paste shapes, status, applicability, Progress uniqueness/stale rejection | Vitest pure model tests; assert no totals/calculations. |
| Component | Keyboard editing, repeated discharge rows, FIN/PSJ split, absent Progress, ordered Sample, independent Skeining/Waste, retained drafts/unavailable/conflict | Testing Library with gateway fakes. |
| Acceptance | Protected routes, narrow overflow, focus/status announcements | Manual viewport/keyboard smoke; run `pnpm vitest run`, `pnpm lint`, `pnpm build`. |

## Threat Matrix

Routing is retained but workspace composition changes; no execution/VCS boundary exists.

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths | Executable-looking docs | N/A: no file classification | None | None |
| Git repository selection | Relative/absolute selectors | N/A: no VCS execution | None | None |
| Commit state | Index variants | N/A: no commit automation | None | None |
| Push state | Tracking/refspec variants | N/A: no push automation | None | None |
| PR commands | Head/environment/composed commands | N/A: planning only | None | None |

## Migration / Rollout

Feature-chain order: PR1 foundation (complete); PR2 corrective discharge/configuration grid; PR3 Progress/continuity; PR4 Skeining; PR5 Quality profile/configuration; PR6 ordered Sample grid; PR7 Waste; PR8 reporting/records; PR9 corrections/recovery; PR10 accessibility/responsive verification. PR2 rewrites the current uncommitted child-branch `sections/**`, route tests, and gateway additions: its textarea, user-controlled Progress checkbox, and generic five-section model are rejected work-in-progress, not a baseline to preserve. Each child targets its immediate predecessor, must show a clean ≤400-line diff, and carries focused tests; split again before review if measured lines exceed 400. No data, backend, PRD/documentation, or RBAC migration.

## Open Questions

None blocking; concrete HTTP DTO mapping remains deferred until backend contracts exist.
