# Exploration: Backend Runtime Settings

> Planning-only investigation for `backend-runtime-settings`. No application,
> test, documentation, manifest, lockfile, environment file, or Git state was
> modified during exploration.

## Executive Summary

The backend currently has a narrow, hand-rolled `DatabaseSettings.from_env()`
reader in persistence and resolves it during `create_app()` composition. The
recommended change is a small infrastructure configuration boundary: an
`infra.configuration.ApplicationSettings` Pydantic Settings model with a
nested database model, loaded once by the composition root and passed explicitly
to engine construction. This keeps domain/application code framework-free,
preserves existing injection seams and `DATABASE_URL`, and leaves room for
future backend-only settings without inventing unused fields.

## Current State

### Runtime and composition

- `backend/main.py` imports `create_app` and exposes `app = create_app()`.
- Root `pyproject.toml` declares `backend.main:app`; the maintainer runs
  `uv run fastapi dev` from the repository root.
- `bootstrap.http_application.create_app()` currently accepts optional
  `DatabaseSettings`, `Engine`, and `session_factory` injections. If no session
  factory or engine is supplied, it calls `DatabaseSettings.from_env()` and
  `create_db_engine()`, then builds the session factory.
- `create_engine()` is called during application creation but does not connect
  until a session/request uses the engine. The import-time ASGI test proves the
  app can be imported without opening a database connection.
- HTTP composition is already testable without a database by injecting a session
  factory; the unit suite uses stdlib `unittest` and `TestClient`.

### Environment reads

The complete backend/integration environment-read surface is intentionally
small:

| Location | Current behavior |
|---|---|
| `backend/src/infra/persistence/database_settings.py` | Reads and trims `DATABASE_URL`; raises `RuntimeError` when missing, empty, or whitespace-only. |
| `backend/integration_tests/database_test_support.py` | Reads only `TEST_DATABASE_URL`, requires `postgresql+psycopg`, loopback host, port `54322`, and database `postgres`; never falls back to `DATABASE_URL`. |
| `backend/tests/test_bootstrap/test_http_application.py` | Patches `DATABASE_URL` only for the import-time ASGI test; most tests inject a session factory, engine, or settings. |
| `backend/tests/test_infra/persistence/test_database.py` | Supplies a mapping directly to `DatabaseSettings.from_env()` and tests validation without relying on process environment. |

There are no backend `os.getenv`, dotenv, or frontend configuration reads in
the current runtime path. FastAPI's standard extras already make
`python-dotenv` and `pydantic-settings` visible in `uv.lock` transitively, but
`backend/pyproject.toml` does not declare `pydantic-settings` directly. The
lockfile therefore is not proof of declared backend ownership and currently
drifts from the desired direct dependency boundary.

### Authoritative project constraints

- Architecture and stack documents establish FastAPI, Pydantic, SQLAlchemy 2,
  PostgreSQL, DDD, and Hexagonal Architecture.
- Backend technical design requires inward dependency direction and explicit
  ports/adapters. Configuration is an infrastructure/deployment concern, not a
  domain concept.
- `docs/dev-guide/naming-conventions.md` requires Python `snake_case`, classes
  in `PascalCase`, and environment variables in `UPPER_SNAKE_CASE`.
- The deployment plan mentions dev/staging/production and possible Railway/VPS
  infrastructure but does not yet select a provider contract. Production
  deployment itself is outside the current delivery schedule.
- Root `.gitignore` ignores `.env`; `backend/.env.example` currently contains
  only the local `DATABASE_URL`. There is no backend README guidance.
- Frontend architecture makes the frontend a backend API client. Frontend
  runtime configuration is deferred; any future public frontend values must be
  non-secret, while backend CORS origins (when CORS is introduced) belong to
  backend settings rather than frontend settings.

## Affected Areas

- `backend/src/infra/configuration/application_settings.py` — recommended new
  infrastructure-owned settings boundary and future extension point.
- `backend/src/infra/configuration/__init__.py` — optional narrow export if the
  project keeps package facades; do not create a broad `common` settings bucket.
- `backend/src/infra/persistence/database_settings.py` — replace or adapt the
  current dataclass/env reader as the nested database settings model while
  preserving the `DATABASE_URL` contract and normalized URL behavior.
- `backend/src/infra/persistence/database_engine.py` — consume the validated
  database value and unwrap it at the SQLAlchemy boundary if a secret-aware URL
  type is selected.
- `backend/src/bootstrap/http_application.py` — resolve application settings
  once at composition time and pass the database subsection to the engine;
  preserve explicit `settings`, `engine`, and `session_factory` injection.
- `backend/main.py` — remain a thin ASGI composition entry point; no settings
  logic should move into domain/application modules.
- `backend/tests/test_infra/persistence/test_database.py` — settings source,
  precedence, validation, redaction, and engine non-connection coverage.
- `backend/tests/test_bootstrap/test_http_application.py` — explicit settings
  injection, fail-fast import/composition behavior, and no accidental dotenv
  dependency in isolated tests.
- `backend/integration_tests/database_test_support.py` and its tests — retain a
  separate guarded `TEST_DATABASE_URL` path; do not route integration tests
  through production `DATABASE_URL` or a generic fallback.
- `backend/pyproject.toml` — declare `pydantic-settings` as a direct backend
  dependency in implementation; this exploration deliberately does not edit
  it.
- `uv.lock` — regenerate/synchronize manually with `uv` after the manifest
  change; the maintainer owns installation and lockfile updates.
- `.env.example`, `backend/.env.example`, `.gitignore`, and backend/ops docs —
  establish the canonical local example and production secret policy without
  committing secrets.

## Placement Alternatives

| Approach | Benefits | Costs / risks | Assessment |
|---|---|---|---|
| **`infra.configuration.ApplicationSettings` with nested models** | Gives one composition-level boundary; keeps Pydantic Settings in infrastructure; supports future backend-only sections; maps cleanly to Hexagonal dependency direction. | Adds one small configuration package and requires bootstrap to select the nested database model. | **Recommended; Medium-low effort.** |
| **Direct `DatabaseSettings(BaseSettings)` under persistence** | Smallest immediate diff; database adapter owns its own input. | Couples persistence to environment loading; future non-database settings become scattered; composition cannot represent one coherent runtime contract. | Acceptable transitional design, not the preferred growth boundary. |
| **Bootstrap-owned settings** | Composition root controls loading and can pass plain values downward. | Makes bootstrap own a cross-cutting infrastructure concern; risks importing Pydantic/loader details into the HTTP composition module and becomes awkward for non-HTTP entry points. | Reject for the lasting boundary; bootstrap should compose, not model all settings. |

## Dotenv Resolution Alternatives

| Strategy | Root command | Backend directory/tests | Containers and Railway/staging/production | Assessment |
|---|---|---|---|---|
| **Literal `.env` resolved from process CWD** | Works deterministically for the established root `uv run fastapi dev` command. | Resolves from the caller's CWD, so backend-directory execution looks for `backend/.env`; tests must inject settings or disable dotenv explicitly. | Safe when deployment injects OS variables and no file exists; no repository-layout assumptions. | **Recommended.** Document CWD as an invocation contract and keep tests explicit. |
| Explicit repository/backend path derived from package location | Can find one chosen file regardless of CWD. | Couples installed/runtime code to this repository layout; becomes brittle in wheels, containers, and alternate launch layouts. | Unnecessary and potentially wrong for mounted/deployed applications. | Reject. |
| `_env_file` supplied by bootstrap/entrypoint | Makes the file choice explicit per launcher. | Duplicates policy across launchers and makes direct imports/alternate ASGI launchers behave differently. | Works only when every launcher passes the same value; environment-only production still needs special handling. | Reject as the default boundary. |
| CLI-only loading | Avoids application dotenv behavior. | `uv run fastapi dev` imports the app directly and does not provide a stable application-level file contract; direct ASGI imports differ. | Good for strict production, incomplete for local development. | Use environment-only behavior in production, but not as the sole local strategy. |

The model should use `env_file=".env"`, UTF-8 encoding, and
`extra="ignore"`, with OS environment values overriding dotenv values. The
application should not require `.env` to exist. Tests that validate missing
settings must pass `_env_file=None` (or use an explicit settings constructor)
so a developer's untracked root `.env` cannot make a unit test pass accidentally.
The runtime composition path should fail fast when `DATABASE_URL` is absent or
blank; it should not silently select a test or local database.

## Initial Settings Boundary

The first model should contain only:

```text
ApplicationSettings
└── database
    └── database_url  <- DATABASE_URL
```

No auth, email, observability, frontend, or speculative CORS fields should be
added. When CORS is introduced, its allowed origins belong in this backend
settings boundary; frontend public configuration is a separate future change.

Precedence is:

1. Explicit constructor/test overrides.
2. Process environment (`DATABASE_URL`), which overrides dotenv.
3. Literal `.env` in the process CWD when present.
4. No default database URL: missing/blank input is a startup error.

The existing trimming and non-empty validation must remain. A URL containing a
password is sensitive. Prefer `SecretStr` at the settings boundary so model
representations and validation errors do not expose credentials, then call
`get_secret_value()` only inside `create_db_engine()` when passing the URL to
SQLAlchemy. This is a representation change, not a connection-behavior change;
tests must assert redaction and the exact unwrapped value passed to
`create_engine()`. If maintainers prioritize zero API churn for the existing
dataclass constructor, retain a plain string in the adapter-facing value object
and explicitly prevent its repr/logging instead; do not pass `SecretStr`
directly to SQLAlchemy.

## Testability and Integration Safety

- Keep `create_app()` injectable with explicit settings, engine, and session
  factory seams. Settings are application-scoped, not request-scoped and not a
  default FastAPI dependency.
- Preserve engine creation without connection and keep the import-time ASGI
  test as evidence of that property.
- Add settings tests for dotenv loading, OS-over-dotenv precedence, ignored
  extra keys, missing/blank URL fail-fast behavior, and secret redaction. Use a
  temporary CWD or explicit `_env_file` paths rather than the developer's
  actual `.env`.
- Keep unit tests independent of developer dotenv. Tests that inject a session
  factory should never need `DATABASE_URL`.
- Keep `TEST_DATABASE_URL` as a separate integration-only input with its current
  PostgreSQL driver, loopback host, port, and database guards. It must never
  fall back to `DATABASE_URL`, and production/staging URLs must be rejected by
  the existing safety checks.

## Secret, Example, and Production Policy

- Canonical local development should document a root `.env` because the
  supported command runs from the repository root; keep it untracked.
- Provide a root `.env.example` with a clearly local `DATABASE_URL` placeholder
  or local Supabase URL. Decide whether to move the current
  `backend/.env.example` to that canonical location or retain it as a clearly
  documented backend-directory alternative; avoid two contradictory examples.
- Never put real passwords, production URLs, tokens, or frontend secrets in
  `.env.example`, source, tests, `uv.lock`, or tracked docs.
- Production, staging, Railway, containers, and CI should inject secrets through
  the platform environment/secret manager; they should not depend on a checked
  in or image-baked `.env` file.
- `.gitignore` already ignores `.env`; implementation should verify the rule
  covers the canonical location and add only narrowly scoped example/policy
  documentation as needed.

## Dependency Ownership Audit

`backend/pyproject.toml` currently owns FastAPI, Psycopg, and SQLAlchemy but not
`pydantic-settings`. `uv.lock` contains `pydantic-settings` and
`python-dotenv` through FastAPI's standard extra, so the package may be
available today without being a declared direct backend dependency. That is
fragile: a future extra/version change can remove it. The implementation must
add `pydantic-settings` directly to the backend manifest and let the maintainer
run the locked `uv` synchronization manually. Exploration performed no
installation and changed neither manifest nor lockfile.

## Forecast and Chained Delivery

The feature is narrow enough to fit under 400 changed lines in one ordinary PR,
but the requested delivery strategy is force-chained and the boundary has a
clean code/operations split. Two stacked slices are recommended:

1. **PR1 — Typed settings boundary and composition**: configuration models,
   direct dependency declaration, persistence engine adaptation, bootstrap
   wiring, focused unit/ASGI tests, and integration guard preservation.
   Forecast: **220–340 changed lines**.
2. **PR2 — Runtime contract and operational documentation**: canonical
   `.env.example` decision, secret/dotenv/production guidance, focused docs and
   any remaining test fixtures. Forecast: **120–240 changed lines**.

Chain: `main <- PR1 <- PR2`, with each slice independently buildable and
rollbackable. Do not split tests away from the behavior they prove. If the
maintainer chooses to keep all operational documentation inside PR1 and the
measured diff remains below 400 lines, PR2 can be reduced to a documentation
follow-up, but force-chained delivery still favors the two review stories.

## Risks

- A root-CWD `.env` policy can surprise developers who launch from `backend/`;
  document the supported command and avoid repository-path magic.
- A developer `.env` can contaminate tests unless missing-settings tests disable
  dotenv and composition seams remain injectable.
- `SecretStr` changes the settings value API and requires explicit unwrapping at
  the SQLAlchemy boundary; passing it directly may break URL parsing.
- Adding a settings model without direct manifest ownership relies on a
  transitive lock entry and is not reproducible.
- Introducing speculative fields now would create false operational contracts;
  keep the initial model limited to `DATABASE_URL`.
- Existing deployment-provider details are not authoritative enough to encode a
  Railway-specific file/path convention.

## Architecture Recommendation

Adopt `infra.configuration.ApplicationSettings` as the single backend runtime
configuration boundary, with a nested database settings model. Load it once in
the composition path, use literal CWD `.env` resolution with environment
precedence, validate `DATABASE_URL` fail-fast, and pass the database subsection
to the existing engine factory. Keep all Pydantic/dotenv/environment concerns
outside domain and application packages. Preserve explicit test injection and
the guarded, independent `TEST_DATABASE_URL` integration path.

## Proposal Questions

Before proposal/design, confirm:

1. Should the canonical local example move from `backend/.env.example` to a
   root `.env.example` to match `uv run fastapi dev` from repository root, or
   should both locations be supported and documented?
2. Is `SecretStr` acceptable for the settings model, with unwrapping confined
   to `create_db_engine()`, or is preserving a plain string adapter-facing API
   preferred for this first change?
3. Should implementation include the direct `pydantic-settings` manifest and
   lockfile synchronization in PR1, with the maintainer running `uv`, or should
   dependency ownership be a separate chained work unit?

## Ready for Proposal

**Yes, with the three confirmations above.** The current architecture and
runtime seams are sufficient to write a narrow proposal; no frontend
implementation, CORS implementation, domain/application dependency, or
speculative settings field is required.

## Skill Resolution

Loaded the injected `sdd-explore`, Clean DDD/Hexagonal, cognitive document
design, and work-unit-commits skills, plus the shared SDD phase and OpenSpec
conventions. CodeGraph was used before broad filesystem inspection for runtime,
composition, test, and environment-read mapping.
