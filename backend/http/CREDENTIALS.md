# Local Test Credentials

Stable credentials for the local development stack. Managed by
`scripts/setup_local_db.py` (not tracked). Passwords persist across test runs
until the database is reset; the access token does not and is therefore not
documented in the `.http` files.

## Users

| User | Email | Password | Role | State |
| ---- | ----- | -------- | ---- | ----- |
| Admin | `admin@colibri.test` | `AdminTest123!` | `system_administrator` | active |
| Operator | `operator@colibri.test` | `OperatorTest123!` | `operator` | active |

The `operator` role grants `read`/`write` on scope
`yarn_spinning.section.ring_spinning`.

## Getting an access token

Access tokens expire after ~1 hour. Generate one and paste it into the `@token`
variable of the `.http` file you are using:

```bash
curl -s -X POST http://127.0.0.1:54321/auth/v1/token?grant_type=password \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@colibri.test","password":"AdminTest123!"}' | python3 -m json.tool
```

The token request for the operator user is the same, with
`operator@colibri.test` / `OperatorTest123!`.

## Resetting to a known state

```bash
pnpm supabase db reset --local --no-seed
uv run --locked --package backend python scripts/setup_local_db.py
```

After the reset, the first Sign in may require replacing the provisional
password (`ProvisionalAdmin123!` / `ProvisionalOperator123!`) — the setup script
already performs that replacement, so logins work immediately with the
passwords above.
