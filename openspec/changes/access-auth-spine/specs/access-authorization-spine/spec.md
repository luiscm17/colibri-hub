# Access Authorization Spine Specification

## Purpose

Provide persisted, provider-neutral, default-deny Access decisions without implementing Authentication or broad administration.

## Requirements

### Requirement: Trusted Identity and Controlled Bootstrap

The system MUST accept an externally supplied opaque provider subject only through a trusted composition boundary. Production HTTP MUST return `401` until Authentication resolves that identity; tests MAY inject deterministic equivalent subjects. Bootstrap MUST atomically create or return the same active initial profile, System Administrator assignment, two initial scopes, and redacted `initial_bootstrap` audit; conflicting or partial state MUST fail closed.

#### Scenario: Equivalent bootstrap retry

- GIVEN matching opaque subject, profile identifiers, and operation identifier
- WHEN bootstrap is repeated
- THEN it returns the established bootstrap result without duplicate policy state

#### Scenario: Untrusted or conflicting bootstrap

- GIVEN production has no trusted identity resolver, or bootstrap identifiers conflict with existing state
- WHEN HTTP access or bootstrap is attempted
- THEN HTTP returns `401`, or bootstrap rejects without repairing partial state

### Requirement: Exact Active Authorization Policy

The system MUST resolve a subject to one profile and allow only the deduplicated union of active assigned-role permissions with an exact action-and-scope match. Missing/inactive profiles, roles, assignments, or scopes MUST deny. The only initial scopes MUST be `access_control` and `warehouse.raw_materials`; direct grants, denies, wildcards, inheritance, and unregistered scopes MUST NOT grant access.

#### Scenario: Additive exact permission

- GIVEN an active profile with active roles granting separate exact permission pairs
- WHEN it requests either granted action and scope pair
- THEN the evaluator allows that pair and denies a non-granted pair

#### Scenario: Inactive policy state

- GIVEN the matching profile, assignment, role, or scope is inactive
- WHEN the profile requests its formerly granted pair
- THEN the evaluator denies it by default

### Requirement: Reserved System Administrator Semantics

The reserved active System Administrator role MUST authorize every action in every recognized current or future scope through an explicit global rule, not a wildcard or inheritance permission. Ordinary roles MUST remain exact-pair roles.

#### Scenario: Global administrator snapshot

- GIVEN an active profile currently assigned the reserved role
- WHEN authorization or self access is evaluated
- THEN it is global without enumerating synthetic per-scope permissions

#### Scenario: Ordinary role cannot become global

- GIVEN an ordinary role with a permission resembling a broad scope
- WHEN it requests another scope or action
- THEN authorization denies it unless that exact recognized pair exists

### Requirement: Self Access and Business Denial Boundary

`GET /api/v1/access/me` MUST return the authenticated profile and effective ordinary permissions, or an explicit global representation for System Administrator. It MUST return self-specific missing or inactive profile outcomes. Protected business resources MUST return only generic `403` `access_denied` for authorization failures and MUST NOT disclose profile or role state.

#### Scenario: Ordinary and global self access

- GIVEN trusted identities mapped to an ordinary profile and a System Administrator
- WHEN each requests `/api/v1/access/me`
- THEN each receives its applicable ordinary or global authorization representation

#### Scenario: Self versus business denial

- GIVEN a trusted subject with no profile or an inactive profile
- WHEN it requests self access and then a protected business resource
- THEN self access is specific while the business resource returns `403 access_denied`

### Requirement: Minimal Invariant-Preserving Policy Mutations

The system MUST expose only profile activation-state, role activation-state, and current-assignment create/remove/activation-state mutations necessary to demonstrate every path that could remove the final operational System Administrator. Each such command MUST atomically reject a resulting state with no active profile holding an active current System Administrator assignment; it MUST preserve the prior state on rejection. Authentication account disable/reset is outside this capability.

#### Scenario: Non-final administrator removal

- GIVEN two operational System Administrators
- WHEN an authorized mutation removes, deactivates, or reassigns one administrator coverage path
- THEN it succeeds and one operational administrator remains

#### Scenario: Final administrator protection

- GIVEN exactly one operational System Administrator
- WHEN a mutation deactivates its profile or role, removes/deactivates its assignment, or removes its role coverage
- THEN it is rejected atomically with the existing coverage unchanged

### Requirement: Auditable and Defended Persistence

The system MUST retain append-only, redacted Access-change history. Bootstrap alone MAY have a null actor; every mutation MUST record its actor, affected subject, change kind, non-secret before/after state, timestamp, and required reason. Persistence MUST enforce defense-in-depth RLS/ACL, named constraints, restrictive history-preserving relationships, and immutable identity/subject/scope identity behavior; application authorization remains authoritative.

#### Scenario: Mutation audit and immutable history

- GIVEN an accepted policy mutation or bootstrap
- WHEN it commits
- THEN one redacted audit record is retained and cannot be altered or deleted through the application

#### Scenario: Restricted persistence access

- GIVEN browser-facing or unauthorized database access
- WHEN it attempts Access policy or audit reads or writes
- THEN RLS/ACL denies it and constraints preserve valid references

## Out of Scope

Supabase Auth, providers, tokens, sessions, credentials, frontend, full administration, presets, other scopes/endpoints, and package installation are excluded. Any installation MUST be user-executed. Local migration reset is a verification prerequisite, not product behavior.
