# HTTP Request Files

REST client files for manual endpoint testing. Compatible with VS Code REST
Client extension and JetBrains HTTP Client.

## Setup

1. Copy `backend/.env.example` to `backend/.env` with real Supabase local values.
2. Start Supabase: `pnpm supabase start`.
3. Reset the database: `pnpm supabase db reset --local --no-seed`.
4. Prepare test users: `uv run --locked --package backend python scripts/setup_local_db.py`.
5. Start backend: `uv run fastapi dev` (from the repo root).
6. Run requests from these files.

`scripts/setup_local_db.py` bootstraps the initial System Administrator,
registers the operator role/scope, and provisions an active operator user.
It is not tracked (see `.gitignore`).

## Credentials and tokens

Stable user/password credentials live in `CREDENTIALS.md` (separate from this
README). Access tokens expire after ~1 hour and are never stored in these
files: run the Sign in request in the `.http` file, copy `access_token` from
the response, and paste it into the `@token` variable at the top of the file.

## Version-aware `expected_version`

Stateful endpoints (`password-reset`, `disable`, `enable`, `PATCH .../status`,
`PUT .../roles`) require `expected_version` to equal the current resource
version. Versions increment on every mutation. The files use sequential
examples for a fresh state; if a request returns `..._version_conflict`, re-read
the resource detail (`GET /auth/accounts/{id}`, `GET /access/roles/{id}`,
`GET /access/users/{id}`) and use the reported `version`.

## File Index

- `auth.http` — Authentication endpoints (user + admin)
- `access.http` — Access Control endpoints (self-access + admin)
- `warehouse.http` — Warehouse bale management
- `CREDENTIALS.md` — Stable test credentials and token retrieval
