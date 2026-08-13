## Exploration: frontend-access-control-compliance

### Current State

The completed `frontend-access-control` change established the Access capability, exact action/scope checks, default-deny protected navigation, one-refresh/no-replay `403` recovery, and a constrained administration shell. Its final verification passed tests/build/lint but failed product compliance: the visible administration surface lacks independent create/edit workflows, complete dirty-origin recovery, governance forms, and fresh preview/confirmation. The report claims seven requirements and eight scenarios but records `0/7`; the checked baseline spec currently contains seven requirement/scenario pairs, so the corrective proposal/spec MUST reconcile the authoritative scenario count instead of carrying the inconsistency forward. The corrective change MUST reference the completed change and MUST NOT rewrite its closed history.

Backend authority is sufficient for most corrective behavior: admin endpoints expose role/preset/scope CRUD and lifecycle, recognized scope definitions, two read-only preview contracts, loaded versions/reasons, and paginated audit history. The backend audit response exposes actor, time, reason, subject, and change kind, but not previous/resulting configuration. There is no Scope detail endpoint, no role-members directory contract, and no preview for profile/preset/scope/lifecycle/create operations.

### Affected Areas

- `openspec/changes/frontend-access-control/` — closed baseline, including proposal/spec/design/tasks, evidence, and failed verification report; use as historical reference only.
- `frontend/src/features/access-control/administration/AdministrationPage.tsx` — current generic `family/:subjectId?` route fetches every detail family, including unsupported Scope detail and History detail implications; lacks create/edit modes, origin snapshots, dirty departure, and uniform recovery.
- `frontend/src/features/access-control/administration/GovernancePanel.tsx` and `governance.ts` — current mutation path directly replaces user roles or toggles status; `MutationGate` is bookkeeping, not a rendered fresh-preview/confirmation gate.
- `frontend/src/app/routes/index.tsx` and `frontend/src/app/navigation-data.tsx` — administration routing currently uses one generic protected route and must consume the corrective operation matrix without speculative requests.
- `backend/src/access/adapters/http/admin_router.py` and `backend/src/access/adapters/http/models.py` — authoritative endpoint and response limits: exact preview payloads, loaded versions, recognized definitions, and audit fields.
- `backend/src/access/ports/previews.py` and `backend/src/access/domain/{actions,scopes,authorization}.py` — preview semantics, exact action/scope matching, inactive-scope denial, reserved actions, and no scope-prefix inheritance.
- `docs/prd/access-control.md`, `docs/architecture/context-map.md`, `docs/domain/ubiquitous-language.md` — normative ownership and business rules: roles own permissions, presets copy independently, inactive scopes deny ordinary access, and Access remains policy-only.
- `openspec/changes/frontend-access-control-compliance/` — new corrective delta artifacts; only `exploration.md` is created in this phase.

### Corrective Delta and Non-Goals

The delta should restore the missing frontend behavior while preserving the completed foundation: backend-authoritative exact action/scope RBAC, default-deny decisions, protected-content clearing, latest-only publication, abort silence, and no mutation replay.

Non-goals are backend authorization redesign, new preview/reservation/idempotency contracts, audit-detail invention, role-members discovery, direct user permissions, scope-prefix inheritance, authentication/account provisioning, and absorption of #78's MultiSelect/member-directory ownership. #82 owns addressability/origin/dirty departure; #83 owns governance forms/matrices/lifecycle/history presentation; #84 owns preview gates for exactly the two existing preview contracts.

### Operation Matrix Decision Boundary

The corrective specification MUST make this matrix explicit before implementation:

| Family | Collection | Detail | Create | Edit | Lifecycle | History/detail authority |
|---|---|---|---|---|---|---|
| Users | Supported | Supported | Not Access-owned; Authentication provisioning | Assignment/status only, per existing contracts | Supported | No user audit detail endpoint |
| Roles | Supported | Supported | Supported | Supported | Supported | No audit-detail endpoint |
| Presets | Supported | Supported | Supported | Supported | Supported | No audit-detail endpoint |
| Scopes | Supported | **Not supported**; collection/definition context only | Registration from recognized definition | No Scope detail/edit contract | Supported from collection row/version | No audit-detail endpoint |
| History | Supported with exactly four existing filters | **Not supported** | Not supported | Not supported | Not supported | Existing collection response only |

This is the recommended resolution because it follows actual backend contracts and the PRD boundary. The broad prior wording for “all families” must be narrowed explicitly rather than implemented through generic routes.

### Unresolved Product and Contract Decisions

The following decisions are required in proposal/spec/design; they are not all safely inferable from code:

1. **Audit before/after exposure:** recommend narrowing the frontend requirement to currently authoritative fields. Do not derive previous/resulting values or add an endpoint. Exposing those values is a backend/product contract decision outside this frontend-only correction.
2. **Adjustable preset semantics:** recommend an isolated role draft initialized from preset data and submitted through ordinary role creation. Preserve the existing exact-copy endpoint as exact-copy-only. Copy wording MUST state “copied once; later changes do not synchronize.”
3. **Inactive scopes:** backend authorization filters inactive scopes and ordinary permission validation rejects inactive references. Recommend showing existing inactive references as historical/read-only where safely returned, excluding inactive scopes from new grants, and requiring removal through an ordinary role edit; do not invent a contract that permits retaining an inactive permission in a new update.
4. **Scopes and History operations:** recommend the matrix above. Genuine product confirmation is only needed if the product wants Scope detail or History detail beyond current contracts; implementation MUST wait for an approved backend contract in that case.
5. **Copy wording:** product copy should distinguish “Exact copy” from “Adjustable draft” and explicitly communicate independent role ownership. This is a human wording decision, with the semantic rule already authoritative in the PRD/backend.
6. **Reason timing/validation:** recommend collecting a nonblank, trimmed reason before preview/apply UI can proceed; preview does not consume it, apply does. Backend currently accepts a string model but domain/application validation must remain authoritative; whitespace-only behavior requires confirmation or a backend contract check before relying on client validation.
7. **Affected-user presentation:** recommend count-first summary with bounded progressive disclosure for the backend-returned list, while clearly labeling it “Users affected by this proposed change,” never membership. Exact threshold/list behavior is a human product decision.
8. **Zero delta:** the backend preview can return empty additions/removals. Whether an unchanged replacement is blocked or intentionally audited as a no-op is a human product decision; recommend blocking as no meaningful mutation unless product explicitly requires an audited no-op.
9. **Role metadata preview:** the role preview reports permission impact only, not name/description changes. Recommend summarizing metadata changes locally as draft changes, while labeling permission impact as backend preview evidence; product must approve whether metadata-only changes can share the same confirmation or require a separate confirmation presentation.

### Dependencies and Ordering

Recommended dependency order is `#82 → #83 → #84`, with #78 overlapping #84 only at user role-assignment input and remaining outside this delta's ownership. #82 establishes stable supported routes, origin snapshots, dirty-discard, and fallback semantics consumed by both governance forms and mutation-local confirmation. #83 then builds role/preset/scope forms and the permission draft that #84 previews. #84 is last because it consumes #83's draft and must bind confirmation to the final normalized subject/draft/version.

The order is not a backend dependency: the backend contracts already exist. It is a frontend integration dependency that prevents duplicate routing, draft, and matrix authorities. #78 may proceed independently for current assignments and complete role catalog loading, but its selector must consume #84's preview gate and must not infer membership from preview `affected_users`. If #78 changes the assignment draft shape, #84's fingerprint contract must be reviewed before integration.

### PR7/PR8/PR9 Work-Unit Assessment

Treat the proposed slices as valid autonomous work units only with explicit boundaries:

1. **PR7 / #82 — addressable administration and recovery:** valid first unit. It should include the operation matrix, supported route states, origin/dirty-discard/fallback behavior, and focused tests/evidence. It must not include governance forms or mutation preview. Estimated review load: medium; keep within the 800-line session budget by avoiding broad component rewrites.
2. **PR8 / #83 — governance forms and scope/history compliance:** valid second unit after PR7. It should include role/preset matrices, exact versus adjustable copy, recognized scope registration/lifecycle, inactive-scope presentation, and constrained history. It must not implement fresh preview/confirmation or affected-user impact. Estimated review load: high; split internally if authored changes plus tests exceed roughly 600–700 changed lines, rather than treating “PR8” as automatically reviewable.
3. **PR9 / #84 — sensitive mutation preview and recovery:** valid final unit after PR8. It should include only user-role and shared-role permission preview, explicit confirmation, version binding, conflict/authority/session invalidation, no replay, privacy, focus, and evidence. Estimated review load: high; likely requires a focused sub-slice for shared-role impact presentation if the 800-line budget is approached.

With `auto-chain`, use a feature-branch chain `PR7 → PR8 → PR9` into the existing Access tracker branch. The 400-line default is not silently waived: the session budget is 800 changed lines, so tasks must forecast additions plus deletions and split any unit that would consume the budget or exceed reasonable reviewer cognitive load. Tests, documentation, and evidence belong with the behavior they verify.

### Approaches

1. **Contract-first corrective delta with dependency-ordered chained work units** — Narrow the matrix to backend-supported operations, implement #82 then #83 then #84, and record genuine product choices as explicit decisions.
   - Pros: preserves backend authority; prevents speculative endpoints; keeps issue ownership clear; supports autonomous rollback and review.
   - Cons: requires product decisions before some UI copy/edge behavior; PR8/PR9 may need an additional split under the 800-line budget.
   - Effort: High

2. **Generic administration framework expansion** — Make the existing family route dynamically support every CRUD/detail variant and attach generic mutation behavior.
   - Pros: superficially reduces route code and initial duplication.
   - Cons: conflicts with Scope/History contract limits; encourages speculative requests; obscures ownership and operation differences; makes dirty state and preview semantics unsafe.
   - Effort: High

### Recommendation

Choose the contract-first corrective delta. Record the operation matrix and backend limitations as the first planning authority, preserve the completed change as historical baseline, and use `#82 → #83 → #84` as the default chain. Mark affected-user threshold, zero-delta treatment, reason timing/whitespace policy, metadata confirmation, and final copy as explicit human decisions; recommend defaults where the existing PRD/backend semantics already constrain the safe direction. Keep #78 separate and integrate only through an explicit role-assignment draft/preview contract.

### Risks

- The broad prior specification can be accidentally re-expanded into unsupported Scope or History detail operations.
- Audit before/after values are normative PRD expectations but absent from the current HTTP response; claiming compliance without a backend contract would be false.
- Inactive-scope UX can accidentally offer stale permissions for new grants or silently drop historical references.
- Preview impact is authoritative but bounded list presentation can create privacy, performance, and accessibility tradeoffs.
- PR8 and PR9 are behaviorally dense; an 800-line budget does not guarantee a single reviewable PR per issue.
- Existing route/API genericity can create duplicate authorities for operation matrices, origin state, or mutation fingerprints.

### Ready for Proposal

Yes, with the operation matrix and non-goals carried forward. Before proposal/spec approval, obtain product decisions for zero-delta behavior, reason timing/whitespace validation, affected-user disclosure bounds, metadata-change confirmation, and user-facing copy. No code implementation or `sdd-apply` is authorized by this exploration.
