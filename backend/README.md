# Backend runtime configuration

The backend reads one required setting: `DATABASE_URL`. Local development uses
an ignored `backend/.env`; deployed environments use platform-injected values.

## Local quick path

From the repository root:

```bash
cp backend/.env.example backend/.env
# Set DATABASE_URL in backend/.env for your local database.
uv run fastapi dev
```

Do not pass `--env-file`. `backend/main.py` explicitly supplies its direct
sibling `backend/.env`, so this works independently of the invoking directory.
The file is optional: if it is absent, only operating-system environment
variables are considered.

## Source and safety rules

| Topic | Runtime behavior |
|---|---|
| Settings owner | `infra.configuration.ApplicationSettings` is the only environment/dotenv reader. |
| Precedence | An operating-system `DATABASE_URL` overrides the value in `backend/.env`. |
| Validation | Missing, blank, whitespace-only, or malformed URLs fail before the application is healthy. |
| Secrets | The URL is stored as `SecretStr`; configuration representations and validation messages redact it. |
| Connection | Constructing settings and the SQLAlchemy engine does not connect. A session use performs database I/O. |

Use `DATABASE_URL` only for the backend application. Unit tests construct
settings directly or disable dotenv sources. PostgreSQL integration tests use a
separate, guarded `TEST_DATABASE_URL`; it never falls back to `DATABASE_URL`.

## Boundaries

One deployment environment can supply both frontend and backend configuration,
but their visibility differs: backend `DATABASE_URL` is secret, while Vite
`VITE_*` values are public browser values. Do not put backend secrets in
`VITE_*` variables. Frontend configuration and CORS behavior are outside this
backend runtime-settings change.
