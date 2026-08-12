# Design: Frontend Access Control

## Technical Approach

Access owns authorization and administration.

## Architecture Decisions

| Decision | Rejected | Rationale |
|---|---|---|
| Separate Access | Extend Authentication | Preserves ownership. |
| Exact catalog + identity | Strings/roles/routes; last response | Backend pairs decide; prevents staleness. |
| Backend governance | Client inference | Previews, versions, reasons, recognition, invariants stay authoritative. |

## Authentication Handoff and State

Authentication is external and exposes `{condition, accountId?, handoffId?, retryable?}`. Opaque `handoffId` changes per session/account transition but is stable for equivalent events. Bootstrap identity is `(accountId, handoffId, load_access)`.

| Condition/event | Access result |
|---|---|
| unresolved | `waiting-for-authentication`; clear/withhold; no request. |
| eligible `authenticated + load_access`, new identity | `loading`; bootstrap. |
| repeated eligible identity | No bootstrap. |
| password change | `waiting-for-authentication`; clear snapshot/drafts. |
| unauthenticated/ended | `waiting-for-authentication`; abort, clear snapshot/drafts, withhold content. |
| Authentication unavailable | `unavailable`; no snapshot/request. |
| eligible retry | `loading`; new operation identity. |

`/access/me`: active -> `ready`; normalized `profile_not_found`/`profile_inactive` -> matching `blocked`; non-profile `403` -> normalized denied/unavailable, never profile inference; `401/authentication_required` -> session-ended and clearing; network/service/invalid -> `unavailable`. Bootstrap publishes only when handoff/operation are current; abandoned work is silent.

## Ownership, Flow, and Contracts

`Authentication handoff -> Access snapshot/check -> navigation, guards, actions, administration APIs`.

`Requirement` is exact `{action, scope}`: ordinary matches a pair, global supplied actions only, `anyOf` one, `allOf` all. Roles never authorize. Routes/navigation/features consume it; Access neither imports internals nor infers policy.

| Owner | Exact requirements and consumers |
|---|---|
| Warehouse | Read/write: `warehouse.raw_materials`, `warehouse.finished_products`, `warehouse.production_supplies`; views read, records write. |
| Yarn sections | Independent read/write: `yarn_spinning.section.preparation`, `ring_spinning`, `bobbin_winding`, `twisting`, `skeining`; dashboards/read, operations/write. |
| Quality/Waste | Independent read/write: `yarn_spinning.process_quality`, `yarn_spinning.waste`. |
| Lot Processing | Dashboard/queue/detail: `read lot_processing`; stages inventory, dyeing, drying, winding, bagging, quality independently use `lot_processing.stage.*` read/write. |
| Transversal dashboard | `read transversal.consolidated_dashboard`; filters neutral. |

Unexpected protected `403` preserves safe input, refreshes once, rechecks route/action, and NEVER replays a mutation.

## Administration and Operation Correlation

Five gated families are addressable independent of mounted rows. Valid origin restores; missing/stale/denied/history subjects clear to nearest permitted destination. Collections paginate, label local filtering, distinguish load/refresh.

| Family | Contract |
|---|---|
| Profiles/assignments | Creation stays Authentication provisioning. Status reason/no conflict. Active selectable; inactive read-only. Replacement previews, sends preview version/reason. |
| Roles | Create/edit/lifecycle reason; supported pairs. Preview version; edit/`409` reloads current, requires new preview. |
| Presets | Loaded version/reason; no preview. Exact copy unchanged; adjustable isolated editable draft; both roles independent. |
| Scopes | Register recognized definition + reason; no free-form/automatic grants. Lifecycle loaded version/reason; no preview. |
| History | Read-only pagination; supported filters only. |

Every bootstrap, collection, detail, preview, refresh, and mutation carries `{kind, subject-or-criteria, generation}`. New identity invalidates old work; only current work publishes; subject switches clear prior content. Initial load retains nothing; refresh labels retained content. A mutation fingerprint admits one submit. Drafts are isolated, never reload-persisted: preserve safe input for recoverable failure/`403` explanation/`409`; invalidate preview on edit/conflict/authority change; clear on success, denied departure, session end; dirty departure confirms discard/focus.

## File Changes

| File | Action |
|---|---|
| `frontend/src/features/access-control/` | Create capability and correlation. |
| Auth, shell/routes/navigation | Modify handoff, requirements; retire seam. |
| Capability integrations/API/test configuration | Modify denial handling and focused verification. |

## Risk-to-Evidence Matrix

| Risk | Focused logic | Interaction | Integration | Workflow / recorded manual |
|---|---|---|---|---|
| Handoff, adaptation, races | state/adapter/identity | loading/silence | Auth-to-Access | real-backend handoff |
| Route/history, no-replay `403` | decisions | denied/fallback/input | router + refresh | protected journey |
| Admin recovery/concurrency | invalidation/fingerprint | draft/preview/conflict | API/version | mutation/last-admin/recovery |
| Responsive, keyboard/focus, assistive tech | — | selector/matrix/preview | — | viewport/keyboard/screen-reader |

Mocks stop at deterministic frontend boundaries, not operational contracts. Notify the user before real-backend checks and await user startup. Run lint/build per slice. Keep auto-chained boundaries reviewable within the active session budget when practical; PR1 uses the maintainer-approved `size:exception` for its structurally required generated dependency lockfile diff.

## Threat Matrix

| Boundary | Applicability | Response / planned RED tests |
|---|---|---|
| Documentation-like paths | N/A — no execution/classification | None. |
| Git repository selection | N/A — no VCS integration | None. |
| Commit state | N/A — no commit automation | None. |
| Push state | N/A — no push automation | None. |
| PR commands | N/A — no PR automation | None. |

Routing is applicable outside these rows: RED interaction/integration proof covers loading, blocked, unavailable, direct/history denial, fallback, and no protected disclosure.

## Migration / Rollout

Introduce Access contract/guards, migrate every `isResourceAllowed` consumer, then delete the seam after inventory. No persistence, Supabase, or RLS migration.

## Open Questions

- [ ] Authentication must prove opaque handoff identity and session-ended publication before foundation acceptance.
