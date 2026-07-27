# Colibri Hub — Backend

REST API for the Colibri Hub platform. Built with FastAPI, SQLAlchemy (repository
pattern), and Supabase-managed PostgreSQL.

## Quick Start

```bash
# From the repository root
cp backend/.env.example backend/.env   # Set DATABASE_URL for your local database
uv sync --locked                       # Install all workspace dependencies
uv run fastapi dev                     # Start the development server
```

The server reads `DATABASE_URL` from `backend/.env` (local) or from the
operating-system environment (deployed). See `.env.example` for the expected
format.

## Tests

```bash
# Unit tests (no database required)
uv run --locked python -m unittest discover -s backend/tests -v

# Single module
uv run --locked python -m unittest backend.tests.test_warehouse.bales.domain.test_raw_material_batch -v

# PostgreSQL integration tests (requires local Supabase)
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres \
  uv run --locked python -m unittest discover -s backend/integration_tests -v
```

## Documentation

Detailed backend documentation lives in [`backend/docs/`](docs/README.md):

- [Architecture Overview](docs/architecture/overview.md)
- [API Conventions](docs/api/conventions.md)
- [Database & Migrations](docs/database/migrations.md)
- [Testing Strategy](docs/testing/strategy.md)
- [Deployment](docs/operations/deployment.md)

For product-level business rules, PRDs, and system architecture see
[docs/README.md](../docs/README.md).
