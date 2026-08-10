# HTTP Request Files

REST client files for manual endpoint testing. Compatible with VS Code REST
Client extension and JetBrains HTTP Client.

## Setup

1. Copy `backend/.env.example` to `backend/.env` with real Supabase local values.
2. Start Supabase: `pnpm supabase start`.
3. Reset the database: `pnpm supabase db reset --local --no-seed`.
4. Start backend: `uv run --package backend fastapi dev` (from the repo root).
5. Provision the test users following the manual steps in `CREDENTIALS.md`.
6. Run requests from these files.

There is no tracked setup script. After a database reset, follow the manual
provisioning flow in `CREDENTIALS.md`: bootstrap the initial System
Administrator with the tracked CLI, replace the provisional password, register
the needed scopes, create the test roles, and provision the test users through
the admin API. This is temporary until the frontend is implemented.

## Credentials and tokens

Stable user/password credentials live in `CREDENTIALS.md` (separate from this
README). Access tokens expire after ~1 hour and are never stored in these
files: run the Sign in request in the `.http` file, copy `access_token` from
the response, and paste it into the `@token` variable at the top of the file.

## Version-aware `expected_version`

Stateful endpoints (`password-reset`, `disable`, `enable`, `PATCH .../status`,
role/preset updates, and `PUT .../roles`) require `expected_version` to equal the current resource
version. Versions increment on every mutation. The files use sequential
examples for a fresh state; if a request returns `..._version_conflict`, re-read
the resource detail (`GET /auth/accounts/{id}`, `GET /access/roles/{id}`,
`GET /access/role-presets/{id}`, `GET /access/users/{id}`) and use the reported
`version`.

Impact-preview responses expose that same value as `subject_version`. Preview
requests are read-only and do not reserve it. Confirm with `expected_version`
equal to `subject_version`; a `409 access_version_conflict` means the preview is
stale and must be run again.

## File Index

- `auth.http` — Authentication endpoints (user + admin)
- `access.http` — Access Control endpoints (self-access + admin)
- `warehouse.http` — Warehouse bale management
- `CREDENTIALS.md` — Stable test credentials and token retrieval
