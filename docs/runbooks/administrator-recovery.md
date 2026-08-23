---
document_type: runbook
status: active
scope: access-control
owner: security-operations
---

# Administrator Recovery

## Purpose

Restore two distinct operational System Administrators when controlled initialization cannot do so. This procedure is external to ordinary RBAC: no application endpoint, backend bypass, or ordinary administrator credential may activate recovery.

An operational System Administrator has an Active Authentication account, an active Access profile, and a current assignment to the reserved System Administrator role.

## Custody and Evidence

- Designate two distinct recovery custodians and record their current contact channels.
- Store recovery material outside Colibri Hub under dual custody; ordinary administrators cannot access it.
- Retain the request, approver identities, time, reason, affected identities, actions, evidence location, and closure record with the audit-retention owner.

## Ordinary Recovery

1. Record the loss of continuity and the target second operational administrator.
2. Obtain and record approval from both designated custodians.
3. Use controlled provider and database operations to establish the account, active profile, and current reserved-role assignment.
4. Verify two distinct operational administrators, record the evidence in the continuity migration state, and enable ordinary enforcement.
5. Notify stakeholders, revoke temporary recovery material, and close the event.

## Administrative Emergency

One custodian may activate recovery only for a documented administrative emergency that prevents timely dual approval. The custodian must record the emergency, immediately notify the other custodian, follow the ordinary verification steps, revoke temporary material, close the event, and complete a post-incident review with both custodians.

## Prohibited Actions

- Do not use recovery for ordinary access administration.
- Do not create a recovery API, privileged application bypass, shared account, or duplicate reserved role.
- Do not delete identities or history as part of recovery.
