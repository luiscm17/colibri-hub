## Exploration: access-administrator-continuity

### Current State
Colibri Hub currently models the System Administrator as a reserved Access role with global authorization semantics. The normative Access and Authentication PRDs require at least one active/operational administrator, while the implementation enforces a weaker survivorship invariant: mutations are rejected only when they would leave zero active users assigned to the reserved role. The backend checks role replacement and profile deactivation, and related authentication lifecycle operations reuse the same last-administrator error. PostgreSQL currently permits only one role row marked `is_system_administrator`, so continuity is represented by multiple assignments to one reserved role rather than by multiple administrator role definitions.

The current integration evidence is not fully isolated. The critical last-administrator test deactivates pre-existing seeded administrators and restores them in teardown, and the lifecycle fixture creates an administrator through bootstrap before provisioning a target administrator. GitHub issue #92's fixture-isolation correction is therefore related test evidence for the policy: tests must create and clean up independent administrator fixtures without mutating canonical seeded state. It is not, by itself, a production policy decision or a runtime fix.

The accepted direction of at least two operational System Administrators is promising, but it is not yet normative. The exploration must distinguish a minimum redundancy target from a hard invariant, define what “operational” means across Authentication and Access states, and specify recovery behavior when the target cannot be maintained.

### Affected Areas
- `docs/prd/access-control.md` — currently defines one active System Administrator as the survivorship floor, reserves global access, and treats the reserved role as the policy boundary.
- `docs/prd/auth.md` — contains the cross-capability rule for an enabled, authenticating System Administrator and applies the invariant to account disablement, password reset, profile changes, and assignments.
- `docs/data-models/conceptual/access-dictionary.md` — describes the reserved global administrator invariant and controlled initialization vocabulary.
- `backend/src/access/application/replace_user_roles.py` — enforces last-administrator protection during complete role replacement and uses row locking for concurrent removal.
- `backend/src/access/application/deactivate_access_user.py` — enforces last-administrator protection during Access profile deactivation.
- `backend/src/access/adapters/persistence/user_repository.py` — defines the active-administrator count and its locking behavior; it currently counts active profiles with current assignments to the single reserved role.
- `backend/integration_tests/test_access_control_critical.py` — provides concurrency evidence but mutates existing administrator fixtures, making it a target for issue #92's isolation correction.
- `backend/integration_tests/test_auth_lifecycle_local_supabase.py` — creates administrator fixtures through bootstrap and provisions a second administrator; its fixture lifecycle is relevant to proving cross-context continuity.
- `supabase/migrations/20260804200832_access_control_administration.sql` — establishes the unique reserved-role marker, constraining the data model to one System Administrator role definition.
- `supabase/migrations/20260806120000_seed_system_administrator_role.sql` — seeds the canonical reserved role used by integration setup.
- `openspec/config.yaml` — requires RFC 2119 scenarios, bounded-context/API impact, migration and Supabase implications, and reviewable task grouping.

### Approaches
1. **Two-operational-administrator survivorship invariant** — define a minimum of two distinct operational System Administrators and reject ordinary mutations that would reduce the count below two.
   - Pros: provides genuine continuity for absence, revocation, and concurrent administration; aligns the Access and Authentication policy around one explicit cross-context concept; preserves the existing single reserved role model.
   - Cons: requires precise operational-state semantics, bootstrap/recovery exceptions, and migration of existing environments with only one administrator; may block legitimate planned retirement unless replacement happens first.
   - Effort: Medium

2. **Advisory redundancy target with one-admin hard floor** — retain the current zero-loss/one-admin invariant, add monitoring and administrative warnings when fewer than two operational administrators exist, and treat two as an operational objective rather than an authorization denial.
   - Pros: low migration risk and backward compatibility; avoids locking out organizations during bootstrap or emergency recovery.
   - Cons: does not guarantee continuity; warnings can be ignored; the policy remains vulnerable to the exact single-person failure mode that motivated the change.
   - Effort: Low

3. **Two administrators plus explicit break-glass recovery** — make two operational administrators the normal hard floor, while defining a separately audited, time-bounded recovery path for controlled initialization or emergency restoration when the floor cannot be met.
   - Pros: combines continuity with recoverability; makes exceptional bypass visible and governable instead of relying on database/service access implicitly.
   - Cons: highest policy complexity; requires trusted recovery authority, credential and audit boundaries, expiry/revocation semantics, and careful separation from ordinary RBAC.
   - Effort: High

### Recommendation
Proceed to proposal with Approach 3 as the target policy shape, but do not make it normative until the decision gaps below are resolved. The normal invariant should require at least two distinct operational System Administrators, while controlled initialization and a narrowly defined emergency recovery path should prevent the invariant from becoming an irreversible lockout. Keep the existing single reserved `system_administrator` role unless a concrete requirement proves that separate administrator role definitions are needed; continuity is a property of distinct operational principals, not of duplicate role rows.

The eventual change should include issue #92 as test evidence: integration fixtures must use unique, independently owned administrator identities and must never deactivate, repurpose, or restore canonical seeded administrators. The fixture correction should be implemented and verified alongside policy enforcement, but it should not be used as evidence that the production invariant itself is satisfied.

Before specification, decide: the exact operational state matrix (Authentication Active, Access profile Active, role assignment current, session/password state); whether two means distinct persons, identities, or accounts; whether pending password replacement counts; how bootstrap creates the first administrator and adds the second; who may invoke break-glass recovery and under what audit/expiry rules; whether role deactivation or assignment replacement must preserve two administrators atomically; and how existing installations are migrated when only one administrator exists.

### Risks
- A hard two-administrator floor can create an administrative deadlock unless bootstrap and emergency recovery are explicit, independently authenticated, and auditable.
- Counting active Access profiles alone can overstate continuity if Authentication is disabled, awaiting mandatory password replacement, session access is revoked, or the person cannot complete login.
- Concurrent checks must protect the invariant across account, profile, assignment, and role mutations; application-only counts are insufficient without transaction and locking guarantees.
- Existing seeded fixtures and shared database state can make tests pass or fail for the wrong reason; issue #92's isolation correction is required for trustworthy evidence.
- Changing normative PRDs without synchronizing the conceptual dictionary, API contracts, migrations, and error semantics would leave cross-context policy drift.

### Ready for Proposal
Yes, with decision gaps explicitly carried into the proposal. The orchestrator should present the recommended normal two-person invariant plus controlled recovery as a candidate policy, ask the user to resolve the operational-state and break-glass semantics, and then run proposal/spec/design before any runtime or fixture implementation.
