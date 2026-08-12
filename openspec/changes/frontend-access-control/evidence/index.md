# Frontend Access Control Evidence Index

## Current deterministic status

| Slice | Status | Recorded evidence |
| --- | --- | --- |
| PR1 foundation and handoff | Passed | Authentication-to-Access state, exact grant adaptation, stale-result rejection, and session-clear behavior are covered by focused tests and recorded maintainer observations. |
| PR2 protected shell and routes | Passed | Direct/history denial, no protected disclosure, navigation omission, and permitted fallback are recorded in [PR2](pr2.md). |
| PR3 protected-operation recovery | Passed | The single Warehouse Bale `403` caused one Access refresh, preserved safe input, and made no automatic replay; see [PR3](pr3.md). |
| PR4 administration families | Passed within current backend contracts | Latest-only collection publication, abort silence, route fallback, and constrained family contracts are recorded in [PR4](pr4.md). |
| PR5 governance | Passed within current backend contracts | Deterministic recovery coverage and a reversible role-replacement checkpoint are recorded in [PR5](pr5.md). |
| PR6 hardening | Passed | The complete Vitest run passed: 8 files and 24 tests. Build and lint passed; Vite emitted its existing >500 kB chunk warning only. Maintainer live evidence passed after removing the invalid inline reduced-motion media key. |

## PR6 matrix and live evidence

The deterministic matrix covers Authentication handoff/session clearing, Access
bootstrap correlation and aborting, default-deny disclosure, route recovery,
latest-only administration loading, and current keyboard-accessible native and
Mantine controls. The focused provider test was corrected to mock the established
Access-denial recovery boundary; production behavior did not change.

Commands: `pnpm vitest run --reporter=verbose --pool=forks --maxWorkers=1
--no-file-parallelism` passed with 8 files and 24 tests; `pnpm build` passed;
`pnpm lint` passed. The final local diff is within the PR6 400-line boundary.

The retired `isResourceAllowed` authorization seam has no remaining frontend
consumer. The Access public entry point exports the provider, hook, controller,
snapshot factory, handoff/requirement/snapshot/state types, and catalog helpers;
no new authorization fixture or backend contract was invented.

Maintainer live evidence passed for Authentication handoff/session clearing,
latest-only navigation, responsive critical actions, keyboard/focus,
screen-reader announcements, and no mutation replay. The only observed frontend
gap was React's unsupported inline `@media (prefers-reduced-motion: reduce)`
style key on the Bale workflow card. The invalid key was removed and the existing
global reduced-motion media query now disables that card transition through the
scoped `.bale-workflow-card` class. Visual behavior is otherwise unchanged.

The React DevTools console message is informational. A rejected-credential
Supabase token `400` was non-blocking because a subsequent login succeeded; no
Authentication or backend behavior was changed. Authentication's opaque handoff
identity and ended-state publication remain an external capability contract, now
proven by maintainer evidence rather than owned by Access.

Do not infer RBAC from these checks. Backend Access APIs and Authentication remain
authoritative, and issue #78 is outside this change.
