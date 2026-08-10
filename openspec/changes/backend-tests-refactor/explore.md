## Exploration: Backend Tests Refactor

### Current State

The backend test tree contains two incompatible generations:

- The newer Warehouse suite is organized by technical layer (`api/`, `application/`, `domain/`, `persistence/`, `runtime/`) and uses `backend/tests/support/` for Warehouse-specific builders, values, payloads, and doubles.
- Authentication and Access Control remain mostly flat under `backend/tests/`, with 12 root modules totaling approximately 3,085 lines. Several large modules mix multiple use cases and layers, including files of approximately 600, 569, and 542 lines.
- The root suite contains duplicated inline doubles. The most material repetitions are `InMemoryAccountRepository`, `InMemoryAuditRepository`, `FakeIdentityProvider`, `FakeAccessProvisioning`, and `FakeClock` across Authentication application/API/bootstrap tests; Access tests independently repeat `Users`, `Roles`, `Scopes`, repository fakes, clocks, transactions, and audit doubles. These are behaviorally similar but not always contract-equivalent, so consolidation must preserve per-test capabilities rather than blindly centralizing every fake.
- The current unit command was independently verified: 252 tests passed in 1.258 seconds. The preliminary claim that syntax is broken is contradicted by this run and by the existing clean compile result; no syntax defect was found.
- `backend/integration_tests/` is already a separate PostgreSQL-only namespace with an explicit `TEST_DATABASE_URL` guard. It should not be merged into the unit tree.

The production package structure is capability/context-oriented and inward-facing: `warehouse`, `access`, `auth`, `infra`, `bootstrap`, and `shared`, with domain/application/ports/adapters boundaries. The authoritative architecture explicitly favors capability-first packaging over a global layer-first source layout and requires domain/application code to remain testable without infrastructure. The testing strategy describes the same layer taxonomy, but the current tree applies it consistently only to Warehouse.

`RequestPipeline` is operationally orphaned. `backend/src/auth/adapters/identity_provider/request_pipeline.py` defines account lookup, disabled-account rejection, eight-hour session-age validation, and awaiting-password-change endpoint restrictions, and `backend/tests/test_auth_pipeline.py` contains 12 focused cases. However, source references show no runtime caller: `bootstrap.auth_dependency.compose_auth()` returns the JWT validator directly, and the HTTP routers depend directly on that resolver. Therefore the implementation and its tests are real but do not protect the current HTTP flow.

This is not safe to classify as semantically disposable. The Authentication PRD requires eight-hour sessions, session termination, and restriction of awaiting-password-change accounts; `supabase/config.toml` also sets `[auth.sessions].timebox = "8h"`. The pipeline is therefore an unintegrated implementation of normative behavior, not merely a meaningless test artifact. Connecting it requires a separate behavior decision and integration proof. It must not be wired opportunistically as part of a test-only structure refactor.

The provider seam adds a material constraint: `IdentityProviderAdapter.get_session()` and `revoke_sessions()` query `auth.sessions` through the Supabase Data API schema client, while `supabase/config.toml` exposes only `public` and `graphql_public`. Existing adapter tests assert those calls, but they do not prove the local provider path works. Any future pipeline wiring must resolve this provider/runtime boundary first or explicitly document the resulting fail-closed behavior.

The Starlette warning is environment/dependency-originated. The full unit run emits it while importing `fastapi.testclient` from the installed FastAPI/Starlette/httpx stack, before test code executes. Test modules only construct `TestClient`; they do not import or configure Starlette's deprecated integration directly. The warning affects dependency maintenance and verification noise, not the target directory convention. It should remain outside this refactor unless dependency upgrade is separately approved.

### Affected Areas

- `backend/tests/` — normalize the currently mixed context/layer structure without changing test behavior.
- `backend/tests/support/` — retain a small shared kernel for stable technical doubles and builders; add context-local support where a fake encodes business semantics.
- `backend/tests/api/`, `backend/tests/application/`, `backend/tests/domain/`, `backend/tests/persistence/`, `backend/tests/runtime/` — preserve the successful Warehouse layering while bringing Authentication and Access Control under the same convention.
- `backend/src/warehouse/`, `backend/src/access/`, `backend/src/auth/` — test ownership should follow these bounded contexts and their inward layer boundaries; no production edits are authorized by this exploration.
- `backend/src/bootstrap/` — composition and dependency tests must distinguish injected test seams from production auth composition.
- `backend/src/auth/adapters/identity_provider/request_pipeline.py` and `backend/tests/test_auth_pipeline.py` — classify as an unconnected authentication policy slice; defer deletion or wiring to an explicit auth decision.
- `backend/integration_tests/` — keep isolated from unit tests and preserve PostgreSQL-only claims, especially session/provider, schema, constraint, and transaction behavior.
- `docs/prd/`, `docs/architecture/`, `docs/domain/`, `backend/docs/testing/strategy.md`, `AGENTS.md`, and `backend/pyproject.toml` — authority and naming constraints for the refactor.

### Approaches

1. **Context-first, layer-second test packages (recommended)** — organize tests under `warehouse/`, `yarn_production/`, `batch_processing/`, `access/`, and `auth/`, then use cohesive `domain/`, `application/`, `ports/`, `adapters/`, `api/`, or `runtime/` modules only where the context has that concern. Keep files aligned with behavior/capability, not every production file.
   - Pros: mirrors bounded-context ownership and capability-first architecture; gives every context one navigable convention; limits cross-context leakage; scales when Yarn and Lot Processing are implemented.
   - Cons: requires moving the existing Warehouse tests and deciding how `bootstrap`, `infra`, and cross-context HTTP tests are represented; Python package names need snake_case aliases for documented `yarn-production` and `batch-processing` contexts.
   - Effort: Medium

2. **Global layer-first test packages** — keep `domain/`, `application/`, `persistence/`, `api/`, and `runtime/` as the primary directories, grouping contexts inside each layer.
   - Pros: minimal migration from the current Warehouse layout; simple layer-wide commands and comparisons.
   - Cons: repeats the architecture's rejected layer-first navigation problem; makes Access/Auth/Warehouse support and ownership easy to mix; scales poorly as contexts grow.
   - Effort: Low initially, High maintenance

3. **Context-local test trees beside each production capability** — place tests inside each source capability package or create a strict one-to-one mirror of every production directory.
   - Pros: maximum locality and direct source/test pairing; useful for very large independent capabilities.
   - Cons: conflicts with the current centralized `backend/tests` discovery contract; increases package/import complexity; creates excessive symmetry and brittle file coupling for the current codebase.
   - Effort: High

### Recommendation

Proceed to proposal with Approach 1, using a staged migration rather than a big-bang move. Establish one context-first convention, retain layer names only when they communicate a real contract, and split oversized root files by cohesive capability (for example, Authentication domain/application/API and Access domain/application/presets/previews/API). Move genuinely reusable technical doubles into `support/` only when their protocol and state semantics are stable; keep Access/Auth-specific repository fakes and scenario builders local to their context until their contracts are proven identical. Do not introduce pytest, coverage, a linter, or a new fixture framework because the repository is explicitly stdlib `unittest` with no such tooling configured.

Treat `RequestPipeline` as a separate decision gate: current runtime behavior confirms it is dead/unwired, while PRD and Supabase configuration confirm its intended policy is required. The proposal should preserve its tests as evidence of the missing integration, then require either (a) an explicitly approved auth integration change with provider-session feasibility proof, or (b) a separately approved removal/replacement that demonstrates equivalent enforcement. The warning should be recorded as dependency noise and excluded from structural scope.

### Risks

- **CRITICAL** — Deleting or merely relocating `RequestPipeline` tests could erase evidence of an authentication policy that the current HTTP flow does not enforce. A test refactor must not convert an uncovered security requirement into an intentional omission.
- **CRITICAL** — Wiring the pipeline without resolving the `auth.sessions` provider access path may produce fail-closed requests or ineffective session revocation because the configured Data API schemas exclude `auth`.
- **WARNING** — Consolidating doubles with different method surfaces or state behavior can make tests pass for the wrong reason or hide missing port contracts. Consolidate by protocol and semantic responsibility, not by class name.
- **WARNING** — Moving modules can change `unittest discover` import paths and break focused commands documented in `AGENTS.md`; preserve compatibility or update the command contract in the proposal.
- **WARNING** — A single large migration of 12 root modules risks review overload and accidental assertion changes. Use small context/layer slices with green checkpoints.
- **INFO** — The Starlette/httpx warning is dependency-level noise and should be handled in dependency maintenance, not by changing TestClient usage or test structure.
- **INFO** — `yarn-production` and `batch-processing` are architectural aliases but are not implemented Python packages yet; use valid snake_case test package names if scaffolding future contexts.

### Ready for Proposal

Yes. The repository evidence and authoritative PRD/architecture constraints are sufficient to draft a proposal. The proposal should explicitly separate structural test migration from the unresolved Authentication runtime-policy decision, preserve PostgreSQL integration boundaries, retain stdlib `unittest`, and define staged reviewable slices.
