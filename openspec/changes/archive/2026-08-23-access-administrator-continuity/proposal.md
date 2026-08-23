# Proposal: Access Administrator Continuity

## Intent

Prevent ordinary administration from leaving Colibri Hub dependent on one administrator. Require two distinct operational System Administrators while providing an externally governed recovery procedure for exceptional restoration.

## Scope

### In Scope
- Define operational: Active Authentication account, Active Access profile, and current reserved-role assignment.
- Preserve two distinct operational administrators atomically across ordinary reducing mutations.
- Define controlled initialization and a manual external-recovery procedure: two-custodian approval for ordinary recovery; unilateral activation only for a documented administrative emergency, with immediate notification, closure, revocation of temporary material, and post-incident review.
- Align PRDs, conceptual vocabulary, enforcement, and error/API semantics.
- Implement #92 fixture isolation: independent fixtures never mutate canonical seeded administrators.

### Out of Scope
- Duplicate administrator roles, hierarchy, direct grants, or self-service recovery.
- Ordinary-administrator access to recovery credentials or operations.
- Treating #92 as a production-policy substitute.
- Any dedicated backend recovery operation or API; that automation is a later change.

## Capabilities

### New Capabilities
- `access-administrator-continuity`: Cross-context two-administrator policy, recovery contract, enforcement, and evidence.

### Modified Capabilities
None. Existing password-replacement and frontend safe-rejection contracts remain unchanged.

## Approach

Preserve one reserved role; count principals, not role rows. Centralize the normal two-administrator invariant in trusted Access/Authentication application boundaries with transactional locking. Recovery remains external to ordinary RBAC and manual-first: two custodians approve ordinary activation; one may activate only for a documented administrative emergency and must immediately notify the other, close the event, revoke temporary material, and complete post-incident review. No recovery endpoint, privileged API, or automated bypass is delivered here.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `docs/prd/access-control.md`, `docs/prd/auth.md`, `docs/data-models/conceptual/access-dictionary.md` | Modified | Floor, operational state, recovery governance |
| `docs/runbooks/administrator-recovery.md` | New | External custody and manual recovery procedure |
| `backend/src/access/`, `backend/src/auth/` | Modified | Atomic policy enforcement |
| `supabase/migrations/` | Modified | Persistence/locking support if required |
| `backend/integration_tests/` | Modified | #92 isolated evidence |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Emergency exception becomes ordinary access | Med | Restrict unilateral action to documented emergencies; require immediate co-custodian notification, closure, temporary-material revocation, and review |
| Cross-context races violate the floor | Med | Transactional decision, locking, integration proof |
| Existing single-admin installations block changes | High | Controlled migration/recovery path before enforcement |

## Rollback Plan

Revert enforcement and schema together to the prior guard; retain recovery evidence and never delete identities or history. Revoke any active external recovery authorization and complete the runbook closure.

## Dependencies

- Two designated recovery custodians, documented emergency criteria, and an audit-retention owner.
- #92 fixture isolation for trustworthy integration evidence.

## Success Criteria

- [ ] Ordinary reducing mutations cannot leave fewer than two operational administrators.
- [ ] The manual runbook requires two-custodian ordinary approval and constrains unilateral action to documented emergencies with immediate notification, closure, temporary-material revocation, and post-incident review.
- [ ] Isolated integration evidence proves normal enforcement and recovery boundaries without canonical-fixture mutation or a recovery API.
