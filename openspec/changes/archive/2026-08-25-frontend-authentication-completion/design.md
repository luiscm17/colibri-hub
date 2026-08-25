# Design: Frontend Authentication Completion

## Technical Approach

Strengthen the existing provider chain without another store. `AuthProvider` owns session identity, `/auth/me` validation, credentials, and account state; `AccessProvider` consumes its semantic handoff once and resolves validated return intent. Existing backend contracts remain unchanged; provisioning, re-enable, and Access review remain excluded.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Race identity | Track a monotonic event epoch plus effective provider-session identity; every validation/submission captures both and may publish only while current. | Abort only; callback ordering assumptions. | Abort is advisory and duplicate provider events can still complete out of order. |
| Handoff | Mint one handoff identity only when the current `/auth/me` result is `load_access`; Access deduplicates it and owns destination/navigation resolution. | Navigate in provider callbacks; let Auth inspect permissions. | Preserves singular authorities and exactly-once semantic effects. |
| Return intent | Parse a relative in-app path, reject external/protocol-relative/auth-only destinations, then offer it to Access. | Blind redirect; Auth permission checks. | Prevents open redirects while retaining Access ownership. |
| Async/mutations | Use operation generations and one in-flight mutation; invalidate old snapshots before refresh. Conflicts preserve non-secret reason separately, clear passwords/confirmation, reload, then require renewed confirmation. | Automatic replay or version replacement. | Prevents stale publication and applying an old decision to new state. |
| Logout/replacement | Serialize one shared termination promise: attempt backend termination when applicable, always provider sign-out, clear Auth/Access/drafts, then publish logged-out once. Replacement `204` enters this local termination path without `/auth/me`. | Page-owned cleanup; await backend success. | Guarantees browser recovery and fresh sign-in despite failures. |

## Data Flow

```text
provider event ── epoch/session key ──> /auth/me ── current? ──> Auth semantic state
                                                                  │ one handoff
                                                                  v
return intent ── safe parser ──> Access bootstrap ── permission ──> one navigation
admin mutation ── expected_version ──> 204/conflict ── invalidate/reload ──> detail
```

Unavailable exposes retry without protected publication. Session/account changes abandon prior results and clear identity-sensitive drafts. Missing or forbidden detail navigates to Accounts, then the nearest Access-permitted destination.

## File Changes

| File | Action | Description |
|---|---|---|
| `frontend/src/features/auth/context/AuthContext.tsx` | Modify | Normalize event/session epochs, stable handoff, retry, serialized logout, and session clearing. |
| `frontend/src/features/auth/context/auth-context.ts` | Modify | Expose only semantic Auth operations/state. |
| `frontend/src/features/auth/provider/providerSession.ts` | Modify | Return normalized session identity with lifecycle events. |
| `frontend/src/features/auth/pages/LoginPage.tsx` | Modify | Latest-only submit, generic denial, focus/secret lifecycle, validated intent input. |
| `frontend/src/features/auth/pages/MandatoryPasswordChangePage.tsx` | Modify | Dirty-leave guard, safe retry, invalidation, and `204` termination. |
| `frontend/src/features/auth/pages/AuthenticationAccountsPage.tsx` | Modify | Confirmation/draft lifecycle, conflict invalidation, latest refresh, and safe navigation. |
| `frontend/src/features/auth/pages/AuthenticationHistoryPage.tsx` | Modify | Preserve opaque-cursor generation and accessible retry states. |
| `frontend/src/app/routes/index.tsx` | Modify | Addressable sign-in/replacement composition and Auth-state routing. |
| `frontend/src/features/access-control/access-controller.ts` | Modify | Consume each eligible handoff once and resolve permitted intent/navigation once. |
| `frontend/src/app/layout/AppLayout.tsx` | Modify | Use serialized logout consequence; no independent navigation. |
| Corresponding `*.test.ts(x)` files | Modify/Create | Focused race, route, form, mutation, and accessibility evidence. |

## Interfaces / Contracts

`AuthenticationAccessHandoff` remains unresolved, ended, password-change-required, unavailable, or eligible `{ accountId, handoffId }`. An Access-owned destination request carries only a validated relative path; no credential, token, role, or permission crosses.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Focused | epochs, deduplication, intent parser, cursor/mutation generations | Vitest deterministic tests |
| Interaction | denial focus, secret clearing, dirty leave, serialized logout, confirmations/conflicts | Testing Library + Vitest |
| Integration | Auth→Access handoff/bootstrap/navigation and route recovery | Memory router/provider tests |

Vitest is available despite stale OpenSpec metadata: `vitest@4.1.10`, configuration, and tests exist; the focused command passed 37/37. Verification runs `pnpm vitest run --reporter=verbose`, `pnpm lint`, and `pnpm build` from `frontend/`.

## Threat Matrix

| Boundary | Applicability | Safe/failure behavior | Planned RED tests |
|---|---|---|---|
| Browser route/return intent | Applicable | Accept normalized same-app paths only; reject absolute, protocol-relative, auth-loop, malformed, or unpermitted intent and use Access fallback once. | One case per accepted/rejected class plus duplicate navigation. |
| Documentation-like paths | N/A: no executable-file classification | No classification/execution boundary changes. | None |
| Git repository selection | N/A: no VCS automation | No repository selection. | None |
| Commit state | N/A: no VCS automation | No index/worktree operation. | None |
| Push state | N/A: no VCS automation | No push operation. | None |
| PR commands | N/A: no PR automation | No command composition. | None |

## Migration / Rollout

No migration, backend change, or feature flag is required. Deliver auto-chained, review-sized capability slices with focused tests and independent rollback before route integration.

## Open Questions

None; no blocking issue was found.
