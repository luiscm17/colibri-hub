# Frontend Authentication Specification

## Purpose
Define observable Authentication behavior; Access retains authorization and destination ownership.

## Requirements

### Requirement: Session Handoff
The frontend MUST publish one of `initializing`, `unauthenticated`, `password-change-required`, `authenticated`, or `unavailable`, and validate provider sessions through `/auth/me` before identity. Only current `load_access` MAY hand off once; ended, replacement-required, and unavailable states MUST withhold Access.

#### Scenario: Validation publication
- GIVEN current or superseded validation
- WHEN it completes
- THEN only the current result publishes one Access handoff

### Requirement: Entry and Logout
Sign-in MUST accept non-secret valid return intent; Access SHALL use it only when permitted. Denial MUST be generic, latest-only, clear password, and retain email only where safe. Logout MUST attempt termination, locally sign out, clear state, secrets, and drafts, and reach sign-in once.

#### Scenario: Entry or failed logout
- GIVEN permitted intent or failed termination
- WHEN entry or logout completes
- THEN Access resolves permission and local logout clearing still occurs

### Requirement: Account Administration and History
Accounts, detail, reset, disable, and History MUST expose only Authentication data. Actions MUST use latest `expected_version`, reason, confirmation, one pending mutation, and post-`204` refresh. Conflict MUST retain safe input, clear secrets, reload detail, and require renewed confirmation. History MUST use opaque cursors and reject stale results.

#### Scenario: Action recovery
- GIVEN reset, disable, conflict, or missing account
- WHEN the outcome completes
- THEN state refreshes or clears to the nearest destination

### Requirement: Async, Secret, and Accessible Outcomes
Only latest results MAY publish; abandoned results MUST be invisible and mutations MUST NOT replay. Secrets MUST clear on unsafe failure, departure, reload, session end, or success and MUST NOT enter URLs, storage, logs, telemetry, or presentation. Forms MUST provide associated text, safe announcements, focus, keyboard operation, and non-color meaning.

#### Scenario: Draft or session end
- GIVEN recoverable draft failure, session end, or account switch
- WHEN state updates
- THEN safe recovery follows choice; secrets and stale identity clear
