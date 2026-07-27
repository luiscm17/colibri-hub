---
document_type: conceptual-model
status: active
implementation: partial
scope: access-control
authority: conceptual
owner: architecture
last_reviewed: 2026-07-27
---

# Access DB Dictionary

This dictionary is a concise review aid for the current Access DBML. Access is an authorization policy context: it owns canonical users, active/inactive lifecycle, technical roles, scoped assignments, individual exceptions, and access-change history. It does not own operational records or workflow meaning.

## Review focus

- `access_users.user_id` is the canonical user identity. Existing operational `*_user_id` fields remain external audit references; they do not decide authorization and do not become Access-owned records.
- Every user has one current technical role. Role codes and names describe capability profiles, never organizational job titles.
- `sys_admin` is the mandatory, unique active System Administrator technical role. It has all five fixed actions and gives an active holder automatic global operational authorization for every current and future section, unit, and area. This narrow bypass needs no scope assignment and cannot be constrained by individual exceptions; it is not a scope hierarchy, wildcard, or generic permission engine.
- Ordinary roles allow actions; concurrent user-to-scope assignments determine where those actions apply. Default deny applies when no valid exception exists and a required active role allowance or assignment is absent.
- Initial scopes are deliberately flat: Operation Unit at section level, and other targets at unit or area level. `access_scopes` is the small Access-owned approved-scope registry: it validates an external target with its owning context before confirmation, then only an `active` target can authorize. It has no cross-context foreign key, hierarchy, wildcard, or resource registry.
- `write` authorizes real owner-scope handoffs, including Quality Send and Warehouse acceptance. Those remain domain events, not RBAC actions.
- `edit` is an audited correction of a recorded fact within the operational window. Only the System Administrator technical role may receive `edit_outside_window` or `manage_access`.
- Individual exceptions directly grant or restrict one action in one scope for explicit dates. A restriction wins; a grant supplies that one targeted allowance without changing the global role. Grants for `edit_outside_window` and `manage_access` are rejected.
- Initial deployment uses one controlled database seed or migration transaction to create the active `sys_admin` role, its five action rows, the initial active bootstrap user, and the corresponding `initial_bootstrap` audit rows. This is the only exception to requiring a pre-existing active System Administrator actor: the bootstrap user creator, the five role-action creators, and bootstrap audit actors are null. Every later lifecycle or access-administration change requires an active `sys_admin` actor and normal audit evidence.
- After bootstrap, a database transaction must atomically reject any deactivation, reassignment, revocation, or other change that would leave no active user whose current role is the active `sys_admin` role.
- Deactivation denies new decisions immediately and advances the user's authorization epoch. Reactivation advances it again, preserving history but requiring explicit new assignments and exceptions.

## Authorization decision

1. Deny when the user is inactive.
2. Allow every fixed action for an active user whose active current role is `sys_admin`. This narrow System Administrator bypass applies to every current and future section, unit, and area without a scope assignment; individual exceptions do not constrain it.
3. For every other user, deny when the scope is not `active` or the assignment/exception authorization epoch differs from the user's current epoch.
4. Deny an ordinary user when a currently valid individual restriction covers the action and scope.
5. Allow a currently valid individual grant for that action and scope, except `edit_outside_window` and `manage_access`, which cannot be individually granted.
6. Otherwise, allow an ordinary user only when the current role is active, allows the action, and an active scoped assignment covers the requested scope.
7. Deny every other request. `edit_outside_window` and `manage_access` remain exclusive to `sys_admin`.

The DBML defines storage, not the runtime evaluator or correction-window rule. PostgreSQL constraints or transaction validation must enforce the annotated role/action, System Administrator actor, authorization-epoch, and approved-scope lifecycle rules; these checks cannot be expressed as DBML foreign keys alone.

## Tables

### `access_roles`

Represents configurable technical capability profiles.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `role_id` | Technical identifier for the role profile. | No. |
| `role_code`, `role_name` | Stable technical profile identity and readable name. | No; neither may be an organizational title. |
| `is_system_administrator` | Marks the mandatory, unique active `sys_admin` technical role, which has all five actions and global operational authorization. | No; enforce exactly one active role with `role_code = sys_admin` and this flag. |
| `is_active` | Retires a profile without deleting history. | No. |
| `created_at`, `updated_at` | System capture and last update timestamps. | Created no; updated yes. |

### `access_users`

Represents the canonical user identity and authorization lifecycle.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `user_id` | Canonical Access-owned identity referenced externally for operational audit evidence. | No. |
| `role_id` | Holds exactly one current technical role. | No. |
| `user_code`, `display_name` | Stable visible identifier and readable identity. | No. |
| `is_active` | Immediately blocks new authorization decisions when false. | No. |
| `authorization_epoch` | Separates the user's current authorization generation from historical grants. | No; increment on each deactivation and reactivation. |
| `created_by_user_id`, `created_at` | Records the active System Administrator creation action. | Creator is null only for the initial active `sys_admin` bootstrap user in the controlled deployment transaction; creation time is not optional. |
| `deactivated_by_user_id`, `deactivated_at` | Preserves deactivation evidence. | Yes; required when deactivated. |
| `reactivated_by_user_id`, `reactivated_at` | Preserves reactivation evidence. | Yes; required when reactivated. |
| `updated_at` | Last system update time. | Yes. |

### `access_role_actions`

Represents the fixed action allowances of a technical role.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `role_action_id` | Technical identifier for the allowance. | No. |
| `role_id`, `action` | Allows one fixed action for one role; the pair is unique. | No; the mandatory active `sys_admin` role has all five actions, while `manage_access` and `edit_outside_window` require that role. |
| `created_by_user_id`, `created_at` | Audits configuration creation alongside the full change audit. | Creator is null only for the five `sys_admin` action rows inserted in the controlled initial deployment transaction; otherwise it must be an active `sys_admin` actor. |

### `access_scopes`

Represents the small, flat Access-owned approved-scope registry for external targets.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `scope_id`, `scope_code` | Access identifier and stable registry code for one external target. | No. |
| `scope_kind` | Limits first-slice scope storage to Operation Unit sections and other units or areas. | No; do not add process, shift, wildcard, or hierarchy kinds in this pass. |
| `owning_context`, `external_scope_id` | Identifies the external business target without making Access own it or creating a cross-context FK. | No. |
| `status` | Holds pending confirmation, active, inactive, or rejected state. | No; only `active` can authorize or receive assignments/exceptions. |
| `confirmed_by_user_id`, `confirmed_at` | Records the active System Administrator confirmation after validating the target with its owning context. | Required when `status` is `active`. |
| `rejected_by_user_id`, `rejected_at`, `rejection_reason` | Retains an unconfirmed target that was rejected rather than allowing it to become an authorization input. | Required when `status` is `rejected`. |
| `created_at`, `updated_at` | System capture and last update timestamps. | Created no; updated yes. |

### `access_user_scope_assignments`

Represents a user's concurrent active or historical scope assignments.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `assignment_id` | Technical identifier for the assignment. | No. |
| `user_id`, `scope_id`, `authorization_epoch` | Connects one user to one approved scope in the user's current authorization generation. | No; a user may have multiple concurrent scopes, but a prior epoch never becomes effective after reactivation. |
| `valid_from`, `valid_to` | Defines when the assignment applies. | End date yes; it must not precede the start date. |
| `granted_by_user_id`, `granted_at` | Records the active System Administrator grant. | No. |
| `revoked_by_user_id`, `revoked_at`, `revoke_reason` | Preserves an early revocation. | Yes; actor/time required when revoked; actor must be an active System Administrator. |
| `created_at` | System capture time. | No. |

### `access_user_action_exceptions`

Represents one direct individual grant or restriction for one action and one scope.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `exception_id` | Technical identifier for the exception. | No. |
| `user_id`, `scope_id`, `authorization_epoch`, `action` | Pinpoints the individual, scope, authorization generation, and fixed action affected. | No; a prior epoch never becomes effective after reactivation. |
| `effect` | Distinguishes a direct grant from a direct restriction. | No; restrict overrides allowance, while grants for `manage_access` and `edit_outside_window` are rejected. |
| `valid_from`, `valid_to` | Requires explicit, bounded validity. | No; end date must not precede start date. |
| `reason` | Explains why exceptional access was necessary. | No. |
| `granted_by_user_id`, `granted_at` | Records the active System Administrator grant. | No. |
| `revoked_by_user_id`, `revoked_at`, `revoke_reason` | Preserves early revocation evidence. | Yes; actor/time required when revoked; actor must be an active System Administrator. |
| `created_at` | System capture time. | No. |

### `access_change_audits`

Represents the append-only audit trail for Access configuration and lifecycle changes.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `access_change_audit_id` | Technical identifier for the audit entry. | No. |
| `change_kind` | Fixed category for the user, role, scope, assignment, or exception change. | No; extend only when a new Access change is justified. |
| `subject_table`, `subject_id` | Identifies the changed Access record without a generic policy engine. | No. |
| `performed_by_user_id`, `occurred_at` | Records the active System Administrator actor and time. | Actor is null only for `initial_bootstrap` records created atomically with the initial `sys_admin` role, its action rows, and bootstrap user; otherwise it must be an active `sys_admin` actor. |
| `reason` | Captures the change rationale when relevant. | Yes. |
| `before_values`, `after_values` | Preserves the changed Access configuration or lifecycle values. | Yes; require the applicable snapshot for a change type at implementation. |
| `created_at` | System capture time. | No. |

## Out of scope for this pass

- Authentication, sessions, tokens, and identity-provider integration.
- ABAC, role hierarchy, business-title roles, or a seeded business role matrix.
- A generic permissions, policy, resources, or catalog engine.
- Scope hierarchy, nested sets, wildcard matching, or invented organizational nodes.
- Domain workflow ownership, Quality sub-actions, or Warehouse acceptance as an RBAC action.
- Application code, SQL, indexes beyond DBML uniqueness, or runtime authorization enforcement.
