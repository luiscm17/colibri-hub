# Proposal: Backend Runtime Settings

> Planning artifact only; it does not prove implementation or authorize deployment.

## Intent

Replace the hand-rolled persistence environment reader with one typed backend runtime boundary. Today `DATABASE_URL` loading is scattered at composition, lacks declared dependency ownership, and makes the root development command/dotenv policy implicit.

## Scope

### Goals
- Make configuration deterministic, typed, testable, and secret-safe without crossing Hexagonal boundaries.
- Make the supported local root command and environment precedence explicit.

### In Scope
- `infra.configuration.ApplicationSettings` with a nested database model, initially limited to `DATABASE_URL` as `SecretStr`.
- Load settings once during bootstrap composition; inject typed database settings into persistence and unwrap only at the SQLAlchemy boundary.
- Fail fast for missing, blank, or invalid required settings before the service is healthy; preserve engine creation without connection and existing injection seams.
- Establish local, test, staging, and production runtime policy plus direct `pydantic-settings` ownership.

### Out of Scope
- Auth, email, observability, frontend configuration, or CORS implementation.
- Any request-scoped FastAPI settings dependency, deployment-provider convention, or production dotenv file.

## Capabilities

### New Capabilities
- `backend-runtime-settings`: Typed, infrastructure-owned backend configuration and runtime-source policy.

### Modified Capabilities
None; no baseline OpenSpec capabilities exist.

## Approach

`infra.configuration.ApplicationSettings` is the sole `BaseSettings` source. Bootstrap resolves it once and passes its database subsection to persistence; domain/application never import Pydantic Settings, dotenv, `os.environ`, or deployment concerns. The root command is `uv run fastapi dev`: local onboarding copies `backend/.env.example` to ignored `backend/.env`. OS environment overrides dotenv. Staging/production use platform-injected variables/secrets only. `TEST_DATABASE_URL` remains separately guarded with no `DATABASE_URL` fallback.

## Impact

No HTTP API, database schema, or domain behavior changes. Startup becomes intentionally stricter: an invalid required database setting prevents health; explicit settings, engine, and session-factory injection remain non-breaking.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/src/infra/configuration/` | New | Settings boundary and nested database model |
| `backend/src/infra/persistence/` | Modified | Validated secret unwrapping at engine boundary |
| `backend/src/bootstrap/http_application.py` | Modified | One-time settings composition; retain injections |
| `backend/tests/`, `backend/integration_tests/` | Modified | Source isolation, precedence, fail-fast, redaction, guard tests |
| `backend/pyproject.toml`, `uv.lock` | Modified | Direct dependency, manually installed by maintainer |
| `backend/.env.example`, `.gitignore`, docs | Modified | Local onboarding and secret policy |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Developer dotenv contaminates tests | Med | Direct construction or disabled sources in unit tests |
| Secret exposure or `SecretStr` misuse | Low | Redaction tests; unwrap only for SQLAlchemy; never log values |
| Root-command confusion | Med | Document `backend/.env` and verify root invocation |

## Rollback Plan

Revert each stacked work unit independently: restore the existing persistence reader/composition first, then remove examples/docs. Do not alter database schema or deployed data.

## Dependencies

- `pydantic-settings` is a direct backend runtime dependency. The maintainer installs/synchronizes `backend/pyproject.toml` and `uv.lock` atomically in PR1; agents do not install packages.

## Success Criteria

- [ ] Root `uv run fastapi dev` reads ignored `backend/.env`; OS values win.
- [ ] Invalid/missing `DATABASE_URL` prevents healthy startup without leaking secrets.
- [ ] Tests cannot load developer dotenv; guarded integration settings remain isolated.
- [ ] `main <- PR1 <- PR2`: PR1 settings/composition/tests; PR2 example/ignore/docs, each <=399 lines.
