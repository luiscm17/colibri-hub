---
document_type: domain
status: active
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
- Defines the production identity and visible lot code before
  production. Yarn count is the canonical shared reference used in that
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

Warehouse stock is a custody quantity, distinct from availability state, which
expresses readiness for release or distribution.

## Core Concepts

| Concept | Warehouse meaning |
| --- | --- |
| Raw-material batch | A supplier-shipment grouping identified by shipment number, containing one or more bales and shared evidence/characteristics. It is not a production lot. |
| Bale | An independently identified raw-material unit and lifecycle owner. Its business-visible identity is shipment number + bale number. Attributes include material type, dtex, gross weight, and container weight. Net weight is always derived. |
| Reception | The business act (application action) of registering one complete raw-material batch and its bales. It is not a domain aggregate or entity. |
| Delivery | The act of delivering a whole bale from Warehouse to Production. In practice, delivered = used — there is no intermediate state. Binary, irreversible. |
| Production identity | The Warehouse-defined cross-context identity, represented by production identity and lot code. |
| Finished product receipt | The single Warehouse acceptance of a production identity after its Quality Send. |
| Availability state | Warehouse's operational disposition of accepted finished product. It is not quality or stock. |
| Physical presentation | The physical form Warehouse receives or stores, kept separate from quality and availability. |
| Supply | A Warehouse-managed production input with its own receipt, delivery, and stock history. |

## Bale Lifecycle States

Bales follow a simple, one-directional lifecycle:

| State | Meaning |
| --- | --- |
| In Warehouse | Bale is under Warehouse custody |
| Delivered | Bale has been physically transferred to Production |

**Transition:** In Warehouse → Delivered (one-way).

- A newly received bale always starts in In Warehouse.
- The only permitted transition is In Warehouse → Delivered.
- Delivery is irreversible — no reversal mechanism exists.
- Controlled reversal (correction) requires a separate capability under Warehouse's
  general correction policy (audited, authorized, reason documented).

## Reception

Reception is the business act of registering a supplier shipment into Warehouse
custody. Key domain characteristics:

- Registers exactly one raw-material batch and one or more bale records.
- The entire operation is atomic — all or nothing.
- The reception date is a **business date** (calendar date of physical reception),
  not a system timestamp.
- All bales start with status In Warehouse.
- Adding bales after initial registration requires a separate correction capability.

For complete reception rules and acceptance criteria, see the
[Bale Management PRD](../prd/warehouse/bale-management.md) §7.

## Delivery

Delivery is the act of handing a whole bale from Warehouse to Production.
In practice, delivery and consumption are the same event — once delivered,
the bale is considered used.

- A bale is always delivered whole — partial delivery is not supported.
- Delivery records the delivery date — a business date entered by the user.
- Delivery does not link the bale to any production identity or lot code.
- No authorization workflow is modeled.

For complete delivery rules and acceptance criteria, see the
[Bale Management PRD](../prd/warehouse/bale-management.md) §9.

## Business Flows

1. **Raw-material custody:** The receiving action registers one complete
   raw-material batch and one or more independently identified bale records
   in one transaction. A bale can be delivered once, whole and only to
   Production. Delivery moves the bale from In Warehouse to Delivered;
   that custody condition means delivered and used by Production. Delivery never
   links the bale to a production identity or lot code.
2. **Production identity:** Separately from bale reception, Warehouse defines
   one production identity and lot code with the requested yarn count
   and production requirements. Yarn Spinning and Lot Processing use that
   identity as shared context; Lot Processing appends the operational stage
   history.
3. **Finished-product handoff:** One Quality Send places the identity pending
   Warehouse validation. Warehouse verifies the existing route-sheet facts and
   accepts the finished product once. It records acceptance, differences, and
   physical presentation; it does not recapture Operational weight, bag count,
   unit count, or quality state.
4. **Finished-product lifecycle:** After acceptance, Warehouse manages
   availability state, physical presentation, delivery by direct sale or
   Commercialization transfer, and returns that reference the original delivery.
5. **Supplies:** Warehouse receives supplies, delivers them to Production, and
   records returns to suppliers. Supplier, destination, and category remain
   labels until a justified catalog is needed.

## Boundaries and Non-Goals

- Warehouse does not own Yarn Spinning production records, lot-stage history,
  process quality, final lot quality, or production waste.
- A cross-context traceability view may show the full journey, but each context
  writes only its own records.
- Quality state, availability state, and physical presentation are separate
  dimensions. Warehouse reads quality as context and does not persist a quality
  snapshot.
- Shared Reference Data owns the minimal yarn counts catalog. Warehouse does
  not introduce supplier, destination, or category catalogs without evidence.
- This map does not prescribe tables, field dictionaries, APIs, identifier
  formats, or authorization assignments.

## Vocabulary

| Term | Meaning in this map |
| --- | --- |
| shipment number | Business-visible identity of a raw-material batch; globally unique. |
| bale number | Bale identifier within a batch; unique within its parent batch only. |
| reception date | Business date (calendar date) of physical reception. |
| material type | Raw-material classification; normalized to uppercase. |
| dtex | Linear density of the raw material. |
| gross weight | Gross weight of a bale in kilograms. |
| container weight | Tare/container weight in kilograms. |
| net weight | Derived net weight (gross minus tare); never persisted. |
| yarn count | Canonical yarn count used when defining production identity. |
| production identity | Warehouse-owned technical identity shared across the production flow. |
| lot code | Visible business code for the same production identity. |
| availability state | Warehouse operational readiness for release or distribution. |
| physical presentation | Physical finished-product form under Warehouse handling. |

## Sources

- [Bale Management PRD](../prd/warehouse/bale-management.md) — normative source for bale business rules
- [Warehouse Area PRD](../prd/warehouse/overview.md) — area-level scope and subdomain overview
- [Ubiquitous Language](ubiquitous-language.md) — canonical naming contract
- [Context Map](../architecture/context-map.md) — context ownership and boundaries
