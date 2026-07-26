# Exploration: Align Warehouse Persistence Naming

> **Pre-change investigation.** This artifact records the state and assumptions
> observed before implementation. Final authority for this change is the
> proposal, specification, design, tasks, apply progress, and current
> code/migration/tests. Where this exploration conflicts with those sources,
> the later implemented evidence governs.

## Pre-Change State

This is a Warehouse-only, planning-only correction. The current implementation
already establishes the intended domain relationship and lifecycle:

- `backend/src/warehouse/bales/domain/raw_material_batch.py` stores
  `bale_ids: tuple[BaleId, ...]`, validates a non-empty, duplicate-free group,
  and exposes `bale_count`.
- `backend/src/warehouse/bales/domain/bale.py` stores its own identity and
  `raw_material_batch_id`; `deliver()` transitions only
  `BaleStatus.IN_WAREHOUSE` to `BaleStatus.DELIVERED`.
- `backend/src/warehouse/bales/domain/bale_status.py` contains exactly
  `IN_WAREHOUSE` and `DELIVERED`. `IN_PRODUCTION` MUST NOT be reintroduced.

These files directly verify the required 1:N model: one RawMaterialBatch owns a
collection of Bale IDs, while each independently addressable Bale references
the batch ID and owns its lifecycle. The current result/application flow also
creates one batch ID and assigns it to every independently generated Bale.

At exploration time, the authoritative persistence baseline was
`supabase/migrations/20260722130455_create_raw_material_reception_storage.sql`.
It then created `public.raw_material_receptions` and
`public.raw_material_bales`; the detail table has `reception_id` referencing
the header. The baseline has:

| Object | Observed pre-change definition |
|---|---|
| Header key | `id uuid NOT NULL`, constraint `pk_raw_material_receptions` |
| Header business key | `shipment_number varchar(10) NOT NULL`, unique constraint `uq_raw_material_receptions_shipment_number` |
| Header data | `received_at timestamptz NOT NULL`, `provider_name text NOT NULL` |
| Bale key/data | `id uuid`, `bale_number varchar(10)`, `material_type varchar(20)`, `dtex numeric`, `gross_weight_kg numeric`, `container_weight_kg numeric`, `status varchar(40)`, all required |
| Relationship | `raw_material_bales.reception_id` → `raw_material_receptions.id`, `ON DELETE RESTRICT`, constraint `fk_raw_material_bales_reception_id` |
| Bale uniqueness | `uq_raw_material_bales_reception_bale_number` on `(reception_id, bale_number)` |
| Bale index | `ix_raw_material_bales_reception_id` on `(reception_id)` |
| Security | RLS enabled on both tables; no policies; all privileges revoked from `anon`, `authenticated`, and `service_role` |

At exploration time, there were no baseline checks, triggers, views, sequences, or application
grants. SQLite adapter tests cannot prove PostgreSQL DDL, RLS, ACL, or
constraint diagnostics; the PostgreSQL integration suite is required for those
claims.

Before this change, the ORM and adapters exposed the old physical vocabulary. `RawMaterialBatchRecord`
maps to `raw_material_receptions`; `BaleRecord.reception_id` points to that
table; `BaleMapper` translates the domain `raw_material_batch_id` through the
old record field; transaction diagnostics use the old unique-constraint names;
and the concrete classes are `BaleRepository`, `RawMaterialBatchRepository`,
and `SqlAlchemyTransaction`. Bootstrap wires those concrete adapters, plus
`UuidIdentityGenerator`, into `RegisterRawMaterialBatch`.

The HTTP contract is intentionally in scope for this revised input. `POST
/api/v1/warehouse/bales` remains the route and registration action, but
`RegisterRawMaterialBatchResult.reception_id`, `BaleReceptionResponse.reception_id`,
their mapping, OpenAPI/runtime assertions, and related tests must become
`raw_material_batch_id`. This is an intentional breaking contract change; do
not preserve API v1 `reception_id`.

Existing PRD/architecture/domain/database prose still contains stale
`IN_PRODUCTION` and historical persistence recommendations. Current code and
the explicit lifecycle decision override that prose. The implementation handoff
must update only affected Warehouse terminology/documentation; it must not
implement a lifecycle redesign.

## Affected Areas

### Baseline migration and physical schema

- `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql`
  — replace the original Warehouse baseline in place; this is the exact
  migration-history file affected. Do not add a forward rename migration.
- Target baseline tables: `public.raw_material_batches` and
  `public.raw_material_bales`.
- Target relationship: `raw_material_bales.raw_material_batch_id` references
  `raw_material_batches.id` with `ON DELETE RESTRICT`.
- Target names: `pk_raw_material_batches`,
  `uq_raw_material_batches_shipment_number`,
  `fk_raw_material_bales_raw_material_batch_id`,
  `uq_raw_material_bales_raw_material_batch_bale_number`, and
  `ix_raw_material_bales_raw_material_batch_id`.
- Preserve the exact current types, nullability, primary keys, unique rules,
  composite uniqueness semantics, RLS enablement, empty policy set, and
  revokes. The approved target migration adds only the named
  `ck_raw_material_bales_status` lifecycle CHECK for `in_warehouse` and
  `delivered`; it must have no `delivered_at`, trigger, policy, grant, or
  production-context object.

### ORM, mappers, repositories, and transaction adapter

- `backend/src/warehouse/bales/adapters/persistence/raw_material_batch_record.py`
  — table and shipment constraint metadata.
- `backend/src/warehouse/bales/adapters/persistence/bale_record.py` — mapped
  FK attribute/target, composite constraint columns/name, and index name.
- `backend/src/warehouse/bales/adapters/persistence/bale_mapper.py` — map
  `Bale.raw_material_batch_id` to the renamed record attribute in both
  directions.
- `backend/src/warehouse/bales/adapters/persistence/raw_material_batch_mapper.py`
  — verify the 1:N `bale_ids` mapping remains unchanged in meaning.
- `backend/src/warehouse/bales/adapters/persistence/transaction.py` — update
  constraint constants and diagnostic matching; rename the concrete class to
  the role-based `TransactionAdapter`.
- `backend/src/warehouse/bales/adapters/persistence/bale_repository.py` and
  `raw_material_batch_repository.py` — evaluate and apply the concrete names
  `BaleRepositoryAdapter` and `RawMaterialBatchRepositoryAdapter`; ports keep
  technology-neutral role contracts. No concrete class name should expose
  SQLAlchemy or another framework/library.
- `backend/src/warehouse/bales/adapters/identity/identity_generator.py` —
  evaluate `Uuid4IdentityGenerator`; retaining the algorithm name is
  appropriate because UUID v4 is the behavior, unlike a framework name.
- `backend/src/bootstrap/warehouse_bale_dependency.py` and persistence
  exports — update imports, construction, and same-session wiring.
- `backend/src/warehouse/bales/application/register_raw_material_batch.py` —
  rename any result field/constructor vocabulary needed for
  `raw_material_batch_id`; preserve transaction order and domain behavior.

### HTTP/application contract

- `backend/src/warehouse/bales/application/register_raw_material_batch_result.py`
  — rename the outward batch identifier to `raw_material_batch_id`.
- `backend/src/warehouse/bales/adapters/http/bale_reception_response.py` and
  `bale_reception_mapping.py` — expose and map only `raw_material_batch_id`.
- `backend/src/warehouse/bales/adapters/http/router.py` and composition —
  retain `POST /api/v1/warehouse/bales`, status codes, validation, and error
  envelopes; only the accepted breaking identifier changes.
- Commands remain batch-oriented and contain no reception identifier; do not
  add one merely for compatibility.

### Tests and verification

- `backend/tests/test_warehouse/adapters/persistence/test_persistence_schema.py`
  — exact target ORM tables, columns, keys, constraints, and index metadata.
- `backend/tests/test_warehouse/adapters/persistence/test_bale_repository.py`,
  `test_warehouse_transaction.py`, and bootstrap tests — renamed attribute,
  adapter classes, wiring, and constraint diagnostics.
- HTTP tests under
  `backend/tests/test_warehouse/adapters/http/` — assert the breaking
  `raw_material_batch_id` response/OpenAPI contract and absence of
  `reception_id`.
- `backend/tests/test_warehouse/bales/application/test_register_raw_material_batch.py`
  — result field and independent Bale IDs sharing one batch ID.
- `backend/integration_tests/test_migrated_warehouse_schema.py` — PostgreSQL
   introspection for exact target tables/columns/keys/named status CHECK/constraints,
  index, RLS, policy absence, and ACL revokes.
- `backend/integration_tests/test_warehouse_transaction.py`,
  `test_register_bale_reception.py`, and `database_test_support.py` — target
  table/FK names, rollback, duplicate-bale diagnostics, 1:N persistence, and
  cleanup.
- Domain lifecycle tests remain evidence for `IN_WAREHOUSE -> DELIVERED`;
  they must not be changed to add `IN_PRODUCTION`.

### Documentation and operational housekeeping

- `docs/db/warehouse-dictionary.md` — make target physical names and
  constraints authoritative; correct stale status prose to
  `IN_WAREHOUSE`/`DELIVERED` without adding lifecycle schema.
- `docs/architecture/ARCHITECTURE.md`, `docs/architecture/backend.md`,
  `docs/architecture/backend/persistence-decisions.md`,
  `docs/architecture/backend/persistence-design-principles.md`,
  `docs/domain/warehouse.md`, and `docs/domain/ubiquitous-language.md` — update
  only stale Warehouse persistence/API vocabulary and lifecycle claims touched
  by this handoff. Other bounded contexts are out of scope.
- `docs/db/warehouse.dbml` and `warehouse.dbdiagram` — update only if they are
  intended to describe this implemented baseline; they are not migration
  authority and must not introduce lifecycle or unrelated context changes.
- Ignored cache cleanup, if performed separately, is limited to backend
  `__pycache__`/`.pyc` residue. Never remove `.codegraph`, assets, virtual
  environments, migrations, or unrelated untracked artifacts.

## Approaches

1. **Replace the resettable Warehouse baseline (recommended)** — rewrite the
   existing migration file with the target schema, then reset every relevant
   pre-production database and deploy code/docs against that baseline.
   - Pros: matches the confirmed absence of data to preserve; no mixed-version
     rename window; one authoritative migration; simplest rollback by restoring
     the file and resetting.
   - Cons: any database not reset will diverge; migration history/file review
     must be explicit; external SQL consumers must update together.
   - Effort: Medium

2. **Add a forward rename migration** — retain the historical migration and
   rename its objects later.
   - Pros: preserves an applied migration history and data in a persistent
     environment.
   - Cons: directly contradicts the confirmed resettable pre-production
     assumption; leaves obsolete baseline history; creates an unnecessary hard
     rename deployment gap; rejected for this change.
   - Effort: Medium

3. **Expand/contract compatibility bridge** — keep old and new physical names
   temporarily through duplicate columns/views or compatibility objects.
   - Pros: supports mixed-version deployments.
   - Cons: unnecessary with no data to preserve; complicates RLS/ACL, writes,
     exact constraint verification, and rollback; rejected unless deployment
     assumptions change.
   - Effort: High

## Recommendation

Use Approach 1. Replace
`20260722130455_create_raw_material_reception_storage.sql` rather than creating
any new migration. The target baseline must use
`raw_material_batches`, `raw_material_bales`, and
`raw_material_batch_id` consistently, with all keys/checks/constraints/indexes
   named from those physical names. Add the approved named status CHECK and
   otherwise preserve schema behavior: UUID keys, timestamp/text/numeric/varchar types, required columns,
global shipment uniqueness, per-batch Bale-number uniqueness, restricted FK,
   RLS, no policies, and revokes remain. The CHECK permits exactly
   `in_warehouse` and `delivered`.

Rename the ORM and concrete persistence adapters as a coherent role-based
cutover: `TransactionAdapter`, `RawMaterialBatchRepositoryAdapter`, and
`BaleRepositoryAdapter`; retain `Uuid4IdentityGenerator` if the identity
algorithm rename is included. Rename the external result/response field to
`raw_material_batch_id` as an intentional breaking contract while keeping the
route and registration behavior. Do not alter `BaleStatus`, add `IN_PRODUCTION`,
   add lifecycle columns beyond the approved status CHECK, or redesign the 1:N
   aggregate relationship.

## Reset and Verification Procedure

1. Confirm the worktree and migration diff contain only this planning handoff;
   do not stage or delete unrelated artifacts.
2. Replace the single baseline migration file, then reset each relevant local
   or pre-production database using the repository procedure:
   `supabase db reset --local --no-seed` (the `--no-seed` flag is required
   because the configured seed file is absent). For another disposable
   environment, apply the complete migration set from an empty database; do
   not attempt an in-place preservation migration.
3. Verify migration history has exactly the replaced baseline filename and no
   new alignment migration. Inspect with `supabase migration list --local`.
4. Run the backend unit suite and the PostgreSQL integration suite against the
   local Supabase database. Integration verification must assert the exact
   target names, column types/nullability, PK/FK/unique/index definitions,
   `ON DELETE RESTRICT`, RLS enabled, zero policies, and revokes for
   `anon`, `authenticated`, and `service_role`.
5. Verify behavior: one batch persists with multiple independently identified
   Bales; the same Bale number is rejected within one batch and allowed in a
   different batch; `raw_material_batch_id` is returned by HTTP; and lifecycle
   tests prove only `IN_WAREHOUSE -> DELIVERED`.

Rollback for this pre-production, resettable baseline is not a down migration:
restore the previous migration file from version control and reset the affected
databases again. If code has already been cut over, restore code and migration
as one unit before reset. No data-preserving rollback or forward reverse
migration is required or appropriate under the confirmed assumptions.

## Workload Forecast and Chained Delivery

The configured strategy is force-chained, stacked-to-main, with a 400 changed
line review budget. Forecast three reviewable work units, each keeping tests
with the behavior they prove:

1. **PR1 — Resettable schema and ORM contract**: replacement baseline
   migration, target ORM records/mappers, schema unit tests, and PostgreSQL
   metadata tests. Forecast: 280–380 changed lines.
2. **PR2 — Role-based adapters and composition**: transaction constants,
   `TransactionAdapter`, repository adapter names, optional
   `Uuid4IdentityGenerator`, exports, bootstrap wiring, and focused tests.
   Forecast: 180–300 lines.
3. **PR3 — Breaking HTTP contract, integration, and docs**: result/response
   rename, HTTP/application tests, registration/cleanup integration updates,
   Warehouse dictionary and corrected architecture/domain references. Forecast:
   300–390 lines; split documentation into a fourth stacked slice if the
   measured diff exceeds 400.

Dependency chain: `main <- PR1 <- PR2 <- PR3` (each child is based on the
previous slice and targets the immediate parent branch under stacked-to-main).
No size exception is planned; measure additions plus deletions before each
slice and split PR3 rather than exceeding the review budget.

## Risks

- Resetting is mandatory: any unreset database retains the old physical schema
  despite the replacement file.
- A hard physical/API rename breaks old ORM binaries and API clients; coordinate
  the manual implementation and publish the breaking `raw_material_batch_id`
  contract.
- PostgreSQL integration, not SQLite, is required to prove RLS, ACL, FK, and
  constraint diagnostics.
- ORM-generated index names can drift from the migration; assert exact names.
- Stale docs may reintroduce `IN_PRODUCTION` or reception vocabulary unless
  implementation review checks the explicit lifecycle and 1:N evidence.
- Untracked planning/assets/cache files make broad cleanup or staging unsafe.

## Ready for Proposal

Yes. The revised decisions remove the prior ambiguities: Warehouse only,
1:N RawMaterialBatch-to-Bale, `DELIVERED` lifecycle, replacement baseline with
reset, breaking API rename, and role-based adapter naming are all explicit. The
next phase can turn this into a proposal/spec/design/tasks for manual
implementation without changing code, schema, migrations, tests, or docs in
this exploration phase.

## Skill Resolution

Loaded the requested `sdd-explore`, Clean DDD/Hexagonal, Supabase, Supabase
PostgreSQL best-practices, chained-PR, and work-unit-commits skills. Current
CodeGraph/source evidence and the `warehouse/bale-lifecycle-status` decision
were treated as authoritative over stale planning artifacts and documentation.
