# Warehouse Domain Map

Warehouse owns physical custody and documentary control for raw-material bales,
finished product, and production supplies. It also defines the single production
identity used across Warehouse and Lot Processing.

## Authority

- Owns raw-material bale custody, whole-bale delivery to Production, production
  identity definition, finished-product acceptance, availability, physical
  presentation, stock movements, supplies, and corrections of Warehouse records.
- Defines the technical `production_identity_id` and visible `lot_code` before
  production. `yarn_count` is the canonical shared reference used in that
  definition.
- Consumes Lot Processing's Quality Send, quality state, delivery conditions,
  and route-sheet facts as upstream context. It does not own or snapshot quality.
- Access Control decides who may act under policy; business responsibilities do
  not define system permissions.

## Responsibility

Warehouse maintains current business truth for its records and preserves an
auditable correction history. Corrections are controlled by policy and retain
the actor, system time, reason, authorization basis when relevant, and before/
after values. They are not modeled as a blanket append-only prohibition.

Warehouse stock is a custody quantity, distinct from `availability_state`, which
expresses readiness for release or distribution.

## Core Concepts

| Concept | Warehouse meaning |
|---|---|
| RawMaterialBatch | A supplier-shipment grouping identified by `ShipmentNumber`, containing one or more bales and shared evidence/characteristics. It is not a production lot. |
| Bale | An independently identified raw-material unit and lifecycle owner. Its business-visible identity is `shipment_number` + `bale_number`. |
| Production identity | The Warehouse-defined cross-context identity, represented by `production_identity_id` and `lot_code`. |
| Finished product receipt | The single Warehouse acceptance of a production identity after its Quality Send. |
| `availability_state` | Warehouse's operational disposition of accepted finished product. It is not quality or stock. |
| `physical_presentation` | The physical form Warehouse receives or stores, kept separate from quality and availability. |
| Supply | A Warehouse-managed production input with its own receipt, delivery, and stock history. |

## Business Flows

1. **Raw-material custody:** The receiving application action registers one
   complete `RawMaterialBatch` and one or more independently identified `Bale`
    aggregates in one transaction. Reception is not a domain aggregate. A bale
    can be delivered once, whole and only to Production. Delivery moves the bale
    from `IN_WAREHOUSE` to `DELIVERED`; that resulting custody condition does not
    mean consumed or processed. This
   delivery never links the bale to a `production_identity_id` or `lot_code`.
2. **Production identity:** Separately from bale reception, Warehouse defines
   one `production_identity_id` and `lot_code` with the requested `yarn_count`
   and production requirements. Yarn Spinning and Lot Processing use that
   identity as shared context; Lot Processing appends the operational stage
   history.
3. **Finished-product handoff:** One Quality Send places the identity pending
   Warehouse validation. Warehouse verifies the existing route-sheet facts and
   accepts the finished product once. It records acceptance, differences, and
   `physical_presentation`; it does not recapture Operational weight, bag count,
   unit count, or quality state.
4. **Finished-product lifecycle:** After acceptance, Warehouse manages
   `availability_state`, physical presentation, delivery by direct sale or
   Commercialization transfer, and returns that reference the original delivery.
5. **Supplies:** Warehouse receives supplies, delivers them to Production, and
   records returns to suppliers. Supplier, destination, and category remain
   labels until a justified catalog is needed.

## Boundaries And Non-Goals

- Warehouse does not own Yarn Spinning production records, lot-stage history,
  process quality, final lot quality, or production waste.
- A cross-context traceability view may show the full journey, but each context
  writes only its own records.
- Quality state, `availability_state`, and `physical_presentation` are separate
  dimensions. Warehouse reads quality as context and does not persist a quality
  snapshot.
- Shared Reference Data owns the minimal `yarn_counts` catalog. Warehouse does
  not introduce supplier, destination, or category catalogs without evidence.
- This map does not prescribe tables, field dictionaries, APIs, identifier
  formats, or authorization assignments.
- Persistence maps `RawMaterialBatch` and `Bale` through canonical batch/bale
  names without defining the aggregate shape.

## Vocabulary

| Term | Meaning in this map |
|---|---|
| `yarn_count` | Canonical yarn count used when defining production identity. |
| `ShipmentNumber` | Business-visible identity of a `RawMaterialBatch`; transported as `shipment_number`. |
| `production_identity_id` | Warehouse-owned technical identity shared across the production flow. |
| `lot_code` | Visible business code for the same production identity. |
| `availability_state` | Warehouse operational readiness for release or distribution. |
| `physical_presentation` | Physical finished-product form under Warehouse handling. |

## Sources

- [Warehouse PRD](../prd/warehouse.md)
- [Warehouse functional records](../prd/warehouse/warehouse-records.md)
- [Context boundaries and ownership](../architecture/context-boundaries-and-ownership.md)
- [Ubiquitous Language](ubiquitous-language.md)
- [Warehouse DBML](../db/warehouse.dbml) and [dictionary](../db/warehouse-dictionary.md)
- [Persistence decisions](../architecture/backend/persistence-decisions.md)
