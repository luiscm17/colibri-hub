# Local Test Credentials

Stable credentials and the manual provisioning flow for the local development
stack. There is **no tracked setup script**: after a database reset you
recreate the test users with the manual steps below. This document is a
temporary aid until the frontend is implemented; it is not product
documentation.

## PRD alignment — why there is no `operator` role

The Access Control PRD (`docs/prd/access-control.md`) forbids using the generic
name "Operator" for an RBAC preset or technical role: "Machine Operator" is a
business actor who manipulates production equipment and is not a direct system
user, so the name would make both concepts ambiguous.

Test roles therefore use the organizational references the PRD explicitly
allows: `section-responsible` (the minimum responsibility level expected to use
the system directly) and `supervisor` (read-only operational consultation).
Display names identify synthetic people, while role names identify their system
responsibilities.

## Users

| User | Email | Password | Role(s) | State |
| ---- | ----- | -------- | ------- | ----- |
| Alex Rivera | `admin@colibri.test` | `AdminTest123!` | `system_administrator` | active |
| Sofía Torres | `section@colibri.test` | `SectionTest123!` | `section-responsible` | active |
| Diego Morales | `supervisor@colibri.test` | `SupervisorTest123!` | `supervisor` | active |

Test role permission sets (scopes as documented in the scope definitions seed):

- `section-responsible` — `read`/`write`/`edit` on
  `yarn_spinning.section.ring_spinning`.
- `supervisor` — `read` on `yarn_spinning.section.ring_spinning`.

## Manual setup after a database reset

`pnpm supabase db reset --local --no-seed` removes both Auth users and the
application account rows. Recreate them in this order (backend must be
running):

### 1. Bootstrap the initial System Administrator

The bootstrap CLI does not load `backend/.env` (only the FastAPI dev entrypoint
does), so export it first. Run from the repository root:

```bash
set -a; source backend/.env; set +a

BOOTSTRAP_EMAIL=admin@colibri.test \
BOOTSTRAP_PASSWORD=AdminBootstrap123! \
BOOTSTRAP_USER_CODE=USR-ADM-001 \
BOOTSTRAP_DISPLAY_NAME="Alex Rivera" \
uv run --locked --package backend python -m auth.adapters.bootstrap_command
```

The bootstrap CLI is the only tracked provisioning path and it is idempotent
for the same identifiers. The account starts in `awaiting_password_change` with
the provisional password above.

### 2. Replace the provisional password with the stable one

Sign in with `admin@colibri.test` / `AdminBootstrap123!` (see "Getting an
access token"), then call the `password-change` request in `auth.http`
(`current_password` = provisional, `new_password` = `AdminTest123!`).

### 3. Register the yarn spinning scope (if not already registered)

The `access_control` scope is registered by the seed migration; the yarn
spinning scopes exist as definitions but need registration:

```http
POST /api/v1/access/scopes
{ "definition_key": "yarn_spinning.section.ring_spinning", "reason": "Enable test role scope" }
```

If it returns `409`, the scope is already registered — continue. Get the
`scope_id` from `GET /api/v1/access/scopes?page=1&page_size=50`.

### 4. Create the test roles

```http
POST /api/v1/access/roles
{
  "role_code": "section-responsible",
  "role_name": "Section Responsible",
  "description": "Minimum responsibility level for direct system use",
  "permissions": [
    { "action": "read", "scope_id": "<ring_spinning_scope_id>" },
    { "action": "write", "scope_id": "<ring_spinning_scope_id>" },
    { "action": "edit", "scope_id": "<ring_spinning_scope_id>" }
  ],
  "reason": "Local test fixture"
}
```

Repeat for `supervisor` with `read` only. Roles must exist before you provision
the users that reference them.

### 5. Provision the test users

Use a **temporary provisional password**, different from the documented final
one: the activation step requires `current != new` (see step 6).

```http
POST /api/v1/auth/accounts
{
  "email": "section@colibri.test",
  "provisional_password": "TempSection123!",
  "user_code": "USR-SEC-001",
  "display_name": "Sofía Torres",
  "role_codes": ["section-responsible"],
  "reason": "Local test fixture"
}
```

Repeat for `supervisor@colibri.test` with `display_name: "Diego Morales"`,
`role_codes: ["supervisor"]`, and a different temporary provisional (e.g.
`TempSupervisor123!`).

### 6. Activate the test users

Provisioning leaves the account in `awaiting_password_change`. The mandatory
password replacement rejects `current_password == new_password`
(422 `replacement_password_must_differ`), so you cannot provision directly with
the documented final password. For each user:

1. Sign in with the temporary provisional (see "Getting an access token").
2. Call the `password-change` request in `auth.http`: `current_password` =
   the temporary provisional, `new_password` = the documented stable password.

The account transitions `awaiting_password_change -> active`, and the final
password matches the table at the top of this document.

## Getting an access token

Access tokens expire after ~1 hour. Generate one and paste it into the `@token`
variable of the `.http` file you are using:

```bash
curl -s -X POST http://127.0.0.1:54321/auth/v1/token?grant_type=password \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@colibri.test","password":"AdminTest123!"}' | python3 -m json.tool
```

The token request for the other users is the same, with their email and
password.

## Resetting to a known state

```bash
pnpm supabase db reset --local --no-seed
# start the backend, then follow the manual setup steps above
```

The setup is not a single command: there is intentionally no tracked script
(the previous `scripts/setup_local_db.py` was never tracked and is not
restored). The steps above are idempotent — after a reset they rebuild the same
stable users.
