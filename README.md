# Colibri Hub

Enterprise resource planning system for yarn manufacturing — covering raw material reception, production tracking, inventory management, and delivery operations.

## Monorepo Structure

```text
backend/          Python backend (FastAPI, DDD/Hexagonal, Supabase)
frontend/         React frontend (Vite, Mantine, TypeScript)
supabase/         Database migrations and local dev setup
docs/             Global documentation (product, architecture, domain)
notebooks/        Analysis notebooks
data/             Reference datasets
```

## Documentation

| Area | Path | Scope |
| --- | --- | --- |
| Global docs | [`docs/`](./docs/README.md) | Product requirements, architecture, domain, dev guides |
| Backend docs | [`backend/docs/`](./backend/docs/README.md) | API, database, testing, operations |
| Frontend docs | [`frontend/docs/`](./frontend/docs/README.md) | Architecture, patterns, design system, accessibility |

## Quick Start

1. Clone the repository
2. Backend setup — see [`backend/docs/`](./backend/docs/README.md) for environment and dependencies
3. Frontend setup — run `pnpm install --frozen-lockfile` and `pnpm dev` from `frontend/`
4. Database — requires Supabase CLI and Docker: `pnpm supabase start` then `pnpm supabase db reset --local --no-seed`

## Key Documents

- [Product Overview](./docs/prd/product-overview.md) — business scope, actors, and transversal rules
- [System Architecture](./docs/architecture/system-overview.md) — components, contexts, and principal flows
- [Technology Baseline](./docs/architecture/technology-baseline.md) — verified stack and capabilities
- [Git Workflow](./docs/dev-guide/git-workflow.md) — branches, commits, PRs
- [Naming Conventions](./docs/dev-guide/naming-conventions.md) — code, files, database, API naming rules
