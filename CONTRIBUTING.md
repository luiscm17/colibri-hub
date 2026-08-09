# Contributing to Colibri Hub

Thanks for contributing. This guide keeps changes consistent across the
repository. It is intentionally short — follow the rules below and read the
linked documents before opening a pull request.

## Where to start

- Business requirements are authoritative in the capability PRDs under
  `docs/prd/`, followed by `docs/architecture/` and
  `docs/domain/ubiquitous-language.md`. When prose is stale, executable code
  and configuration win.
- Keep the bounded contexts separate: Warehouse, Yarn Spinning, Lot
  Processing, Access Control, and Shared Reference Data. They have distinct
  identities, aggregates, and authorization rules.
- Frontend validation is advisory; backend domain and application policy is
  authoritative.

## How to contribute

### Branch naming

Branches follow `<layer>/<context>-<topic>`:

- `layer`: `back` (Python backend), `front` (React frontend), `devops`
  (infrastructure), `docs` (documentation).
- `context`: bounded-context alias — `wh` (Warehouse), `yarn` (Yarn
  Spinning), `lots` (Lot Processing), `access` (Access Control), `cat`
  (Shared Reference Data), or `auth` (Authentication).
- `topic`: 2–3 words describing the functional change — never the file or
  issue number.

Examples: `back/wh-bale-reception`, `front/access-admin-module`,
`docs/git-conventions`.

Cross-cutting work (frontend shell, CI/CD, global documentation) uses the
layer followed by a topic only: `devops/local-dev-setup`, `docs/rbac-design`.

A full-stack feature is paired branches with the same topic, one per layer
(`back/wh-bale-reception` + `front/wh-bale-reception`), never one oversized
branch.

### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

- `type`: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`.
- `scope`: the bounded-context alias (`wh`, `yarn`, `lots`, `access`, `cat`,
  `auth`) for any change that touches a context — regardless of layer. Use
  `ui`, `infra`, or `docs` only for cross-cutting work.
- `description`: imperative mood, no trailing period, describe the functional
  change — never the file.

### Pull requests

- Target `main`. `main` is protected by the `main shield` ruleset: every PR
  requires at least one approval before merge.
- Open one PR per concern. If a change is too large, split it into stacked
  PRs — do not open one oversized PR.
- Merge strategy is **squash merge**: one clean conventional commit per PR.
- Fill the pull request template (summary and changes). No issue linkage or
  label convention is required.

## Conventions

- Follow `docs/dev-guide/naming-conventions.md`: Python `snake_case`, React
  components `PascalCase.tsx`, plural `snake_case` database tables, singular
  `snake_case` database columns.

## Development

- Python is pinned to 3.13 (`.python-version`). Run `uv` from the repository
  root; backend commands need `--package backend`, provisioned with
  `uv sync --locked`.
- Backend unit tests: `uv run --locked --package backend python -m unittest
  discover -s backend/tests -v`. Tests use stdlib `unittest`.
- Frontend: run from `frontend/` — `pnpm install --frozen-lockfile`,
  `pnpm dev`, `pnpm build` (typecheck + production build), `pnpm lint`.
- Schema changes are ordered imperative SQL migrations under
  `supabase/migrations/`; there is no Alembic configuration.
- Plan substantial changes under `openspec/changes/` before implementation.
  Treat those artifacts as planning, not proof of implementation.
