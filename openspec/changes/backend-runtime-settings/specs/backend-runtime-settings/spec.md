# Backend Runtime Settings Specification

## Purpose

Define typed, infrastructure-owned backend runtime configuration without changing domain behavior or HTTP APIs.

## Requirements

### Requirement: Composition Settings Boundary

`infra.configuration.ApplicationSettings` MUST be the sole environment/dotenv source, initially exposing only typed database settings. Bootstrap MUST load it once while composing the application and pass typed settings to persistence. Explicit settings, engine, or session-factory injection MUST bypass source loading; existing `create_app` test seams MUST remain usable.

#### Scenario: Default composition
- GIVEN no explicit dependency is injected
- WHEN bootstrap composes the application
- THEN settings are loaded once and injected into persistence

#### Scenario: Explicit seam
- GIVEN an explicit settings, engine, or session factory
- WHEN `create_app` is called
- THEN no environment or dotenv source is read

### Requirement: Local Runtime Sources

The local dotenv source MUST be `backend/.env`, resolved independently of the invoking CWD; commands from another CWD are supported with identical resolution. Root `uv run fastapi dev` MUST work without `--env-file`. OS environment values MUST override dotenv values.

#### Scenario: Root command and precedence
- GIVEN `backend/.env` defines `DATABASE_URL` and the OS defines another value
- WHEN the root development command starts
- THEN the OS value is used

#### Scenario: Alternate CWD
- GIVEN the same repository and `backend/.env`
- WHEN startup is invoked from another CWD
- THEN the canonical dotenv is resolved, not a CWD-relative file

### Requirement: Database Setting Validity and Startup Safety

`DATABASE_URL` MUST retain its external name and be represented as `SecretStr`. Missing, empty, whitespace-only, or malformed values MUST fail validation before health/readiness. Settings and engine construction MUST NOT open a database connection.

#### Scenario: Invalid configuration
- GIVEN a missing, blank, whitespace-only, or malformed `DATABASE_URL`
- WHEN default startup composes the service
- THEN startup fails before the service is healthy

#### Scenario: Deferred connection
- GIVEN a valid database setting
- WHEN settings and the SQLAlchemy engine are constructed
- THEN no database connection is made

### Requirement: Secret Adapter Boundary

The database URL MUST be redacted from settings representations, errors, logs, and documentation. It MUST be explicitly unwrapped only at the SQLAlchemy engine-creation boundary.

#### Scenario: Redaction
- GIVEN a URL containing credentials
- WHEN settings are represented or a validation failure is reported
- THEN the credential value is absent

### Requirement: Test Configuration Isolation

Unit tests MUST construct settings directly or disable runtime sources so developer dotenv files cannot affect results. `TEST_DATABASE_URL` guards MUST remain separate, MUST NOT fall back to `DATABASE_URL`, and MUST retain their existing integration-test safety restrictions.

#### Scenario: Isolated unit test
- GIVEN a developer `backend/.env` exists
- WHEN a unit test constructs isolated settings
- THEN the dotenv value is not read

#### Scenario: Missing test URL
- GIVEN `TEST_DATABASE_URL` is absent and `DATABASE_URL` is present
- WHEN integration test support creates its engine
- THEN it fails for the missing test URL

### Requirement: Ownership, Environments, and Boundaries

`pydantic-settings` MUST be a direct backend dependency; the maintainer MUST synchronize `backend/pyproject.toml` and `uv.lock` atomically with its first use, and agents MUST NOT install it. Local onboarding MUST copy tracked `backend/.env.example` to ignored `backend/.env`; no secrets MAY be committed. Staging/production MUST use platform environment/secrets and MUST NOT require dotenv. Domain and application layers MUST NOT depend on Pydantic, dotenv, `os.environ`, or deployment concerns.

#### Scenario: Deployment configuration
- GIVEN staging or production platform secrets provide `DATABASE_URL`
- WHEN the service starts without a dotenv file
- THEN configuration succeeds without exposing the secret

#### Scenario: Non-goals
- GIVEN a request for frontend env, CORS, auth, email, observability, request-scoped settings, or production dotenv
- WHEN this capability is implemented
- THEN it is not added by this change
