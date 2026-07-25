## Exploration: backend-capability-first-refactor

> **Historical pre-cutover investigation.** These observations and constraints
> describe the P0 starting point. The P0 cutover was completed; later
> persistence/API/adapter naming decisions are superseded by
> `../align-warehouse-persistence-naming/`. Retained old physical names,
> `reception_id`, and transaction class names below are historical, not current
> authority.

### Pre-Cutover State

The committed backend implements the Warehouse raw-material receiving slice in a
layer-first `warehouse.{domain,application,ports,adapters}` tree, with the
capability hidden below the cross-cutting `raw_material` namespace. The current
flow is:

`backend/src/bootstrap/http_application.py` creates the FastAPI application,
registers global exception handlers, and mounts the bale router directly at
`/api/v1/warehouse/bales`. The router maps the collective POST request to
`RegisterBaleReception`. The use case creates a persisted header model
(`BaleReception`) and independent `Bale` objects, adds the header before the
details, and commits through one shared `Session` and `WarehouseTransaction`.

Persistence intentionally uses historical names: `raw_material_receptions` is
the physical header for the domain `RawMaterialBatch`, and
`raw_material_bales.reception_id` is the header reference. The migration remains
authoritative for the two named uniqueness constraints, foreign key, index, RLS,
privileges, and column types. The transaction adapter translates only
`uq_raw_material_bales_reception_bale_number` and
`uq_raw_material_receptions_shipment_number`; unknown integrity errors are
re-raised.

The current public contract is collective `POST /api/v1/warehouse/bales`, with
the existing request/response field names, error mapping, status codes,
multi-Bale behavior, slash behavior, and atomicity. Package discovery is a
setuptools `src` layout including `warehouse*`, `infra*`, and `bootstrap*`.

The repository is on `back/capability-first-refactor`. There is no
`backend/src/warehouse/bales/` tree and no tracked partial capability-first
implementation. The current implementation remains under the old namespace,
which is the expected P0 starting point. The working tree is not globally clean:
`pyproject.toml` is modified and numerous unrelated files/directories are
untracked, including agent metadata, notebooks, raw reference files, and
documentation. Those paths are protected and are not part of this exploration
or future change scope. No cleanup or restoration of them is authorized here.

P1 delivery is explicitly deferred. P0 must not add `DeliverBales`,
`delivered_at`, `IN_PRODUCTION`, new lifecycle states, delivery endpoints, or
multi-Bale delivery atomicity decisions. P0 preserves current runtime behavior;
the approved future Bale lifecycle is a P1 concern, not a reason to alter the
registration slice now.

### Affected Areas

- `backend/src/warehouse/` — move the receiving slice from the transversal
  `raw_material` namespace into capability-owned `warehouse.bales`, preserving
  dependency direction and avoiding a `Reception` domain type.
- `backend/src/warehouse/domain/raw_material/` — rename/re-home domain concepts
  so `RawMaterialBatch` represents the shipment grouping and `Bale` remains an
  independently identified lifecycle owner; do not implement P1 lifecycle work.
- `backend/src/warehouse/application/raw_material/` — rename the receiving
  action and its command/result vocabulary while keeping the collective
  behavior and transport compatibility.
- `backend/src/warehouse/ports/` — relocate repository, identity, and
  transaction contracts under the capability; repositories should reflect
  aggregate behavior rather than physical table names.
- `backend/src/warehouse/adapters/http/raw_material/` — relocate HTTP models,
  mapping, errors, and the leaf router under `warehouse.bales`; keep public
  request/response names and error semantics stable.
- `backend/src/warehouse/adapters/persistence/raw_material/` — relocate ORM
  records, mappers, repositories, and constraint-aware transaction wiring;
  retain historical table/column/constraint names as persistence details.
- `backend/src/bootstrap/http_application.py` and
  `backend/src/bootstrap/warehouse_bale_dependency.py` — compose the new
  capability and router hierarchy without creating a second session or route.
- `backend/src/bootstrap/http_error_handlers.py` — retain global registration
  while importing canonical capability-owned application/domain errors.
- `backend/tests/` and `backend/integration_tests/` — move/update tests with
  each work unit, preserving HTTP, application, domain, transaction,
  constraint-translation, schema, and package-discovery coverage.
- `backend/pyproject.toml` — verify the existing discovery pattern still finds
  the new package; do not modify the protected working-tree change during this
  exploration.
- `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql`
  — implementation evidence only; no migration change is needed for P0.
- `docs/prd/warehouse.md`, `docs/prd/warehouse/warehouse-records.md`,
  `docs/architecture/`, `docs/domain/`, `docs/db/warehouse-dictionary.md`,
  and `backend/docs/task.md` — authoritative meaning and constraints already
  support the target; no documentation edits are part of this planning-only
  exploration.

### Contracts to Preserve

| Boundary | P0 invariant |
|---|---|
| HTTP | Exactly `POST /api/v1/warehouse/bales`; same slash policy, payload, collective response, validation, error shape, and status codes. |
| Application | One receiving action creates one complete `RawMaterialBatch` grouping and one or more `Bale` objects, then returns the existing collective result. |
| Domain | `RawMaterialBatch` is not a production lot; `Bale` has independent technical identity; no `Reception` or `BaleReception` domain aggregate. |
| Transaction/session | One request-scoped session is shared by repositories and transaction; header insertion precedes details; commit and rollback remain atomic. |
| Constraints | Translate only the two named uniqueness constraints; propagate unknown integrity failures. |
| Persistence | Keep table, column, FK, index, uniqueness, RLS, privileges, and migration history unchanged. |
| Packaging | Preserve `warehouse*`, `infra*`, and `bootstrap*` discovery; canonical ownership moves to `warehouse.bales`. |
| Tests | Tests move with behavior and continue to prove the same contracts; no test execution occurs during exploration. |

### Stable P0 Naming and Explicit Deferrals

Stable P0 structural names to validate in proposal/design are:

- capability root: `warehouse.bales`;
- domain concepts: `RawMaterialBatch`, `Bale`, and existing value objects where
  a rename is not required by the capability boundary;
- receiving action: provisional but consistent `ReceiveBales`;
- application data: `ReceiveBalesCommand` and `ReceiveBalesResult`, with
  `execute()`;
- transaction abstraction: `Transaction` if the existing contract is renamed
  without changing its responsibility;
- repository contracts named for aggregate behavior, such as
  `RawMaterialBatchRepository` and `BaleRepository`, only where the use case
  genuinely needs both ports.

The HTTP transport may retain legacy names such as `reception_id` and existing
request/response model fields because transport compatibility is a P0 invariant.
Historical ORM names such as `BaleReceptionRecord` and `reception_id` may also
remain as explicitly documented persistence compatibility names if a rename
would add risk without improving the capability boundary. The proposal should
choose one canonical policy and avoid permanent two-way aliases.

The following are P1 or later and must not enter P0: `DeliverBales`,
`DeliverBalesCommand`, `delivered_at`, `IN_PRODUCTION`, any replacement for the
current lifecycle enum, delivery actors, delivery endpoint(s), and atomicity
rules for delivering multiple Bales. The current implementation's observed
status behavior is preserved during P0 rather than silently corrected as part
of the package refactor.

### Hierarchical Router Ownership

Use one owner per path segment:

```text
bootstrap application
└── /api/v1 router                 owns only /api/v1
    └── Warehouse HTTP router      owns only /warehouse
        └── Bales capability router owns only /bales and POST handler
```

The leaf capability router owns request mapping, the endpoint declaration, and
capability-specific HTTP dependencies. The Warehouse router is a composition
boundary, not a second implementation of the endpoint. The API-version router
is a bootstrap/composition concern. This yields exactly
`/api/v1/warehouse/bales`, avoids duplicated prefixes, and keeps future
Warehouse capabilities composable without moving the FastAPI application
factory into a domain package.

### Approaches

1. **Direct capability move with hierarchical composition** — create the
   `warehouse.bales` ownership boundary, move the complete existing slice,
   update imports and tests, and add `/api/v1` → `/warehouse` → `/bales`
   composition without behavior changes.
   - Pros: establishes the requested architecture in one coherent direction;
     keeps the old namespace from remaining canonical; makes ownership and
     future capability growth discoverable.
   - Cons: broad rename/move diff; requires careful test and import updates;
     temporary aliases may be needed only for proven internal consumers.
   - Effort: High

2. **Compatibility wrapper first** — add `warehouse.bales` packages that wrap
   the current `raw_material` implementation, then migrate internals later.
   - Pros: smaller first diff and lower immediate import churn.
   - Cons: violates the required ownership direction (`new -> old`), leaves the
     transversal namespace canonical, prolongs duplicate vocabulary, and risks
     repeating the interrupted PR1 failure mode.
   - Effort: Medium initially, High overall

3. **Leave the current tree and add only routers** — introduce hierarchical
   composition while retaining the existing layer-first implementation.
   - Pros: lowest short-term risk to behavior.
   - Cons: does not establish capability-first ownership, does not resolve
     `Reception`/`RawMaterialBatch` naming, and defers the architectural problem.
   - Effort: Low, but insufficient

### Recommendation

Use Approach 1, delivered as force-chained stacked-to-main work units. Make the
new `warehouse.bales` tree canonical, keep any old FQN only as a temporary
old-to-new alias with a named consumer and removal criterion, and avoid aliases
when all consumers are internal and can be updated in the same slice. Treat
transport and persistence compatibility as separate from domain naming: the
domain should say `RawMaterialBatch`, while `reception_id` and physical table
names may remain compatibility vocabulary at their boundaries.

The smallest safe target is therefore a structural P0 refactor of the existing
collective receiving capability, not a redesign of receiving semantics and not
an implementation of delivery. No DB migration or reset is required to change
the schema; a local reset with `--no-seed` is a later verification step only.

### Chained Delivery Forecast

The requested stacked-to-main strategy is appropriate because the full move is
likely above the 400 changed-line review budget once renames, imports, tests,
and package initializers are counted. A candidate sequence is:

1. **PR1 — router/composition seam:** introduce the three-level router ownership
   and bootstrap wiring while preserving the existing leaf behavior; include
   focused bootstrap/router tests. Estimate 180–300 changed lines.
2. **PR2 — domain/application capability ownership:** move and rename the
   domain/application contracts to `warehouse.bales`, including
   `RawMaterialBatch` and receiving command/result vocabulary; move associated
   unit tests. Estimate 300–390 changed lines.
3. **PR3 — ports, persistence, and dependency composition:** move adapters,
   records/mappers, repositories, transaction wiring, and capability DI;
   preserve session sharing and constraint translation. Include adapter tests.
   Estimate 320–395 changed lines.
4. **PR4 — canonical import cleanup and complete verification surface:** remove
   unnecessary legacy aliases, update remaining HTTP/error/integration/package
   tests, and add discovery/import/OpenAPI assertions where missing. Estimate
   250–380 changed lines.

These are estimates, not task commitments. Rename-heavy slices may need to be
rebalanced after a design-level file map. Each slice must have a clear start and
finish, include its verifying tests, remain independently understandable, and
target the immediately preceding stack position while the overall chain
progresses to `main`. No migration diff belongs in any slice.

### Risks

- A rename can accidentally change transport field names or OpenAPI route
  registration even when runtime behavior appears equivalent.
- Moving ORM records can break SQLAlchemy registry discovery or produce duplicate
  table registration if old and new modules are imported together.
- Constraint translation depends on exact PostgreSQL constraint names; changing
  constants or mapping locations without tests can turn known conflicts into
  generic failures.
- The current working tree contains protected unrelated modifications and
  untracked files; broad cleanup, checkout, or formatting could destroy them.
- The current code's lifecycle naming differs from the approved future P1 model;
  mixing that correction into P0 would violate the behavior-preservation goal.
- Temporary aliases can become permanent architecture if their consumers and
  deletion criteria are not recorded in the design/tasks.

### Proposal Questions and Unresolved Technical Decisions

- Is `ReceiveBales` the final accepted application verb, or should the proposal
  retain a different verb while still avoiding `Reception` as a domain noun?
- Should the persisted header's technical identity be renamed to
  `RawMaterialBatchId`, or should its existing identifier/value-object name stay
  as a compatibility detail during P0?
- Which repository operations are truly required by the collective receiving
  use case, and should header/detail repository ports remain separate despite
  one atomic application transaction?
- Which old FQNs, if any, have real consumers that justify temporary aliases?
  Internal tests and bootstrap imports should otherwise move in the same slice.
- Should the API-version and Warehouse routers live under `bootstrap` and
  `warehouse.adapters.http` respectively, or should a small bootstrap HTTP
  composition module own both non-capability routers?
- What exact OpenAPI and trailing-slash assertions are required to prove that
  hierarchical inclusion added no duplicate or redirecting route?
- Can the existing protected `pyproject.toml` modification be left untouched
  while package discovery is verified against the working tree, or must a later
  implementation session first establish a clean protected baseline with the
  user?

### Ready for Proposal

Yes. The proposal can be written for a P0 structural refactor with no migration
change, no Supabase execution during planning, and no P1 delivery behavior.
It should preserve the exact HTTP/application/persistence contracts above,
make `warehouse.bales` canonical, define the alias policy and router ownership,
and use the four-slice stacked forecast as the initial review-budget guard.
