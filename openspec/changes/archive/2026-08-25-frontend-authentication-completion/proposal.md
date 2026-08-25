# Proposal: Frontend Authentication Completion

## Intent

Complete the frontend Authentication contract so users receive a validated application session and exactly one semantic handoff to Access. Complete account administration without extending product or API authority.

## Scope

### In Scope
- Normalize provider lifecycle events; reject stale session/validation results; preserve `unavailable`; clear session-bound state; and hand off only validated `load_access` sessions to Access exactly once.
- Make sign-in addressable with validated, permitted return intent; implement latest-submission, generic-denial, draft-clearing, and focus/announcement behavior.
- Complete restricted mandatory replacement, including validation, dirty-leave confirmation, recovery, provider invalidation, secret clearing, `204` termination, and fresh sign-in.
- Complete idempotent logout, Accounts/detail/reset/disable/History lifecycle, confirmations, version/state-conflict recovery, navigation, draft safety, and accessibility semantics.

### Out of Scope
- Frontend provisioning, account re-enablement, and Access account-review flows.
- New backend APIs, changes to backend/PRD authority, or frontend authorization policy.

## Capabilities

### New Capabilities
- `frontend-authentication`: Observable Authentication session, entry, replacement, logout, account-administration, async, security, and accessibility requirements.

### Modified Capabilities
- `frontend-access-control`: Consume Authentication semantic state for bootstrap and permitted destination resolution without absorbing Authentication ownership.
- `authentication-password-replacement`: Align the existing replacement contract with its complete frontend restricted-experience and recovery consequences.

## Approach

Use `AuthProvider` and the provider adapter as the single session authority. Publish semantic state before navigation; let Access resolve authorization and destination. Deliver capability-owned slices—session/handoff, entry/logout, replacement, administration, verification—rather than page-by-page patches.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `frontend/src/features/auth/` | Modified | Provider, context, routes, pages, API normalization, and tests. |
| `frontend/src/app/routes/index.tsx` | Modified | Access-aware protected and sign-in composition. |
| `frontend/src/app/layout/AppLayout.tsx` | Modified | Published state navigation/logout consequences. |
| `openspec/specs/` | Modified/New | Authentication and Access contract deltas. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Event/session identity ambiguity | Med | Centralize normalization and test stale/duplicate paths. |
| Access contract drift | Med | Exchange only semantic state; retain Access destination authority. |
| Stale mutation/draft disclosure | Med | Invalidate before refresh; clear secrets and require renewed confirmation. |

## Rollback Plan

Revert the affected frontend slices together, restoring the prior provider/context and routes. No persistence or API contract is introduced; retain backend behavior and remove newly added client-only tests with the reverted code.

## Dependencies

- `frontend/docs/features/authentication.md` and its normative Authentication/Access PRDs remain authoritative.
- Focused frontend tests plus `pnpm lint` and `pnpm build` from `frontend/`.
- Forecast: likely auto-chained delivery because the work exceeds the 400-line review budget.

## Success Criteria

- [ ] Focused tests prove session races, handoff, intent, replacement, logout, administration, draft, and accessibility outcomes.
- [ ] Lint and build pass, and no excluded flow or artificial backend contract is introduced.
