# PR4 Evidence: Addressable Administration Families

## Deterministic Evidence

`pnpm vitest run src/features/access-control/administration --reporter=verbose --pool=forks --maxWorkers=1 --no-file-parallelism` passed with 1 file and 5 tests. The suite covers latest-only collection publication, page-local no-match feedback, missing User fallback, exact History filter serialization, silent normalized abort cleanup, and visible non-abort failure feedback.

`pnpm build && pnpm lint` passed. Vite emitted only its existing >500 kB chunk warning.

## Maintainer-Confirmed Live Result

- Users, Roles, Presets, Scopes, and History navigation works with the current backend contracts.
- Rapid navigation no longer emits `ApiError: The request was cancelled`; the browser console contains only the informational React DevTools message.
- The maintainer accepted the prior manual checklist for the current minimal/placeholder scope.

## Explicit Scope Boundary

- Scopes use collection-derived selected context; no `/scopes/{id}` endpoint was called or invented.
- History remains a filtered paginated collection only, using `subject_type`, `change_kind`, `date_from`, and `date_to`; no detail endpoint was called or invented.
- Unsupported administration detail and operation depth is a future owner/backend extension, not a PR4 blocker. This evidence does not claim those absent surfaces were implemented.

## Rollback

Revert the administration component and tests, its lazy route export/import, and the administration route. PR1–PR3 authorization, navigation, and protected-operation behavior remain intact.
