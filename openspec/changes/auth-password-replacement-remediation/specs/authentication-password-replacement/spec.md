# Authentication Password Replacement Specification

## Purpose

Define secure mandatory password replacement for F-1, F-2, and F-3 without changing administrative or frontend behavior.

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

The system MUST mutate a mandatory-replacement credential only through a provider capability that verifies the submitted current password. It MUST NOT use an administrative reset, enable, recovery, direct provider-database operation, or replacement session as a fallback. On success, it MUST preserve the existing HTTP 204 and frontend revalidation contract.

#### Scenario: Wrong current password is rejected without side effects

- GIVEN an authenticated user required to replace their password
- WHEN the submitted current password is incorrect
- THEN the request is rejected and the credential remains unchanged
- AND the account state, credential version, and success audit remain unchanged

#### Scenario: Capability gate blocks unproven provider behavior

- GIVEN a candidate provider configuration has not passed the controlled capability gate
- WHEN its current-password verification or session continuity cannot be demonstrated
- THEN the capability MUST NOT be selected for mandatory replacement
- AND no administrative fallback is permitted

#### Scenario: Successful replacement retains the client contract

- GIVEN a selected capability has passed the controlled capability gate
- WHEN mandatory replacement succeeds
- THEN the API returns the existing HTTP 204 response
- AND the existing frontend revalidation contract remains valid

### Requirement: Original session timebox continuity (F-3)

After a successful mandatory replacement, the system MUST preserve the original authenticated provider session, whose bounded maximum duration is configured by the identity provider and begins with the originating login. Replacement MAY continue only within that session's remaining duration. The frontend, backend, and application administrators MUST NOT independently calculate, configure, restart, extend, rotate, or substitute that duration or session.

#### Scenario: Successful replacement preserves the original session

- GIVEN a session whose identity-provider-configured bounded maximum duration began with the originating login
- WHEN mandatory replacement succeeds with the correct current and acceptable new password
- THEN the old password fails and the new password succeeds
- AND the original provider session remains usable only within its remaining duration, without a restarted, extended, rotated, or substituted session

#### Scenario: Original session expires on its original schedule

- GIVEN a successful replacement and the original provider session
- WHEN the identity-provider-configured bounded maximum duration that began with the originating login has elapsed
- THEN the original session is no longer usable
- AND replacement MUST NOT have independently calculated, configured, restarted, extended, rotated, or substituted the session or its duration

### Requirement: Secret-safe outcomes and evidence

The system MUST redact passwords, tokens, session identifiers, and raw provider error payloads from API responses, success audits, logs, and controlled-integration evidence. It MAY retain safe error classifications and boolean/assertion results.

#### Scenario: Rejected replacement is recorded safely

- GIVEN a weak-password or wrong-current-password attempt
- WHEN observability records the outcome
- THEN it contains only safe classification and outcome data
- AND it contains no submitted secret, token, session identifier, or raw provider payload

### Requirement: Controlled provider integration proof

The system MUST treat provider support as unproven until a controlled integration run against local and target-equivalent configuration demonstrates wrong-current rejection without side effects, old-password failure, new-password success, original-provider-session usability, and continuity only within the remaining duration of the provider-configured maximum that began with the originating login. The proof MUST use disposable identities and credential-free evidence.

#### Scenario: Complete capability gate passes

- GIVEN disposable integration identities and an eligible provider configuration
- WHEN the controlled run records every required assertion as passing
- THEN the configuration is eligible for implementation selection
- AND the recorded evidence contains no credentials or tokens

#### Scenario: Any gate assertion fails or is unavailable

- GIVEN a controlled run with a failed, skipped, or unavailable required assertion
- WHEN capability eligibility is evaluated
- THEN the configuration is ineligible for selection
- AND the remediation remains blocked rather than using a prohibited fallback

## Out of Scope

F-4, administrative reset or enable behavior, recovery, voluntary password changes, Access Control, roles, permissions, and frontend changes are excluded.
