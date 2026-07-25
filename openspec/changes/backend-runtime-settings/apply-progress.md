# Apply Progress: Backend Runtime Settings — PR1

## Delivery

- Mode: force-chained, stacked-to-main (`main <- PR1 <- PR2`)
- Work unit: PR1 runtime settings, composition, persistence, and guards
- Authored runtime/test/manifest/lock diff: 215 additions + 68 deletions = **283 lines** (excluding root `pyproject.toml`, unrelated worktree changes, and SDD artifacts); within the 399-line cap.

## Completed Tasks

- [x] 1.1–1.5 Dependency verification and RED tests
- [x] 2.1–2.4 Green runtime implementation and dependency verification
- [x] 3.1–3.2 Verification and review-budget checkpoint

## RED / GREEN Evidence

| Stage | Command / result |
|---|---|
| RED | Focused modules before runtime code: 3 import errors for missing `infra.configuration` (expected). |
| GREEN | `uv run --locked --no-sync python -m unittest backend.tests.test_infra.test_configuration backend.tests.test_infra.persistence.test_database backend.tests.test_bootstrap.test_http_application backend.tests.test_integration_database_test_support -v` — 20 tests passed. |
| Regression | `uv run --locked --no-sync python -m unittest discover -s backend/tests -v` — 182 tests passed. |
| Runtime harness | `DATABASE_URL=... uv run --locked --no-sync python -c "import backend.main; assert backend.main.app is not None"` — exit 0; no server or database connection. |

## Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test | 20 passed; configuration sources/validation/redaction, composition/bypasses, engine unwrap, and test URL guards covered. |
| Runtime harness | Import-safe `backend.main` command exited 0 with an explicit OS URL; no persistent server started. |
| Rollback boundary | Revert PR1 runtime/test files and the maintainer-created `backend/pyproject.toml`/`uv.lock` pair; restore the former persistence reader/composition. |

## Notes

- `pydantic-settings` 2.14.2 was already declared, locked, and importable; no explicit install, sync, lock regeneration, staging, commit, push, or PR action occurred.
- PostgreSQL integration evidence is recorded below after running against the guarded local `TEST_DATABASE_URL`; unit guard tests also prove direct URL handling and target restrictions.
- PR2 tasks were pending when this PR1 record was written; their completion evidence appears below.

## PostgreSQL Verification

| Check | Command / result |
|---|---|
| Local Supabase availability | `pnpm supabase status` — repository wrapper confirmed local development setup running; PostgreSQL available at the guarded loopback target. No reset or schema mutation ran. |
| Guarded focused support | `uv run --locked python -m unittest backend.tests.test_integration_database_test_support -v` — 2 tests passed. |
| Full PostgreSQL integration | `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest discover -s backend/integration_tests -v` — 12 tests passed. |

- No PR1 defect was exposed and no production or test code changed during verification.
- The exact mandated `uv run --locked` command reported `Installed 6 packages in 60ms`; no explicit install or sync command was invoked, and Git manifests/lockfile were not changed.

## PR2 Documentation and Ignore Policy

| Evidence | Result |
|---|---|
| Implemented behavior check | CodeGraph confirmed `backend.main` passes only its sibling `.env`, OS values override explicit dotenv input, settings fail fast/redact values, engine construction defers connection, and `TEST_DATABASE_URL` is separately guarded. |
| Ignore policy | `git check-ignore -v` confirmed `backend/.env` and variants are ignored. `backend/.env.example` and nested examples remain unignored/trackable. No environment file content was read. |
| Documentation safety | The tracked example uses placeholders; changed documentation has no credential-shaped URL or Markdown link to validate. `--env-file` appears only in explicit “do not use” guidance. |
| Diff quality | `git diff --check` passed. PR2-only authored diff from `1196838`: 134 additions + 3 deletions = **137 lines**, excluding SDD artifacts and unrelated worktree changes. |

- PR2 tasks 4.1–4.3 are complete. All 14 change tasks are checked complete.
- No runtime, test, dependency, frontend, CORS, or schema change was made in PR2.
