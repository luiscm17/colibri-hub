# Exploration: frontend-access-control

## Executive Summary

The frontend has Authentication composition and a temporary resource-based authorization seam, but no Access Control capability. The backend already exposes the current-access snapshot and the complete administrative endpoint family, while frontend administration, exact authorization, protected navigation/routes/actions, and their verification are missing. This is one coherent Access Control change; implementation should be dependency-ordered into reviewable work units rather than split into separate SDD changes.

## Current-State Evidence

### Composition and temporary seams

- `frontend/src/main.tsx` mounts only `AuthProvider` around `App`.
- `frontend/src/features/auth/context/AuthContext.tsx` owns Authentication state and exposes `isResourceAllowed(resourceType)`, but the implementation is a stub that always returns `true`.
- `frontend/src/features/auth/context/auth-context.ts` exposes the resource-string callback as the only authorization-like public seam; it has no action/scope contract or Access snapshot.
- `frontend/src/app/navigation-data.tsx` declares `resourceType` values such as `warehouse:bales`, `spinning:quality`, and `admin`, which are inconsistent with backend scope identifiers and the specification's exact action/scope requirements.
- `frontend/src/app/layout/Sidebar.tsx` filters navigation through that resource callback. It does not derive visibility from effective authorization, exact requirements, `anyOf`/`allOf`, or global grants.
- `frontend/src/app/routes/index.tsx` protects only authentication state. All authenticated users can reach business routes, the placeholder `/admin/master-data`, and `/profile`; direct URLs are not authorization-checked.
- `frontend/src/app/layout/AppLayout.tsx` consumes the temporary callback and renders the existing shell. No Access blocked, unavailable, denied, or authorization-transition state exists.
- `frontend/src/features/admin/pages/AdminPage.tsx` is only a title placeholder. No Access users, roles, presets, scopes, or history experience exists.

### Backend contracts and authority

- `backend/src/access/adapters/http/self_access_router.py` implements `GET /api/v1/access/me`, returning identity, role summaries, and either an ordinary exact permission list or a global grant with backend-supplied supported actions and authorization version.
- `backend/src/access/adapters/http/admin_router.py` implements the endpoint family for users, roles, previews, presets, scopes, and paginated access audits; administrative routes enforce `manage_access + access_control` through backend authorization.
- `backend/src/access/adapters/http/models.py` defines strict response/request models and the ordinary/global authorization variants.
- `backend/src/access/domain/actions.py` defines the exact action vocabulary: `read`, `write`, `edit`, `edit_outside_window`, and `manage_access`.
- Backend tests cover `/access/me` ordinary/global responses, fail-closed protected Warehouse authorization, preview behavior, lifecycle invariants, pagination, and version conflicts. They do not prove frontend adaptation or interaction behavior.

### Verification availability

- `frontend/package.json` provides `pnpm lint` and `pnpm build`, but no frontend test runner, E2E tool, or coverage command is configured (`openspec/config.yaml`).
- Baseline verification completed during exploration: `pnpm lint` passed; `pnpm build` passed with a pre-existing large-chunk warning; 31 focused backend Access tests passed.
- Frontend contract, interaction, integration, accessibility, race, draft, and security scenarios currently have no automated test surface.

## Responsibility Classification

| Responsibility | Classification | Evidence / consequence |
| --- | --- | --- |
| Authentication semantic eligibility consumed by Access | Blocked by external dependency | Authentication owns login, session, account state, and `next_step`; this change must consume only the narrow semantic contract and must not redesign Authentication. |
| Effective-authorization bootstrap and singular state | Missing | No `/access/me` frontend adapter, Access state machine, atomic snapshot, refresh, or clear-on-auth-end behavior exists. |
| Exact action-and-scope decision | Missing / inconsistent | The resource callback always allows; navigation uses labels/resource strings; no exact pair, global-action, default-deny, or `anyOf`/`allOf` decision exists. |
| Protected navigation | Inconsistent with specification | Sidebar derives from temporary resource names, includes empty/unauthorized groups, and is not based on the Access snapshot. |
| Protected routes and direct URL/history behavior | Missing | Authenticated-only is the only guard; route requirements and denied/unavailable/blocked outcomes are absent. |
| Protected actions and backend `403` recovery | Missing | Existing business pages have no standardized action capability checks, one-refresh rule, safe-input preservation, or no-repeat mutation behavior. |
| Read-only administration | Missing | Admin page is a placeholder; no five destination collections/details/transitions exist. |
| User access governance | Backend implemented and conforming; frontend missing | Backend provides profiles, details, role replacement, status lifecycle, previews, and invariants; frontend has no unified account/access presentation or role governance. |
| Roles and presets | Backend implemented and conforming; frontend missing | Backend supports CRUD, reserved/global semantics, previews, and independent preset copies; frontend matrix, drafts, and flows are absent. |
| Scope lifecycle | Backend implemented and conforming; frontend missing | Backend provides recognized definitions, registration, lifecycle, versions, and no automatic ordinary grants; frontend consultation/registration is absent. |
| Access history | Backend implemented and conforming; frontend missing | Backend provides filtered paginated metadata; frontend has no read-only collection or supported filters. |
| Previews, drafts, concurrency | Backend partially implemented for core previews/conflicts; frontend missing | Backend preview and version invariants exist; frontend must preserve safe drafts, invalidate previews, map `409` outcomes, and prevent duplicate submissions. |
| Accessibility and responsive behavior | Partially implemented in generic shell; Access-specific behavior missing | Mantine shell exists, but no matrix/selector/preview semantics, announcements, focus restoration, or responsive Access surfaces exist. |
| Async behavior and stale-result rejection | Partially implemented in isolated existing APIs; Access missing | Existing HTTP client supports `AbortSignal`; no Access request identity, cancellation lifecycle, atomic replacement, or stale collection/detail/preview rejection exists. |
| Security and backend authority | Backend implemented and conforming; frontend missing/inconsistent | Backend denies protected operations; frontend currently exposes routes and actions based on a permissive client stub and must remain default-deny without treating UI controls as security. |

## Affected Areas

- `frontend/src/features/auth/` — expose only the minimal Authentication semantic eligibility/session-end contract required to start or clear Access; Authentication implementation remains external to this change.
- `frontend/src/features/access-control/` (new capability owner) — own Access models, API adaptation, state, authorization decisions, administration flows, and public contract; exact internal layout remains intentionally flexible.
- `frontend/src/app/routes/` — compose protected route requirements and state outcomes without absorbing Access policy.
- `frontend/src/app/navigation-data.tsx` and `frontend/src/app/layout/` — replace resource-string filtering with capability-owned exact requirements and derived navigation.
- Existing protected capability pages and mutation adapters — adopt narrow action/scope checks and standardized unexpected-`403` refresh/re-evaluation behavior without moving business rules into Access Control.
- `frontend/src/api/httpClient.ts` / `frontend/src/api/httpError.ts` — adapt existing authenticated transport and normalized failures as needed for strict Access response/error handling; preserve central token attachment.
- `backend/src/access/adapters/http/` and backend Access tests — consumed contract authority and integration fixtures; no backend redesign is implied unless implementation exposes a concrete contract gap.
- `frontend/docs/testing/strategy.md` and repository test/tooling configuration — verification capability is currently absent for frontend behavior and will need an explicit, justified test approach during design/tasks.

## External Dependency Boundary

Authentication is not part of this SDD change. The implementation may require an explicit semantic contract from `AuthProvider` for unresolved, unauthenticated/ended, password-change-required, eligible `load_access`, and unavailable states, plus a reliable session-end notification. Any missing or incompatible Authentication behavior must be reported as an external dependency and resolved in the separate Authentication work; it must not be absorbed into Access Control or used as permission evidence.

## Approaches

1. **Capability-owned Access Control with composition adapters** — Add one Access Control capability with a narrow public snapshot/check/refresh contract; let the shell compose it with Authentication and let business capabilities consume exact requirements.
   - Pros: preserves singular authorization ownership, backend authority, inward dependency direction, and incremental delivery.
   - Cons: requires deliberate migration away from the existing auth-owned stub and resource strings; introduces broad frontend verification work.
   - Effort: High

2. **Extend `AuthContext` into a combined authorization provider** — Put `/access/me`, administration state, and permission decisions into Authentication's existing context.
   - Pros: smaller initial composition change.
   - Cons: violates capability ownership, couples Authentication to Access administration, risks a second/merged authority, and makes the external dependency boundary ambiguous.
   - Effort: High

## Recommendation

Use capability-owned Access Control with a narrow semantic Authentication dependency. Keep one canonical effective-authorization snapshot; derive navigation, routes, and actions from exact backend action/scope requirements; keep backend authorization authoritative and default-deny. Migrate the temporary `isResourceAllowed` seam in one direction and retire it once all consumers use the Access contract. Do not infer authorization from roles, labels, routes, URLs, HTTP methods, or scope prefixes.

## Recommended SDD Scope

This single SDD change covers the complete frontend Access Control specification: bootstrap/state, exact decisions, protected navigation/routes/actions, read-only administration, user governance, roles/presets, scope lifecycle, access history, previews/drafts/concurrency, accessibility, async behavior, security, and verification. It explicitly excludes Authentication internals, credentials, provider/session design, independent profile provisioning, backend policy redesign, and business-context validation.

## Dependency-Ordered Work Units and Likely Delivery Boundaries

The following are implementation slices inside this ONE SDD change, not separate SDD changes:

1. **Foundation and contract adaptation** — Define the Authentication semantic input, strict `/access/me` mapping, Access state machine, atomic snapshot, clear/refresh behavior, exact decision function, and focused contract tests. Likely PR 1.
2. **Shell protection migration** — Replace resource strings; add exact route requirements, protected navigation derivation, direct-entry/history handling, denied/blocked/unavailable states, and retire the permissive seam. Likely PR 2.
3. **Protected operation integration** — Apply exact capability requirements to existing Warehouse and current routes/actions; implement normalized unexpected-`403` refresh once, safe input preservation, and no automatic mutation retry. Likely PR 3.
4. **Read-only administration surfaces** — Build Users, Roles, Role Presets, Scopes, and Access History collections/details with pagination, local-page search rules, responsive/accessibility semantics, and addressable navigation. Likely PR 4.
5. **Governance mutations** — Add user status/role governance, role/preset editing and copy flows, scope registration/lifecycle, reasons, drafts, previews, confirmation, version conflicts, last-administrator feedback, and refresh reconciliation. Likely PRs 5–6 depending on measured authored-line size.
6. **Hardening and verification** — Add frontend focused/interaction/integration coverage or document justified manual checks, verify races, accessibility, security disclosure rules, responsive behavior, and full specification completion. Likely final PR.

With the configured 400-line review budget and `auto-chain`, chained PRs are recommended. Exact boundaries must be finalized by `sdd-tasks` after design; the change should remain one SDD DAG and one coherent specification scope.

## Risks

- Authentication may not currently expose the exact semantic eligibility and session-end contract Access requires; this is an external dependency, not Access scope.
- The existing auth-owned permissive callback and resource names may have consumers beyond the inspected shell; migration must inventory and retire every parallel authority.
- The backend admin router is implemented, but frontend contract tests must protect strict ordinary/global variants, error normalization, pagination, and endpoint field mappings.
- No frontend test runner or E2E tool is configured; the implementation could appear complete while lacking proof for route guards, races, drafts, focus, accessibility, and denial recovery.
- The complete administration surface is broad and likely exceeds one 400-line review slice; delivery boundaries must be autonomous and reversible.
- Backend `403` and concurrency outcomes can invalidate visible client state; stale snapshots and old previews must never authorize or confirm mutations.
- Lazy loading must not expose administration code/content on the initial path to users lacking `manage_access + access_control`, while direct-route checks remain authoritative.
- Existing UI copy contains non-English labels, but generated SDD artifacts remain English; implementation should follow existing UI conventions unless the product language policy says otherwise.

## Ready for Proposal

Yes. Proceed to proposal/design for the single `frontend-access-control` change, carrying forward the Authentication external-dependency gap, the capability-owned contract recommendation, the backend endpoint evidence, and the dependency-ordered chained delivery boundaries. Do not create Authentication artifacts or split this scope into multiple SDD changes.
