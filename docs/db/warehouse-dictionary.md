# Warehouse Database Dictionary

This Markdown dictionary explains the Warehouse raw-material storage currently
implemented by the Supabase migration. It is design detail below the migration,
which remains authoritative for physical tables, columns, constraints, RLS, and
privileges. The DBML and dbdiagram files are not authority for this implemented
slice and are intentionally unchanged by this alignment.

## Conceptual Mapping

| Domain concept | Implemented physical representation | Meaning |
|---|---|---|
| `RawMaterialBatch` | `raw_material_batches` header row | Raw-material shipment grouping identified for the business by `shipment_number`; it is not a production lot. |
| `Bale` | `raw_material_bales` detail row | Independently identified raw-material unit and owner of its custody lifecycle. |
| Batch-to-Bale reference | `raw_material_bales.raw_material_batch_id` | Named foreign key that links detail to header; it does not create a `Reception` aggregate. |

The normalized header/detail shape is a persistence decision. Table and record
names do not require same-named domain aggregates.

## `raw_material_batches`

Physical header for one `RawMaterialBatch`.

| Column | Current meaning |
|---|---|
| `id` | Technical UUID primary key named `pk_raw_material_batches`. |
| `received_at` | Timestamp recorded for the batch receiving action. |
| `shipment_number` | Business-visible `ShipmentNumber`; required and globally unique through `uq_raw_material_batches_shipment_number`. |
| `provider_name` | Shared provider evidence for the batch. |

All columns are required and have no database default.

## `raw_material_bales`

Physical detail for each `Bale` in the batch.

| Column | Current meaning |
|---|---|
| `id` | Independent technical UUID primary key named `pk_raw_material_bales`. |
| `raw_material_batch_id` | Named `fk_raw_material_bales_raw_material_batch_id` foreign key to the batch header, with `ON DELETE RESTRICT`; indexed by `ix_raw_material_bales_raw_material_batch_id`. |
| `bale_number` | Business-visible Bale number, unique only within the referenced batch/header. |
| `material_type` | Recorded raw-material classification. |
| `dtex` | Recorded linear-density value. |
| `gross_weight_kg` | Recorded gross Bale weight. |
| `container_weight_kg` | Recorded container/tare weight. |
| `status` | Persisted Bale lifecycle condition. `ck_raw_material_bales_status` permits only `in_warehouse` and `delivered`. |

`uq_raw_material_bales_raw_material_batch_bale_number` enforces uniqueness of
`bale_number` within the persisted batch. The same canonical Bale
number may occur in a different batch. For business users, Bale identity is
`shipment_number` + `bale_number`; `id` remains its independent technical identity.

## Registration And Delivery

The current public registration contract remains
`POST /api/v1/warehouse/bales`. It registers one complete `RawMaterialBatch`
with one or more Bales in one transaction, preserving existing payload and
names. Successful responses and OpenAPI expose `raw_material_batch_id`, never
`reception_id`. The migration's header/detail names do not redefine that
application action as a domain aggregate.

The current Bale transition is `IN_WAREHOUSE -> DELIVERED`. Delivery does not
mean consumed or processed, and repeat delivery must be rejected. The current
baseline adds no delivery timestamp or actor.

The frontend reception client remains excluded because it targets a different
endpoint and incompatible payload. A future change must align endpoint, payload,
and response together rather than applying a field-only rename.

## Security And Historical Behavior

The existing migration remains unchanged:

- RLS is enabled on both tables.
- No RLS policies are defined by this migration.
- All privileges are revoked from `anon`, `authenticated`, and `service_role`.
- The named keys and constraints are `pk_raw_material_batches`,
  `pk_raw_material_bales`, `uq_raw_material_batches_shipment_number`,
  `fk_raw_material_bales_raw_material_batch_id`,
  `uq_raw_material_bales_raw_material_batch_bale_number`,
  `ix_raw_material_bales_raw_material_batch_id`, and
  `ck_raw_material_bales_status`.

Future schema changes require a new migration. This dictionary cannot override
or retroactively change applied migration behavior.
