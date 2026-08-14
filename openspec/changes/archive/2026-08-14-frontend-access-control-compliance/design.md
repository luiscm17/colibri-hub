# Design: Frontend Access Control Compliance

## Technical Approach

Correct Access administration without new APIs. Replace generic routing with capability-owned adapters; compose existing guards/recovery. Covers all requirements/scenarios through #82 → #83 → #84; #78/#85 remain boundaries.

## Architecture Decisions

| Decision | Alternatives rejected | Rationale |
|---|---|---|
| One `administration/operations.ts` matrix owns routes, controls, adapters. | Generic CRUD. | Prevents Scope/History detail requests. |
| Capability-local route state/drafts; shell composes routes. | Global store; query-string drafts. | Keeps protected content local. |
| Exactly two preview gates. | Generic preview framework; preview every mutation. | Only user-role replacement and role permission replacement have backend preview contracts. |
| One final confirmation, optional form-level reason. | Per-field reasons; fabricated explanation. | One atomic mutation needs one reason. Empty omission remains `reason: ""` until #85 aligns HTTP/application/audit policy. |

## Operation and Route Model

| Family | Supported states / contract | Explicitly unavailable |
|---|---|---|
| Users | `/access/users`, `/:userId`, assignment replacement, status lifecycle | Access-owned create, role-members |
| Roles | collection, `new`, `/:roleId`, `/:roleId/edit`, lifecycle | direct permissions |
| Presets | collection, `new`, `/:presetId`, `/:presetId/edit`, lifecycle, exact-copy and adjustable role draft | synchronization |
| Scopes | collection, registration from definitions, row lifecycle | detail/edit route/request |
| History | collection and four filters only | detail/create/edit/lifecycle |

`AdministrationRouteState` serializes family, mode, subject ID, criteria, page. Entry captures `{family, criteria, page, selectedSubject?}`; direct URLs reconstruct without a row. Drafts/previews/reason/impact never enter URL/history/storage. Dirty departure confirms: decline preserves; confirm clears/restores origin. Missing/invalid/stale detail → collection; denied/session loss → nearest permitted profile/forbidden after clearing; abort publishes nothing; empty page decrements once with criteria.

## Module Boundaries and Data Flow

Create `operations.ts`, `route-state.ts`, `AdministrationShell.tsx`; split `AdministrationPage.tsx`. Keep forms, presets, scopes, History and mutations private to Access. Routes declare only matrix states; `GovernancePanel.tsx` retires.

```
route + origin → AdministrationShell → operation adapter → httpJson
                                   ↓                 ↑
                           isolated draft → MutationGate → preview/apply
Access/Auth generation ────────────┴───────────────────────┘
```

Matrix uses `/access/scopes` + `/access/scope-definitions`: active registered scopes/supported actions only; reserved actions cannot select. Inactive references are historical/read-only/removable. Exact copy uses its endpoint; adjustable copy creates its isolated role draft. Both state “copied once; later changes do not synchronize.” History renders only returned actor, time, reason, subject, kind.

## File Changes

| File | Action | Description |
|---|---|---|
| `frontend/src/features/access-control/administration/{operations,route-state,AdministrationShell}.ts(x)` | Create | Matrix, safe route/origin, composition. |
| `frontend/src/features/access-control/administration/{forms,presets,scopes,history,mutations}/` | Create | Governance, constrained read models, two gates. |
| `AdministrationPage.tsx`, `GovernancePanel.tsx`, `governance.ts` | Modify/Delete | Retire generic/direct-mutation behavior. |
| `frontend/src/app/routes/index.tsx` | Modify | Explicit supported routes only. |

## Mutation Contract

```ts
type PreviewKey = { operation: 'replace-user-roles' | 'replace-role-permissions'; subjectId: string; fingerprint: string; subjectVersion: number; accessGeneration: string; requestGeneration: number }
```

Normalize sorted unique IDs/pairs and metadata; fingerprint JSON. States: `editing → previewing → ready → confirming → applying → succeeded|editing`. Draft/subject/session changes, stale response, `409`, last-admin, `403`, `401` invalidate. Pending key suppresses duplicates; apply once uses preview version. `403` refreshes/re-evaluates, never replays. Access loss clears draft/impact; conflict reloads and requires preview.

Confirmation shows local metadata changes separately from backend permission impact. It blocks zero delta. Impact is labelled “Users affected by this proposed change,” not membership: show total and first six, with keyboard-accessible expandable remainder. Added/removed values use text/icons, not color alone.

## Testing and Evidence

| Layer | Coverage |
|---|---|
| Deterministic Vitest RED→GREEN | matrix/prohibited URLs; origin/discard/recovery; inactive references; independent presets; scope/history limits; gate fingerprints/generations/one apply/no replay; six-user expansion, zero delta, reason wire value, focus/announcements/privacy. |
| Router/component integration | direct refresh, dirty departure, 404/empty-page/latest-only/abort, 403/Auth handoff clearing, both confirmations and `409` outcomes. |
| Real backend/manual | reversible role, preset, scope, user-role, and ordinary shared-role journeys; request counts/responses, History filters, responsive keyboard/screen-reader checks. No mock substitutes for these journeys. |

Observability records operation, phase, outcome, correlation, duration—not reason, identities, matrices, payloads. Dialogs provide semantics, focus return, announcements; narrow layouts retain impact/actions.

## Threat Matrix

N/A — no shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary. Routing is covered by the RED tests above; the referenced threat-matrix file was not present in the installed skill path.

## Rollout / Rollback

Feature chain: #82 routes/recovery (revert shell/routes); #83 governance (revert forms/adapters); #84 gates (revert gate/confirmation). No persistence/RLS. Under 800 lines, split #83 into forms/matrix+presets then scopes/history; split #84 into gate+user then shared-role impact/accessibility if forecast exceeds 600–700. Tests/evidence stay with work units.

## Open Questions

- [ ] #85 must establish durable omitted/trimmed/required-reason policy; this change preserves current empty-string compatibility only.
