# HTTP Request Files

REST client files for manual endpoint testing. Compatible with VS Code REST Client extension and JetBrains HTTP Client.

## Setup

1. Copy `backend/.env.example` to `backend/.env` with real Supabase local values.
2. Start Supabase: `pnpm supabase start`
3. Reset database: `pnpm supabase db reset --local --no-seed`
4. Start backend: `uv run --locked --package backend fastapi dev`
5. Run requests from these files.

## Getting a Token

Sign in via the Supabase Auth API to get a real access token:

```bash
curl -s -X POST http://127.0.0.1:54321/auth/v1/token?grant_type=password \
  -H "apikey: <anon_key>" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@colibri.test","password":"TestAdmin123!"}' | python3 -m json.tool
```

Copy the `access_token` value into the `@token` variable in the `.http` files.

## File Index

- `auth.http` — Authentication endpoints (user + admin)
- `warehouse.http` — Warehouse bale management
