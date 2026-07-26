# Design: Backend Runtime Settings

> Planning artifact only; implementation and deployment require separate approval.

## Technical Approach

Resolve one infrastructure-owned settings graph in `create_app`, then pass only `DatabaseSettings` to persistence. Source-checkout entrypoint `backend/main.py` explicitly hands bootstrap its adjacent `backend/.env` path. No other layer discovers paths.

## Architecture Decisions / Decision Log

| Option | Tradeoff | Decision |
|---|---|---|
| Nested `DatabaseSettings(BaseModel)` in `ApplicationSettings(BaseSettings)` | One environment reader | Chosen over nested `BaseSettings`; immutable typed infrastructure models preserve boundaries. |
| Explicit entrypoint dotenv handoff | One extra composition argument; no hidden package-depth convention | `backend/main.py` derives `Path(__file__).resolve().with_name(".env")` and passes it as `settings_env_file`. `infra.configuration` accepts only that explicit path and never probes CWD, parents, repository roots, or `site-packages`. |
| No configured default dotenv | Installed callers must opt in to a file | `ApplicationSettings` has no `env_file` default; `_env_file=None` means OS-only. An absent explicit file also falls back only to OS environment. This is the formal installed/container/staging/production contract. |
| Nested `DATABASE_URL` → `database.url` | Internal/external names differ | Use one `_` split; avoid a custom source and preserve the external name. |
| Minimal URL-shape validation | No connectivity/driver allowlist | Strip; require nonblank `scheme://remainder` without whitespace. SQLAlchemy owns dialect support. |
| `ApplicationSettings` injection | One extra wrapper | `create_app(settings, settings_env_file, engine, session_factory)` remains the composition seam; `EngineFactory` accepts `DatabaseSettings`. |

## Contracts and Flow

```text
backend.main → sibling backend/.env path ─┐
installed/other caller → no path ─────────┼→ create_app
                                         └→ ApplicationSettings(_env_file=path|None) once
                                              → settings.database → create_db_engine
                                              → unwrap SecretStr → create_engine
                                              → session factory → FastAPI app
```

`DatabaseSettings` exposes frozen `url: SecretStr`, forbids extras, and hides error input. `ApplicationSettings` is frozen, case-insensitive, ignores unrelated variables, configures one nested split and UTF-8—but no `env_file`. OS environment outranks an explicit dotenv. `create_db_engine` alone unwraps the secret; outputs never format it. Invalid input fails before readiness.

When `session_factory` exists, neither engine nor settings is resolved; when `engine` exists, settings is not resolved; explicit settings bypasses all sources and ignores `settings_env_file`. Engine construction still performs no connection. No request cache/dependency supplies settings.

**Installed-artifact contract:** `backend/main.py` is outside setuptools-discovered `src` packages. Installed composition omits `settings_env_file`; OS environment is then the only source. Missing `backend/.env` is valid: proposal/spec remain satisfied because dotenv is optional local onboarding and platform `DATABASE_URL` is authoritative elsewhere.

## File Changes

| Slice | Files | Action |
|---|---|---|
| PR1 | `backend/src/infra/configuration/{__init__,application_settings,database_settings}.py`; configuration tests | Create models, exports, source/validation tests. |
| PR1 | `backend/main.py`, `backend/src/bootstrap/http_application.py`, bootstrap tests | Hand off the direct sibling path; compose once; prove path/source and injection bypasses. |
| PR1 | `backend/src/infra/persistence/database_engine.py` and persistence tests | Inject nested config, unwrap once, prove no-connect. |
| PR1 | `backend/src/infra/persistence/database_settings.py` | Delete superseded reader. |
| PR1 | `backend/integration_tests/database_test_support.py`; guard tests | Use typed construction; retain direct `TEST_DATABASE_URL`, target guards, and no fallback. |
| PR1 | `backend/pyproject.toml`, `uv.lock` | Maintainer adds direct `pydantic-settings` and synchronizes lock atomically; agents never install. |
| PR2 | `backend/.env.example`, `.gitignore`, `backend/README.md`, `AGENTS.md` | Preserve validated placeholder/ignore policy; document copy and root command. |
| PR2 | `docs/dev-guide/backend-runtime-configuration.md`, `docs/plan/deployment-configuration.md` | Dev precedence/testing and platform-env deployment/failure/rollback guidance; no provider policy. |

## Testing and Verification

| Layer | Matrix |
|---|---|
| Unit | Isolate `os.environ`; use explicit temporary paths or `_env_file=None`. Cover validation/redaction/precedence, root/non-root CWD, absent explicit dotenv, and installed-like `__file__` with unrelated CWD/ancestor `.env` files proving no probe. |
| Composition | Assert `backend.main` supplies its direct sibling path; settings constructs exactly once. Prove explicit settings/engine/session bypass all sources, engine receives nested config, unwrapping occurs once, and import does not connect. |
| Integration safety | Keep `TEST_DATABASE_URL` independent; prove `DATABASE_URL` alone fails and all existing target guards remain. No database integration change is required. |

Verification: lock/import checks, full backend unit suite, source-entrypoint import with OS `DATABASE_URL`, and ignore-policy checks. No server is launched; maintainer performs dependency installation separately.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary changes.

## Rollout, Work Units, and Rollback

Stack `main <- PR1 <- PR2`. PR1 is runtime-complete at **340–395 changed lines**; PR2 is documentation/operations-complete on PR1 at **130–210**. Both stay below 400 lines and are independently reviewable/rollbackable on their stated base; PR2 is intentionally not standalone against `main`. If PR1 approaches 399, reduce test duplication—not behavior—or move non-runtime prose to PR2. Roll back PR2 first; then restore the dataclass reader/composition and manifest/lock pair. No data migration exists.

## Non-goals and Open Questions

Frontend/CORS/auth/email/observability, request-scoped settings, production dotenv, provider selection, and integration URL redesign are excluded. Open questions: none.
