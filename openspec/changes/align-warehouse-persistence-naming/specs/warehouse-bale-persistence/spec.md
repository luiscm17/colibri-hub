# Warehouse Bale Persistence Specification

## Purpose

Define the reset-only Warehouse batch/bale baseline, enforced Bale statuses, and returned batch identifier.

## Requirements

### Requirement: Authorized reset-only baseline

The system MUST replace `20260722130455_create_raw_material_reception_storage.sql` in place. Before reset, an authorized owner MUST attest that each target is disposable, retains no data, and may be deleted/reset; otherwise it MUST be a no-go. The system SHALL add no forward, down, rename, or data-preserving migration.

#### Scenario: Authorized reset applies the baseline
- GIVEN an authorized attestation and an empty disposable database
- WHEN the complete migration set is applied
- THEN only the canonical Warehouse baseline objects are created

#### Scenario: Unattested target is blocked
- GIVEN a target lacks reset authorization or contains retained data
- WHEN deployment is requested
- THEN it is not renamed or reset in place

### Requirement: Canonical physical schema and status constraint

The system MUST expose `public.raw_material_batches` (`id uuid`, `received_at timestamptz`, `shipment_number varchar(10)`, `provider_name text`) and `public.raw_material_bales` (`id uuid`, `raw_material_batch_id uuid`, `bale_number varchar(10)`, `material_type varchar(20)`, `dtex numeric`, `gross_weight_kg numeric`, `container_weight_kg numeric`, `status varchar(40)`). Listed columns MUST be NOT NULL with no database default.

The system MUST use `pk_raw_material_batches`, `pk_raw_material_bales`, `uq_raw_material_batches_shipment_number`, `fk_raw_material_bales_raw_material_batch_id`, `uq_raw_material_bales_raw_material_batch_bale_number`, `ix_raw_material_bales_raw_material_batch_id`, and `ck_raw_material_bales_status`. The CHECK MUST allow exactly `in_warehouse` and `delivered`.

#### Scenario: PostgreSQL metadata matches
- GIVEN the reset baseline
- WHEN PostgreSQL metadata is inspected
- THEN physical names, types, nullability, keys, index, and named CHECK match this requirement

#### Scenario: Obsolete vocabulary is absent
- GIVEN the reset baseline
- WHEN Warehouse metadata is inspected
- THEN `raw_material_receptions` and `reception_id` are absent

### Requirement: Batch-to-Bale integrity and lifecycle enforcement

Each Bale MUST reference one batch through the named `ON DELETE RESTRICT` FK; shipment numbers MUST be globally unique and Bale numbers unique only within a batch. A Batch SHALL group non-empty, duplicate-free Bale IDs; Bales remain independently identified and lifecycle-owned. Registration MUST default a Bale to `in_warehouse`; database and ORM metadata MUST permit only `in_warehouse` or `delivered`. The system MUST reject `in_production` and arbitrary values, and MUST NOT add a state, operation, actor, or timestamp.

#### Scenario: Scoped uniqueness and protected batch
- GIVEN two batches and Bales with the same Bale number
- WHEN the Bales are persisted and a duplicate or referenced-batch deletion is attempted
- THEN cross-batch Bales persist, while the duplicate and deletion are rejected

#### Scenario: Default and accepted statuses
- GIVEN a registration without a status, or a persistence write using an accepted status
- WHEN the Bale is persisted
- THEN registration uses `in_warehouse` and both accepted values succeed

#### Scenario: Rejected status values
- GIVEN a direct persistence write using `in_production` or an arbitrary value
- WHEN PostgreSQL evaluates the row
- THEN it rejects the write through `ck_raw_material_bales_status`

### Requirement: Security posture and adapter alignment

The system MUST enable RLS on both tables, define zero policies, and revoke all privileges from `anon`, `authenticated`, and `service_role`. It MUST NOT add policies, grants, triggers, views, or production-context objects. ORM records, mappers, diagnostics, and repositories MUST align with the schema and named CHECK. Concrete adapters MUST be `TransactionAdapter`, `RawMaterialBatchRepositoryAdapter`, and `BaleRepositoryAdapter`; bootstrap MUST compose them. `Uuid4IdentityGenerator` MAY name its algorithm, but adapter names MUST NOT expose a framework/library.

#### Scenario: Security and ORM inspection
- GIVEN the reset baseline and mapped ORM metadata
- WHEN RLS, policies, ACLs, and CHECK metadata are inspected
- THEN RLS is enabled, policies and role privileges are absent, and the ORM matches the named CHECK

### Requirement: Public contract and verification boundaries

`RegisterRawMaterialBatchResult`, HTTP mapping, runtime response, and OpenAPI for `POST /api/v1/warehouse/bales` MUST expose `raw_material_batch_id`, never `reception_id`; route, validation, status codes, and errors SHALL otherwise remain unchanged. Unit/SQLite tests MUST NOT prove PostgreSQL DDL, RLS, ACLs, FK action, or CHECK diagnostics. PostgreSQL integration/reset verification MUST prove those contracts, accepted values, and rejection of `in_production` and arbitrary values. Cleanup MAY remove only backend `__pycache__` and `.pyc` as separate housekeeping.

#### Scenario: Response hard cutover
- GIVEN a valid registration request
- WHEN the endpoint returns 201 or OpenAPI is inspected
- THEN `raw_material_batch_id` is present and `reception_id` is absent

#### Scenario: PostgreSQL integration proof and safe cleanup
- GIVEN verification runs after an authorized reset and cache residue exists
- WHEN PostgreSQL integration and separate housekeeping run
- THEN PostgreSQL proves the physical/security/status contracts and only permitted cache residue is removed
