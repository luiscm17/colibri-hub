# SDD Exploration: Rebuild Backend Test Suite

**Change:** `rebuild-backend-test-suite`  
**Mode:** hybrid  
**Delivery:** force-chained, stacked to `main`  
**Review budget:** 400 changed lines; implementation slices must remain at or below 399

## Status

- **Status:** success
- **Executive summary:** The current backend has a coherent `warehouse.bales` capability with a framework-free domain/application core, SQLAlchemy/PostgreSQL adapters, and a composed FastAPI boundary. The deleted `backend/tests/` tree must be treated as discarded legacy material; the replacement suite should be derived from current code, authoritative documents, migration contracts, and runtime behavior rather than porting assertions. Remaining PostgreSQL integration tests contain useful contract evidence but require canonical renaming, fixture hardening, and expanded boundary coverage.
- **Artifacts:** `openspec/changes/rebuild-backend-test-suite/exploration.md`; Engram `sdd/rebuild-backend-test-suite/explore`
- **Next recommended:** `sdd-propose` after the proposal questions below are confirmed
- **Risks:** The working tree contains intentional test deletions plus unrelated manifest/untracked changes. No files other than this exploration artifact may be changed during planning.
- **Skill resolution:** `paths-injected` — requested `sdd-explore`, `clean-ddd-hexagonal`, `cognitive-doc-design`, and `work-unit-commits` skills were loaded; shared SDD contracts were also consulted.

## Exploration: rebuild-backend-test-suite

### Current State

The current backend follows inward dependency direction:

```text
HTTP / FastAPI
  → application command/use case/result/errors
    → domain entities/value objects + ports
      ← persistence, identity, transaction adapters
        ← bootstrap composition, settings, engine, session lifecycle
```

The implemented capability is `warehouse.bales`:

- Domain: immutable `RawMaterialBatch` identity/membership and `Bale` custody state, with value objects for IDs, shipment/bale numbers, reception time, material, dtex, and weights. Current rules normalize shipment/bale/material strings, require timezone-aware reception time, finite positive dtex and weights, positive gross/container weights with gross greater than container, non-empty provider and batch membership, and reject duplicate Bale IDs. `Bale.deliver()` permits only `IN_WAREHOUSE → DELIVERED`.
- Application: `RegisterRawMaterialBatch` canonicalizes Bale numbers, rejects duplicate numbers before identity generation, creates one batch and one or more Bales, inserts the batch before Bales, commits through one transaction, translates only the two named uniqueness conflicts, and returns `raw_material_batch_id` plus collective Bale results.
- Ports: repository protocols for batch and Bale insertion, identity generation, transaction protocol, and named transaction conflict types. The application does not import FastAPI or SQLAlchemy.
- Persistence: SQLAlchemy records map to `raw_material_batches` and `raw_material_bales`; mappers translate records/domain objects; repositories add the batch (and flush) then Bales; `TransactionAdapter` rolls back failures and translates PostgreSQL diagnostic constraint names. The migration currently has an historical filename but its contents define the current canonical tables, named constraints, RLS, no policies, and revoked API-role privileges.
- HTTP: `POST /api/v1/warehouse/bales` is composed as `/api/v1` → `/warehouse` → `/bales`, returns 201, uses frozen Pydantic request/response models, requires at least one Bale, requires decimal values as JSON strings, rejects extra fields, requires aware datetimes, and exposes `raw_material_batch_id`. Errors map request validation to 422, domain validation to 422, duplicate Bale numbers to 422, duplicate shipment numbers to 409, and unexpected failures to 500. OpenAPI declares the response/error models at the route.
- Bootstrap/runtime: `backend/main.py` creates the ASGI `app` through `create_app`, passing the sibling `backend/.env` path. `create_app` loads settings only when no explicit engine/session seam is provided, builds an engine/session factory, creates a per-request session dependency, composes the use case, registers handlers, and includes the API router. Settings are infrastructure-owned, typed, frozen, and secret-redacting; engine construction does not connect.

The old `backend/tests/` tree is entirely tracked as deleted. It is intentionally not evidence for this exploration. The only remaining tests are under `backend/integration_tests/`, and they are candidates for validation rather than authoritative requirements.

### Authoritative Context Read

Business meaning was resolved in the required order:

1. `docs/prd/warehouse/` and `docs/prd/warehouse.md`: receiving is one complete raw-material batch with one or more Bales; shipment numbers are globally unique; Bale numbers are unique within a batch; receiving is not a production lot; the current action is atomic.
2. `docs/architecture/`: Warehouse owns the capability, contexts remain separate, domain/application boundaries point inward, and corrections/audit remain broader architectural concerns rather than invented tests for this slice.
3. `docs/domain/ubiquitous-language.md` and `docs/domain/warehouse.md`: `RawMaterialBatch`, `Bale`, `ShipmentNumber`, `stock`, `lot`, and production identity must not be conflated; receiving is an application action, not a `Reception` aggregate.
4. `docs/db/warehouse-dictionary.md` and the applied Supabase migration: the migration is physical authority for tables, types, named keys, FK behavior, status CHECK, RLS, policies, and ACLs. SQLite cannot prove these PostgreSQL claims.
5. Current OpenSpec contracts: `align-warehouse-persistence-naming` and `backend-runtime-settings` are current implementation contracts; the `backend-capability-first-refactor` spec explicitly marks its old persistence/API references as historical or superseded.
6. `AGENTS.md` and dev guides: Python 3.13, stdlib `unittest`, no configured pytest/linter/type checker/coverage tool, guarded local PostgreSQL integration, and no install or dependency-tooling change during this exploration.

### Affected Areas

- `backend/src/warehouse/bales/domain/` — value-object, entity, normalization, identity, membership, and state-transition behavior.
- `backend/src/warehouse/bales/application/` — command construction, atomic registration, result shape, duplicate/error boundaries.
- `backend/src/warehouse/bales/ports/` — protocol contracts and dependency-direction characterization.
- `backend/src/warehouse/bales/adapters/persistence/` — records, mappers, repositories, transaction diagnostics, SQLAlchemy coupling.
- `backend/src/warehouse/bales/adapters/http/` — Pydantic request/response schemas, mapping, router, OpenAPI and error responses.
- `backend/src/infra/configuration/` — settings source isolation, URL validation, secret redaction, nested environment mapping.
- `backend/src/infra/persistence/` — engine/session factory and deferred-connect behavior.
- `backend/src/bootstrap/` and `backend/main.py` — composition, dependency/session lifecycle, handler registration, ASGI startup.
- `backend/integration_tests/` — PostgreSQL-only schema/security/diagnostic proof and end-to-end persistence candidates.
- `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql` — physical PostgreSQL authority; retain its current filename during this test rebuild and do not infer requirements from its historical name.

## Behavior / Contract Inventory

| Behavior or contract | Source authority | Recommended test level |
|---|---|---|
| Value objects are frozen, normalize canonical strings, preserve UUID identity, and reject empty/oversized values | Current domain source; ubiquitous language for names | Unit |
| Reception time must be timezone-aware | `ReceptionDateTime`; persistence dictionary | Unit plus PostgreSQL round-trip integration |
| Decimal values are finite; dtex and gross/container weights are positive; gross exceeds container; net weight is derived | `Dtex`, `BaleWeight` | Unit; Decimal round-trip in PostgreSQL integration |
| Batch provider is trimmed/non-empty; batch has at least one distinct Bale ID; equality is by batch ID | `RawMaterialBatch` | Unit |
| Bale defaults to `IN_WAREHOUSE`, exposes availability, and delivers exactly once to `DELIVERED` | `Bale`, PRD WH-RM-04 | Unit |
| Registration canonicalizes Bale numbers, rejects empty/duplicate collection values, preserves input order, and creates a complete batch | Application use case and command/result | Application unit with fakes |
| Batch is persisted before Bales; one transaction commits both or rolls back all | Use case, repository adapter, transaction port | Application unit plus PostgreSQL integration |
| Only named shipment and per-batch Bale uniqueness conflicts become application errors; unknown integrity errors propagate | Transaction adapter, OpenSpec persistence contract | Adapter unit for fake diagnostics; PostgreSQL integration for real diagnostics |
| Shipment uniqueness is global; Bale-number uniqueness is scoped to a batch; FK deletion is restricted | Migration and DB dictionary | PostgreSQL integration only |
| Persisted statuses are exactly `in_warehouse` and `delivered`; invalid writes report the named CHECK | Migration/OpenSpec | PostgreSQL integration only |
| Mapper round trips preserve domain values and PostgreSQL Decimal/timezone types | Mapper source and migration | Mapper unit; PostgreSQL integration for driver round-trip |
| Request rejects extra fields, empty Bale collections, non-string decimal JSON, invalid/non-finite decimal strings, naive datetime, and malformed shapes | Pydantic HTTP models | HTTP model unit / ASGI contract |
| Request mapping and response mapping preserve names, order, Decimal values, aware datetime, status, and `raw_material_batch_id` | HTTP mapping and response models | HTTP adapter unit and ASGI contract |
| Route hierarchy exposes exactly one POST at `/api/v1/warehouse/bales`, no duplicate or redirect behavior | Router composition and OpenAPI | ASGI/OpenAPI contract |
| HTTP status/error envelope and field paths are stable for validation, domain, duplicate Bale, duplicate shipment, and unexpected errors | Handler/mapping source and route declarations | ASGI contract plus focused handler unit |
| `create_app` uses explicit dependency seams, loads settings once only when needed, composes session/use-case dependencies, and registers handlers | Bootstrap source; runtime-settings OpenSpec | Bootstrap unit/composition tests |
| Settings source precedence, malformed/missing URL failure, secret redaction, and no-connect engine construction | Runtime-settings OpenSpec and configuration source | Unit/composition tests; no live DB |
| Per-request session context closes sessions and the integration guard reads only `TEST_DATABASE_URL` with loopback PostgreSQL restrictions | Bootstrap helper and integration support | Unit for lifecycle/guard; PostgreSQL suite for guarded behavior |
| Domain/application/ports do not import HTTP, ORM, settings, environment, or deployment details | Architecture docs and current imports | Small architecture/import tests |
| PostgreSQL RLS, zero policies, role ACL revocation, FK action, CHECK diagnostics, timezone and Decimal behavior | Applied migration and DB dictionary | PostgreSQL integration only; never SQLite |

This inventory is a current behavior specification. It is **not** a resurrection of the deleted suite or of any prior refactor's test structure.

## Proposed Test Taxonomy and Architecture

Use stdlib `unittest`. There is no evidence that introducing pytest, a linter, type checker, coverage package, or another framework is required. Adding such tooling is a separate scope decision, not an implicit consequence of rebuilding tests.

### Canonical unit/contract package layout

Prefer cohesive feature files over a mirror of every production directory:

```text
backend/tests/
├── test_warehouse_bales/
│   ├── __init__.py
│   ├── test_domain.py              # value objects, RawMaterialBatch, Bale
│   ├── test_application.py         # command/use case/result/errors
│   ├── test_http.py                # models, mappings, handlers, router contract
│   ├── test_persistence.py         # records, mappers, repositories, fake diagnostics
│   └── test_identity.py            # UUID adapter, if still warranted as a unit
├── test_infra/
│   ├── __init__.py
│   ├── test_configuration.py
│   └── test_persistence.py         # engine/session factory, no-connect seams
├── test_bootstrap/
│   ├── __init__.py
│   ├── test_application.py         # create_app composition and OpenAPI
│   ├── test_dependencies.py        # session/use-case lifecycle
│   └── test_error_handlers.py
└── test_architecture.py             # narrowly scoped dependency rules
```

Keep PostgreSQL-only proof in the existing separate namespace:

```text
backend/integration_tests/
├── database_test_support.py
├── test_warehouse_schema.py
├── test_warehouse_transaction.py
└── test_warehouse_registration.py
```

The exact filenames may be refined in proposal/design, but the rule is stable: organize by discoverable capability and contract, not by mechanically reproducing every `src` folder.

### Pyramid

1. **Domain/application unit base (largest):** fast, deterministic, framework-free tests using explicit fakes and builders.
2. **Adapter contract tests:** HTTP models/mappings, persistence mappers/repositories, settings and bootstrap seams; use SQLite only for behavior that is genuinely dialect-independent.
3. **ASGI contract tests:** build `create_app` with an injected session factory or fake use case; prove route, OpenAPI, response, validation, and error mapping without network or production DB.
4. **PostgreSQL integration (small, high-value):** migration metadata, RLS/ACL, FK action, named constraints/diagnostics, timezone and Decimal round trips, transaction rollback, and real end-to-end registration.

### Fixtures/builders and determinism

- Use small explicit builders such as `received_bale_command()`, `register_batch_command()`, and `raw_material_batch_record()` with keyword overrides.
- Defaults must be valid, readable, and deterministic; use constants for semantic values (`DEFAULT_MATERIAL_TYPE`, `DEFAULT_STATUS`) rather than accidental legacy names.
- Generate UUIDs through an injected deterministic identity fake in unit tests; integration tests should assert UUID shape/relationships, not patch `uuid4` call order.
- Use fixed timezone-aware datetimes only when the test is about exact time preservation; otherwise use a named deterministic fixture. Never use `datetime.now()` in assertions.
- Use `Decimal("...")` strings for exact values and explicitly test scale/round-trip where relevant.
- Never embed credentials, real URLs, production IDs, developer dotenv values, or old `reception_*` terminology in canonical tests. The only integration URL source is `TEST_DATABASE_URL`, with the existing loopback/port/database guards.
- Reset/cleanup must be isolated and deterministic. Unit tests own their fakes; ASGI tests inject dependencies; PostgreSQL tests use guarded disposable local data and cleanup that cannot target production.

### Architecture tests worth having

Keep architecture tests few and semantic:

- Import the domain and application packages in an environment where FastAPI/SQLAlchemy are not required by those layers, or inspect their import graph with a narrow allow/deny rule.
- Assert domain/application modules do not import `fastapi`, `sqlalchemy`, `pydantic`, `pydantic_settings`, `os.environ`, or deployment modules.
- Assert bootstrap is the composition owner and HTTP routes reach the application use case rather than repositories directly.
- Assert each route is registered once and OpenAPI contains the canonical path once.

Avoid brittle source-inspection tests for exact line text, private helper names, folder symmetry, import ordering, implementation call counts, or internal SQLAlchemy details that the public contract does not require. Prefer runtime behavior and public symbols.

## Remaining Integration-Test Audit

| File | Classification | Rationale and required treatment |
|---|---|---|
| `backend/integration_tests/database_test_support.py` | **Keep with minor rewrite** | The fail-fast `TEST_DATABASE_URL` guard is aligned with current runtime settings and correctly rejects non-PostgreSQL, non-loopback, wrong-port, and wrong-database targets without falling back to `DATABASE_URL`. Retain this safety boundary; rename no business concepts, and make cleanup/documentation explicit about disposable local PostgreSQL only. |
| `backend/integration_tests/test_migrated_warehouse_schema.py` | **Rewrite, retain as PostgreSQL contract** | It covers useful physical metadata, status CHECK diagnostics, RLS/policy state, and ACL absence. Rewrite names/builders around batch/Bale, avoid relying on the migration filename, use isolated deterministic rows, and keep all PostgreSQL catalog/diagnostic assertions here. Add explicit FK `ON DELETE RESTRICT` and exact named-key/index coverage if not already represented. |
| `backend/integration_tests/test_warehouse_transaction.py` | **Rewrite, retain as PostgreSQL transaction contract** | Rollback and composite Bale conflict evidence is valuable, but the file uses obsolete local `reception_id` terminology and does not cover shipment conflict or unknown integrity propagation. Replace helper names, add batch-first atomicity, both named diagnostics, unknown errors, and cleanup/isolation checks. |
| `backend/integration_tests/test_register_bale_reception.py` | **Rewrite, retain as PostgreSQL end-to-end contract** | It proves persistence, timezone and Decimal round trips, and duplicate shipment rollback, but uses obsolete reception locals and patches UUID generation by call order. Rebuild around `RegisterRawMaterialBatch`, injected deterministic identity only where needed, and add duplicate Bale, cross-batch Bale-number reuse, complete response/result relationships, and rollback invariants. |
| `backend/integration_tests/__init__.py` | **Keep if discovery requires it** | Package marker only; no business behavior. Preserve only if it remains useful for module discovery/import stability. |
| `backend/integration_tests/__pycache__/` and `.pyc` files | **Delete as housekeeping only** | Generated residue, not test evidence. Remove only in an explicitly authorized cleanup step, never as part of test design or production changes. |

No remaining integration test is accepted as automatically correct. Each must pass against the current migration, ORM records, mappers, transaction adapter, and runtime settings after rewrite.

## HTTP, OpenAPI, and Startup Contract Plan

- Build an ASGI app with a fake/injected session factory and a fake or real application seam; do not instantiate `backend.main` in unit tests because it intentionally requires runtime `DATABASE_URL` at import time.
- Assert one `POST /api/v1/warehouse/bales`, 201 success, no slash redirect, canonical response fields, Decimal JSON representation, aware datetime, and OpenAPI request/response/error declarations.
- Exercise malformed shape, extra field, empty Bales, non-string/invalid/infinite decimal, naive datetime, domain errors, duplicate Bale, duplicate shipment, and unexpected error mapping. Assert status, envelope code/message, and field paths without coupling to logger implementation.
- Test `create_app` injection matrix: explicit session factory bypasses settings/engine, explicit engine bypasses settings, explicit settings are honored, default composition loads once, and the session dependency closes the session after generation.
- Test `backend/main.py` only through a controlled import/composition seam if needed; do not read developer secrets and do not launch a server.

## Production-Change Policy Recommendation

Production code and migrations should be **strictly forbidden during this SDD exploration and normal test-suite implementation**. A test may expose a verified production defect, but that defect must stop the current slice, be documented with a minimal reproduction against an authoritative contract, and require explicit user approval for a separate production fix (or an explicitly approved follow-up slice). Do not weaken or rewrite tests to fit accidental behavior, and do not silently fix production code while rebuilding coverage.

## Workload Forecast and Chained Delivery

The rebuild is high-risk for review size and should use autonomous stacked slices. Forecast **6 slices**, each independently green and below 399 changed lines:

1. **Domain/application core contracts** — builders, value objects/entities, command/result, use-case fakes and error/atomicity behavior. No framework or DB.
2. **Persistence adapter contracts** — records, mappers, repositories, transaction adapter fake-diagnostic tests, SQLite only where dialect-neutral.
3. **HTTP and error contracts** — request/response models, mapping, handlers, router and OpenAPI/ASGI tests with injected seams.
4. **Infrastructure/bootstrap/settings** — configuration, engine/session, session lifecycle, composition and ASGI startup tests; no dependency or manifest changes.
5. **PostgreSQL schema/security/transaction proof** — rewritten schema and transaction integration tests, guarded local target, exact constraints/RLS/ACL/diagnostics/time/Decimal checks.
6. **PostgreSQL registration and suite hardening** — rewritten end-to-end registration integration, isolation/determinism review, discovery documentation and final green checkpoint.

Each slice should include its tests, fixtures/builders, and verification for the behavior it introduces; avoid a giant “tests only” PR. The expected reviewer burden is medium-to-high because the suite is a new specification, but stacked slices keep each diff focused. The 400-line guard is **High risk for the overall change, Low-to-medium per slice if enforced during task planning**.

**Decision needed before apply: Yes**  
**Chained PRs recommended: Yes**  
**400-line budget risk: High**

## Proposal Questions Requiring Confirmation

1. Confirm that the remaining three substantive integration tests should be **rewritten and retained as candidates**, rather than deleted, while preserving their PostgreSQL-only responsibilities.
2. Confirm whether adding a coverage tool or changing test framework is in scope. Recommendation: **no**; retain stdlib `unittest` and existing commands first.
3. Confirm that production code and migrations remain forbidden unless a separately approved, contract-backed defect is demonstrated.
4. Confirm whether generated `__pycache__`/`.pyc` cleanup is a separate housekeeping action, not part of the suite rebuild.
5. Confirm that the six-slice stacked-to-main delivery forecast is acceptable before proposal/design/tasks are created.

## Recommendation

Proceed to proposal only after the user confirms the questions above. The proposal should explicitly state that the suite is rebuilt from current behavior contracts, that deleted tests are not restored or mined for requirements, that SQLite is not evidence for PostgreSQL claims, and that every slice has a green checkpoint, deterministic fixtures, no network, no production database, and no unapproved production changes.

## Risks

- The absence of the old unit tree means the new suite can reveal uncharacterized behavior; this is expected discovery, not a reason to restore legacy assertions.
- The migration filename is historical while its contents are current; tests must target physical contracts, not filename vocabulary.
- PostgreSQL diagnostics, RLS/ACL, FK actions, timezone behavior, and Decimal round trips cannot be substituted with SQLite.
- `backend.main` loads settings at import time; careless test imports can require ambient credentials or connect unexpectedly.
- Hardcoded UUID call-order patches, timestamps, credentials, and old reception terminology can reintroduce fragile or misleading tests.
- A broad rebuild can exceed the review budget unless slices remain autonomous and tests stay with the behavior they specify.

## Ready for Proposal

**Yes, conditionally.** The code and authoritative contract inventory is sufficient for a proposal. The orchestrator should obtain confirmation on integration-test retention, framework/coverage scope, production-change policy, cache cleanup scope, and the six-slice stacked delivery plan before advancing.
