# Backend Test Suite Specification

## Purpose

Define fresh, deterministic `unittest` evidence for current `warehouse.bales` contracts without recreating legacy behavior.

## Requirements

### Requirement: Authority and Freshness
Technical input MUST follow current runtime, PRD, architecture/domain, migration, OpenSpec, then project guides. It MUST NOT include deleted-test contents or assertions from Git/history, `.kiro`, failed-refactor artifacts/memories, or obsolete terminology. Current integration assertions are rewrite candidates, not authority, and MUST be rewritten from current contracts.

#### Scenario: Legacy or current-test conflict
- GIVEN a legacy or retained integration assertion conflicts with current authority
- WHEN a fresh contract is selected
- THEN the authority governs and the assertion is excluded or rewritten

### Requirement: Deterministic Test Taxonomy
The suite MUST use stdlib `unittest` unit, adapter/ASGI, bootstrap, and guarded integration locations. Fixtures MUST use semantic names, stable UUIDs, aware times, `Decimal` literals, and no secrets, network, implementation coupling, or accidental hardcoding.

#### Scenario: Isolated unit discovery
- GIVEN deterministic unit discovery without infrastructure configuration
- WHEN a fixture is exercised
- THEN it requires no network or live database

### Requirement: Domain and Registration Contracts
Tests MUST prove value normalization/validation, identity equality, valid Bale transition, and RawMaterialBatch provider trimming, nonempty unique Bale IDs, and batch-ID equality. Registration MUST require Bales, canonicalize numbers, persist batch before Bales, commit atomically, map known conflicts, and propagate unknown integrity errors.

#### Scenario: Invalid domain or registration input
- GIVEN invalid aggregate state or canonical duplicate Bale numbers
- WHEN construction, delivery, or registration occurs
- THEN the applicable domain or mapped application error is raised

### Requirement: Boundary and Persistence Units
Tests MUST verify observable port contracts, field preservation, ordering, rollback, and named-conflict diagnostics. SQLite MAY prove dialect-neutral mapping/session behavior and MUST NOT prove PostgreSQL diagnostics, RLS, FK actions, timezone, Decimal, or constraints.

#### Scenario: Unknown integrity failure
- GIVEN an unnamed integrity failure during a transaction
- WHEN it commits or exits
- THEN it rolls back and propagates the failure

### Requirement: HTTP and OpenAPI
Injected ASGI tests MUST prove only `POST /api/v1/warehouse/bales`, without a trailing-slash duplicate, returns `201` with `raw_material_batch_id` and `in_warehouse`. Validation MUST map to `422`; shipment duplicate MUST map to `409`/`duplicate_shipment_number`/`shipment_number`; Bale duplicate MUST map to `422`/`duplicate_bale_number`/`bales[].bale_number`; unexpected errors MUST map to `500`. OpenAPI MUST document these responses.

#### Scenario: HTTP errors
- GIVEN validation, shipment duplicate, Bale duplicate, or unexpected use-case failure
- WHEN the exact route receives a request
- THEN it returns the corresponding documented `422`, `409`, `422`, or `500` envelope

### Requirement: Configuration and Bootstrap
Tests MUST prove settings precedence, `SecretStr` redaction, dotenv isolation, lazy engine creation, request-scoped sessions, composition, and injected seams that bypass environment and database access.

#### Scenario: Injected application
- GIVEN an injected session factory
- WHEN the application is created
- THEN settings and engine construction are bypassed

### Requirement: Guarded PostgreSQL Evidence
Integration tests MUST require only allowlisted loopback `TEST_DATABASE_URL` and MUST NOT fall back to `DATABASE_URL`; every scenario MUST isolate state. Slice 5 MUST own URL guard/support, exact schema, named constraints/index/FK, RLS zero-policy/revoked-role security, and aware-time/`Decimal` round trips. Slice 6 MUST own real transaction diagnostics, unknown-failure propagation, rollback, atomic registration, duplicate behavior, and isolation hardening.

#### Scenario: PostgreSQL ownership and safety
- GIVEN Slice 5 or 6 runs against an absent or unsafe target
- WHEN integration setup begins
- THEN it fails before connection or mutation; otherwise each slice proves only its assigned contracts

### Requirement: Evidence-Backed Production Fixes
The suite MUST cover validation, conflicts, unknown failures, rollback, and isolation. A fix MAY enter its proving slice only after fresh authority evidence proves a defect; it MUST be minimal and documented. If it risks the 399-line limit, work MUST stop and trigger re-slicing before proceeding; broader behavior MUST require an explicit scope decision.

#### Scenario: Oversized or broader fix
- GIVEN a proven minimal fix threatens the limit or expands behavior
- WHEN it is assessed
- THEN re-slicing occurs before continuation or scope is explicitly decided

### Requirement: Delivery and Completion
`5730050` is the approved deletion-only `size:exception` prerequisite, outside the six fresh slices and not green evidence. Slice 1 MUST measure from `5730050`; each later slice MUST measure from its immediate accepted parent. The 399-line maximum applies to each fresh slice diff, never cumulative history. Six stacked-to-`main` slices MUST be independently green: domain/application, persistence, HTTP, bootstrap, PostgreSQL schema/security/types/support, then PostgreSQL transactions/registration/hardening. The work MUST NOT add tooling, frontend/product behavior, or compatibility resurrection; staging, commits, and PRs MUST NOT be automatic.

#### Scenario: Slice acceptance
- GIVEN a fresh slice exceeds 399 changed lines, has the wrong parent, or is not green
- WHEN it is reviewed
- THEN it is not accepted or advanced
