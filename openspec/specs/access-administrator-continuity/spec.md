# Access Administrator Continuity Specification

## Purpose

Define resilient System Administrator continuity across Authentication and Access without creating an emergency backend interface.

## Requirements

### Requirement: Operational Administrator State

The system MUST treat a principal as an operational System Administrator only when it has an active Authentication account, an active Access profile, and a current System Administrator role assignment. The system MUST count distinct principals, not role rows, and MUST evaluate this state across both contexts.

#### Scenario: Count distinct operational administrators

- GIVEN two distinct principals satisfy all operational-state conditions
- WHEN the system evaluates administrator continuity
- THEN it reports two operational System Administrators

#### Scenario: Exclude an inactive cross-context state

- GIVEN a principal has the role but its Authentication account or Access profile is inactive
- WHEN continuity is evaluated
- THEN that principal MUST NOT count as operational

### Requirement: Atomic Normal Continuity Floor

The system MUST preserve at least two distinct operational System Administrators for ordinary account or profile deactivation, role-assignment removal or replacement, and account lifecycle transitions that make a principal non-operational, including administrative password reset and disablement. The decision and mutation MUST be atomic; a rejected mutation MUST leave all affected state unchanged. Account deletion is not governed by this continuity requirement.

#### Scenario: Allow a reducing lifecycle mutation above the floor

- GIVEN three distinct operational System Administrators
- WHEN an ordinary in-scope lifecycle mutation makes one principal non-operational
- THEN the mutation succeeds and two remain

#### Scenario: Reject an in-scope mutation at the floor

- GIVEN exactly two distinct operational System Administrators
- WHEN an in-scope deactivation, role-assignment removal or replacement, or lifecycle transition would make either principal non-operational
- THEN the system MUST reject it without a partial cross-context change

### Requirement: Controlled Single-Administrator Migration

The system MUST identify installations with fewer than two operational System Administrators before enforcing the normal floor. Migration MUST establish a second distinct operational administrator through controlled initialization or the external recovery procedure, retain evidence of the transition, and only then enable ordinary continuity enforcement.

#### Scenario: Migrate a single-administrator installation

- GIVEN an installation has exactly one operational System Administrator
- WHEN its continuity migration is performed
- THEN a second distinct operational administrator is established before enforcement begins

#### Scenario: Refuse incomplete migration

- GIVEN a single-administrator installation lacks a second operational administrator
- WHEN activation of normal continuity enforcement is requested
- THEN the system MUST refuse activation and preserve existing state

### Requirement: External Manual Recovery Governance

Recovery MUST remain outside ordinary RBAC and MUST NOT expose a backend recovery API or privileged application bypass. Ordinary recovery activation MUST require approval by two distinct designated custodians. One custodian MAY activate only for a documented administrative emergency and MUST immediately notify the other custodian, close the event, revoke temporary recovery material, and complete post-incident review.

#### Scenario: Execute ordinary external recovery

- GIVEN two designated custodians approve a documented recovery
- WHEN they perform the manual procedure
- THEN it restores the required operational state with retained evidence

#### Scenario: Execute an emergency unilateral activation

- GIVEN one designated custodian documents an administrative emergency
- WHEN that custodian activates recovery alone
- THEN notification, closure, temporary-material revocation, and review MUST be recorded

#### Scenario: Deny ordinary unilateral activation

- GIVEN no documented administrative emergency exists
- WHEN one custodian seeks ordinary recovery activation
- THEN the procedure MUST NOT authorize activation

### Requirement: Isolated Continuity Evidence

Integration evidence for issue #92 MUST use independently owned mutable administrator fixtures and MUST NOT mutate canonical seeded administrator state. Tests MUST prove normal atomic enforcement and recovery boundaries, including the absence of a recovery API, and remain valid when executed independently or with other tests.

#### Scenario: Preserve canonical seeded administrators

- GIVEN an integration test prepares an administrator state change
- WHEN the test mutates its fixture
- THEN canonical seeded administrators remain unchanged

#### Scenario: Prove no emergency endpoint

- GIVEN the system is in a continuity failure condition
- WHEN an application recovery endpoint or bypass is requested
- THEN no such operation is available
