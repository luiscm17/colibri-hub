---
document_type: domain
status: active
implementation: partial
scope: warehouse
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

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
| --- | --- |
| RawMaterialBatch | A supplier-shipment grouping identified by `shipment_number`, containing one or more bales and shared evidence/characteristics. It is not a production lot. |
| Bale | An independently identified raw-material unit and lifecycle owner. Its business-visible identity is `shipment_number` + `bale_number`. Attributes include `material_type`, `dtex`, `gross_weight_kg`, and `container_weight_kg`. Net weight is always derived. |
| Reception | The business act (application action) of registering one complete raw-material batch and its bales. It is not a domain aggregate or entity. |
| Delivery | A custody transfer — the physical handoff of a whole bale from Warehouse to Production. It does not assert consumption, processing, or assignment to a production identity. |
| Production identity | The Warehouse-defined cross-context identity, represented by `production_identity_id` and `lot_code`. |
| Finished product receipt | The single Warehouse acceptance of a production identity after its Quality Send. |
| `availability_state` | Warehouse's operational disposition of accepted finished product. It is not quality or stock. |
| `physical_presentation` | The physical form Warehouse receives or stores, kept separate from quality and availability. |
| Supply | A Warehouse-managed production input with its own receipt, delivery, and stock history. |

## Bale Lifecycle States

Bales follow a simple, one-directional lifecycle:

| State | Canonical value | Meaning |
| --- | --- | --- |
| In Warehouse | `in_warehouse` | Bale is under Warehouse custody |
| Delivered | `delivered` | Bale has been physically transferred to Production |

**Transition:** `in_warehouse → delivered` (one-way).

- A newly received bale always starts in `in_warehouse`.
- The only permitted transition is `in_warehouse → delivered`.
- In the current scope, delivery is irreversible — no reversal mechanism exists.
- Future controlled reversal (correction) may be introduced under Warehouse's
  general correction policy (audited, authorized, reason documented).

## Reception

Reception is the business act of registering a supplier shipment into Warehouse
custody. Key domain characteristics:

- Registers exactly one `RawMaterialBatch` and one or more `Bale` records.
- The entire operation is atomic — all or nothing.
- `received_at` is a **business date** (calendar date of physical reception),
  not a system timestamp.
- All bales start with status `in_warehouse`.
- Adding bales after initial registration is not part of the current flow.

For complete reception rules and acceptance criteria, see the
[Bale Management PRD](../prd/warehouse/bale-management.md) §7.

## Delivery

Delivery is the custody transfer of a whole bale from Warehouse to Production.

- A bale is always delivered whole — partial delivery is not supported.
- Delivery is a custody change only. It does **not** mean:
  - The bale has been consumed or processed.
  - The bale has been assigned to a production identity or lot.
- Delivery does not link the bale to any `production_identity_id` or `lot_code`.
- What Production does with the bale after delivery is outside Warehouse scope.

For complete delivery rules and acceptance criteria, see the
[Bale Management PRD](../prd/warehouse/bale-management.md) §9.

## Business Flows

1. **Raw-material custody:** The receiving action registers one complete
   `RawMaterialBatch` and one or more independently identified `Bale` records
   in one transaction. A bale can be delivered once, whole and only to
   Production. Delivery moves the bale from `in_warehouse` to `delivered`;
   that custody condition does not mean consumed or processed. Delivery never
   links the bale to a `production_identity_id` or `lot_code`.
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

## Boundaries and Non-Goals

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

## Vocabulary

| Term | Meaning in this map |
| --- | --- |
| `shipment_number` | Business-visible identity of a `RawMaterialBatch`; globally unique. |
| `bale_number` | Bale identifier within a batch; unique within its parent batch only. |
| `received_at` | Business date (calendar date) of physical reception. |
| `material_type` | Raw-material classification; normalized to uppercase. |
| `dtex` | Linear density of the raw material. |
| `gross_weight_kg` | Gross weight of a bale in kilograms. |
| `container_weight_kg` | Tare/container weight in kilograms. |
| `net_weight_kg` | Derived net weight (gross minus tare); never persisted. |
| `yarn_count` | Canonical yarn count used when defining production identity. |
| `production_identity_id` | Warehouse-owned technical identity shared across the production flow. |
| `lot_code` | Visible business code for the same production identity. |
| `availability_state` | Warehouse operational readiness for release or distribution. |
| `physical_presentation` | Physical finished-product form under Warehouse handling. |

## Sources

- [Bale Management PRD](../prd/warehouse/bale-management.md) — normative source for bale business rules
- [Warehouse Area PRD](../prd/warehouse.md) — area-level scope and subdomain overview
- [Ubiquitous Language](ubiquitous-language.md) — canonical naming contract
- [Context Map](../architecture/context-map.md) — context ownership and boundaries
