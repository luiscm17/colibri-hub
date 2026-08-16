# PR5 Evidence: Governance, Forms, Previews, and Conflicts

## Deterministic Evidence

`pnpm vitest run src/features/access-control/administration --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` passed with 2 files and 8 tests. The PR5 RED initially failed because `governance.ts` did not exist. The completed focused suite proves duplicate fingerprint blocking, preview invalidation, and classification of version-conflict, last-system-administrator, and authority-change recovery paths, alongside the PR4 administration collection coverage.

`pnpm build && pnpm lint` passed. Vite emitted only its existing >500 kB chunk warning.

## Maintainer-Confirmed Live Result

- The maintainer, authenticated as a System Administrator, performed one real, reversible User role replacement using the current comma-separated UUID input.
- The change appeared in Access History and was then restored. No RBAC data remains changed by the checkpoint.
- Local fixtures now distinguish people from roles: Alex Rivera/System Administrator, Sofía Torres/Section Responsible, and Diego Morales/Supervisor. Authentication and Access display names were updated transactionally; `backend/http/CREDENTIALS.md` documents the fixtures.

## Current Contract Boundary and Limitations

- Profile creation remains Authentication-owned. The Access interface only governs existing profile lifecycle and role replacement.
- Existing deterministic/current-contract coverage closes PR5’s supported governance seam; unsupported future backend depth is not claimed as implemented.
- The comma-separated UUID role input is accepted for this slice but is UX debt tracked in GitHub issue #78, `feat(access): improve role assignment and membership visibility`. Do not expand it in PR5.
- A member-directory/MultiSelect requires an explicit future backend role-member listing contract. This PR does not infer members, issue N+1 calls, or misuse impact previews as a member directory.
- Scope registration, role/preset depth, and preview presentation remain bounded to currently exposed backend operations. The frontend never infers grants; backend `authorization.is_global` remains authoritative.

## Rollback

Revert the PR5 governance modules/forms/tests, AdministrationPage integration, `httpClient` PATCH support, and `@mantine/form` manifest/lockfile update. The fixture-documentation update in `backend/http/CREDENTIALS.md` may be reverted independently; never revert or mutate backend RBAC data for this frontend rollback.
