# Warehouse Database Dictionary

This Markdown dictionary explains the Warehouse raw-material storage currently
implemented by the Supabase migration. It is design detail below the migration,
which remains authoritative for physical tables, columns, constraints, RLS, and
privileges. The DBML and dbdiagram files are not authority for this implemented
slice and are intentionally unchanged by this alignment.

## Conceptual Mapping

| Domain concept | Implemented physical representation | Meaning |
|---|---|---|
| `RawMaterialBatch` | `raw_material_receptions` header row | Raw-material shipment grouping identified for the business by `shipment_number`; it is not a production lot. |
| `Bale` | `raw_material_bales` detail row | Independently identified raw-material unit and owner of its custody lifecycle. |
| Batch-to-Bale reference | `raw_material_bales.reception_id` | Historical persistence name that links detail to header; it does not create a `Reception` aggregate. |

The normalized header/detail shape is a persistence decision. Table and record
names do not require same-named domain aggregates.

## `raw_material_receptions`

Historical physical header for one `RawMaterialBatch`.

| Column | Current meaning |
|---|---|
| `id` | Technical UUID primary key used by persistence. |
| `received_at` | Timestamp recorded for the batch receiving action. |
| `shipment_number` | Business-visible `ShipmentNumber`; required and globally unique through `uq_raw_material_receptions_shipment_number`. |
| `provider_name` | Shared provider evidence for the batch. |

The domain calls this grouping `RawMaterialBatch`; retaining the physical
`raw_material_receptions` name is compatibility, not domain authority.

## `raw_material_bales`

Physical detail for each `Bale` in the batch.

| Column | Current meaning |
|---|---|
| `id` | Independent technical UUID primary key for the Bale record. |
| `reception_id` | Foreign key to the persisted batch header, with delete restricted. |
| `bale_number` | Business-visible Bale number, unique only within the referenced batch/header. |
| `material_type` | Recorded raw-material classification. |
| `dtex` | Recorded linear-density value. |
| `gross_weight_kg` | Recorded gross Bale weight. |
| `container_weight_kg` | Recorded container/tare weight. |
| `status` | Persisted Bale lifecycle condition. The approved target states are `IN_WAREHOUSE` and `IN_PRODUCTION`. |

`uq_raw_material_bales_reception_bale_number` enforces uniqueness of
`bale_number` within the persisted batch/reception. The same canonical Bale
number may occur in a different batch. For business users, Bale identity is
`shipment_number` + `bale_number`; `id` remains its independent technical identity.

## Registration And Delivery

The current public registration contract remains
`POST /api/v1/warehouse/bales`. It registers one complete `RawMaterialBatch`
with one or more Bales in one transaction, preserving existing payload and
response names during P0. The migration's header/detail names do not redefine
that application action as a domain aggregate.

The approved target Bale transition is `IN_WAREHOUSE -> IN_PRODUCTION`.
Delivery is the fact; `IN_PRODUCTION` is the resulting custody/location and does
not mean consumed or processed. Current mandatory delivery evidence is
`delivered_at`, and repeat delivery must be rejected. The migration does not yet
contain that column or its future constraint, and this documentation change does
not alter the schema. Delivery actors are not mandatory current evidence.

## Security And Historical Behavior

The existing migration remains unchanged:

- RLS is enabled on both tables.
- No RLS policies are defined by this migration.
- All privileges are revoked from `anon`, `authenticated`, and `service_role`.
- Primary keys, foreign key, unique constraints, index, names, and types remain as migrated.

Future schema changes require a new migration. This dictionary cannot override
or retroactively change applied migration behavior.
