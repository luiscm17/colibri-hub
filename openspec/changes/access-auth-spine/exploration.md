# SDD Exploration: Access Authorization Spine

**Change:** `access-auth-spine`  
**Mode:** hybrid (OpenSpec + Engram)  
**Execution:** interactive  
**Delivery:** single PR  
**Review budget:** 800 changed lines (repository SDD guard remains 400 lines by default)

## Status

- **Status:** success, conditionally ready for proposal
- **Executive summary:** The repository has no Access Control implementation or backend Authentication boundary. The first viable slice is a deliberately narrow Access authorization spine: provider-neutral trusted-identity input, persisted Access policy state, exact action-and-scope evaluation, controlled Access bootstrap, `/access/me`, and protection of one existing Warehouse write operation. Full role/preset/scope administration, Supabase Authentication, and frontend work must remain later slices.
- **Artifacts:** `openspec/changes/access-auth-spine/exploration.md`; Engram `sdd/access-auth-spine/explore`
- **Next recommended:** `sdd-propose` after the interactive product questions below are answered
- **Risks:** The local PostgreSQL instance is running but is stale relative to the checked-in migrations; the current integration suite has five errors caused by the missing `delivery_date` column. Supabase Auth configuration also does not yet satisfy the Authentication specification.
- **Skill resolution:** `paths-injected` — the requested `sdd-explore`, `clean-ddd-hexagonal`, `supabase`, `supabase-postgres-best-practices`, and `work-unit-commits` skills were loaded from the exact paths supplied; shared SDD and OpenSpec conventions were also read.

## Exploration: access-auth-spine

### Current State

#### Authoritative product and architecture model

Access Control is a policy bounded context. It owns access profiles, additive roles, exact action-and-business-scope permissions, presets, assignments, and access-configuration history. Authentication owns credentials, provider identity, account state, and sessions. A successful Authentication event establishes identity but grants no business permission. The Access PRD explicitly forbids direct user grants, explicit denies, role or scope inheritance, job-title and shift authorization, and client-supplied authoritative scope.

The conceptual model recently aligned with that boundary: one Authentication account maps to one Access profile; a profile may hold multiple roles; effective permissions are the deduplicated union of active role permissions; and the reserved System Administrator is a policy invariant rather than a wildcard permission row. The context map makes Warehouse, Yarn Spinning, and Lot Processing consumers of Access decisions, not owners of authorization semantics.

The backend technical specification is substantially broader than a first spine. It describes the eventual complete Access capability, including every administrative endpoint, presets, recognized-scope registration, impact previews, optimistic concurrency, audit queries, bootstrap, PostgreSQL constraints, and all protected operations. It also explicitly excludes login, logout, credentials, sessions, token issuance, provider selection, and frontend route work. Treat that document as the target architecture, not as evidence that those features already exist.

#### Current backend implementation

The implemented backend is a capability-first, hexagonal `warehouse.bales` module. Domain code is framework-free; application use cases own orchestration and transaction boundaries; ports define repositories, identity generation, and transactions; SQLAlchemy adapters persist to PostgreSQL; and `bootstrap.http_application.create_app` composes settings, engine/session dependencies, handlers, and routers.

The current Warehouse HTTP surface includes:

- `POST /api/v1/warehouse/bales` — register a complete raw-material batch and bales;
- `GET /api/v1/warehouse/bales` — stock summary;
- `GET /api/v1/warehouse/bales/{shipment_number}/{bale_number}` — bale detail; and
- `POST /api/v1/warehouse/bales/deliver` — best-effort delivery.

There is no authentication dependency, actor context, Access package, authorization port, Access persistence, audit persistence, or protected route. `create_api_router` currently includes only the Warehouse router. `create_app` currently accepts settings, engine, and session seams, but no identity or authorization seam. CORS allows `Content-Type` but not `Authorization`.

The `RegisterRawMaterialBatch` use case is the best first protected operation: it is already a cohesive application command, has a clear business action (`write`), maps unambiguously to `warehouse.raw_materials`, and mutates state inside one transaction. Authorization can therefore be tested before any domain validation or repository write without changing Warehouse invariants. The other three endpoints should not be silently protected under a different action model in this slice.

#### Persistence and runtime evidence

The repository uses imperative, forward-only Supabase CLI migrations. SQL migrations are physical authority; SQLAlchemy records mirror them. Existing Warehouse tables enable RLS and revoke `anon`, `authenticated`, and `service_role` privileges, with the backend connection as the application path. There is no declarative schema directory and no Alembic setup.

The backend package discovery rule currently includes only `warehouse*`, `infra*`, and `bootstrap*`; adding `access*` is required for a new capability package. The root workspace uses Python 3.13 and uv; backend dependencies are FastAPI, SQLAlchemy, psycopg, and pydantic-settings. No new provider SDK is justified by this slice.

Local Supabase status confirms the stack is running, PostgreSQL is on `127.0.0.1:54322`, and Auth is enabled. That status does **not** verify provider behavior. The checked-in `supabase/config.toml` currently has `enable_signup = true` and leaves the Auth session timebox commented out, while the Authentication specification requires signup disabled and an eight-hour timebox. Those settings belong to the later Authentication change and must not be assumed or changed as part of this Access exploration.

The local migration list shows only `20260722130455` applied locally, while the two later checked-in migrations are unapplied. Running the guarded integration command produced 11 tests with 5 errors, all caused by the ORM inserting `delivery_date` into a local table that lacks that column. This is an existing environment/schema drift finding, not an Access implementation task. Unit tests currently pass: 32 tests, `OK`.

### Exact First-Slice Boundary

#### Recommended inclusion

1. **Provider-neutral identity seam**
   - Define an immutable trusted identity contract containing an opaque `subject` and, if needed for later coordination, an optional provider-neutral session identifier.
   - Treat the subject as an identifier only; Access must never parse JWTs, call Supabase, read request bodies for identity, or trust arbitrary client headers.
   - Add an injectable HTTP/composition identity resolver. Until Authentication exists, the production default must fail closed with `401`; tests and future Authentication composition may provide the trusted identity.

2. **Access authorization core**
   - Add the `access` capability using the repository's `domain/application/ports/adapters` layout.
   - Model the five stable actions, recognized scope definitions, Access profile lifecycle, active/inactive roles, role assignments, ordinary permission pairs, and reserved System Administrator semantics.
   - Implement exact `(action, scope)` matching, additive multi-role union, default deny, inactive-profile/role/scope denial, and global System Administrator behavior for existing and newly recognized scopes.
   - Expose a narrow authorization port for Warehouse rather than Access repositories or ORM records.

3. **Minimal persisted policy state**
   - Persist the state needed to resolve the identity and evaluate the first protected operation: Access users, roles, current/historical assignments, recognized/registered scopes, role permissions, and append-only Access-change audit rows.
   - Register at least `access_control` and `warehouse.raw_materials` through server-owned scope definitions; do not accept free-form scope metadata.
   - Use named constraints, restrictive foreign keys, immutable identity/subject and scope-code fields, explicit active-state checks, RLS on every public Access table, and revocation of browser/service-role table privileges.
   - Do not add presets or the complete administrative model merely because the eventual specification contains them; the first schema should not claim those workflows are implemented.

4. **Controlled Access bootstrap**
   - Define an internal bootstrap application contract receiving an opaque initial identity subject, user code, display name, and operation identifier. It must never receive or persist a password, token, or provider-private claim.
   - In one PostgreSQL transaction, create or resolve the reserved active System Administrator role, required initial scopes, one active Access user, one current assignment, and a redacted `initial_bootstrap` audit record.
   - Make the same-identifier bootstrap idempotent and fail closed on conflicting partial state. After bootstrap, a null audit actor is forbidden except for explicitly controlled initialization.
   - Keep provider identity creation outside this Access slice; Authentication will later own provider ordering and call this contract.

5. **First HTTP contracts**
   - Add `GET /api/v1/access/me` for the authenticated current Access profile and effective authorization snapshot, including a global System Administrator representation without enumerating every scope.
   - Protect `POST /api/v1/warehouse/bales` with `write + warehouse.raw_materials`; deny before the Warehouse use case executes.
   - Preserve the existing Warehouse domain/application behavior and response contracts after authorization succeeds.
   - Return `401` for missing/untrusted identity and a non-enumerating `403 access_denied` for the protected business operation. `/access/me` may distinguish unmapped and inactive Access profiles because it is a self-access bootstrap contract.
   - Add `Authorization` to CORS allowed headers. Do not add broad future HTTP methods or provider-specific CORS behavior without a confirmed API need.

6. **Tests and proof**
   - Add deterministic unit tests for action/scope exactness, additive roles, inactive state, global administrator behavior, identity mapping, and fail-closed denial.
   - Add application tests proving authorization precedes Warehouse persistence/domain execution and that `/access/me` maps ordinary/global results.
   - Add PostgreSQL integration tests for the Access migration's constraints, RLS/ACL posture, bootstrap idempotency/conflict behavior, append-only audit behavior, and protected-operation authorization with real persisted state.
   - Record the current local migration drift as a prerequisite to verification; do not weaken tests to accommodate it.

#### Explicit non-goals

- Supabase Auth SDK integration, JWT signature/issuer/audience validation, token refresh, sessions, password handling, login/logout, password replacement, account enablement/disablement, or provider audit retrieval.
- A public Access user-creation endpoint. Profile creation remains an internal provisioning contract owned by the future unified Authentication flow.
- Full Access administration: user lists/details, role CRUD, role assignment replacement, presets, scope registration/lifecycle endpoints, impact previews, version conflicts, and Access audit query endpoints.
- Frontend Authentication, AccessProvider, navigation, route guards, client permission utilities, or UI changes. Frontend specifications are downstream contracts only.
- Protection of all Warehouse endpoints or any Yarn Spinning/Lot Processing operation.
- Operational Warehouse audits, correction windows, shift rules, record ownership, or domain-specific authorization.
- RLS as the primary business authorization evaluator. Application-layer authorization remains authoritative; database RLS/ACL is defense in depth.
- Runtime authorization caching, wildcard/hierarchical scope matching, direct user grants, deny rules, or role precedence.
- Changing Supabase Auth configuration or claiming that local Auth provider behavior has been verified.

### Affected Areas

- `backend/src/access/` — new Access Control capability package for domain, application, ports, and persistence/HTTP adapters.
- `backend/src/bootstrap/http_application.py` — compose Access repositories, evaluator, identity seam, CORS header, and the protected Warehouse dependency graph.
- `backend/src/bootstrap/api_router.py` — include the Access router while preserving the existing `/api/v1/warehouse` composition.
- `backend/src/bootstrap/warehouse_bale_dependency.py` and `backend/src/warehouse/bales/adapters/http/router.py` — inject the narrow authorization port and protect only batch registration.
- `backend/src/infra/persistence/record_registry.py` — import Access ORM records so metadata and session mappings are registered.
- `backend/pyproject.toml` — extend setuptools package discovery from `warehouse*`, `infra*`, `bootstrap*` to include `access*`.
- `backend/src/infra/configuration/` — only the minimum CORS/config seam required for `Authorization`; no Supabase provider settings in this slice.
- `supabase/migrations/` — one forward-only Access schema migration, if proposal confirms persisted bootstrap/core state.
- `backend/tests/` — unit, application, HTTP/composition, and architecture-boundary tests for the spine.
- `backend/integration_tests/` — guarded PostgreSQL Access schema/bootstrap/protected-operation tests; existing Warehouse drift must be resolved or isolated before a green full suite.
- `docs/prd/access-control.md`, `backend/docs/features/access-control.md`, and frontend feature specifications — reference contracts only during implementation; no documentation rewrite is required to make this exploration valid.

### Domain, Application, Ports, and Audit Semantics

#### Domain

Use small value types/enums for action and stable scope code. Keep policy rules in domain objects: exact permission pairs, no duplicate role permissions, active-state contribution, reserved-role semantics, and no privileged actions on ordinary roles. A role assignment is historical evidence plus current state; it is not a shift or job-title relationship. The System Administrator's global behavior should be an explicit policy branch, not a wildcard row or scope hierarchy.

The Access domain must not import FastAPI, Pydantic, SQLAlchemy, settings, environment variables, Supabase, or Authentication account types. It should accept only the opaque identity subject at an application boundary.

#### Application

The first application services should be `AuthorizeAction`, `GetCurrentAccess`, and `BootstrapAccess`. `AuthorizeAction` resolves the subject to exactly one active Access profile, applies the global administrator branch, loads only active assignments/roles/scopes, and checks the exact requested pair. It returns a typed allow result containing the internal Access user identifier or a typed denial; it must not return partial business data.

`BootstrapAccess` owns the Access transaction boundary, idempotency/conflict handling, initial audit creation, and last-administrator coverage establishment. Future administrative mutations should each own a transaction containing actor resolution, authorization, version/invariant checks, state change, affected-user version increments, and audit insertion. Do not implement those future commands in the first slice merely to demonstrate the pattern.

#### Ports

The minimum ports are an Access user resolver by opaque subject, an effective-authorization query/repository, bootstrap persistence, an append-only audit writer, transaction/unit-of-work, identity generation, clock, and a narrow `AuthorizationPort` consumed by Warehouse. Keep provider-neutral `AuthenticatedIdentity` outside Access persistence; Access stores only its immutable subject mapping.

#### Audit

Access-change audit is configuration history, not a request log. Bootstrap records a controlled `initial_bootstrap` entry with null actor and explicit reason. Ordinary future mutations must include the individual acting Access user, affected subject, change kind, before/after non-secret snapshots, timestamp, and reason when required. Authorization checks themselves are not Access-change audit rows. No credentials, bearer tokens, raw claims, or provider secrets may enter snapshots, errors, logs, or test fixtures.

### Opaque Identity Boundary

The correct contract is:

```python
@dataclass(frozen=True)
class AuthenticatedIdentity:
    subject: str
    session_id: str | None = None
```

Authentication will later create this object only after verifying the provider token/session. Access receives it through an application/composition port and maps `subject` to its own `access_users` row. Access does not know whether the subject came from Supabase, another provider, or a test double. The request body, query parameters, frontend user object, role headers, and client-supplied scope are never identity or authorization sources.

The default runtime before Authentication exists should be a fail-closed resolver that raises the typed unauthenticated result. A development-only fabricated subject or header would create a security boundary that later Authentication must unwind and would make local success misleading. Test composition should inject a deterministic identity resolver without modifying production behavior.

### Representative Warehouse Operation

Protect `POST /api/v1/warehouse/bales` first with `write + warehouse.raw_materials`.

This operation is preferred over the stock-summary read because it exercises the most important safety property: a denied actor must not create a batch or partially open a transaction. It also has an existing clear application boundary and no server-derived resource scope problem—the operation's scope is fixed by the route's owning capability. It is preferred over delivery because delivery currently has best-effort per-bale semantics and would add more ambiguity to denial/error interaction.

The protection sequence should be: resolve trusted identity → require `write` in the fixed Warehouse scope → invoke the existing registration use case. Authentication/Access denial must occur before request-to-domain mapping where practical, and definitely before repository persistence. Existing domain validation still runs after authorization succeeds. Stock summary, bale detail, and delivery remain unprotected or explicitly unavailable until their own authorization contract is added; they must not accidentally be exposed as an implication of protecting registration.

### Bootstrap and Last-Administrator Invariants

Bootstrap is a special controlled operation because no administrator exists yet. It must be atomic across Access records and auditable without an authenticated actor. Same identifiers should return the existing valid bootstrap result; conflicting subject/user code, duplicate reserved role, partial assignment, or incompatible active state should fail rather than silently repair unknown state.

The eventual last-operational-administrator rule is cross-record and cannot be guaranteed by a simple row check. Future mutations that could remove coverage must lock the reserved role, candidate current assignments, and relevant profiles in a consistent order inside one PostgreSQL transaction, then evaluate whether at least one active assigned administrator remains operational. Authentication later asks Access for this policy before disabling/resetting an administrator; it must not reproduce role semantics.

For this first slice, implement and test the invariant needed to establish valid bootstrap and expose a reusable policy/checking port, but do not claim profile deactivation, assignment replacement, role deactivation, or Authentication account reset protection is complete without those mutation use cases. This boundary is a product decision for the proposal round.

### Persistence and Database Security

The migration should use the existing imperative Supabase convention and named constraints. Access tables are public-schema application tables but must enable RLS and revoke `anon`, `authenticated`, and `service_role` privileges, matching the existing Warehouse defense-in-depth posture. Foreign keys should be restrictive; persisted identities, subjects, scope codes, and audit rows should not be hard-deleted by the application.

Recommended first-slice indexes include unique identity subject/user code, one reserved System Administrator role, current assignment uniqueness, role/action/scope uniqueness, scope definition/code uniqueness, and lookup paths for active subject resolution and effective permissions. Use PostgreSQL integration tests for RLS, ACL, partial uniqueness, append-only audit enforcement, and transaction/locking claims; SQLite or in-memory fakes cannot prove those properties.

### Bootstrap and Composition Changes

The composition root should remain the only place that builds SQLAlchemy adapters and joins Access to Warehouse. Add Access record imports to the record registry, construct one shared session-backed Access unit of work, build a narrow `AuthorizationPort`, and inject it into the selected Warehouse use case/router dependency. Avoid making Warehouse import Access persistence classes.

`backend/pyproject.toml` must discover `access*`; otherwise the new package will work only from an editable source checkout and fail in a built backend artifact. `create_app` needs an injectable identity/authorization seam analogous to its existing session seam so tests never load real settings or a provider. CORS must permit the bearer `Authorization` header; `allow_credentials` is not required merely for a bearer header and should not be enabled without a confirmed cookie contract.

### Testing and TDD Resolution

Strict TDD is **not active**. Evidence: `openspec/config.yaml` has `strict_tdd: false`, `rules.apply.tdd: false`, and `test_command: null`. The repository testing strategy uses stdlib `unittest`, with no pytest, coverage tool, linter, formatter, or type checker configured. The implementation should still use test-first work units where practical, but the SDD apply phase must not claim a strict RED-GREEN-REFACTOR gate.

Exact repository commands:

```bash
# Unit suite
uv run --locked --package backend python -m unittest discover -s backend/tests -v

# Guarded PostgreSQL integration suite
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres \
  uv run --locked --package backend python -m unittest discover -s backend/integration_tests -v

# Required local schema refresh before PostgreSQL verification when migrations change
pnpm supabase db reset --local --no-seed

# Confirm migration state
pnpm supabase migration list --local
```

Observed baseline during exploration: unit suite passed 32 tests. The integration command ran 11 tests and had 5 errors because local PostgreSQL has only the first Warehouse migration applied while the ORM expects `delivery_date`; it is not evidence of an Access failure. After the local reset prerequisite, the complete suite should be rerun before claiming green.

### Approaches

1. **Narrow persisted authorization spine (recommended)** — Implement the provider-neutral identity seam, exact evaluator, minimal persisted policy state, controlled bootstrap, `/access/me`, and one protected Warehouse write operation; defer all administrative mutations and Authentication.
   - Pros: establishes the highest-value seam; proves real PostgreSQL resolution and denial-before-mutation; keeps Authentication provider-independent; fits the documented bounded contexts.
   - Cons: Access data must be bootstrapped operationally before any ordinary user exists; no UI or administrator API exists yet; last-administrator mutation checks remain a reusable foundation rather than a complete lifecycle feature.
   - Effort: Medium-High; approximately 750–950 authored changed lines including migration, tests, composition, and adapters.

2. **Complete Access backend specification in one change** — Add all role, preset, scope, user, preview, audit-query, optimistic-concurrency, and lifecycle APIs together with every persistence contract and all protected Warehouse operations.
   - Pros: closer to the eventual backend specification and immediately useful to a future frontend.
   - Cons: couples an authorization foundation to many unvalidated product/API decisions; does not implement Authentication but would need its internal provisioning contract; high migration/concurrency/audit risk; far beyond the 800-line budget and the repository's 400-line reviewer guard.
   - Effort: Very High; likely multiple thousands of authored changed lines and several independent review units.

3. **In-memory policy plus no migration** — Establish only domain evaluator tests and an injected policy fake, leaving persisted Access state and real bootstrap for later.
   - Pros: smallest diff and fastest domain feedback.
   - Cons: does not establish a deployable authorization spine; cannot prove identity mapping, audit transactionality, RLS/ACL, bootstrap, or real denial behavior; creates a second integration seam to replace.
   - Effort: Low, but inadequate for this goal.

### Recommendation

Proceed with Approach 1, but confirm its exact API and invariant boundary before proposal. It creates the stable seam the future Authentication capability needs without coupling Access to Supabase or pretending that frontend visibility is security. The selected Warehouse registration operation gives a concrete, reviewable proof that authorization happens before business mutation. Keep the eventual backend Access specification as the roadmap, not as an excuse to include full administration in this first PR.

The proposed scope is close to the user-provided 800-line budget and exceeds the repository's default 400-line guard. The implementation plan must forecast authored additions plus deletions precisely. If PostgreSQL integration proof and the migration push the slice above 800, do not delete required behavior; either authorize an explicit size exception or change delivery strategy before apply. Work-unit commits should group domain/application behavior with its tests, persistence with its integration proof, and composition/HTTP protection with its contract tests.

### Risks and Contradictions

- **Local database drift:** `pnpm supabase migration list --local` shows only the first migration applied; current integration tests fail on missing `delivery_date`. Reset is required before using integration results as evidence.
- **Supabase Auth is not ready:** local Auth is enabled, but `enable_signup = true` and the eight-hour session timebox is commented out. Do not infer that future Authentication requirements already hold.
- **Specification breadth:** `backend/docs/features/access-control.md` describes complete administration while the requested goal is a first spine. The proposal must make the reduced first slice explicit.
- **Bootstrap ownership:** Authentication PRD says unified provisioning creates both account and Access profile, while Access needs a controlled initial bootstrap before Authentication exists. The proposal must define whether the first slice accepts a pre-established opaque subject or includes a deployment-only Access bootstrap command.
- **Last-administrator completeness:** bootstrap can establish coverage now, but profile/role/assignment mutations needed to enforce the invariant do not exist. Claiming the invariant is complete without those mutations would be false.
- **Protected-route default behavior:** without Authentication, a production default identity resolver must return `401`, not use a development header or fabricated subject. This means the protected route is intentionally unusable until the Authentication slice composes a verifier.
- **CORS scope:** the current middleware allows only `Content-Type`. `Authorization` is required for the seam, but future administrative methods should not be enabled speculatively.
- **Package discovery:** omitting `access*` from setuptools discovery would make local imports pass while packaged deployment fails.
- **Security enforcement location:** application authorization is primary; RLS/ACL protects tables. A future design must not confuse database role membership with business permissions.
- **Review workload:** the requested single-PR strategy conflicts with the repository-wide 400-line default guard if the complete testable spine exceeds that threshold. This needs explicit process resolution rather than silent scope reduction.

### Product Questions for the Interactive Proposal Round

1. Confirm that the first slice is Approach 1: exact evaluator, minimal persisted policy state, controlled bootstrap, `/access/me`, and only `POST /api/v1/warehouse/bales` protected; full Access administration and all Authentication behavior remain out of scope.
2. Decide whether controlled bootstrap receives an already-created provider subject (recommended) or whether the first slice may create a local placeholder identity. Recommendation: accept only an opaque subject and leave provider identity creation to Authentication.
3. Confirm that the pre-Authentication production identity resolver must fail closed with `401`, with identities supplied only through composition/test seams; no temporary header or local bypass.
4. Confirm that the first migration registers only `access_control` and `warehouse.raw_materials`, with the rest of the documented scope catalog added through later reviewed changes.
5. Decide whether the first slice should implement only bootstrap coverage plus a reusable last-administrator policy port, or also include profile/role/assignment mutation commands needed to enforce the invariant end-to-end. Recommendation: defer mutations and state this limitation explicitly.
6. Confirm the `/access/me` denial detail boundary: specific `access_profile_not_found`/inactive responses for self-access versus generic `access_denied` for protected Warehouse resources.
7. Confirm that no Supabase Auth configuration, SDK, token validation, provider behavior, or frontend code is part of this change, despite local Auth being available.
8. Confirm how to handle the current local migration drift before implementation verification: run `pnpm supabase db reset --local --no-seed` and rerun the guarded integration suite; do not repair the database outside the migration workflow.
9. Resolve the review-budget conflict: accept a likely 750–950-line implementation under the user-provided 800-line budget with an explicit exception to the repository's 400-line guard, or authorize chained PRs before tasks/apply.

### Ready for Proposal

**Yes, conditionally.** The code, migrations, runtime configuration, downstream contracts, and test commands are sufficiently understood for a proposal. The orchestrator should ask the nine product/process questions above, especially the first-slice boundary, bootstrap identity source, last-administrator completeness, and the 400-versus-800 review guard. Do not advance to design/tasks until those answers are recorded.

## Key Learnings

1. Access Control has no backend implementation, so the first change must establish both persistence and a provider-neutral authorization seam.
2. The existing Warehouse batch-registration use case is the cleanest first protected write because its scope is fixed and denial can precede all mutation.
3. Local Supabase PostgreSQL is running but lacks the two later checked-in Warehouse migrations, causing five current integration errors.
4. Strict TDD is disabled in OpenSpec configuration, while stdlib unittest remains the authoritative backend test framework.
5. Supabase Auth configuration currently conflicts with the future Authentication specification and must not be assumed verified by Access work.
