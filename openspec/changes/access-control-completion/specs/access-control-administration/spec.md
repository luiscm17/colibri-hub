# Delta for access-control-administration

## ADDED Requirements

### Requirement: Authorization Version Propagation (D3)

The system MUST increment `authorization_version` for all affected users whenever a mutation changes their effective permissions. This includes: role permission changes (all users assigned to that role), role activation/deactivation (all assigned users), scope activation/deactivation (users whose roles reference that scope), and role assignment changes (the affected user).

#### Scenario: Role permission update propagates version

- GIVEN role R is assigned to users A, B, and C
- WHEN the administrator updates role R's permissions
- THEN `authorization_version` is incremented for users A, B, and C within the same transaction

#### Scenario: Role deactivation propagates version

- GIVEN active role R is assigned to users A and B
- WHEN the administrator deactivates role R
- THEN `authorization_version` is incremented for users A and B

#### Scenario: Scope deactivation propagates version

- GIVEN scope S is referenced by role R assigned to user A
- WHEN the administrator deactivates scope S
- THEN `authorization_version` is incremented for user A

#### Scenario: Role assignment replacement propagates version

- GIVEN user U has `authorization_version = 7`
- WHEN the administrator replaces U's roles
- THEN U's `authorization_version` becomes 8

### Requirement: Login Audit Events (C5)

The system MUST persist login-related security audit events. The Authentication module MUST write `login_succeeded` and `login_failed` event types to `authentication_audits` when login outcomes are observed. Events MUST include the provider session correlation when available.

#### Scenario: Successful login audit

- GIVEN a user authenticates successfully via the provider
- WHEN the login outcome is observed by the backend
- THEN an `authentication_audits` entry is written with `event_type = 'login_succeeded'` and `outcome = 'succeeded'`
- AND `provider_session_id` is populated

#### Scenario: Failed login audit

- GIVEN a login attempt fails at the provider
- WHEN the failure is observed by the backend
- THEN an `authentication_audits` entry is written with `event_type = 'login_failed'` and `outcome = 'failed'`
- AND no account existence information is revealed in the audit details

#### Scenario: Audit query includes login events

- GIVEN login audit events exist
- WHEN an administrator queries `GET /api/v1/auth/audits`
- THEN login events appear in the paginated results alongside other authentication audits

## MODIFIED Requirements

### Requirement: Last-Administrator Invariant with Row-Level Locking (C3)

The system MUST protect the last active System Administrator using row-level locking (`SELECT ... FOR UPDATE`) before evaluating the invariant. The invariant MUST be enforced across ALL mutation paths: profile deactivation, role replacement, assignment revocation, role deactivation, and the Authentication policy check for disable/reset operations. (Previously: invariant used `for_update=False` and was only partially enforced in auth queries)

#### Scenario: Concurrent last-admin removal rejected

- GIVEN user A is the only active System Administrator
- WHEN two concurrent requests attempt to remove A's admin assignment
- THEN exactly one succeeds and the other receives `409 last_system_administrator_required`
- AND the reserved role row and assignment are locked during evaluation

#### Scenario: Profile deactivation enforces invariant

- GIVEN user A is the only active System Administrator
- WHEN an administrator attempts to deactivate A's Access profile
- THEN the system returns `409 last_system_administrator_required`

#### Scenario: Role replacement enforces invariant

- GIVEN user A is the only active System Administrator
- WHEN an administrator replaces A's roles with ordinary roles only
- THEN the system returns `409 last_system_administrator_required`

#### Scenario: Auth disable checks invariant with locking

- GIVEN user A is the only active System Administrator
- WHEN Authentication requests the last-admin policy check before disabling A
- THEN the Access module acquires row locks and returns denial
- AND the disable operation is aborted before provider changes

#### Scenario: Multiple administrators allows removal

- GIVEN users A and B are both active System Administrators
- WHEN an administrator removes A's admin assignment
- THEN the operation succeeds because B remains

### Requirement: Provisioning Display Name Fix (C4)

The system MUST use the `display_name` field from the provisioning command when creating the Access profile. The adapter MUST NOT substitute `profile_code` or any other field for `display_name`. Cross-context transactional rollback MUST be verified. (Previously: adapter passed `display_name=profile_code` incorrectly)

#### Scenario: Provisioning uses correct display name

- GIVEN a provisioning command with `display_name = "María García"` and `user_code = "USR-015"`
- WHEN the Access profile is created
- THEN the profile's `display_name` is `"María García"`, not `"USR-015"`

#### Scenario: Cross-context rollback on failure

- GIVEN provisioning creates the Authentication account successfully
- WHEN the Access profile creation fails (e.g., duplicate identity)
- THEN both the Authentication account and Access profile changes are rolled back
- AND no partial state persists
