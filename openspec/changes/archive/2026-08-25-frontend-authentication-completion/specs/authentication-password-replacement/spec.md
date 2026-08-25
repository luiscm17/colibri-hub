# Delta for Authentication Password Replacement

## MODIFIED Requirements

### Requirement: Session termination and reauthentication (F-3)
After mandatory replacement, the system MUST terminate the provider session and require new sign-in with the established password. The account MUST become Active only after provider success; Access Control MUST resolve only after subsequent authentication. The frontend MUST restrict to state inspection, replacement, and logout; validate differing confirmed passwords; consume bodyless `204`, clear secrets and local state, and enter logged-out. Dirty departure SHALL confirm discard; provider invalidation MUST expire without reauthentication or Access handoff.
(Previously: only post-success termination and reauthentication were specified.)

#### Scenario: Successful replacement terminates the current session
- WHEN mandatory replacement succeeds with the correct current and acceptable new password
- THEN the old password fails and the new password succeeds
- AND the session used for replacement is no longer usable
- AND the user must sign in again with the new password before Access Control resolves access

#### Scenario: Provider failure does not activate the account
- GIVEN a mandatory replacement request
- WHEN the provider does not confirm success
- THEN the account remains Awaiting Password Change
- AND no success audit or Access Control resolution is produced

#### Scenario: Dirty replacement departure
- GIVEN unsubmitted replacement passwords
- WHEN discard is confirmed
- THEN every password clears without retention
