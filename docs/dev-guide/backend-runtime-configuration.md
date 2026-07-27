---
document_type: runbook
status: active
implementation: implemented
scope: backend/configuration
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Backend runtime configuration

Use `backend/.env` only for local backend development. The backend has one
required runtime setting: `DATABASE_URL`.

## Local quick path

From the repository root:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with the local DATABASE_URL.
uv run fastapi dev
```

Do not add `--env-file`. `backend/main.py` derives and hands off only its
direct sibling `backend/.env`; it does not search the current directory,
ancestors, repository root, or installed package locations.

## Source precedence

| Source | When it applies | Priority |
|---|---|---|
| Operating-system `DATABASE_URL` | Local, staging, and production | Highest |
| Explicit `backend/.env` | Source-checkout local entrypoint only | Lower |
| No dotenv file | Installed callers and missing local file | OS environment only |

Pydantic Settings parses the explicit file. An OS value overrides it. The
backend fails before readiness when `DATABASE_URL` is missing, blank, or
malformed. Its `SecretStr` representation and validation messages redact the
URL; do not log or print the value.

Creating settings or the SQLAlchemy engine does not open a database connection.
Connection work begins when a request uses a session.

## Test isolation

Unit tests must construct settings directly or use `_env_file=None` so a
developer's `backend/.env` cannot influence test results. Integration tests use
`TEST_DATABASE_URL` separately; it is deliberately guarded to the local
PostgreSQL target and never falls back to `DATABASE_URL`.

## Public and secret boundaries

A shared deployment environment may supply both applications, but values have
different visibility. Vite exposes `VITE_*` values to browser code, so those
values are public and must not carry backend credentials. Frontend configuration
and CORS implementation are not part of this change.
