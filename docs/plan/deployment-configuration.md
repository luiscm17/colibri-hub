# Backend deployment configuration

Staging and production provide backend configuration through platform-injected
environment variables or secret stores. They do not require or deploy a dotenv
file.

## Required setting

| Setting | Requirement |
|---|---|
| `DATABASE_URL` | Required, nonblank URL supplied as a backend secret. |

At startup, `ApplicationSettings` validates the setting before the service is
healthy. The value remains redacted in settings representations and validation
messages. Engine construction does not connect; database activity begins when a
session is used.

## Deployment checklist

- Inject `DATABASE_URL` through the platform's environment or secret facility.
- Do not deploy `backend/.env` or any production dotenv file.
- Keep backend secrets separate from Vite `VITE_*` values, which are public in
  browser bundles.
- Keep `TEST_DATABASE_URL` limited to guarded local integration testing; it is
  not an application fallback.

## Failure and rollback

Missing, blank, or malformed `DATABASE_URL` intentionally prevents a healthy
startup. Correct the injected secret and restart according to the platform's
normal process. If the runtime-settings change itself must be rolled back,
restore the previous composition/reader together with its matching dependency
manifest and lockfile; no schema or data rollback is required.

Provider selection, production dotenv files, frontend implementation, CORS,
auth, email, and observability settings remain out of scope.
