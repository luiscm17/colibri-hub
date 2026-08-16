# Proposal: Frontend Access Control

## Intent

Deliver the complete frontend Access Control experience so users see only currently permitted capabilities and the System Administrator can govern access safely. The frontend consumes backend-resolved authorization; it never becomes an authorization authority.

## Scope

### In Scope
- Capability-owned effective-authorization bootstrap, exact action/scope checks, and default-deny protection for navigation, routes, and actions.
- Complete Access administration: profiles and role assignment, roles, presets, scopes, history, previews, drafts, concurrency, accessibility, async recovery, and verification.
- One-way retirement of the permissive resource-based authorization seam; standardized `403` refresh/re-evaluation without mutation replay.

### Out of Scope
- Authentication credentials, provider/session implementation, or account-administration redesign.
- Backend Access-policy redesign, independent Access-profile provisioning, or business-context validation rules.

## Capabilities

### New Capabilities
- `frontend-access-control`: Frontend effective authorization, protected experience, and Access administration backed by Access APIs.

### Modified Capabilities
None.

## Approach

Create an Access Control capability with a narrow public snapshot/check/refresh contract and one atomic authorization state. It consumes only Authentication eligibility/session-end semantics, adapts strict backend variants, and exposes exact action-plus-scope requirements to composition and business capabilities. Roles, labels, routes, URLs, HTTP methods, and scope prefixes never authorize. Delivery remains one change, sequenced protection-first through chained review slices; exact tasks remain deferred.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/features/access-control/` | New | Capability, API adaptation, state, administration, and public contract. |
| `frontend/src/features/auth/` | Modified | Consume/publish only eligibility and session-end semantic boundary. |
| `frontend/src/app/routes/`, `app/layout/`, `navigation-data.tsx` | Modified | Exact protected navigation, routes, and state outcomes. |
| Protected feature pages and `frontend/src/api/` | Modified | Exact action checks and normalized denial recovery. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Authentication contract is unproven | High | Block foundation/protection acceptance until eligibility and session-end behavior is proven. |
| Stale grants, previews, or edits confirm mutations | High | Preserve safe drafts; reload authority; require fresh preview and explicit confirmation. |
| Broad work exceeds review capacity | High | Use dependency-ordered autonomous chained slices; PR1 has a maintainer-approved exception for its generated dependency lockfile diff. |

## Rollback Plan

Revert the affected delivery slice, restore the prior shell behavior only if backend protection remains intact, and clear published Access snapshots/drafts. Never retain or replay a rejected mutation.

## Dependencies

- Authentication must publish and prove eligibility (`next_step=load_access`) and session-end clearing semantics.
- Existing backend Access APIs and error/version contracts remain authoritative.

## Success Criteria

- [ ] Only `ready` Access state drives protected content; exact backend action/scope grants decide all client protection.
- [ ] The five administration destinations and governed mutations meet draft, preview, concurrency, accessibility, async, and security contracts.
- [ ] Authentication handoff conformance and feature scenarios are proven at justified test/manual levels.
