---
document_type: conceptual-model
status: active
implementation: partial
scope: access-control
authority: conceptual
owner: architecture
last_reviewed: 2026-08-02
---

# Access Control Conceptual Dictionary

This dictionary summarizes the current conceptual data model for Access Control. It is a review aid, not an implemented schema. The normative [Access Control PRD](../../prd/access-control.md) governs authorization behavior, and the normative [Authentication PRD](../../prd/auth.md) governs accounts, credentials, and sessions.

Access Control answers what an authenticated person may do. It owns access profiles, roles, role assignments, permissions, role presets, business scopes, and access-change history. It does not own Authentication accounts, credentials, sessions, or business-process validity.

## Model at a glance

| Concept | Relationship |
| --- | --- |
| Person | Has one Authentication account associated with one Access profile. |
| Access profile | Holds zero or more role assignments and has an independent active or inactive lifecycle. |
| Role | Is a reusable responsibility profile shared by one or more Access profiles. |
| Role assignment | Associates an Access profile with a role while preserving assignment history. |
| Permission | Belongs to a role and combines exactly one general action with one explicit business scope. |
| Role preset | Supplies a reusable starting permission set from which an independent role is copied. |
| Access-change history | Preserves attributable evidence of profile, role, preset, scope, permission, and assignment changes. |

## Authorization rules

1. An inactive Access profile receives no protected authorization.
2. An active profile may hold multiple roles concurrently.
3. Only active assigned roles contribute permissions.
4. Effective permissions are the additive, deduplicated union of permissions from all active assigned roles.
5. Authorization succeeds only when the effective set contains the exact required general action and business scope.
6. Absence of that exact permission results in denial.
7. Permissions belong to roles, never directly to individual users or Access profiles.
8. The model has no direct grants, direct restrictions, explicit denies, role precedence, role inheritance, scope inheritance, or wildcard matching.
9. Authorization does not replace validation by the business context that owns the requested operation.

## Core concepts

### Authentication account

The Authentication-owned login identity for one person. It governs the organizational email, credentials, account state, and sessions. Successful Authentication establishes identity but grants no business permission.

An Authentication account and an Access profile are associated but remain separate concepts with separate lifecycle authority.

### Access profile

The Access Control representation of an authenticated person. It determines whether that identity may receive effective permissions and connects the person to one or more roles.

An Access profile is created only through the unified provisioning flow coordinated by Authentication. Access Control does not expose an independent user-facing profile-creation operation.

Profile lifecycle rules:

- An active profile may receive permissions through its active assigned roles after Authentication admits protected entry.
- An inactive profile receives no protected authorization, even if its role assignments remain recorded.
- Inactivating only the profile does not disable the Authentication account or change credentials.
- Disabling an Authentication account also inactivates the associated Access profile.
- Re-enabling an account may reactivate the profile only after its roles and administrator invariants are valid.
- A profile may be active while its Authentication account awaits mandatory password replacement, but protected authorization remains unavailable until Authentication becomes active.
- Inactivation and reactivation preserve identity, prior assignments, and access history.

### Role

A configurable, reusable set of permissions representing a responsibility profile. Roles describe authorization capabilities, not organizational job titles, shifts, pages, or fixed workflow participants.

Several Access profiles may share one role, and one Access profile may hold several roles. Changing a shared role changes the effective permissions of every profile assigned to it. An inactive role contributes no permission but remains available for historical traceability.

### Role assignment

The association between an Access profile and a role. Assignments support multiple concurrent roles and preserve additions and removals over time so previous access configurations remain traceable.

Role assignment does not represent a shift, job title, business-record owner, or direct permission grant.

### Permission

A role-owned authorization grant consisting of exactly:

- one general action; and
- one explicit business scope.

The supported general actions are:

| General action | Business meaning |
| --- | --- |
| Read | Consult information in the stated business scope. |
| Write | Record a new business fact in the stated business scope. |
| Edit | Correct an existing business fact within the operational window defined by its owning context. |
| Edit Outside the Operational Window | Perform an exceptional correction after the ordinary correction window has closed. |
| Manage Access | Administer Access profiles, roles, presets, assignments, scopes, and permissions. |

Actions are independent. Read does not imply Write or Edit, and presentation details such as pages, dashboards, filters, or HTTP methods do not define the required action.

### Business scope

An explicit authorizable responsibility or area in which a general action may be performed. A scope may represent a business context, organizational area, operational section, cross-section responsibility, consolidated view, Access Control itself, or the complete system for the System Administrator.

Scope names and grouping may aid recognition, but they do not imply hierarchy or inheritance. New scopes grant no permission to ordinary roles until explicitly included in those roles. Date, shift, and other query filters refine information but never grant, restrict, or widen authorization.

### Role preset

A reusable starting configuration for role creation. Creating a role from a preset copies the preset's permissions into a new, independent role. The resulting role has no live dependency on the preset: later changes to either one do not silently alter the other.

Presets may reflect common responsibilities, but they do not turn organizational titles into authorization rules.

### System Administrator

The reserved authorization role responsible for governing Authentication and Access Control across Colibri Hub.

Its invariants are:

- The reserved role cannot be converted into an ordinary role, deactivated, or stripped of its global semantics.
- An active holder has all five general actions across every existing and newly introduced business scope.
- Manage Access and Edit Outside the Operational Window are reserved for the System Administrator and cannot be granted to ordinary roles or presets.
- More than one active person may hold the reserved role.
- Every account, profile, role, or assignment change must preserve at least one active System Administrator who can authenticate and govern accounts and access.
- The initial System Administrator is established through controlled initialization before ordinary provisioning begins.

Global System Administrator authorization is a reserved policy invariant, not a wildcard permission, scope hierarchy, or precedence rule.

### Access-change history

The historical evidence for Access Control configuration and lifecycle changes. It preserves the acting individual, affected profile or configuration, type of change, previous and resulting configuration, date and time, and the reason when required.

History must remain available after profiles, roles, presets, scopes, or assignments become inactive. Shared roles do not weaken individual attribution: operational and administrative actions remain attributable to the person who performed them. Authentication security history and business-operation history remain owned by their respective capabilities.

## Lifecycle coordination

| Authentication account | Access profile | Protected result |
| --- | --- | --- |
| Active | Active | Evaluate the union of exact permissions from active assigned roles. |
| Active | Inactive | Authentication may succeed, but protected entry is denied. |
| Awaiting Password Change | Active or inactive | Only mandatory password replacement, Authentication state inspection, and logout are available. |
| Disabled | Active or inactive | Login and protected entry are denied; coordinated disablement inactivates the profile. |

Unified provisioning is one administrative experience with separate ownership: Authentication establishes the account and credentials, while Access Control establishes the profile and initial role assignments. Incomplete provisioning must never leave usable access.

## Historical traceability

Conceptual relationships are retained rather than erased when access changes:

- profile activation and inactivation preserve the person's Access identity;
- role activation and inactivation preserve prior role usage;
- role assignment additions and removals preserve previous responsibility sets;
- role and preset changes preserve previous and resulting permission configurations;
- privileged or exceptional interventions preserve their reason;
- controlled initialization remains distinguishable from later administrator actions.

## Capability boundaries

This conceptual model does not define:

- Authentication providers, credentials, tokens, sessions, or account storage;
- database tables, columns, foreign keys, indexes, migrations, or APIs;
- direct user permissions, individual exceptions, explicit denies, or role precedence;
- role or scope hierarchy, inheritance, or wildcard behavior;
- job-title, shift, page, route, filter, or record-ownership authorization;
- business-process validity, correction windows, or operational audit storage;
- a generic resource or policy engine.

## References

- [Access Control PRD - Authorization Model](../../prd/access-control.md#authorization-model)
- [Access Control PRD - Business Rules](../../prd/access-control.md#business-rules)
- [Access Control PRD - States and Transitions](../../prd/access-control.md#states-and-transitions)
- [Authentication PRD - Identity and Access Relationship](../../prd/auth.md#identity-and-access-relationship)
- [Authentication PRD - Provision a New User](../../prd/auth.md#provision-a-new-user)
- [Context Map - Access Control](../../architecture/context-map.md#24-access-control)
- [Backend Access Control specification](../../../backend/docs/features/access-control.md)
- [Backend Authentication specification](../../../backend/docs/features/authentication.md)
