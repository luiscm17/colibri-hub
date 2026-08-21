# Proposal: Remediate Mandatory Password Replacement

## Intent

Remediate Authentication defects F-1/F-2/F-3 so mandatory replacement rejects weak and incorrect-current-password attempts, invalidates the provisional credential after success, and continues only within the remaining duration of the original provider session. That session has a bounded maximum duration configured by the identity provider and begins with the originating login; frontend, backend, and application administrators do not independently calculate, configure, restart, extend, rotate, or substitute it. The current administrative update cannot prove the submitted current password; no provider mechanism is yet approved or known to satisfy the contract.

## Scope

### In Scope
- F-1: map provider password-policy rejection to the typed `WeakPassword`/422 outcome.
- F-2: require provider-backed current-password verification before mutation; rejection causes no credential mutation, activation, version change, or success audit.
- F-3: prove successful replacement retains the original provider session and its remaining duration from the originating login.
- Preserve intentionally red characterizations until their corresponding remediation is implemented and made green.

### Out of Scope
- F-4 and any frontend, Access Control, role, or permission change.
- Administrative reset/enable behavior, recovery, voluntary password changes, and direct provider-database password handling.
- Committing secrets or speculative provider configuration changes.

## Capabilities

### New Capabilities
- `authentication-password-replacement`: secure mandatory password replacement, typed provider-policy failures, and session-timebox continuity.

### Modified Capabilities
None. No relevant existing OpenSpec capability exists.

## Approach

Introduce a self-service replacement port distinct from administrative `update_password`; keep provider details in its adapter. Before selecting an implementation, pass a guarded capability gate in local and target-equivalent configuration: wrong-current rejection, old-password failure, new-password success, original-provider-session usability, and unchanged provider-configured duration from the originating login. Prefer a native authenticated provider operation; consider composed reauthentication only if it proves every gate. Never fall back to administrative update or a replacement session, and never independently calculate, configure, restart, extend, rotate, or substitute the provider session.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/src/auth/application/change_required_password.py` | Modified | Provider-first replacement policy and no-side-effects rejection. |
| `backend/src/auth/ports/identity_provider.py` | Modified | Self-service capability contract, separate from admin operations. |
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modified | Selected capability translation and safe typed error mapping. |
| `backend/tests/auth/`, `backend/integration_tests/` | Modified | Retained red characterizations, unit/API, and guarded provider evidence. |
| `supabase/config.toml` / deployment config | Conditional | Verify only; change only after gate evidence and review. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Provider revokes/rotates the session | High | Gate requires original-session and expiry proof. |
| Current-password capability is unavailable | Med | Stop selection; evaluate composed flow, never admin fallback. |
| Secrets or raw provider errors leak | Low | Record classifications/booleans only; preserve typed safe errors. |

## Rollback Plan

Revert the self-service port/adapter and its behavior-centered slice together; retain the red characterizations. Do not revert unrelated admin reset/session behavior or alter provider configuration without its own rollback.

## Dependencies

- Guarded disposable-identity access to local and target-equivalent provider configuration.

## Success Criteria

- [ ] F-1 returns `WeakPassword`/422 for the SDK-shaped policy error.
- [ ] F-2 rejects a wrong current password with no mutation, activation, version change, or success audit.
- [ ] F-3 proves the old password fails, new password succeeds, and replacement continues only within the original provider session's remaining duration from the originating login.
- [ ] Focused unit/API tests, full backend units, and guarded integration evidence are recorded without credentials or tokens.
- [ ] Likely chained slices stay below 400 authored changed lines: F-1 mapping; capability contract/rejection; gated session proof/implementation; final regression.
