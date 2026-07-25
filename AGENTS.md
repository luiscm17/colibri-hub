# Yarn EPR Agent Guide

## Python workspace

- Python 3.13 is pinned by `.python-version`. Run `uv` from the repository root; `backend/` is a workspace member and `uv sync --locked` provisions the lockfile exactly.
- Root owns `openpyxl`, `pandas`, and SQLAlchemy; `backend/` owns FastAPI, Psycopg, and SQLAlchemy. Add backend-only dependencies to `backend/pyproject.toml` and keep `uv.lock` synchronized with both manifests.
- Backend uses setuptools `src` layout and discovers only `warehouse*`, `infra*`, and `bootstrap*`; run through the root uv environment so editable workspace imports resolve.
- Run all backend unit tests: `uv run --locked python -m unittest discover -s backend/tests -v`.
- Run one test module: `uv run --locked python -m unittest backend.tests.test_warehouse.bales.domain.test_raw_material_batch -v`.
- Focus a class or method by appending its dotted name to the module command.
- SQLite adapter tests belong to the unit suite; do not treat them as proof of PostgreSQL constraint diagnostics, migration shape, timezone, or `Decimal` round-trips.
- Tests use stdlib `unittest`; no pytest, Python linter, formatter, type checker, or coverage tool is configured.
- Root `main.py` is print-only scaffolding. `backend/main.py` is the ASGI entrypoint (`app`), declared as `backend.main:app` in root `[tool.fastapi]`, and requires `DATABASE_URL` at import time; application creation builds the engine but does not connect until a request uses a session.

## Database and integration tests

- Schema changes are imperative Supabase migrations under `supabase/migrations/`; there is no Alembic setup. Generate migration filenames with the Supabase CLI.
- Local database provisioning requires the repository Supabase CLI wrapper plus a Docker-compatible runtime. From the repository root run `pnpm supabase start`, then `pnpm supabase db reset --local --no-seed`; `--no-seed` is required because `supabase/config.toml` names `supabase/seed.sql`, which does not exist.
- PostgreSQL integration tests deliberately accept only `postgresql+psycopg` URLs on loopback port `54322`, database `postgres`. Run them after migration with `TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres uv run --locked python -m unittest discover -s backend/integration_tests -v`.
- Inspect local migration state with `pnpm supabase migration list --local`.

## Frontend workspace

- Run frontend commands from `frontend/`: `pnpm install --frozen-lockfile`, `pnpm dev`, `pnpm build`, `pnpm lint`, and `pnpm preview`.
- `pnpm build` is the typecheck plus production build (`tsc -b && vite build`); `pnpm lint` runs ESLint. No frontend test script or test framework is configured.
- Preserve `frontend/pnpm-workspace.yaml` supply-chain policy: 24-hour minimum release age and no-downgrade trust, including its explicit exclusions.
- `src/main.tsx` installs Mantine, notifications, and `AuthProvider`; `src/app/` owns shell/routing and `src/features/` owns feature code. Use the configured `@/*` alias for `src/*`.

## Backend boundaries

- `warehouse.bales.application` is the capability boundary for raw-material batch commands, result, use case, and application errors. `warehouse.bales.ports` exposes repository, identity, transaction, and transaction-conflict contracts; keep SQLAlchemy details in `warehouse.bales.adapters`.
- `bootstrap.http_application.create_app` composes `infra.persistence` and Warehouse adapters into `POST /api/v1/warehouse/bales` and registers the HTTP exception handlers; pass a session factory in tests to avoid requiring `DATABASE_URL` or database access.
- Raw-material batch registration inserts the batch before its bales in one transaction and returns `raw_material_batch_id`. Only the two named uniqueness constraints are translated to application conflicts; unknown integrity failures propagate.
- Shipment numbers are globally unique through `uq_raw_material_batches_shipment_number`. Bale numbers are unique only within a batch through `uq_raw_material_bales_raw_material_batch_bale_number`; the same canonical bale number is valid in different batches.
- Keep ORM records and the Supabase migration aligned: `raw_material_batches`, `raw_material_bales`, and `raw_material_batch_id` use named PK/FK/unique/index constraints, including `ck_raw_material_bales_status` for `in_warehouse` and `delivered`. The migration enables RLS and revokes all privileges from `anon`, `authenticated`, and `service_role`; it defines no policies or runtime authorization flow.

## Business truth

- Resolve business meaning from `docs/prd/` first, then `docs/architecture/`, `docs/domain/ubiquitous-language.md`, and finally `docs/db/` for design detail.
- Keep Warehouse, Yarn Spinning, Lot Processing, Access Control, and Shared Reference Data distinct. Target code aliases are `warehouse`, `yarn-production`, `batch-processing`, `access`, and `catalogs`; `shared` is not a business context.
- Frontend validation is advisory; backend policy and domain decisions are authoritative.

## Repository rules

- Follow `docs/dev-guide/naming-conventions.md`; notable rules are Python `snake_case`, React component `PascalCase.tsx`, plural `snake_case` DB tables, and singular `snake_case` DB columns.
- Follow `docs/dev-guide/git-workflow.md`; branches use `front/`, `back/`, `devops/`, or `docs/`, commits use Conventional Commits, and PRs target `main` for squash merge.
- Treat `openspec/changes/<change-name>/` as planning artifacts, not proof of implementation or authorization.
- No tracked CI, pre-commit config, task runner, Python quality config, code generator, or repo-local OpenCode config exists. `.agents/` directories contain agent skills, not project task commands.
