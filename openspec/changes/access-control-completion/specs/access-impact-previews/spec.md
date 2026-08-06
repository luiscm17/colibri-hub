# Access Impact Previews Specification

## Purpose

Impact previews allow the System Administrator to see the effects of role and assignment mutations before committing them. Previews calculate affected users and permission deltas without mutating state.

## Requirements

### Requirement: Role Change Preview

The system MUST provide a preview of how a role configuration change would affect assigned users. The preview MUST return the count of affected users, their identities, permissions that would be added, and permissions that would be removed from each user's effective set.

#### Scenario: Preview role permission addition

- GIVEN role R is assigned to users A, B, and C
- WHEN the administrator POSTs to `/api/v1/access/roles/{role_id}/preview` with the intended new permission set
- THEN the system returns `affected_user_count: 3`, the list of affected users, and the permission delta
- AND no state is mutated

#### Scenario: Preview role permission removal

- GIVEN role R has permission [write+scope_A] and is assigned to user A who also has [write+scope_A] from role S
- WHEN the preview removes [write+scope_A] from role R
- THEN user A appears in affected users but [write+scope_A] is NOT in `permissions_removed` because role S still grants it

#### Scenario: Preview includes subject version for confirmation

- GIVEN role R has `version = 5`
- WHEN the preview is calculated
- THEN the response includes `subject_version: 5`
- AND confirmation requires sending `expected_version: 5`

### Requirement: User Role Replacement Preview

The system MUST provide a preview of how replacing a user's assigned roles would change their effective permissions. The preview MUST show roles being added, roles being removed, and the net permission delta.

#### Scenario: Preview user role replacement

- GIVEN user U has roles [R1, R2] with combined permissions [read+A, write+A, read+B]
- WHEN the administrator POSTs to `/api/v1/access/users/{user_id}/roles/preview` with roles [R2, R3]
- THEN the system returns the permission delta reflecting removal of R1's exclusive permissions and addition of R3's permissions

#### Scenario: Preview removing last System Administrator assignment

- GIVEN user U is the only active System Administrator
- WHEN the administrator previews replacing U's roles with ordinary roles only
- THEN the system returns `409 last_system_administrator_required`

### Requirement: Preview Does Not Mutate State

Previews MUST be read-only calculations. They MUST NOT reserve state, increment versions, create audit entries, or lock rows. The system SHOULD recalculate invariants inside the write transaction on confirmation.

#### Scenario: Stale preview on confirmation

- GIVEN a preview was generated with `subject_version: 4`
- WHEN another administrator modifies the role (version becomes 5) before confirmation
- THEN the confirmation attempt with `expected_version: 4` returns `409 access_version_conflict`

### Requirement: Preview API Endpoints

The system MUST expose 2 preview endpoints requiring `manage_access` authorization:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/access/roles/{role_id}/preview` | Preview role configuration change |
| POST | `/api/v1/access/users/{user_id}/roles/preview` | Preview user role replacement |

#### Scenario: Preview with unauthorized user

- GIVEN an authenticated user without `manage_access` permission
- WHEN they request a preview endpoint
- THEN the system returns `403 access_denied`

#### Scenario: Preview non-existent role

- GIVEN no role exists with the requested ID
- WHEN an administrator requests its preview
- THEN the system returns `404 access_role_not_found`

### Requirement: Preview Response Contract

The preview response MUST include: `subject_version`, `affected_user_count`, `affected_users` (list with user_id, user_code, display_name), `permissions_added`, and `permissions_removed`. Permission deltas MUST reflect the NET effective change considering all of a user's assigned roles.

#### Scenario: Preview response structure

- GIVEN a valid preview request
- WHEN processed
- THEN the response conforms to the documented JSON structure with all required fields
