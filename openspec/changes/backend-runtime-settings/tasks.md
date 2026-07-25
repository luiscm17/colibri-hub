# Tasks: Backend Runtime Settings

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | PR1: 340–395; PR2: 130–210 |
| 400-line budget risk | Medium (PR1 near cap) |
| Chained PRs recommended | Yes |
| Suggested split | PR1 runtime/tests → PR2 onboarding/docs |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main; `main <- PR1 <- PR2` |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Runtime settings, composition, persistence, guards | PR1 | `uv run --locked --no-sync python -m unittest discover -s backend/tests -v` | Import-safe `backend.main` check; no server | Revert runtime/tests plus maintainer manifest/lock pair |
| 2 | Onboarding and deployment guidance | PR2 | Markdown/link and ignore checks | N/A: docs-only; no server | Revert PR2 docs/examples/ignore changes |

## Phase 1: PR1 Dependency and RED Tests

- [x] 1.1 From repository root, verify `pydantic-settings` is declared in `backend/pyproject.toml`, present in `uv.lock`, and importable with `uv run --locked --no-sync`; do not install. **STOP and ask the maintainer to install/synchronize atomically if absent.**
- [x] 1.2 RED: add isolated configuration tests for `SecretStr`, frozen/extra-forbidden models, nested mapping, blank/malformed validation, redaction, precedence, explicit/absent files, alternate CWD, and no path probing.
- [x] 1.3 RED: add bootstrap tests for sibling `backend/.env`, one settings load, explicit settings/engine/session-factory bypasses, and no-connect composition.
- [x] 1.4 RED: add persistence tests for one `SecretStr` unwrap at `create_db_engine`, safe representations/errors, nested delivery, and deferred SQLAlchemy connection.
- [x] 1.5 RED: adapt integration guard tests to prove `DATABASE_URL` never substitutes for missing `TEST_DATABASE_URL`; retain driver, loopback, port, and database restrictions.

## Phase 2: PR1 GREEN Runtime

- [x] 2.1 Create `backend/src/infra/configuration/{__init__,application_settings,database_settings}.py` with explicit `_env_file`, frozen models, validation, exports, and OS-only fallback.
- [x] 2.2 Update `backend/main.py` and `backend/src/bootstrap/http_application.py` to pass `Path(__file__).resolve().with_name('.env')`, load once, and preserve all injection seams; delete `backend/src/infra/persistence/database_settings.py`.
- [x] 2.3 Update `backend/src/infra/persistence/database_engine.py` and `backend/integration_tests/database_test_support.py`; unwrap only at SQLAlchemy and retain guarded test URL construction.
- [x] 2.4 Verify maintainer-created `backend/pyproject.toml`/`uv.lock` changes; no installation, staging, commits, or PR actions.

## Phase 3: PR1 Verification and Checkpoint

- [x] 3.1 Run focused configuration/bootstrap/persistence/guard tests, then `uv run --locked --no-sync python -m unittest discover -s backend/tests -v`; run import/CLI-safe root checks without launching a server.
- [x] 3.2 Check PR1 is ≤399 changed lines; if approaching the cap, move only non-runtime prose to PR2 and reduce duplicate tests without removing behavior. Checkpoint and rollback: restore the dataclass reader/composition and manifest/lock pair.

## Phase 4: PR2 Documentation and Verification

- [x] 4.1 Update `backend/.env.example`, `.gitignore` (including example exceptions), `backend/README.md`, and root `AGENTS.md` with `uv run fastapi dev`, copy workflow, precedence, test isolation, and frontend/public-secret separation.
- [x] 4.2 Create `docs/dev-guide/backend-runtime-configuration.md` and `docs/plan/deployment-configuration.md` covering platform-only staging/production, absent dotenv, failure/rollback, and excluded providers.
- [x] 4.3 Verify links, ignored secrets, no tracked real env files, and PR2 ≤399 lines; use repository-root checks only. Rollback PR2 first, then PR1.
