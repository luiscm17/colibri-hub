---
document_type: technical-spec
status: draft
implementation: not-started
scope: access-control
authority: explanatory
owner: backend
last_reviewed: 2026-08-01
---

# Technical Specification - Backend Access Control

> **Normative PRD:** [Access Control](../../../docs/prd/access-control.md)

**Product:** Colibri Hub  
**Context:** Access Control  
**Type:** Technical Specification - Backend  
**Status:** Not implemented  
**Technical baseline:** Repository `luiscm17/colibri-hub`, branch `back/auth-rbac`, reviewed 2026-08-01
**Complementary specification:** Frontend Access Control technical specification  
**Date:** 2026-07-31

---

## 1. Executive summary

This document specifies how the backend implements the authorization model defined by the normative Access Control PRD. It covers access profiles, multiple role assignments, configurable roles, role presets, exact action-and-scope permissions, authorization decisions, administrative API contracts, persistence, access-change auditing, and integration with protected business contexts.

Authentication is a separate capability. Access Control receives a trusted authenticated identity and answers whether the corresponding active user may perform a required action in a server-derived business scope. It does not validate credentials, issue tokens, create sessions, or implement login.

The target implementation follows the existing hexagonal backend architecture:

```text
authenticated identity
        ↓
trusted actor context
        ↓
business use case derives action + actual scope
        ↓
authorization policy
        ↓
roles → permissions → allow or deny
        ↓
owning business rules execute only after authorization
```

The model is additive and default-deny. Ordinary permissions require an exact `(action, scope)` grant through at least one active assigned role. There are no direct user permissions, explicit denials, role precedence rules, wildcards, or scope inheritance.

## 2. Related documents and authority

- [Access Control PRD](../../../docs/prd/access-control.md) — normative business rules and acceptance criteria.
- [Backend Architecture Overview](../architecture/overview.md) — module boundaries and dependency direction.
- [API Conventions](../api/conventions.md) — shared HTTP conventions.
- [Error Contract](../api/errors.md) — shared error envelope.
- [Persistence Design Principles](../database/design-principles.md) — persistence ownership and audit rules.
- [Migration Strategy](../database/migrations.md) — Supabase CLI migration workflow.
- [Testing Strategy](../testing/strategy.md) — backend test organization and tools.

If this specification conflicts with the Access Control PRD on business behavior, the PRD prevails. This specification is authoritative only for the backend implementation described here.

## 3. Current state

The backend does not currently implement the `access` module, an authenticated actor context, authorization middleware or policies, access persistence, access administration endpoints, or access-change auditing.

Existing business endpoints execute without per-user authorization. PostgreSQL row-level security is enabled on existing Warehouse tables and privileges are revoked, but no RLS policies or runtime RBAC flow implement the Access Control PRD.

The target implementation therefore introduces a new backend capability. It does not retrofit authentication or change the business invariants owned by Warehouse, Yarn Spinning, Lot Processing, or other contexts.

## 4. Objectives

### 4.1 Functional objectives

- Map a trusted authenticated identity to one Access Control user.
- Deny inactive or unmapped users.
- Assign one or more roles to one user.
- Compute effective permissions as the union of all active assigned roles.
- Represent each ordinary permission as one supported action in one active business scope.
- Create independently editable roles from reusable presets.
- Allow the System Administrator to manage users, roles, presets, scopes, and role assignments.
- Preserve at least one active System Administrator.
- Make all access configuration changes attributable to an individual actor.
- Expose effective permissions for the authenticated frontend session.
- Enforce authorization in the backend even when frontend navigation is hidden or disabled.

### 4.2 Technical objectives

- Preserve hexagonal dependency direction.
- Keep authentication behind an explicit identity contract.
- Derive the protected resource scope on the server rather than trusting a client-supplied authorization scope.
- Keep authorization evaluation independent of HTTP methods and UI routes.
- Apply each administrative change and its audit entry atomically.
- Make role and assignment changes effective immediately after commit.
- Protect shared configuration from lost updates through optimistic concurrency.
- Keep the first implementation exact-match and free of wildcard or hierarchy semantics.
- Use PostgreSQL constraints for structural invariants and application transactions for cross-record invariants.

## 5. Scope

### 5.1 Included

- Access user profiles linked to external authenticated identities.
- Active and inactive user lifecycle.
- Configurable active and inactive roles.
- Multiple concurrent roles per user.
- Reserved System Administrator role.
- Role presets and copied preset permissions.
- Business-scope registry.
- The actions `read`, `write`, `edit`, `edit_outside_window`, and `manage_access`.
- Effective-permission calculation.
- Internal authorization policy used by protected backend use cases.
- Self-access endpoint for the authenticated user.
- Administrative endpoints for users, roles, presets, scopes, assignments, and access audit queries.
- Impact previews for shared role changes and user role replacement.
- Access-change audit persistence.
- Bootstrap of the initial System Administrator.
- Migrations, ORM mappings, dependency composition, error translation, OpenAPI, and automated tests.

### 5.2 Excluded

- Login, logout, credentials, password recovery, MFA, sessions, access tokens, refresh tokens, and token issuance.
- Selection of a final authentication provider.
- Direct permissions or exceptions assigned to individual users.
- Explicit deny permissions.
- Role hierarchy, role inheritance, and permission precedence.
- Scope hierarchy, wildcard matching, and implicit parent or child authorization.
- Shift-based authorization.
- Job-title-based authorization.
- Domain-specific correction windows and editable-field rules.
- Operational audit storage owned by business contexts.
- Frontend navigation, route guards, and page composition.
- Database RLS as the primary business authorization evaluator.

## 6. Authorization semantics

### 6.1 Supported actions

The backend uses the following stable values:

| Value | Required for |
| --- | --- |
| `read` | Querying protected business information |
| `write` | Recording a new business fact |
| `edit` | Correcting an existing fact within the owning context's ordinary correction window |
| `edit_outside_window` | Correcting after that window has closed |
| `manage_access` | Changing Access Control configuration |

Actions describe business intent, not HTTP methods. A `POST` endpoint may require `write`, while an administrative `POST` requires `manage_access`. A state transition uses the action assigned by its owning PRD rather than being inferred from `PATCH` or `PUT`.

### 6.2 Exact scope matching

An ordinary permission matches only the exact active scope referenced by the permission. Scope codes are stable identifiers such as:

```text
warehouse.raw_materials
warehouse.finished_products
warehouse.production_supplies
yarn_spinning.section.preparation
yarn_spinning.section.ring_spinning
yarn_spinning.process_quality
yarn_spinning.waste
lot_processing
lot_processing.stage.inventory
lot_processing.stage.quality
transversal.consolidated_dashboard
access_control
```

The separator has no runtime inheritance meaning. For example:

```text
write + yarn_spinning.section.preparation
```

does not authorize another Yarn Spinning section, Process Quality, Waste, or the consolidated dashboard.

### 6.3 Recognized scope catalog

Access Control does not accept an arbitrary string and turn it into an
authorizable scope. Every scope must first exist in the application-recognized
scope-definition catalog. That catalog is versioned with the product and is
derived from approved business capabilities; it is not editable through an
administrative request.

The initial catalog is:

| Scope code | Owning capability | Authorized responsibility |
| --- | --- | --- |
| `warehouse.raw_materials` | Warehouse / Bale Management | Raw-material dashboard, detail, reception, and delivery |
| `warehouse.finished_products` | Warehouse / Finished Products | Finished-product dashboard, requirement, handoff issue, reception, availability, custody, dispatch, and return |
| `warehouse.production_supplies` | Warehouse / Production Supplies | Supplies dashboard, stock, reception, exits, and returns |
| `yarn_spinning.section.preparation` | Yarn Spinning / Preparation | Section dashboard, production, progress, and corrections |
| `yarn_spinning.section.ring_spinning` | Yarn Spinning / Ring Spinning | Section dashboard, production, progress, and corrections |
| `yarn_spinning.section.bobbin_winding` | Yarn Spinning / Bobbin Winding | Section dashboard, production, progress, and corrections |
| `yarn_spinning.section.twisting` | Yarn Spinning / Twisting | Section dashboard, production, progress, and corrections |
| `yarn_spinning.section.skeining` | Yarn Spinning / Skeining | Section dashboard, production, and corrections |
| `yarn_spinning.process_quality` | Yarn Spinning / Process Quality | Cross-section quality queries, records, and corrections |
| `yarn_spinning.waste` | Yarn Spinning / Waste | Cross-section waste queries, records, and corrections |
| `lot_processing` | Lot Processing | Dashboard, queue, detail, and transversal lifecycle information |
| `lot_processing.stage.inventory` | Lot Processing / Inventory | Inventory-stage technical information and interventions |
| `lot_processing.stage.dyeing` | Lot Processing / Dyeing | Dyeing-stage technical information and interventions |
| `lot_processing.stage.drying` | Lot Processing / Drying | Drying-stage technical information and interventions |
| `lot_processing.stage.winding` | Lot Processing / Winding | Winding-stage technical information and interventions |
| `lot_processing.stage.bagging` | Lot Processing / Bagging | Bagging-stage technical information and interventions |
| `lot_processing.stage.quality` | Lot Processing / Quality | Quality-stage technical information, release-for-reception actions, and handoff responses |
| `transversal.consolidated_dashboard` | Transversal reporting | Consolidated read model across authorized business information |
| `access_control` | Access Control | Access administration and access-change history |

Dot-separated segments are naming structure only. The catalog defines neither
scope inheritance nor a resource tree. Adding a capability requires a reviewed
catalog change and deployment before a System Administrator can activate the
scope and assign it through roles. Registration therefore selects a recognized
definition; it never submits free-form ownership or authorization semantics.

Each definition also declares its supported ordinary actions. Operational
scopes support only the actions justified by their owning PRDs. The transversal
consolidated dashboard supports `read` only. The `access_control` scope supports
`manage_access` only and is exercised through the reserved System Administrator
policy. The backend rejects an action-and-scope pair that the definition does
not support.

### 6.4 Effective permissions

For an ordinary user, effective permissions are the distinct union of permissions from all active roles with active assignments to that active user:

```text
effective_permissions(user)
  = distinct union of role_permissions
    where user is active
      and assignment is active
      and role is active
      and scope is active
```

An authorization request is allowed only when that set contains the exact required `(action, scope)` pair. Every other request is denied.

Deactivating a user denies all requests without deleting role assignments. Deactivating a role removes its contribution from every assigned user without deleting assignment or audit history.

### 6.5 System Administrator

The system contains exactly one reserved role marked as the System Administrator role. More than one active user may be assigned to it.

An active user with an active assignment to that role receives:

- all five supported actions;
- authorization in every existing and newly registered scope;
- `manage_access` permission;
- `edit_outside_window` permission.

This behavior is an explicit policy branch, not a wildcard permission row. The reserved role cannot be deactivated, converted into an ordinary role, or have its global semantics removed. The backend rejects any mutation that would leave no active user assigned to it.

Ordinary roles cannot receive `manage_access` or `edit_outside_window`.

### 6.6 Evaluation order

The authorization service evaluates a request in this order:

1. Require a trusted authenticated identity.
2. Resolve it to exactly one Access Control user.
3. Deny if the user is absent or inactive.
4. Allow if the user is an active System Administrator.
5. Deny if the required scope is absent or inactive.
6. Load permissions from every active assigned ordinary role.
7. Allow if an exact active `(action, scope)` permission exists.
8. Deny otherwise.

The service returns either an authorization success containing the internal actor identifier or a typed denial. It does not return partial domain data.

## 7. Authentication boundary

Authentication completes before Access Control evaluation. The integration contract provides an immutable trusted identity:

```python
@dataclass(frozen=True)
class AuthenticatedIdentity:
    subject: str
```

`subject` is the stable identifier asserted by the configured authentication mechanism. It is opaque to Access Control and is never accepted from a request body, query parameter, or client-controlled header.

The HTTP composition layer is responsible for:

- invoking the authentication adapter;
- rejecting missing, invalid, or expired authentication with `401`;
- placing `AuthenticatedIdentity` in request-scoped actor context;
- passing that context to application use cases.

Access Control is responsible for mapping `subject` to an internal `user_id`. A valid authenticated identity without an active Access profile is not authorized and receives `403`.

Business use cases and domain entities never parse tokens or depend on a specific identity provider.

## 8. Hexagonal architecture

### 8.1 Proposed module structure

```text
backend/src/access/
├── domain/
│   ├── actions.py
│   ├── users.py
│   ├── roles.py
│   ├── presets.py
│   ├── scopes.py
│   └── errors.py
├── application/
│   ├── authorization.py
│   ├── users.py
│   ├── roles.py
│   ├── presets.py
│   ├── scopes.py
│   ├── audits.py
│   └── dto.py
├── ports/
│   ├── repositories.py
│   ├── transaction.py
│   ├── identity.py
│   └── clock.py
└── adapters/
    ├── http/
    │   ├── models.py
    │   ├── router.py
    │   └── error_handlers.py
    └── persistence/
        ├── models.py
        ├── repositories.py
        └── authorization.py
```

HTTP models, routes, and Access-specific error translation remain adapters of
the capability, matching the implemented `warehouse.bales.adapters.http`
pattern. Authentication composition, session-factory ownership, dependency
wiring, and router registration remain in the outer composition layer under
`bootstrap`.

The current package discovery configuration includes only `warehouse`, `infra`,
and `bootstrap`. Introducing `access` therefore also requires adding `access*`
to backend package discovery; it does not justify changing the existing
capability-first layout.

### 8.2 Domain responsibilities

The Access Control domain owns:

- supported action values;
- user and role lifecycle invariants;
- role permission-set validation;
- preset copy semantics;
- reserved System Administrator invariants;
- prevention of privileged actions on ordinary roles;
- required change reasons where policy demands them.

It does not own authentication, HTTP responses, SQLAlchemy sessions, or rules internal to protected business contexts.

### 8.3 Application responsibilities

Application use cases orchestrate:

- authenticated identity resolution;
- authorization decisions;
- user lifecycle changes;
- role and preset creation or modification;
- role assignment replacement;
- registration of recognized scope definitions and scope lifecycle changes;
- impact preview calculation;
- transaction boundaries;
- audit entry creation;
- cross-record validation protecting the last active System Administrator.

### 8.4 Ports

The capability requires explicit ports for:

| Port | Responsibility |
| --- | --- |
| `AccessUserRepository` | Resolve by identity subject and load/change user state |
| `RoleRepository` | Load roles, permissions, assignments, and affected users |
| `PresetRepository` | Load and persist presets and their permission sets |
| `ScopeDefinitionRegistry` | Expose the immutable set of product-recognized scope definitions |
| `ScopeRepository` | Resolve registered stable scope codes and scope state |
| `AccessAuditRepository` | Append and query access-change evidence |
| `TransactionPort` | Commit or roll back one administrative mutation and its audit atomically |
| `IdentityPort` | Generate internal identifiers |
| `ClockPort` | Supply system timestamps for deterministic tests |

The runtime authorization policy is exposed as an application service callable from composition. Protected contexts depend on a narrow authorization port rather than on Access repositories.

### 8.5 Protected-context integration

Each protected business operation declares its required action in backend code and derives its actual scope from trusted route configuration, the command, or the loaded resource.

```python
actor = actor_context.require_authenticated()
scope = scope_policy.for_existing_record(record)
authorization.require(actor, Action.EDIT, scope)
use_case.correct(record, command)
```

Rules:

- A client must never submit the authoritative scope for a protected operation.
- When a scope depends on an existing record, the backend loads the record before authorization and derives the scope from persisted ownership data.
- Denial occurs before the business mutation.
- Authorization success does not bypass domain validation.
- Domain entities do not query Access Control.
- Authorization is applied at the application boundary, with optional route-level early rejection only when the same server-derived scope is unambiguous.

### 8.6 Existing Warehouse integration

The four currently implemented Bale Management endpoints are protected without
changing their application behavior:

| Existing operation | Required action | Server-derived scope |
| --- | --- | --- |
| Register raw-material batch | `write` | `warehouse.raw_materials` |
| Query aggregate bale stock | `read` | `warehouse.raw_materials` |
| Query individual bale detail | `read` | `warehouse.raw_materials` |
| Deliver bales to Production | `write` | `warehouse.raw_materials` |

The HTTP composition passes the authorized internal actor to operations that
create business audit evidence. No current endpoint is reclassified as `edit`,
and Access Control does not change batch, bale, stock, or delivery invariants.

## 9. Application use cases

### 9.1 Queries

- `GetCurrentAccess`: resolve the current user, assigned roles, and effective permissions.
- `AuthorizeAction`: require one action in one scope for an authenticated actor.
- `ListAccessUsers`: filter and paginate access profiles.
- `GetAccessUser`: return one user, current assignments, and effective permissions.
- `ListRoles` and `GetRole`: return role configuration and assigned-user counts.
- `ListRolePresets` and `GetRolePreset`: return preset configuration.
- `ListScopeDefinitions`: return product-recognized definitions and whether each is registered.
- `ListScopes`: return registered scopes and lifecycle state.
- `ListAccessAudits`: filter and paginate immutable access-change evidence.
- `PreviewRoleChange`: calculate affected users and added or removed effective permissions.
- `PreviewUserRoleReplacement`: calculate role and effective-permission differences for one user.

### 9.2 Commands

- `CreateAccessUser`.
- `ActivateAccessUser` and `DeactivateAccessUser`.
- `CreateRole`, `UpdateRole`, `ActivateRole`, and `DeactivateRole`.
- `ReplaceUserRoles`.
- `CreateRoleFromPreset`.
- `CreateRolePreset`, `UpdateRolePreset`, `ActivateRolePreset`, and `DeactivateRolePreset`.
- `RegisterRecognizedScope`, `ActivateScope`, and `DeactivateScope`.

Every command in this list requires `manage_access` in the `access_control` scope and writes an access audit in the same transaction.

Role and preset updates replace their complete permission sets. This avoids ambiguous partial permission patches and makes before/after auditing deterministic.

## 10. API contract

All routes use `/api/v1`, JSON, the shared error envelope, strict request validation, UUID internal identifiers, ISO 8601 timestamps, and cursor or page-based pagination consistent with the shared API conventions.

### 10.1 Self-access endpoint

| Method | Path | Required authorization | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/access/me` | Authenticated active user | Load identity, roles, and effective permissions for the current session |

Ordinary-user response:

```json
{
  "user_id": "0d5221e0-2f79-4d4c-9827-cd871787fcaf",
  "user_code": "USR-014",
  "display_name": "Example User",
  "is_active": true,
  "roles": [
    {"role_id": "248dd6f1-70bc-4b10-8c60-c25509ab71f8", "code": "ring-spinning-responsible", "name": "Ring Spinning Responsible"}
  ],
  "authorization": {
    "global": false,
    "permissions": [
      {"action": "read", "scope": "yarn_spinning.section.ring_spinning"},
      {"action": "write", "scope": "yarn_spinning.section.ring_spinning"}
    ],
    "version": 12
  }
}
```

System Administrator authorization is represented without enumerating every scope:

```json
{
  "global": true,
  "actions": ["read", "write", "edit", "edit_outside_window", "manage_access"],
  "permissions": [],
  "version": 31
}
```

`version` changes whenever a mutation can alter that user's effective authorization. It supports client refresh detection but does not authorize any request by itself.

### 10.2 Administrative endpoint catalog

Every endpoint below requires an active System Administrator.

| Capability | Method | Path |
| --- | --- | --- |
| List users | `GET` | `/api/v1/access/users` |
| Create access profile | `POST` | `/api/v1/access/users` |
| Get user | `GET` | `/api/v1/access/users/{user_id}` |
| Activate or deactivate user | `PATCH` | `/api/v1/access/users/{user_id}/status` |
| Preview role replacement | `POST` | `/api/v1/access/users/{user_id}/roles/preview` |
| Replace assigned roles | `PUT` | `/api/v1/access/users/{user_id}/roles` |
| List roles | `GET` | `/api/v1/access/roles` |
| Create role | `POST` | `/api/v1/access/roles` |
| Get role | `GET` | `/api/v1/access/roles/{role_id}` |
| Preview role update | `POST` | `/api/v1/access/roles/{role_id}/preview` |
| Replace role configuration | `PUT` | `/api/v1/access/roles/{role_id}` |
| Activate or deactivate role | `PATCH` | `/api/v1/access/roles/{role_id}/status` |
| List presets | `GET` | `/api/v1/access/role-presets` |
| Create preset | `POST` | `/api/v1/access/role-presets` |
| Get preset | `GET` | `/api/v1/access/role-presets/{preset_id}` |
| Replace preset configuration | `PUT` | `/api/v1/access/role-presets/{preset_id}` |
| Activate or deactivate preset | `PATCH` | `/api/v1/access/role-presets/{preset_id}/status` |
| Create role from preset | `POST` | `/api/v1/access/role-presets/{preset_id}/roles` |
| List scopes | `GET` | `/api/v1/access/scopes` |
| List recognized scope definitions | `GET` | `/api/v1/access/scope-definitions` |
| Register recognized scope | `POST` | `/api/v1/access/scopes` |
| Activate or deactivate scope | `PATCH` | `/api/v1/access/scopes/{scope_id}/status` |
| Query access audits | `GET` | `/api/v1/access/audits` |

### 10.3 Role configuration request

Role creation and replacement use the complete desired permission set:

```json
{
  "code": "ring-spinning-responsible",
  "name": "Ring Spinning Responsible",
  "description": "Records and consults Ring Spinning operations.",
  "permissions": [
    {"action": "read", "scope_id": "43f46589-19d8-479f-84bd-20ab34ed7a22"},
    {"action": "write", "scope_id": "43f46589-19d8-479f-84bd-20ab34ed7a22"}
  ],
  "expected_version": 4,
  "reason": "Align responsibility with the approved operating model."
}
```

`expected_version` is required for replacement but omitted on creation. The backend rejects duplicate pairs, inactive scopes, unsupported actions, and privileged actions on ordinary roles.

### 10.4 Preview and confirmation

A preview response includes:

```json
{
  "subject_version": 4,
  "affected_user_count": 3,
  "affected_users": [
    {"user_id": "...", "user_code": "USR-021", "display_name": "Example User"}
  ],
  "permissions_added": [
    {"action": "edit", "scope": "yarn_spinning.section.ring_spinning"}
  ],
  "permissions_removed": []
}
```

Preview does not reserve or mutate state. Confirmation must send the same intended configuration and `expected_version`. The backend recalculates invariants inside the write transaction. If the subject changed after preview, it returns `409 access_version_conflict` and requires a new preview.

### 10.5 Replace user roles

The assignment endpoint receives the complete desired role set:

```json
{
  "role_ids": [
    "248dd6f1-70bc-4b10-8c60-c25509ab71f8",
    "f3843d52-d8bd-45c1-bbdd-91b59a325a08"
  ],
  "expected_version": 7,
  "reason": "User now covers section operation and Process Quality."
}
```

The transaction closes removed assignments, creates new assignments, preserves unchanged assignments, increments the user's authorization version, and appends one audit entry containing previous and resulting role sets.

### 10.6 Access-profile creation

Creating an Access profile does not create authentication credentials:

```json
{
  "identity_subject": "opaque-authenticated-subject",
  "user_code": "USR-014",
  "display_name": "Example User",
  "role_ids": [],
  "reason": "Enable access profile for an existing authenticated identity."
}
```

The authentication capability or trusted administrative integration must establish the identity subject before the user can sign in. Access Control only stores the mapping.

### 10.7 Register a recognized scope

Scope registration accepts only the immutable definition key returned by the
recognized catalog:

```json
{
  "definition_key": "transversal.consolidated_dashboard",
  "reason": "Enable the approved consolidated dashboard scope for role configuration."
}
```

The backend supplies the code, display name, owning capability, description,
and supported actions from the recognized definition. Unknown definitions and
attempts to override this metadata are rejected. Registration grants no
ordinary role permission automatically.

## 11. Data model

### 11.1 `access_users`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `user_id` | UUID | Primary key |
| `identity_subject` | TEXT | Unique, immutable mapping to authenticated identity |
| `user_code` | TEXT | Unique stable administrative code |
| `display_name` | TEXT | Human-readable identity |
| `is_active` | BOOLEAN | Denies authorization when false |
| `authorization_version` | BIGINT | Incremented whenever effective access may change |
| `version` | BIGINT | Optimistic concurrency for profile administration |
| `created_at` | TIMESTAMPTZ | System creation time |
| `updated_at` | TIMESTAMPTZ | Last profile mutation time |

Access deactivation does not delete assignments or audit history.

### 11.2 `access_roles`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `role_id` | UUID | Primary key |
| `role_code` | TEXT | Unique stable role code |
| `role_name` | TEXT | Display name |
| `description` | TEXT | Optional responsibility summary |
| `is_system_administrator` | BOOLEAN | Marks the single reserved global role |
| `is_active` | BOOLEAN | Controls permission contribution |
| `version` | BIGINT | Optimistic concurrency |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last mutation time |

A partial unique index enforces at most one role with `is_system_administrator = true`. Bootstrap creates that required role. Application and database protections reject its deactivation or demotion.

### 11.3 `access_user_role_assignments`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `assignment_id` | UUID | Primary key |
| `user_id` | UUID | FK to `access_users` |
| `role_id` | UUID | FK to `access_roles` |
| `assigned_by_user_id` | UUID | FK to acting Access user |
| `assigned_at` | TIMESTAMPTZ | Assignment time |
| `revoked_by_user_id` | UUID | Nullable FK to revoking Access user |
| `revoked_at` | TIMESTAMPTZ | Nullable revocation time |
| `revoke_reason` | TEXT | Required when revoked |

A partial unique index permits only one current assignment for each `(user_id, role_id)` pair where `revoked_at IS NULL`. Historical reassignments remain separate rows.

### 11.4 `access_scopes`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `scope_id` | UUID | Primary key |
| `definition_key` | TEXT | Unique immutable key from the recognized scope-definition catalog |
| `scope_code` | TEXT | Unique immutable exact-match code |
| `scope_name` | TEXT | Catalog-provided display name |
| `owning_context` | TEXT | Catalog-provided capability responsible for the protected business meaning |
| `description` | TEXT | Catalog-provided administrative description |
| `is_active` | BOOLEAN | Only active scopes authorize |
| `version` | BIGINT | Optimistic concurrency |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last mutation time |

No parent identifier, wildcard, path matcher, or implicit hierarchy is stored.
`scope_code` punctuation is naming structure only. Registration must resolve
`definition_key` through `ScopeDefinitionRegistry`; free-form scope metadata is
never persisted from the request.

### 11.5 `access_role_permissions`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `role_permission_id` | UUID | Primary key |
| `role_id` | UUID | FK to `access_roles` |
| `scope_id` | UUID | FK to `access_scopes` |
| `action` | TEXT | Checked against the five supported action values |
| `created_by_user_id` | UUID | FK to acting Access user |
| `created_at` | TIMESTAMPTZ | Creation time |

`(role_id, scope_id, action)` is unique. Ordinary-role constraints reject `manage_access` and `edit_outside_window`. The System Administrator role does not depend on permission rows for global behavior.

### 11.6 `access_role_presets`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `preset_id` | UUID | Primary key |
| `preset_code` | TEXT | Unique stable preset code |
| `preset_name` | TEXT | Display name |
| `description` | TEXT | Optional template description |
| `is_active` | BOOLEAN | Controls availability for new role creation |
| `version` | BIGINT | Optimistic concurrency |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last mutation time |

### 11.7 `access_role_preset_permissions`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `preset_permission_id` | UUID | Primary key |
| `preset_id` | UUID | FK to `access_role_presets` |
| `scope_id` | UUID | FK to `access_scopes` |
| `action` | TEXT | Checked supported action |
| `created_by_user_id` | UUID | FK to acting Access user |
| `created_at` | TIMESTAMPTZ | Creation time |

`(preset_id, scope_id, action)` is unique. Creating a role from a preset copies these pairs into `access_role_permissions`; the created role stores no live dependency on the preset.

### 11.8 `access_change_audits`

| Column | Type | Constraints and purpose |
| --- | --- | --- |
| `access_change_audit_id` | UUID | Primary key |
| `change_kind` | TEXT | Stable category such as `role_updated` or `user_roles_replaced` |
| `subject_type` | TEXT | Access record family affected |
| `subject_id` | UUID | Identifier of affected user, role, preset, scope, or assignment set |
| `performed_by_user_id` | UUID | Acting Access user; nullable only during controlled bootstrap |
| `reason` | TEXT | Required for privileged or destructive configuration changes |
| `before_values` | JSONB | Previous non-secret configuration snapshot |
| `after_values` | JSONB | Resulting non-secret configuration snapshot |
| `occurred_at` | TIMESTAMPTZ | Authoritative system occurrence time |

Audit rows are append-only. Application runtime credentials, authentication tokens, and secrets are never stored in snapshots.

### 11.9 Referential and deletion policy

- Access users, roles, presets, scopes, assignments, permissions, and audits are not hard-deleted through the API.
- Lifecycle changes use activation or deactivation.
- Foreign keys use restrictive deletion behavior.
- Historical assignments and audits remain readable after deactivation.
- Scope codes, definition keys, catalog metadata, and authentication subjects are immutable after creation.
- User, role, and preset display names and descriptions may change with version checks and audit evidence.

## 12. Transaction and concurrency rules

Each administrative command executes in one PostgreSQL transaction containing:

1. authenticated System Administrator resolution;
2. `manage_access` authorization;
3. optimistic-version verification;
4. invariant checks;
5. state mutation;
6. affected-user authorization-version increments;
7. append-only access audit insertion;
8. commit.

Any failure rolls back both configuration and audit changes.

Mutations that can remove the last active System Administrator lock the reserved role and its current assignments before evaluating the invariant. This applies to user deactivation, role replacement, assignment revocation, and any attempted reserved-role lifecycle change.

Role permission changes increment `authorization_version` for every active user currently assigned to that role. Role activation or deactivation does the same. Scope activation or deactivation increments the version for users whose assigned roles reference that scope. These updates make session-facing permission versions change immediately after commit.

No runtime authorization cache is used in this target implementation. Each protected request resolves current state through the authorization query adapter. A later cache must key by authorization version and preserve immediate revocation semantics.

## 13. Bootstrap

The initial deployment requires a controlled bootstrap transaction because no System Administrator exists yet to authorize Access changes.

Bootstrap creates:

- the reserved active System Administrator role;
- the active `access_control` scope;
- one active Access user mapped to a pre-existing authenticated identity;
- one current assignment of that user to the reserved role;
- corresponding `initial_bootstrap` audit entries with a null actor and an explicit bootstrap reason.

Bootstrap configuration receives the initial identity subject, user code, and display name through deployment-managed configuration. It must not contain credentials or tokens.

The bootstrap operation is idempotent for the same identifiers and fails when conflicting partially initialized state exists. After bootstrap, all Access changes require a normal authenticated System Administrator and no other null audit actor is permitted.

## 14. Error handling

All failures use the shared error envelope.

### 14.1 Authentication and authorization

| HTTP | Code | Scenario |
| --- | --- | --- |
| `401` | `authentication_required` | Authentication is absent, invalid, or expired |
| `403` | `access_denied` | Active user lacks the required exact permission |
| `403` | `access_user_inactive` | Authenticated identity maps to an inactive user |
| `403` | `access_profile_not_found` | Authenticated identity has no Access profile |

Protected business endpoints may use the single external code `access_denied` for all authorization denials to avoid exposing access configuration. Administrative and self-access endpoints may return the more specific inactive or unmapped codes because the authenticated user is already the subject.

### 14.2 Administrative failures

| HTTP | Code | Scenario |
| --- | --- | --- |
| `404` | `access_user_not_found` | Requested Access user does not exist |
| `404` | `access_role_not_found` | Requested role does not exist |
| `404` | `access_preset_not_found` | Requested preset does not exist |
| `404` | `access_scope_not_found` | Requested scope does not exist |
| `409` | `duplicate_access_identity` | Identity subject is already mapped |
| `409` | `duplicate_access_user_code` | User code already exists |
| `409` | `duplicate_access_role_code` | Role code already exists |
| `409` | `duplicate_access_preset_code` | Preset code already exists |
| `409` | `duplicate_access_scope_code` | Scope code already exists |
| `409` | `access_version_conflict` | Expected version differs from persisted version |
| `409` | `last_system_administrator_required` | Mutation would leave no active System Administrator |
| `409` | `inactive_access_role` | Assignment references an inactive role |
| `409` | `inactive_access_scope` | Permission references an inactive scope |
| `422` | `invalid_access_action` | Unsupported action value |
| `422` | `unsupported_action_for_scope` | Recognized scope does not support the requested action |
| `422` | `unrecognized_scope_definition` | Registration references a definition not declared by the application |
| `422` | `privileged_action_requires_system_administrator` | Ordinary role or preset includes a reserved action |
| `422` | `duplicate_role_permission` | Request repeats an action-and-scope pair |
| `422` | `access_change_reason_required` | Required administrative reason is absent |
| `422` | `reserved_role_mutation_forbidden` | Request would alter reserved System Administrator semantics |

Unexpected integrity errors are not translated into a known conflict unless they match an explicitly named constraint. Internal SQL, stack traces, identity claims, and audit snapshots are never exposed in error messages.

## 15. Access-change audit

Access Control records, at minimum:

- access profile creation;
- user activation and deactivation;
- role creation, replacement, activation, and deactivation;
- role assignment additions and removals;
- preset creation, replacement, activation, and deactivation;
- scope registration, activation, and deactivation;
- controlled bootstrap.

Each audit identifies the individual acting user, subject, timestamp, reason when required, and before/after configuration. Shared-role changes record the affected-user identifiers or a stable change snapshot sufficient to reconstruct impact.

Authorization checks themselves are not persisted as access-change audits. Security request logs may record denials through platform observability, but that log is distinct from the normative access-configuration history.

Operational record creation and correction audits remain owned by their business contexts. They reuse the authenticated internal `user_id` as actor evidence but do not write to `access_change_audits`.

## 16. Security requirements

- Never trust `user_id`, role, permission, action, or authoritative scope supplied by the frontend for authorization.
- Authentication subjects are treated as identifiers, not bearer credentials.
- Administrative endpoints require both valid authentication and active System Administrator authorization.
- Response payloads never include authentication tokens, credential hashes, or provider-private claims.
- Database runtime credentials remain server-side.
- All Access tables enable RLS and revoke default privileges from `anon`, `authenticated`, and `service_role`, consistent with existing migrations. The backend database role is the only runtime path until an explicit database authorization design replaces it.
- Error messages do not reveal protected-resource existence when authorization fails before resource disclosure is safe.
- Access audit rows are append-only to the application role.
- Scope codes and metadata are copied only from the recognized scope-definition registry; client-defined scope semantics are rejected.
- Administrative list endpoints are paginated and do not expose identity-provider metadata beyond the stored opaque subject when explicitly required by administration.

## 17. Migration strategy

Schema changes are delivered through forward-only Supabase CLI migrations under `supabase/migrations/`. Migrations are the physical schema authority; SQLAlchemy mappings mirror them.

Migration order:

1. Create Access tables, checks, named unique constraints, partial indexes, and foreign keys.
2. Enable RLS and revoke default privileges.
3. Add database protections for reserved-role invariants and append-only audit behavior where application checks alone are insufficient.
4. Apply controlled bootstrap using deployment configuration or a dedicated idempotent bootstrap command after schema creation.
5. Add SQLAlchemy mappings and repository adapters matching the migrated schema.

Bootstrap identity values must not be committed as real-user secrets or production-specific personal data in a migration.

## 18. Testing strategy

Tests use stdlib `unittest` and the repository's established unit, API, and PostgreSQL integration structure.

### 18.1 Domain unit tests

- Supported action validation.
- Ordinary role rejects `manage_access` and `edit_outside_window`.
- Role permission sets reject duplicates.
- Preset copy produces an independent role configuration.
- Reserved System Administrator semantics cannot be removed.
- User and role lifecycle transitions preserve identity and history.

### 18.2 Application unit tests

- No role produces default denial.
- Multiple roles produce a distinct union.
- Inactive user denies every request.
- Inactive role contributes no permission.
- Inactive scope does not authorize.
- Exact matching does not inherit from similarly prefixed scope codes.
- Unknown scope definitions cannot be registered.
- Recognized-scope registration copies server-owned metadata and grants no ordinary role permission.
- System Administrator authorizes every action in existing and newly registered scopes.
- Last active System Administrator cannot be removed.
- Preview calculates affected users and effective permission deltas.
- Version conflict prevents mutation.
- Each successful mutation writes one coherent audit transaction.
- Failed mutations roll back configuration and audit.
- Protected use case derives scope from persisted resource data.

### 18.3 API tests

- Missing or invalid authentication returns `401`.
- Unmapped, inactive, and unauthorized identities return the defined `403` contract.
- `/access/me` returns ordinary and global authorization shapes.
- Every administrative endpoint rejects an ordinary user.
- Scope registration rejects free-form or unknown definitions.
- Strict request validation rejects extra fields.
- Role and assignment replacement require expected versions.
- Preview and confirmation contracts remain stable.
- Error responses conform to the shared envelope.

### 18.4 PostgreSQL integration tests

- Named uniqueness constraints for user, role, preset, scope, permission, and current assignment.
- Historical assignment rows coexist with one current assignment.
- Foreign-key and restrictive-delete behavior.
- Atomic mutation plus audit commit and rollback.
- Concurrent attempts cannot remove the last active System Administrator.
- Concurrent role updates produce one success and one version conflict.
- Scope or role deactivation immediately removes effective authorization.
- Audit rows cannot be updated or deleted by the application role.
- RLS and privilege revocations match migration policy.

### 18.5 Protected-context contract tests

Each business context adds tests proving that:

- the required action is the one defined for the business operation;
- scope is derived by the backend;
- denial occurs before mutation;
- success continues to domain validation;
- a frontend-supplied alternative scope cannot widen access.

## 19. Dependencies

### 19.1 Internal dependencies

- Authenticated actor context supplied by backend composition.
- Shared identity and clock adapters.
- PostgreSQL transaction and repository infrastructure.
- Shared API conventions and error handlers.
- Protected contexts declaring action and scope requirements at their application boundaries.

### 19.2 External dependencies

- PostgreSQL managed through Supabase CLI migrations.
- A separately implemented authentication mechanism capable of producing a stable trusted identity subject.

No authentication-provider SDK is required by the Access domain or application layers.

## 20. Completion criteria

The backend capability is complete when:

1. All Access Control PRD acceptance criteria applicable to backend behavior pass automated tests.
2. Authentication and Access Control are integrated only through the trusted identity contract.
3. Every protected operation is denied by default and uses a server-derived scope.
4. Multiple active roles produce additive exact-match permissions.
5. Preset changes do not mutate existing roles.
6. System Administrator access covers newly recognized scopes and the last active administrator is protected transactionally.
7. Administrative mutations and their audit evidence are atomic.
8. The documented API is represented in OpenAPI and matches API tests.
9. Migrations, ORM mappings, repositories, and integration tests agree on the physical schema.
10. No direct user permissions, explicit denials, arbitrary client-defined scopes, scope inheritance, shift rules, or authentication implementation have been introduced.
