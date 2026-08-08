# Access Role Presets Specification

## Purpose

Role presets provide reusable starting configurations for creating roles. A preset defines a template permission set that is copied on role creation — the resulting role is independent and MAY be changed without altering the source preset.

## Requirements

### Requirement: Preset CRUD Lifecycle

The system MUST support creating, reading, updating, and deactivating role presets. Each preset MUST have a unique code, a display name, and a permission set composed of action-scope pairs. Preset updates MUST replace the complete permission set and require optimistic concurrency via `expected_version`. Presets MUST NOT contain `manage_access` or `edit_outside_window` actions.

#### Scenario: Create a role preset

- GIVEN an active System Administrator
- WHEN they POST to `/api/v1/access/role-presets` with code, name, description, and permissions
- THEN the system creates the preset with `is_active = true` and returns `201`
- AND an access-change audit entry is recorded

#### Scenario: Update a role preset

- GIVEN an existing active preset with `version = 3`
- WHEN the administrator PUTs new permissions with `expected_version = 3`
- THEN the system replaces the full permission set, increments version, and returns `200`
- AND an audit entry records before/after permission snapshots

#### Scenario: Reject privileged actions on preset

- GIVEN a preset creation or update request containing `manage_access`
- WHEN the request is processed
- THEN the system returns `422 privileged_action_requires_system_administrator`

#### Scenario: Reject duplicate preset code

- GIVEN a preset with code `warehouse-operator` already exists
- WHEN another preset is created with the same code
- THEN the system returns `409 duplicate_access_preset_code`

### Requirement: Preset Activation and Deactivation

The system MUST support activating and deactivating presets via PATCH status endpoint. An inactive preset MUST NOT be available for creating new roles. Deactivation MUST NOT alter roles previously created from the preset.

#### Scenario: Deactivate a preset

- GIVEN an active preset used to create 3 roles previously
- WHEN the administrator deactivates it
- THEN the preset becomes inactive and the 3 existing roles remain unchanged
- AND creating a role from this preset is rejected

#### Scenario: Reactivate a preset

- GIVEN an inactive preset
- WHEN the administrator activates it
- THEN the preset becomes available for role creation again

### Requirement: Copy-on-Create Semantics

The system MUST create roles from presets by copying the preset's permission set at creation time. The resulting role MUST be fully independent — subsequent preset modifications MUST NOT propagate to previously created roles.

#### Scenario: Create role from preset

- GIVEN an active preset with 4 permissions
- WHEN the administrator POSTs to `/api/v1/access/role-presets/{preset_id}/roles` with role code and name
- THEN a new active role is created with the same 4 permissions copied from the preset
- AND the role stores no live dependency on the preset

#### Scenario: Preset change does not affect existing roles

- GIVEN a role was created from preset P with permissions [read+scope_A, write+scope_A]
- WHEN the administrator updates preset P to add [edit+scope_A]
- THEN the existing role retains only [read+scope_A, write+scope_A]

### Requirement: Preset API Endpoints

The system MUST expose 6 preset endpoints requiring `manage_access` authorization:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/access/role-presets` | List presets |
| POST | `/api/v1/access/role-presets` | Create preset |
| GET | `/api/v1/access/role-presets/{preset_id}` | Get preset |
| PUT | `/api/v1/access/role-presets/{preset_id}` | Update preset |
| PATCH | `/api/v1/access/role-presets/{preset_id}/status` | Activate/deactivate |
| POST | `/api/v1/access/role-presets/{preset_id}/roles` | Create role from preset |

#### Scenario: Unauthorized access to preset endpoints

- GIVEN an authenticated user without `manage_access` permission
- WHEN they request any preset endpoint
- THEN the system returns `403 access_denied`

#### Scenario: Get non-existent preset

- GIVEN no preset exists with the requested ID
- WHEN an administrator requests it
- THEN the system returns `404 access_preset_not_found`

### Requirement: Preset Persistence

The system MUST persist presets in `access_role_presets` and their permissions in `access_role_preset_permissions` tables. The `(preset_id, scope_id, action)` combination MUST be unique. Preset permission rows MUST reference only active scopes and supported actions.

#### Scenario: Reject inactive scope in preset permissions

- GIVEN scope S is inactive
- WHEN an administrator creates a preset referencing scope S
- THEN the system returns `409 inactive_access_scope`
