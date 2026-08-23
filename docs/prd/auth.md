---
document_type: prd
status: draft
scope: authentication
authority: normative
owner: product
---

# Authentication

## Business Scope

Authentication establishes the trustworthy identity of every person who enters
Colibri Hub. It governs login accounts, credentials, account state, and sessions
without deciding which business information or operations a person may use.

This capability covers:

- administrative provisioning of login accounts;
- organizational email as the unique login identifier;
- provisional passwords defined by the System Administrator;
- mandatory password replacement on first access and after an administrative reset;
- login and logout;
- sessions limited by a bounded maximum duration configured by the identity provider;
- administrative password reset;
- account enablement and disablement;
- termination of access when an account is disabled;
- traceability of security-sensitive authentication events; and
- coordination with Access Control during provisioning and entry.

Creating a user is presented to the System Administrator as one administrative
experience. Authentication establishes the login account. Access Control
establishes the access profile and assigns roles. Authentication does not own
roles, permissions, business scopes, or authorization decisions.

Colibri Hub uses an organizational email address supplied through the
administrative process, but does not create, operate, suspend, or delete the
corresponding mailbox. Mailbox administration and confirmation that an address
is organizationally controlled remain outside Colibri Hub.

## Problem Statement

Colibri Hub must ensure that every person is individually identifiable and that
the organization can withdraw access without losing historical attribution.
Shared credentials, self-registration, personal email addresses, indefinitely
active sessions, or destructive account deletion would weaken accountability
and the reliability of operational audits.

The System Administrator must be able to provision a person with an
organizational email and a provisional password, configure the person's access
in the same flow, and communicate the provisional credential outside Colibri
Hub. The person must replace it before using any protected capability.

Authentication therefore provides a boundary in which:

- one organizational email identifies one login account;
- only the System Administrator provisions and administers accounts;
- provisional credentials cannot become permanent credentials;
- successful authentication establishes identity but grants no business permission;
- sessions have a bounded maximum duration configured by the identity provider;
- disabling an account removes access and terminates its sessions;
- historical identities and actions remain attributable; and
- credentials never become part of business, access, or audit records.

## Stakeholders and Actors

| Actor | Responsibility | Interaction |
| --- | --- | --- |
| System Administrator | Governs login accounts and coordinates provisioning | Creates accounts, defines provisional passwords, initiates role assignment, resets passwords, enables or disables accounts, and reviews authentication history |
| System User | Enters Colibri Hub under an individual identity | Uses an organizational email and password, replaces provisional credentials, starts a session, and logs out |
| Access Control | Determines what an authenticated identity may do | Resolves the access profile and evaluates effective roles and permissions |
| Business Area Owner | Identifies who requires a business responsibility | Requests provisioning or access changes without administering credentials |

## Identity and Access Relationship

| Capability | Question | Owns |
| --- | --- | --- |
| Authentication | Who is attempting to enter Colibri Hub? | Login account, email identifier, credentials, account state, and sessions |
| Access Control | What may the authenticated person do? | Access profile, roles, actions, business scopes, effective permissions, and access state |

One person has one login identity associated with one Access Control profile. A
successful login establishes identity. Entry to a protected area additionally
requires an active access profile with the required effective permission.

The administrative experience may collect account information and role
assignments together, but each capability remains authoritative for its own
rules. Authentication must not copy roles or permissions into the login account,
and Access Control must not store or validate passwords.

## Business Rules

1. Every System User uses an individual account. Shared accounts and credentials are prohibited.
2. Only the System Administrator may provision, enable, disable, or administratively reset an account.
3. Users cannot self-register.
4. Each account uses one organizational email as its unique login identifier.
5. Two accounts cannot use the same email, regardless of letter case.
6. The System Administrator confirms that the email is organizationally controlled before provisioning.
7. Colibri Hub does not create, administer, or verify ownership of the associated mailbox.
8. Each login account is associated with exactly one Access Control profile for the same person.
9. Provisioning is one administrative flow that establishes the account, access profile, and initial roles.
10. Authentication owns the login account; Access Control owns the profile and roles.
11. Incomplete provisioning must never leave usable access.
12. The System Administrator defines a provisional password during provisioning.
13. Colibri Hub does not send provisional passwords by email; the System Administrator communicates them outside the system.
14. The user must replace a provisional password before any protected capability becomes available.
15. The replacement password must differ from the provisional password.
16. After replacement, the provisional password must no longer authenticate the user, the provider session used for replacement is terminated, and the user must sign in with the established password.
17. Users cannot recover or voluntarily change an established password through Colibri Hub.
18. An administrative password reset establishes a new provisional password.
19. A reset terminates active sessions and requires password replacement at the next login.
20. Authentication succeeds only when valid credentials identify an enabled account.
21. Login denial must not reveal whether the email, password, account state, or access profile caused the denial.
22. Successful authentication grants no business permission by itself.
23. Access Control denies protected entry when no associated active profile exists.
24. Roles and permissions are not stored or evaluated as Authentication account attributes.
25. A session has a bounded maximum duration configured by the identity provider, beginning with the originating login regardless of activity.
26. After the maximum duration, the user must authenticate again.
27. Logout terminates the current session and prevents its further use.
28. Disabling an account prevents new logins, terminates active sessions, and inactivates its access profile.
29. Disablement preserves identity, prior assignments, and attributable business and security history.
30. An established account is not physically deleted.
31. Re-enabling an account requires a new provisional password and mandatory replacement.
32. No account or access change, including account disablement, administrative password reset, access-profile inactivation, role replacement, or assignment removal, may leave Colibri Hub without an enabled System Administrator capable of authenticating and governing accounts and access.
33. Provisioning, enablement, disablement, reset, mandatory password replacement, successful and failed login, logout, expiration, and administrative session termination are traceable by identity, date, and time.
34. Passwords and other authentication secrets never appear in audit history, business records, Access Control records, or ordinary messages.
35. Administrative authentication events identify the acting System Administrator.
36. The frontend, backend, and application administrators must not calculate or independently configure, restart, extend, rotate, or substitute the identity-provider-configured maximum session duration.
37. Colibri Hub has an initial System Administrator account associated with an active System Administrator profile before ordinary provisioning begins.
38. The initial System Administrator is established through controlled initialization, not self-registration, and must replace the provisional password before protected access.

## Flows and Processes

### Establish the initial System Administrator

1. An authorized organizational representative identifies the initial System Administrator.
2. Controlled initialization establishes the account and its active System Administrator access profile.
3. A provisional password is established without appearing in audit history.
4. The System Administrator replaces it before accessing protected capabilities.
5. All subsequent account and access changes follow authenticated administrative flows.

### Provision a new user

1. The System Administrator opens the unified provisioning flow.
2. The System Administrator records the organizational email and identifying information.
3. The system verifies email uniqueness.
4. The System Administrator selects initial Access Control roles.
5. The System Administrator defines a provisional password.
6. Authentication establishes the account and Access Control establishes the profile and assignments.
7. The system confirms success only when the complete configuration is usable and consistent.
8. The system records the administrative event without recording the provisional password.
9. The System Administrator communicates the login identifier and provisional password outside Colibri Hub.

### Complete first access

1. The user enters the organizational email and provisional password.
2. The system validates the credentials and account state and establishes a session whose identity-provider-configured bounded maximum duration begins at that login.
3. While the account remains in Awaiting Password Change, the session is restricted to inspecting Authentication state, replacing the provisional password, and logging out.
4. The user replaces the provisional password with a different password, and the provisional password becomes unusable.
5. A successful mandatory replacement terminates the provider session used for replacement. The account becomes Active only after the provider confirms the replacement, and the user must sign in again with the established password.
6. Access Control resolves the active profile and effective permissions only after that subsequent authentication.
7. The user enters an authorized area or is denied when no suitable access exists.

### Log in

1. The user enters the organizational email and established password.
2. The system validates the credentials and account state.
3. A session with the identity-provider-configured bounded maximum duration is established.
4. Access Control resolves the active profile and effective permissions.
5. Authentication success does not bypass an Access Control denial.

### Reset a password administratively

1. The user requests assistance through an organizational channel outside Colibri Hub.
2. The system verifies that moving the account to Awaiting Password Change would not leave Colibri Hub without an operational System Administrator.
3. The System Administrator defines a new provisional password for the account.
4. Active sessions are terminated.
5. Mandatory password replacement is required at the next login.
6. The event is recorded without the provisional password.
7. The System Administrator communicates the provisional password outside Colibri Hub.

### Disable an account

1. The System Administrator selects the account.
2. The system checks the last-System-Administrator invariant.
3. The System Administrator confirms the action.
4. New logins are blocked, active sessions are terminated, and the access profile is inactivated.
5. Identity, assignments, and historical actions are preserved.
6. The administrative event is recorded.

### Re-enable an account

1. The System Administrator selects a disabled account.
2. The associated profile and roles are reviewed.
3. The System Administrator defines a new provisional password.
4. The account and access profile are enabled only with a valid complete configuration.
5. Protected access remains blocked until the user replaces the provisional password.
6. The administrative event is recorded.

### End a session

1. A session ends on logout, expiration, account disablement, administrative password reset, or successful mandatory password replacement.
2. The ended session cannot be used again.
3. Access to a protected area requires a new successful login.

### Handle unsuccessful entry

1. Invalid credentials, a disabled account, or an incomplete entry condition causes denial.
2. The user receives a generic message that does not disclose account conditions.
3. The security event is recorded without the supplied password.
4. When Authentication succeeds but Access Control denies entry, the system states that no active access is available without exposing permission configuration.

## States and Transitions

### Login account state

| State | Description | Allowed transitions |
| --- | --- | --- |
| Awaiting Password Change | Enabled with a provisional password; protected capabilities remain unavailable | Active, Disabled |
| Active | Uses an established password and may authenticate, subject to Access Control | Awaiting Password Change, Disabled |
| Disabled | Cannot authenticate; identity and history are preserved | Awaiting Password Change |

An administrative reset moves an Active account to Awaiting Password Change.
Re-enabling a Disabled account also moves it to Awaiting Password Change.

### Session condition

| Condition | Description | Result |
| --- | --- | --- |
| Active | Within the identity-provider-configured bounded maximum duration that began with the originating login and not terminated by another rule | The identity may request operations subject to account state and Access Control |
| Ended | Logged out, expired, disabled, reset, or administratively terminated | The session cannot be reused; a new login is required |

## Acceptance Criteria

1. Only a System Administrator can provision an account.
2. Provisioning requires a unique organizational email, an Access Control profile, initial roles, and a provisional password.
3. Duplicate email is rejected case-insensitively.
4. Provisioning neither creates nor administers an external mailbox.
5. Failed provisioning leaves no usable partial access.
6. Colibri Hub does not send or audit provisional passwords.
7. A provisioned user cannot access protected capabilities before replacing the provisional password.
8. The established password differs from the provisional password, which becomes unusable after replacement.
9. No self-registration, self-service recovery, or voluntary password change is available.
10. Successful Authentication without an active Access Control profile grants no protected access.
11. Authentication neither assigns nor evaluates roles or business permissions.
12. A session cannot remain usable beyond the identity-provider-configured bounded maximum duration that began with the login that created it, including a login performed with a provisional password.
13. A successful mandatory password replacement terminates the provider session used for replacement; the account becomes Active only after provider success, and Access Control resolves access only after a subsequent sign-in with the established password.
14. Logout, reset, disablement, and expiration make affected sessions unusable.
15. Disablement prevents login and inactivates the associated access profile without deleting history.
16. Re-enablement requires a new provisional password and mandatory replacement.
17. Disablement, administrative password reset, profile inactivation, role replacement, assignment removal, or any coordinated access change is rejected when it would leave no operational System Administrator.
18. Login denial does not reveal account existence or state.
19. Security history identifies affected accounts and acting administrators without exposing secrets.
20. The initial System Administrator is established without self-registration and replaces the provisional password before protected access.

## Capability Boundaries

Authentication does not define:

- roles, permissions, business scopes, presets, or authorization decisions;
- operational rules owned by Warehouse, Operation, Access Control, or another context;
- creation, administration, suspension, or deletion of organizational mailboxes;
- automated delivery of provisional passwords or invitations;
- self-registration, self-service recovery, or voluntary password change;
- multifactor authentication;
- calculation or independent configuration, restart, extension, rotation, or substitution of the identity-provider-configured maximum session duration by the frontend, backend, or application administrators;
- physical deletion of established accounts; or
- providers, schemas, APIs, tokens, libraries, or other implementation design.

Access Control remains normative for roles, permissions, business scopes,
access-profile lifecycle, and authorization. Technical specifications may
describe coordination but cannot merge ownership or redefine these rules.
