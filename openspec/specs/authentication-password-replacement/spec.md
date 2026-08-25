# Authentication Password Replacement Specification

## Purpose

Define secure mandatory password replacement for F-1, F-2, and F-3 without changing administrative behavior. The frontend change is limited to clearing authentication state and directing the user to sign in after successful replacement.

## Requirements

### Requirement: Typed weak-password rejection (F-1)

The system MUST translate a provider password-policy rejection during mandatory replacement into the existing typed `WeakPassword` outcome and HTTP 422 response. It MUST NOT report a successful replacement or activate the account on this outcome.

#### Scenario: Provider rejects a weak replacement password

- GIVEN an authenticated user required to replace their password
- WHEN the provider returns its password-policy rejection for the submitted new password
- THEN the API returns `WeakPassword` with HTTP 422
- AND no success outcome or account activation is produced

#### Scenario: Non-policy provider failure

- GIVEN a mandatory replacement request with a provider failure not classified as a password-policy rejection
- WHEN the replacement is attempted
- THEN the API MUST NOT classify the failure as `WeakPassword`
- AND it MUST NOT return HTTP 204

### Requirement: Verified-current-password replacement (F-2)

The system MUST mutate a mandatory-replacement credential only through a provider capability that verifies the submitted current password. It MUST NOT use an administrative reset, enable, recovery, or direct provider-database operation as a fallback. On provider-confirmed success, it MUST activate the account, terminate the provider session used for replacement, and require a new sign-in before Access Control resolution.

#### Scenario: Wrong current password is rejected without side effects

- GIVEN an authenticated user required to replace their password
- WHEN the submitted current password is incorrect
- THEN the request is rejected and the credential remains unchanged
- AND the account state, credential version, and success audit remain unchanged

#### Scenario: Capability gate blocks unproven provider behavior

- GIVEN a candidate provider configuration has not passed the controlled capability gate
- WHEN its current-password verification, session termination, or fresh-sign-in behavior cannot be demonstrated
- THEN the capability MUST NOT be selected for mandatory replacement
- AND no administrative fallback is permitted

#### Scenario: Successful replacement requires a new sign-in

- GIVEN a selected capability has passed the controlled capability gate
- WHEN mandatory replacement succeeds
- THEN the API returns the existing HTTP 204 response without a replacement session or token
- AND the session used for replacement is terminated
- AND a new sign-in with the established password is required before Access Control resolves access

### Requirement: Session termination and reauthentication (F-3)

After a successful mandatory replacement, the system MUST terminate the provider session used for replacement and require a new sign-in with the established password. The account MUST become Active only after provider-confirmed success. Access Control MUST resolve the active profile and effective permissions only after that subsequent authentication.

#### Scenario: Successful replacement terminates the current session

- WHEN mandatory replacement succeeds with the correct current and acceptable new password
- THEN the old password fails and the new password succeeds
- AND the session used for replacement is no longer usable
- AND the user must sign in again with the new password before Access Control resolves access

#### Scenario: Provider failure does not activate the account

- GIVEN a mandatory replacement request
- WHEN the provider does not confirm successful replacement
- THEN the account remains Awaiting Password Change
- AND no success audit or Access Control resolution is produced

The frontend MUST restrict to state inspection, replacement, and logout; validate differing confirmed passwords; consume bodyless `204`, clear secrets and local state, and enter logged-out. Dirty departure SHALL confirm discard; provider invalidation MUST expire without reauthentication or Access handoff.

#### Scenario: Dirty replacement departure
- GIVEN unsubmitted replacement passwords
- WHEN discard is confirmed
- THEN every password clears without retention

### Requirement: Secret-safe outcomes and evidence

The system MUST redact passwords, tokens, session identifiers, and raw provider error payloads from API responses, success audits, logs, and controlled-integration evidence. It MAY retain safe error classifications and boolean/assertion results.

#### Scenario: Rejected replacement is recorded safely

- GIVEN a weak-password or wrong-current-password attempt
- WHEN observability records the outcome
- THEN it contains only safe classification and outcome data
- AND it contains no submitted secret, token, session identifier, or raw provider payload

### Requirement: Controlled provider integration proof

The system MUST treat provider support as unproven until a controlled integration run against locally controlled Supabase Auth development demonstrates wrong-current rejection without side effects, old-password failure, new-password success after a fresh sign-in, termination of the replacement session, and Access Control resolution only after subsequent authentication. The proof MUST use disposable identities and credential-free evidence. No remote or target-equivalent provider configuration is required.

#### Scenario: Complete capability gate passes

- GIVEN disposable integration identities in locally controlled Supabase Auth development
- WHEN the controlled run records every required assertion as passing
- THEN the locally proven capability is eligible for implementation selection
- AND the recorded evidence contains no credentials or tokens

#### Scenario: Any gate assertion fails or is unavailable

- GIVEN a controlled run with a failed, skipped, or unavailable required assertion
- WHEN capability eligibility is evaluated
- THEN the configuration is ineligible for selection
- AND the remediation remains blocked rather than using a prohibited fallback

## Out of Scope

F-4, administrative reset or enable behavior, recovery, voluntary password changes, Access Control, roles, permissions, and frontend changes beyond the required post-replacement sign-out transition are excluded.
