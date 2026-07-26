# Warehouse Bales Specification

> **Historical P0 specification.** Its behavior-preservation requirements were
> valid for the capability cutover. Later persistence/API/adapter naming is
> superseded by `../../../align-warehouse-persistence-naming/`; references to
> `reception_id` or unchanged old schema are not current requirements.

## Purpose

Define canonical atomic batch and Bale registration without changing P0 behavior.

## Requirements

### Requirement: Canonical capability ownership

`warehouse.bales` MUST canonically own Bale behavior and be independently discoverable. Core behavior MUST depend inward and work without HTTP, ORM, or database frameworks. After cutover, static checks MUST reject `warehouse.*.raw_material` dependencies.

#### Scenario: Discovery
- GIVEN the capability
- WHEN ownership checks run
- THEN `warehouse.bales` is canonical and framework-free

### Requirement: Batch and Bale identity

`RawMaterialBatch` MUST have opaque stable `RawMaterialBatchId` and immutable globally unique visible `ShipmentNumber`, domain-owned apart from persistence and transport. It MUST own shared attributes and immutable one-to-many Bales, not be a production lot, or use `BaleReceptionId`. Each Bale MUST have `BaleId` and `BaleNumber`, reference batch without `ShipmentNumber`, and resolve visible identity from batch `ShipmentNumber` plus `BaleNumber`.

#### Scenario: Batch identities
- GIVEN a batch with both identities
- WHEN they are inspected
- THEN ID is stable and opaque; ShipmentNumber is immutable and globally unique

#### Scenario: Bale number reuse
- GIVEN two shipment numbers
- WHEN each registers the same BaleNumber
- THEN both identify different Bales

#### Scenario: Association invariant
- GIVEN a constructed batch
- WHEN its Bale membership is changed
- THEN its invariants remain unchanged

### Requirement: Complete atomic registration

`RegisterRawMaterialBatch` MUST atomically register one complete batch with at least one Bale. It MUST reject empty or duplicate BaleNumbers. Persistence failure MUST roll back the header and every Bale.

#### Scenario: Success
- GIVEN valid batch data with unique Bales
- WHEN registration is requested
- THEN all Bales and the batch commit together

#### Scenario: Invalid collection
- GIVEN empty or duplicate BaleNumbers
- WHEN registration is requested
- THEN it is rejected and nothing persists

#### Scenario: Failure
- GIVEN persistence failure after registration
- WHEN the transaction ends
- THEN neither header nor Bales persist

### Requirement: P0 correction boundary

P0 MUST NOT append or correct omitted Bales. Future correction MUST be explicit and audited.

#### Scenario: Omission
- GIVEN a batch is registered
- WHEN an omitted Bale is later submitted
- THEN P0 exposes no append or silent correction workflow

### Requirement: HTTP compatibility

MUST preserve `POST /api/v1/warehouse/bales`, request and collective response fields (including `reception_id`), validation, statuses, errors, slash behavior, and one OpenAPI declaration.

#### Scenario: Existing client
- GIVEN a valid client payload
- WHEN posted there
- THEN its response and status are unchanged, without duplicate route or redirect

### Requirement: Hierarchical route ownership

Route composition MUST assign `/api/v1`, `/warehouse`, and `/bales` distinct owners; Bales MUST own the leaf without duplication.

#### Scenario: Routes
- GIVEN the application
- WHEN routes are inspected
- THEN the hierarchy resolves to one Bales POST endpoint

### Requirement: Transaction and error compatibility

Each request MUST use one session and persist the batch header before Bales. Named shipment and per-batch Bale duplicates MUST retain conflict translation; unknown integrity failures MUST propagate.

#### Scenario: Integrity errors
- GIVEN duplicate and unrelated integrity errors
- WHEN registration is attempted
- THEN only named duplicates map to conflicts; unknown failures propagate

### Requirement: Persistence stability

P0 MUST NOT change schema, migrations, tables, columns, constraints, RLS, or privileges. Reset only verifies it.

#### Scenario: Schema
- GIVEN migrated databases before and after P0
- WHEN schema metadata is compared
- THEN the storage contract is unchanged

### Requirement: Operational compatibility and scope protection

Unit, HTTP, bootstrap, and PostgreSQL integration behavior MUST remain green. Implementations MUST NOT modify protected files.

#### Scenario: Verification
- GIVEN the refactor and protected baseline
- WHEN verification runs
- THEN behavior passes and protected paths are unchanged

### Requirement: P0 exclusions

P0 MUST NOT add delivery, `IN_PRODUCTION`, `delivered_at`, actors, multi-Bale atomicity, corrections, states, API, or schema redesign.

#### Scenario: Exclusion
- GIVEN delivery or lifecycle expansion
- WHEN P0 scope is evaluated
- THEN it is deferred without changing this capability
