---
document_type: prd
status: draft
scope: access-control
authority: normative
owner: product
last_reviewed: 2026-08-01
---

# Access Control

## Business Scope

Access Control governs who may consult, record, correct, or administer information across Colibri Hub. It applies to every business context without redefining the processes owned by Warehouse, Operation, Administration, or any other area.

The capability separates organizational responsibilities from system authorization. Job titles and reporting structures may change while business processes remain stable. Access must therefore be configured through reusable roles, general actions, and explicit business scopes rather than through conditions tied to current job titles, pages, shifts, or individual workflows.

Access Control covers:

- user access lifecycle;
- configurable roles;
- reusable role presets;
- assignment of one or more roles to a user;
- permissions expressed as a general action within a business scope;
- access administration by the System Administrator;
- traceability of access changes;
- authorization decisions based on the user's effective permissions.

Authentication, operational record ownership, and the internal rules of each business process are outside this capability.

## Problem Statement

The organization needs to assign the same responsibility to several users, combine responsibilities when necessary, and reassign work when the organizational structure changes. A single role may be shared by users working different shifts, while one user may need more than one role because the user performs several responsibilities.

If authorization is tied directly to job titles, shifts, screens, or fixed workflow participants, every organizational change forces changes to the product. If permissions are assigned directly to individual users, repeated configurations drift and become difficult to review. If broad permissions do not distinguish business scopes, access to one responsibility can unintentionally grant access to unrelated information.

Access Control must provide a stable model in which:

- roles group permissions that can be reused by several users;
- presets accelerate role creation without freezing organizational titles into the system;
- users may combine roles;
- each permission joins a general action with an explicit business scope;
- absence of an explicit permission results in denial;
- the individual user remains identifiable for audit purposes, even when several users share the same roles.

## Stakeholders and Actors

| Actor | Responsibility | Interaction |
| --- | --- | --- |
| System Administrator | Governs access throughout the system | Manages users, roles, presets, role assignments, and access configuration; may intervene across all business scopes |
| Role Holder | Uses one or more roles to perform assigned responsibilities | Receives the combined permissions of all assigned active roles |
| Business Area Owner | Defines which responsibilities exist within a business area | Identifies the actions and business scopes that Access Control must be able to authorize |
| Supervisor or Management User | Consults operational information according to assigned roles | May receive read access across several sections or to consolidated views without receiving write access |
| Section Responsible | Represents the minimum responsibility level commonly expected to use the system directly | Consults, records, or corrects information only in explicitly authorized section scopes |

Organizational references such as Manager, Director, Unit Head, Section Responsible, or Secretary may inspire role presets or configurable role names. They do not constitute hardcoded authorization rules, do not create a technical role hierarchy, and do not grant permissions by job title.

"Machine Operator" remains a business actor distinct from Access Control roles. A Machine Operator manipulates production equipment and is not currently a direct system user. The generic name "Operator" must therefore not be used for an RBAC preset or technical role because it would make these concepts ambiguous.

## Authorization Model

### Users and roles

A user may hold one or more roles at the same time. A role is a configurable set of permissions representing a reusable responsibility profile. Several users may share the same role, including users who perform that responsibility in different shifts.

The permissions effective for a user are the union of the permissions granted by all assigned active roles. Roles are additive: the model does not include explicit denial permissions or precedence rules between roles.

### Permissions

Each permission combines one general action with one business scope.

| General action | Business meaning |
| --- | --- |
| Read | Consult information available in the authorized business scope |
| Write | Record a new business fact in the authorized business scope |
| Edit | Correct an existing business fact within the operational window defined by its owning business context |
| Edit Outside the Operational Window | Perform an exceptional correction after the ordinary correction window has closed |
| Manage Access | Create and change users, roles, presets, assignments, and permissions |

The action vocabulary is intentionally general. Business expressions such as register, capture, fill in, or add are forms of Write when they create a new business fact. The meaning of an action is determined by the requested business operation, not by a screen interaction or transport mechanism.

Edit Outside the Operational Window remains distinct because it grants exceptional authority to bypass an ordinary business restriction and therefore requires stronger traceability.

### Business scopes

A business scope identifies the responsibility or area in which an action is permitted. It must be specific enough to prevent access to one responsibility from granting access to unrelated responsibilities.

Business scopes may represent:

- a complete business context;
- an organizational unit or area;
- an operational section;
- a cross-section responsibility;
- a consolidated business view;
- Access Control itself;
- the complete system for the System Administrator.

The scope structure must support growth without assuming that the current organization is permanent. A new direction, unit, section, or cross-cutting responsibility becomes a new authorizable business scope and receives no ordinary role permissions automatically.

### Operational and dashboard scope boundaries

Within an operational context such as Yarn Spinning, the responsibility of a section includes its production records, applicable progress records, and section dashboard. The action determines whether the user may consult, record, or correct information within that section.

Process Quality and Waste are independent cross-section responsibilities. Each must be authorizable separately because each may be assigned to a different role and may involve machines from every plant section.

A section dashboard presents queries within a specific section scope. Read permission in that scope allows the user to consult the dashboard and use available filters such as date or shift. Those filters refine the query; they are not actions, permissions, or scopes by themselves.

The consolidated dashboard is a transversal read scope that may combine information from several sections, business contexts, or plant areas. It is not owned exclusively by Yarn Spinning or by any other operational context. Access to every section dashboard does not automatically grant access to the consolidated dashboard, and access to the consolidated dashboard grants no Write or Edit permission in the contexts represented by the view.

Labels such as Shift Summary or Daily Summary describe filtered queries or dashboard states. They must not become independent capabilities, actions, or business scopes solely because of the selected time filter.

## Business Rules

1. Access must be granted through roles. Permissions are not assigned directly to individual users.
2. A user may hold multiple roles concurrently.
3. A user's effective permissions are the union of the permissions granted by all assigned active roles.
4. A permission consists of one general action and one explicit business scope.
5. The supported general actions are Read, Write, Edit, Edit Outside the Operational Window, and Manage Access.
6. A permission grants only its stated action within its stated business scope. Read never implies Write, Edit, Edit Outside the Operational Window, or Manage Access.
7. Read authorizes consultation of information in its stated scope. A dashboard, table, detail view, report, or filtered query is a presentation of that consultation and does not create a different RBAC action.
8. Date, shift, section, and similar filters refine the information consulted. A filter must not independently grant, restrict, or widen authorization.
9. If no assigned role explicitly grants the required action in the required business scope, access must be denied.
10. Roles do not contain explicit denials. No role overrides or subtracts a permission granted by another assigned role.
11. Roles are configurable and must not depend on hardcoded organizational job titles.
12. Several users may share the same role. Their permissions are shared, but their identities and activities remain individually traceable.
13. Changing a role changes the effective permissions of every user assigned to that role.
14. Before a role change is confirmed, the affected users and the permissions being added or removed must be identifiable to the System Administrator.
15. A role preset is a reusable starting configuration for creating a role.
16. Creating a role from a preset copies the preset configuration. The resulting role is independent and may be changed without altering the preset.
17. Changing a preset must not silently change roles that were previously created from it.
18. New business scopes are denied to ordinary roles until the System Administrator grants explicit permissions for them.
19. Shift is operational and audit context. It must not grant, restrict, or widen authorization.
20. Users who share a role across different shifts remain distinct users. Every recorded action must identify the individual who performed it.
21. The System Administrator has access across the complete system, including newly introduced business scopes.
22. Manage Access and Edit Outside the Operational Window are reserved for the System Administrator.
23. The system must retain at least one active System Administrator so access governance cannot be left without an authorized administrator.
24. An inactive user cannot obtain authorization, regardless of assigned roles.
25. An inactive role grants no effective permission but must remain available for historical traceability.
26. Deactivation must preserve the user's identity, prior assignments, and access history.
27. Access configuration changes must identify the acting user, the affected user or role, the change, the previous and resulting configuration, and the date and time of the change.
28. The reason for an exceptional correction or another privileged access intervention must be preserved.
29. Access Control determines whether an action is authorized. The owning business context determines whether the requested operation is valid under its own business rules.
30. A business context must not infer authorization from shift, job title, page visibility, or an operational user reference stored in a business record.
31. Operational audits must identify the individual user and may include business date, time, shift, correction reason, and changed values. These facts do not alter the authorization decision.
32. Access Control must not invent actions for domain-specific events. A domain event uses the applicable general action within the scope owned by that business context.

## Flows and Processes

### Create a role from a preset

1. The System Administrator selects a preset representing a common responsibility profile.
2. The system presents the actions and business scopes that will be copied.
3. The System Administrator names the new role and adjusts its permissions as required.
4. The system creates an independent role.
5. The system records who created the role, when it was created, and which permissions it initially contained.

### Assign roles to a user

1. The System Administrator selects an active user.
2. The system presents the user's current roles and resulting permissions.
3. The System Administrator adds or removes one or more active roles.
4. The system presents the resulting permission changes before confirmation.
5. The system applies the assignment and records the acting user, affected user, previous roles, resulting roles, date, and time.

### Evaluate an access request

1. The system identifies the active user requesting the business operation.
2. The requested operation identifies the required general action and actual business scope.
3. The system determines the permissions granted by all active roles assigned to the user.
4. The system allows the request when the effective permissions contain the required action and scope.
5. The system denies the request in every other case.
6. When authorization succeeds, the owning business context evaluates its own process rules before performing the operation.

### Modify a shared role

1. The System Administrator selects an active role.
2. The system identifies every user assigned to that role.
3. The System Administrator adds or removes permissions.
4. The system presents the affected users and the effective permission changes before confirmation.
5. The system applies the change to the shared role.
6. The system records the acting user, previous role configuration, resulting configuration, date, and time.

### Introduce a new business scope

1. A business area establishes a new authorizable responsibility or area.
2. The System Administrator makes the business scope available for role configuration.
3. Ordinary roles retain no access to the new scope by default.
4. The System Administrator explicitly updates suitable presets or roles.
5. Existing roles created from a changed preset remain unchanged unless edited explicitly.

### Correct an operational record

1. The owning business context determines whether the record remains within its ordinary correction window.
2. A correction within the window requires Edit permission in the record's business scope.
3. A correction outside the window requires Edit Outside the Operational Window permission in that business scope.
4. The owning business context validates which information can be corrected and which evidence is required.
5. The operational audit identifies the individual user, date, time, shift when applicable, reason, and changed values.

## States and Transitions

### User access state

| State | Description | Allowed transitions |
| --- | --- | --- |
| Active | The user may receive authorization through assigned active roles | Inactive |
| Inactive | The user cannot receive authorization; identity and history are preserved | Active |

### Role state

| State | Description | Allowed transitions |
| --- | --- | --- |
| Active | The role contributes permissions to assigned users | Inactive |
| Inactive | The role grants no permission and remains available for historical traceability | Active |

Reactivation of a user or role must not erase the access-change history associated with prior states.

## Acceptance Criteria

1. A user with no assigned role is denied access to every protected business operation.
2. A user with one role receives exactly the actions and business scopes granted by that active role.
3. A user with several roles receives the union of their permissions without requiring a composite role.
4. Two users assigned to the same role receive the same permissions while their actions remain attributable to their individual identities.
5. A Read permission does not allow recording or correcting information in the same business scope.
6. A Write permission in one Yarn Spinning section does not allow writing in another section.
7. Write access to Process Quality does not grant Write access to Waste or to section production records.
8. Write access to Waste does not grant Write access to Process Quality or to section production records.
9. Read access to a section permits consultation of its dashboard and available filters without granting Write access to its records.
10. Read access to all sections of one or more operational contexts does not by itself grant access to the transversal consolidated dashboard.
11. Read access to the transversal consolidated dashboard permits consultation of its aggregated information but does not grant Write or Edit access to any represented context.
12. Changing a date, shift, section, or similar dashboard filter does not change the user's effective permissions.
13. Shift changes do not alter a user's effective permissions.
14. Creating a role from a preset produces an independently editable role.
15. Changing a preset does not alter roles previously created from that preset.
16. Changing a shared role identifies the affected users before confirmation and changes the permissions of all assigned users after confirmation.
17. Adding a new business scope does not grant it to existing ordinary roles automatically.
18. An inactive user is denied even when active roles remain assigned.
19. An inactive role contributes no permission to its assigned users.
20. A user without Edit Outside the Operational Window permission cannot correct a record after its owning business context closes the ordinary correction window.
21. Only the System Administrator can manage access or authorize an exceptional correction outside the operational window.
22. The System Administrator can operate across existing and newly introduced business scopes.
23. The system prevents an access change that would leave no active System Administrator.
24. Every role creation, role change, role assignment, role removal, user activation, and user deactivation is traceable to the individual who performed it and the date and time of the change.
25. Authorization does not replace domain validation: an authorized request is still rejected when it violates the owning business context's rules.
26. Operational audit records identify the individual user rather than only the shared role.

## Capability Boundaries

Access Control does not define:

- authentication providers, credentials, sessions, or identity tokens;
- database structures, service interfaces, routes, or transport contracts;
- navigation layout, page composition, or visual route protection;
- the validity of production, Warehouse, quality, waste, or lot operations;
- correction windows or correctable information for individual business contexts;
- shift assignment, attendance, or workforce scheduling;
- operational approval, confirmation, delivery, reception, or consolidation acts unless an owning business PRD defines them;
- role hierarchy, inherited roles, explicit deny permissions, or conflict precedence between roles;
- direct permission assignments to individual users;
- use of job titles or shifts as authorization rules.

Frontend and backend specifications may describe how these rules are implemented, but they must not redefine this authorization model.
