# Delta for authentication-foundation

## ADDED Requirements

### Requirement: Auth Admin Route Authorization (C1)

The system MUST enforce `manage_access` authorization on all administrative Authentication endpoints (`/api/v1/auth/accounts/*`, `/api/v1/auth/audits`). The HTTP adapter MUST resolve the authenticated identity AND verify System Administrator authorization before executing any administrative use case.

#### Scenario: Authorized admin access

- GIVEN an active System Administrator with `manage_access` permission
- WHEN they request `GET /api/v1/auth/accounts`
- THEN the system processes the request normally

#### Scenario: Unauthorized user rejected

- GIVEN an authenticated user without `manage_access` permission
- WHEN they request `POST /api/v1/auth/accounts`
- THEN the system returns `403 access_denied` without executing the use case

#### Scenario: Inactive user rejected

- GIVEN an authenticated user whose Access profile is inactive
- WHEN they request any auth admin endpoint
- THEN the system returns `403 access_user_inactive`

#### Scenario: Unauthenticated request rejected

- GIVEN a request without a valid bearer token
- WHEN it targets any auth admin endpoint
- THEN the system returns `401 authentication_required`

### Requirement: Functional Bootstrap CLI (C2)

The system MUST provide an executable CLI command (`uv run --package backend python -m auth.adapters.bootstrap_command`) that creates the initial System Administrator. The command MUST: seed the `system_administrator` role via migration, create the provider identity, create the Authentication account in `awaiting_password_change`, invoke Access Control bootstrap, and write redacted audits.

#### Scenario: Bootstrap creates initial administrator

- GIVEN no System Administrator exists and the `system_administrator` role is seeded
- WHEN the bootstrap command runs with email, provisional password, user code, and display name
- THEN the system creates the provider identity, Authentication account, Access profile, and role assignment
- AND the account status is `awaiting_password_change`

#### Scenario: Bootstrap is idempotent

- GIVEN the initial System Administrator already exists with the same identifiers
- WHEN the bootstrap command runs again
- THEN the command succeeds without creating duplicates

#### Scenario: Bootstrap rejects conflicting state

- GIVEN a partial initialization exists with conflicting identifiers
- WHEN the bootstrap command runs
- THEN the command fails closed with a clear error

#### Scenario: System Administrator role seed migration

- GIVEN a fresh database with migrations applied
- WHEN the application starts
- THEN the `system_administrator` role exists in `access_roles` with `is_system_administrator = true`
- AND the `access_control` scope exists in `access_scopes`
