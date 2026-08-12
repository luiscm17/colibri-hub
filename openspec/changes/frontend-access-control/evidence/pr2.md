# PR2 Runtime Evidence: Protected Catalog, Shell, and Routes

## Deterministic Evidence

- `timeout 60s pnpm vitest run src/app src/features/access-control/catalog.test.ts --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` — exit 0; 3 files and 6 tests passed in 2.20s.
- `pnpm lint && pnpm build` — exit 0; existing Vite >500 kB chunk warning only.

## Maintainer-Controlled Runtime Evidence

An ordinary authenticated user was used. No role name was used as an authorization rule; the observations are based on the backend-resolved effective authorization snapshot and protected-route outcomes.

- `GET /api/v1/access/me` returned HTTP 200.
- Direct entry to `/warehouse/bales` rendered Access Denied and did not disclose protected page content.
- Warehouse was omitted from the derived navigation while Yarn Spinning remained visible.
- The denied-state Profile fallback navigated safely to `/profile`.
- Browser Back returned to `/warehouse/bales` and preserved the denied outcome.
- Maintainer supplied the missing permitted outcome: direct entry to `/spinning/ring-spinning` rendered the Hilatura page without Access Denied while Warehouse remained absent.

## Cleanup and Rollback

- The bounded Playwright browser session was closed. No credentials or tokens were persisted.
- No services were started, stopped, provisioned, or modified.
- Revert the PR2 catalog, route, and layout changes while retaining the PR1 Access public contract.
