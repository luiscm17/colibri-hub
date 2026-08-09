# Colibri Hub Agent Guide

## Start here

- Treat the capability PRDs under `docs/prd/` as business authority, then `docs/architecture/` and `docs/domain/ubiquitous-language.md`.
- Keep Warehouse, Yarn Spinning, Lot Processing, Access Control, and Shared Reference Data separate. Their code aliases are `warehouse`, `yarn-production`, `batch-processing`, `access`, and `catalogs`; `shared` is not a business context.
- Frontend validation is advisory; backend domain and application policy is authoritative.

## Backend

- Python 3.13 is pinned by `.python-version`. Run `uv` from the repository root; `backend/` is a uv workspace member and uses a setuptools `src` layout.
- Root dependencies live in `pyproject.toml`; backend-only dependencies live in `backend/pyproject.toml`. Keep `uv.lock` synchronized with both manifests and provision with `uv sync --locked`.
- `backend/main.py` exposes the ASGI `app`; root `[tool.fastapi]` declares `backend.main:app`.
- For local startup, create untracked `backend/.env` from `backend/.env.example`, then run `uv run --package backend fastapi dev` from the root. The entrypoint explicitly loads that sibling file; OS environment values take precedence.
- `bootstrap.http_application.create_app` is the composition root. Inject a session factory in tests to avoid settings and database creation.
- Package by capability and keep dependencies inward: domain, application, ports, then adapters. Current top-level packages are `warehouse`, `access`, `auth`, `shared`, `infra`, and `bootstrap`; `shared` contains cross-context technical contracts, `infra` owns technical persistence/configuration, and `bootstrap` may wire all layers.

## Backend tests

- Full unit suite: `uv run --locked --package backend python -m unittest discover -s backend/tests -v`.
- Focused module: `uv run --locked --package backend python -m unittest backend.tests.domain.test_core_contracts -v`. Append a class or method dotted name for a narrower run.
- Tests use stdlib `unittest`; no pytest, Python linter, formatter, type checker, or coverage tool is configured.
- SQLite-backed unit tests do not prove PostgreSQL constraint diagnostics, migration shape, timezone, or `Decimal` behavior.
- Integration tests require explicit `TEST_DATABASE_URL`; the guard accepts only `postgresql+psycopg`, loopback, port `54322`, database `postgres`, and never falls back to `DATABASE_URL`.
- Full integration suite after local migrations: `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v`.

## Database and integration tests

- Schema changes are imperative SQL migrations under `supabase/migrations/`; there is no Alembic configuration. Generate migration timestamps with the Supabase CLI.
- Local provisioning requires the Supabase CLI and a Docker-compatible runtime: run `pnpm supabase start`, then `pnpm supabase db reset --local --no-seed` from the root.
- `--no-seed` is required because `supabase/config.toml` enables `./seed.sql`, but `supabase/seed.sql` is absent.
- Read all migrations in timestamp order; never infer the current schema from an earlier migration alone.
- Keep SQLAlchemy records and migrations aligned. Named constraints are part of conflict translation and integration-test diagnostics.
- Inspect local migration state with `pnpm supabase migration list --local`.

## Frontend workspace

- Run frontend commands from `frontend/`: `pnpm install --frozen-lockfile`, `pnpm dev`, `pnpm build`, `pnpm lint`, and `pnpm preview`.
- `pnpm build` is the typecheck plus production build (`tsc -b && vite build`); `pnpm lint` runs ESLint. No frontend test script or test framework is configured.
- Preserve `frontend/pnpm-workspace.yaml` supply-chain policy: 24-hour minimum release age and no-downgrade trust, including its explicit exclusions.
- `src/main.tsx` installs Mantine, notifications, and `AuthProvider`; `src/app/` owns shell/routing and `src/features/` owns feature code. Use the configured `@/*` alias for `src/*`; Vite proxies `/api` to `http://127.0.0.1:8000` in development.

## Repository rules

- Follow `docs/dev-guide/naming-conventions.md`; notable rules are Python `snake_case`, React component `PascalCase.tsx`, plural `snake_case` DB tables, and singular `snake_case` DB columns.
- Follow `docs/dev-guide/git-workflow.md`; branches use `<layer>/<context>-<topic>` with layers `front`, `back`, `devops`, or `docs` and context aliases `wh`, `yarn`, `lots`, `access`, `cat`, or `auth`. Commits use Conventional Commits; PRs target `main` for squash merge.
- Treat `openspec/changes/<change-name>/` as planning artifacts, not proof of implementation or authorization.
- No tracked CI, pre-commit configuration, task runner, Python quality configuration, code generator, or repo-local OpenCode configuration exists. `.agents/` directories contain agent skills, not project task commands.
