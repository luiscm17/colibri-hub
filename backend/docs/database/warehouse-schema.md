---
document_type: technical-spec
status: active
implementation: implemented
scope: backend/database/warehouse
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Warehouse Schema

This document describes the implemented warehouse raw-material storage schema. It explains the structure, constraints, and design decisions behind the tables without duplicating the full migration SQL.

## Authority

The Supabase migration `20260722130455_create_raw_material_reception_storage.sql` is the **physical authority** for table definitions, columns, constraints, RLS configuration, and privilege grants. This document is explanatory — it provides context and rationale for the schema but cannot override or retroactively change applied migration behavior. Future schema changes require a new migration.

## Tables

### `raw_material_batches`

Header table representing a raw-material shipment grouping identified by its `shipment_number`.

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `uuid` | NOT NULL | Technical primary key |
| `received_at` | `timestamptz` | NOT NULL | Timestamp of the batch receiving action |
| `shipment_number` | `varchar(10)` | NOT NULL | Business-visible shipment identifier, globally unique |
| `provider_name` | `text` | NOT NULL | Provider evidence for the batch |

No columns have database defaults. All values must be supplied at insert time.

### `raw_material_bales`

Detail table representing each independently identified bale within a batch.

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `uuid` | NOT NULL | Independent technical primary key |
| `raw_material_batch_id` | `uuid` | NOT NULL | Foreign key to the batch header |
| `bale_number` | `varchar(10)` | NOT NULL | Business-visible bale number, unique within batch |
| `material_type` | `varchar(20)` | NOT NULL | Raw-material classification |
| `dtex` | `numeric` | NOT NULL | Linear-density value |
| `gross_weight_kg` | `numeric` | NOT NULL | Gross bale weight |
| `container_weight_kg` | `numeric` | NOT NULL | Container/tare weight |
| `status` | `varchar(40)` | NOT NULL | Bale lifecycle condition (`in_warehouse` or `delivered`) |

## Constraints

| Name | Table | Type | Details |
| --- | --- | --- | --- |
| `pk_raw_material_batches` | `raw_material_batches` | PRIMARY KEY | `(id)` |
| `uq_raw_material_batches_shipment_number` | `raw_material_batches` | UNIQUE | `(shipment_number)` — global uniqueness |
| `pk_raw_material_bales` | `raw_material_bales` | PRIMARY KEY | `(id)` |
| `fk_raw_material_bales_raw_material_batch_id` | `raw_material_bales` | FOREIGN KEY | `(raw_material_batch_id)` → `raw_material_batches(id)` ON DELETE RESTRICT |
| `uq_raw_material_bales_raw_material_batch_bale_number` | `raw_material_bales` | UNIQUE | `(raw_material_batch_id, bale_number)` — uniqueness within batch |
| `ck_raw_material_bales_status` | `raw_material_bales` | CHECK | `status IN ('in_warehouse', 'delivered')` |

## Indexes

| Name | Table | Column(s) |
| --- | --- | --- |
| `ix_raw_material_bales_raw_material_batch_id` | `raw_material_bales` | `(raw_material_batch_id)` |

This index supports the foreign key lookup. The unique constraints also create implicit indexes on their respective columns.

## Security

- Row Level Security (RLS) is enabled on both tables.
- No RLS policies are defined by the current migration.
- All privileges are revoked from `anon`, `authenticated`, and `service_role`.

Application access is managed outside these tables' privilege grants. The backend uses a privileged connection that bypasses RLS.

## Design Decisions

### Header/Detail Pattern

The schema uses a normalized header/detail structure (`raw_material_batches` → `raw_material_bales`). This is a persistence decision — table and record names do not imply same-named domain aggregates. The domain model maps `RawMaterialBatch` to the header and `Bale` to each detail row.

### Bale Identity

For business users, bale identity is the composite of `shipment_number` + `bale_number`. The same canonical bale number is valid in different batches. The `id` column remains the independent technical identity for referential integrity.

### Status Lifecycle

The bale `status` column permits only two values: `in_warehouse` and `delivered`. The transition is `in_warehouse → delivered`. In practice, delivered means delivered and used by Production. Repeat delivery is rejected at the application layer. The `delivered_at` column (business date) should be added in a future migration.

### ON DELETE RESTRICT

The foreign key uses `RESTRICT` to prevent orphaning bale detail rows. A batch cannot be deleted while it has associated bales.

## Domain Mapping

| Domain Concept | Physical Representation |
| --- | --- |
| `RawMaterialBatch` | `raw_material_batches` header row |
| `Bale` | `raw_material_bales` detail row |
| `ShipmentNumber` | `raw_material_batches.shipment_number` |
| Batch-to-Bale reference | `raw_material_bales.raw_material_batch_id` FK |

## Related Resources

- Migration: `supabase/migrations/20260722130455_create_raw_material_reception_storage.sql`
- API endpoint: `POST /api/v1/warehouse/bales` (registers a batch with bales in one transaction)
- Domain model: `warehouse.bales.domain`
