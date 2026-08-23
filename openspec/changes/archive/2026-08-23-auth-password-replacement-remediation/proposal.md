# Proposal: Remediate Mandatory Password Replacement

## Intent

Remediate Authentication defects F-1/F-2/F-3 so mandatory replacement rejects weak and incorrect-current-password attempts, invalidates the provisional credential after provider-confirmed success, terminates the provider session used for replacement, and requires a new sign-in with the established password. The current administrative update cannot prove the submitted current password; no provider mechanism is yet approved or known to satisfy the contract.

## Scope

### In Scope
- F-1: map provider password-policy rejection to the typed `WeakPassword`/422 outcome.
- F-2: require provider-backed current-password verification before mutation; rejection causes no credential mutation, activation, version change, or success audit.
- F-3: prove successful replacement terminates the provider session and requires a new sign-in before Access Control resolution.
- Preserve intentionally red characterizations until their corresponding remediation is implemented and made green.

### Out of Scope
- F-4 and any Access Control, role, or permission change. The frontend change is limited to clearing authentication state and directing the user to sign in after successful replacement.
- Administrative reset/enable behavior, recovery, voluntary password changes, and direct provider-database password handling.
- Committing secrets or speculative provider configuration changes.

## Capabilities

### New Capabilities
- `authentication-password-replacement`: secure mandatory password replacement, typed provider-policy failures, and post-replacement reauthentication.

### Modified Capabilities
None. No relevant existing OpenSpec capability exists.

## Approach

Introduce a self-service replacement port distinct from administrative `update_password`; keep provider details in its adapter. Before selecting an implementation, pass a guarded capability gate against locally controlled Supabase Auth development: wrong-current rejection without side effects, old-password failure, new-password success after a fresh sign-in, termination of the replacement session, and no Access Control resolution before that fresh sign-in. Prefer a native authenticated provider operation; consider composed reauthentication only if it proves every gate. Never fall back to administrative update, recovery, or direct provider-database handling.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/src/auth/application/change_required_password.py` | Modified | Provider-first replacement policy and no-side-effects rejection. |
| `backend/src/auth/ports/identity_provider.py` | Modified | Self-service capability contract, separate from admin operations. |
| `backend/src/auth/adapters/identity_provider/admin_client.py` | Modified | Selected capability translation and safe typed error mapping. |
| `backend/tests/auth/`, `backend/integration_tests/` | Modified | Retained red characterizations, unit/API, and guarded provider evidence. |
| `supabase/config.toml` | Verify only | Local Supabase Auth development is the required controlled-integration environment; no provider configuration change is planned. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Provider does not terminate the replacement session | High | Gate requires session termination and fresh-sign-in proof. |
| Current-password capability is unavailable | Med | Stop selection; evaluate composed flow, never admin fallback. |
| Secrets or raw provider errors leak | Low | Record classifications/booleans only; preserve typed safe errors. |

## Rollback Plan

Revert the self-service port/adapter and its behavior-centered slice together; retain the red characterizations. Do not revert unrelated admin reset/session behavior or alter provider configuration without its own rollback.

## Dependencies

- Guarded disposable-identity access to locally controlled Supabase Auth development.

## Success Criteria

- [ ] F-1 returns `WeakPassword`/422 for the SDK-shaped policy error.
- [ ] F-2 rejects a wrong current password with no mutation, activation, version change, or success audit.
- [ ] F-3 proves the old password fails, the new password succeeds only after a fresh sign-in, the replacement session is terminated, and Access Control resolves only after that authentication.
- [ ] Focused unit/API tests, full backend units, and guarded integration evidence are recorded without credentials or tokens.
- [ ] Likely chained slices stay below 400 authored changed lines: F-1 mapping; capability contract/rejection; gated session proof/implementation; final regression.
