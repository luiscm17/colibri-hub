---
document_type: prd
status: active
implementation: partial
scope: warehouse/bales
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Bale Management — Normative PRD

> **Authority:** This is the single normative source for all bale-related business rules.
> Backend specifications, frontend specifications, and domain documents derive from this PRD.
> Technical specifications may not redefine business rules documented here.

---

## 1. Business Scope

This PRD defines the business rules for **raw-material bale management** within the Warehouse context of Colibri Hub:

- **Reception** of bales from suppliers as raw-material batches.
- **Inventory** of bales under Warehouse custody.
- **Query** of individual bales and aggregate summaries.
- **Delivery** of whole bales to Production.

Bale management is the first operational capability of Warehouse. It handles physical raw material from supplier arrival through transfer to Production. It does not cover production identity definition, finished product, or supplies — those are separate Warehouse capabilities documented elsewhere.

### Relationship to Other Capabilities

| Capability | Relationship |
|---|---|
| Production Identity Definition | Separate act; delivery does not link bales to a production identity or lot code |
| Finished Product | Separate subdomain; not covered here |
| Supplies | Separate subdomain; not covered here |
| Lot Processing | Downstream consumer; receives delivered bales but this PRD does not govern their processing |

---

## 2. Problem Statement

Warehouse personnel receive raw-material bales from suppliers and must track them from arrival through delivery to Production. The business needs:

1. A reliable record of what was received, from whom, and when.
2. Identity and weight traceability for each individual bale.
3. Visibility into current stock (what is still in warehouse vs. already delivered).
4. A controlled, auditable process for transferring bales to Production.

Without this capability, stock discrepancies, lost traceability, and uncontrolled material flow create operational risk.

---

## 3. Stakeholders and Actors

| Actor | Role | Interaction |
|---|---|---|
| Warehouse Personnel | Operational executor | Registers receptions, executes and records deliveries |
| Warehouse Unit Manager | Operational supervisor | Oversees reception quality, authorizes corrections |
| Production Manager | Authorizer | Authorizes deliveries to Production |
| System | Automated | Generates timestamps, enforces constraints, calculates derived values |

> **Note on permissions:** These actors describe current operational practice. The assignment of who registers, validates, authorizes, or corrects is configurable by access policy (see `docs/prd/access-control.md`). This PRD does not fix permissions rigidly to roles.

---

## 4. Identity Rules

### 4.1 Raw-Material Batch Identity

A **raw-material batch** (`RawMaterialBatch`) represents a supplier shipment grouping one or more bales.

| Rule | Description |
|---|---|
| Identifier | `shipment_number` |
| Uniqueness | Globally unique across all batches |
| Format | String, maximum 10 characters after normalization |
| Normalization | Uppercase; applied before persistence and comparison |

### 4.2 Bale Identity

A **bale** (`Bale`) is an independently identified raw-material unit with its own lifecycle.

| Rule | Description |
|---|---|
| Identifier within batch | `bale_number` |
| Uniqueness | Unique within the parent batch; the same canonical bale number is valid in different batches |
| Format | String, maximum 10 characters after normalization |
| Normalization | Uppercase; applied before persistence and comparison |
| Business-visible identity | `shipment_number` + `bale_number` (composite) |
| Technical identity | Independent UUID (`id`); used for write operations |

### 4.3 Identity Invariants

1. A bale always belongs to exactly one raw-material batch.
2. The composite identity `shipment_number` + `bale_number` uniquely identifies a bale across the entire system.
3. `bale_number` alone is insufficient for identification — it may repeat across batches.
4. Technical identifiers (`id`) are never exposed as primary identity to business users.

---

## 5. Attributes

### 5.1 Raw-Material Batch Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| `shipment_number` | String(10) | Yes | Globally unique batch identifier |
| `received_at` | Date | Yes | Business date of reception (see §5.3) |
| `provider_name` | String | Yes | Supplier name |

### 5.2 Bale Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| `bale_number` | String(10) | Yes | Bale identifier within batch |
| `material_type` | String(20) | Yes | Raw-material classification; normalized to uppercase |
| `dtex` | Decimal | Yes | Linear density; finite, greater than zero |
| `gross_weight_kg` | Decimal | Yes | Gross weight in kilograms; finite, greater than zero |
| `container_weight_kg` | Decimal | Yes | Tare/container weight in kilograms; finite, greater than zero, less than gross weight |
| `status` | Enum | Yes | Lifecycle state: `in_warehouse` or `delivered` |

### 5.3 Reception Date Semantics

- `received_at` is a **business date** — the calendar date when the physical reception occurred.
- It does not carry a time component.
- It does not represent when the system record was created (that is a separate technical concern: `created_at`).

---

## 6. Weight Model

### 6.1 Weight Attributes

| Weight | Canonical Name | Source | Persistence |
|---|---|---|---|
| Gross weight | `gross_weight_kg` | User-provided at reception | Persisted |
| Tare weight | `container_weight_kg` | User-provided at reception | Persisted |
| Net weight | `net_weight_kg` | Calculated | Derived, not persisted |

### 6.2 Calculation Rules

1. **Net weight = gross weight − tare weight** (`net_weight_kg = gross_weight_kg - container_weight_kg`).
2. Net weight is always calculated, never accepted as direct input from users or external systems.
3. Gross weight must be strictly greater than tare weight (ensuring net weight is always positive).
4. All weights use kilograms as the unit of measure.
5. All weight values are decimal with arbitrary precision — no premature rounding.

### 6.3 Aggregation Rules

When computing aggregate weights (e.g., inventory summary):

1. Aggregation is performed in the persistence layer (SQL), not in application memory.
2. When no bales match the filter criteria, aggregate weights are zero (not null).
3. Aggregates respect the same filter conjunction as counts (see §11).

---

## 7. Reception Flow

### 7.1 Business Act

Reception is the physical arrival of raw material from a supplier. It is an **application action** (use case), not a domain aggregate. The system does not model a `Reception` entity.

### 7.2 Steps

1. Warehouse personnel identify the incoming shipment and determine the `shipment_number`.
2. The operator registers one complete raw-material batch with all its bales in a single operation.
3. The system validates all data before persisting.
4. The system creates the batch header and all bale records in one atomic transaction.
5. All bales are registered with initial status `in_warehouse`.
6. The system returns a confirmation with batch summary.

### 7.3 Reception Rules

| ID | Rule |
|---|---|
| RCP-01 | A reception registers exactly one `RawMaterialBatch` and one or more `Bale` records. |
| RCP-02 | The entire reception is atomic — if any bale fails validation, the entire batch is rejected. |
| RCP-03 | A batch must contain between 1 and 100 bales. |
| RCP-04 | `shipment_number` must not already exist in the system. |
| RCP-05 | Within the batch, all `bale_number` values must be unique. |
| RCP-06 | The batch is inserted before its bales; the operation returns the batch technical identifier. |
| RCP-07 | Adding bales to an already-registered batch is not part of the current flow. A future correction capability must be explicit and audited. |
| RCP-08 | Business identifiers (`shipment_number`, `bale_number`, `material_type`) are normalized (uppercase) before persistence. |

### 7.4 Transport Fields

Transport information (truck number, license plate, driver) is **not part of the current bale management capability**. If needed in the future, it must be added through an explicit requirement.

---

## 8. States and Transitions

### 8.1 Canonical State Names

| State | Persistence Value | Display (English) | Display (Spanish) | Meaning |
|---|---|---|---|---|
| In Warehouse | `in_warehouse` | In Warehouse | En almacén | Bale is under Warehouse custody |
| Delivered | `delivered` | Delivered | Entregado | Bale has been delivered to and used by Production |

Layer conventions:
- **Database and API layer:** `in_warehouse`, `delivered` (lowercase)
- **Domain/enum code layer:** `IN_WAREHOUSE`, `DELIVERED` (uppercase constants)
- **Business documentation and display:** "In Warehouse", "Delivered" / "En almacén", "Entregado"

### 8.2 Transition Rules

```text
┌──────────────┐         deliver()         ┌──────────────┐
│ in_warehouse │ ────────────────────────► │  delivered   │
└──────────────┘                           └──────────────┘
```

| ID | Rule |
|---|---|
| ST-01 | A newly created bale always starts in `in_warehouse`. |
| ST-02 | The only permitted transition is `in_warehouse → delivered`. |
| ST-03 | A bale in `delivered` cannot transition to any other state. |
| ST-04 | There are no additional states beyond these two. |
| ST-05 | The transition is enforced by domain logic, not by direct status-string manipulation. |
| ST-06 | Two concurrent delivery attempts for the same bale must result in exactly one success; the other receives a conflict. |

### 8.3 Reversibility

The delivery transition is **irreversible** in the current scope. There is no reversal mechanism. A future controlled reversal may be introduced following the standard correction policy (audited, authorized, reason documented).

---

## 9. Delivery Meaning

`delivered` means that the bale has been **delivered to and used by Production**. In practice, delivery and consumption are treated as the same event — once a bale leaves Warehouse, it is considered used. The system models this as a binary, irreversible fact.

- Delivery is a **checklist-style operation**: the user marks which bales were delivered and when.
- There is no intermediate state between "in warehouse" and "delivered/used".
- No approval workflow, contract, or intermediary is modeled for this project.
- Delivery does not link the bale to a production identity or lot code.

### 9.1 Delivery Rules

| ID | Rule |
|---|---|
| DLV-01 | A bale is always delivered whole — partial delivery is not supported. |
| DLV-02 | The delivery target is always Production — no other destination is required or persisted. |
| DLV-03 | A bale can be delivered only once. A repeat delivery attempt must be rejected. |
| DLV-04 | Delivery records `delivered_at` — a business date (calendar day, no time component) entered by the user representing when the physical delivery occurred. |
| DLV-05 | Delivery does not link the bale to a production identity or lot code. |
| DLV-06 | The delivery act changes the bale's lifecycle state; it does not create a separate movement record. |
| DLV-07 | No authorization workflow is modeled in the current scope (the real-world authorization process is acknowledged but omitted from the system). |

### 9.2 Future Delivery Enhancements (Not in Current Scope)

The following may be added through future explicit requirements:

- Responsible actors (who delivers, who receives)
- Delivery reference or authorization number
- Reversal/correction capability
- Multi-bale delivery command atomicity

---

## 10. Inventory Summary

### 10.1 Purpose

The inventory summary provides aggregated visibility into bale stock without requiring users to enumerate all individual bales.

### 10.2 Summary Metrics

| Metric | Description |
|---|---|
| Total bale count | Count of all bales matching current filters |
| In-warehouse bale count | Count of filtered bales with status `in_warehouse` |
| Delivered bale count | Count of filtered bales with status `delivered` |
| Total net weight (kg) | Sum of net weights for all filtered bales |
| In-warehouse net weight (kg) | Sum of net weights for filtered bales in warehouse |
| Delivered net weight (kg) | Sum of net weights for filtered delivered bales |

### 10.3 Summary Rules

| ID | Rule |
|---|---|
| INV-01 | Summary metrics are computed in the persistence layer, not by loading all bales into memory. |
| INV-02 | When no bales match the filters, all counts are zero and all weights are zero (not null, not an error). |
| INV-03 | When a status filter is applied, the total represents only that subset and the other status counter is zero. |
| INV-04 | Net weight for summary purposes is calculated as `gross_weight_kg - container_weight_kg` per bale. |

---

## 11. Query Capabilities

### 11.1 Aggregate Query (Summary)

Filters all combine by conjunction (AND): a bale must satisfy all provided filters.

| Filter | Type | Semantics |
|---|---|---|
| Received from | Date | Inclusive lower bound on `received_at` |
| Received to | Date | Inclusive upper bound on `received_at` |
| Shipment number | String | Exact match after normalization |
| Status | Enum | `in_warehouse` or `delivered` |
| Provider name | String | Case-insensitive exact match, trimmed |
| Material type | String | Exact match after normalization |
| Dtex | Decimal | Exact decimal match |

All filters are optional. When both date bounds are provided, `received_from` must not be after `received_to`.

### 11.2 Individual Bale Query (Detail)

A single bale is queried by its composite business identity:

- **Required:** `shipment_number` AND `bale_number`
- **Semantics:** Values are normalized before lookup
- **Result:** Full bale detail including batch-level attributes, bale attributes, calculated net weight, and current status
- **Not found:** A missing combination produces a "not found" result without revealing whether the batch exists

### 11.3 Query Non-Goals

- There is no paginated list of all bales.
- There is no full-text search.
- There is no query by technical UUID (UUID is used only for write operations after discovery).

---

## 12. Acceptance Criteria

### 12.1 Reception

| ID | Criterion |
|---|---|
| AC-RCP-01 | A complete batch with 1 to 100 bales can be registered in one atomic operation. |
| AC-RCP-02 | `shipment_number` must be globally unique; a duplicate produces a clear conflict response. |
| AC-RCP-03 | `bale_number` must be unique within the batch; a duplicate within the same registration is rejected. |
| AC-RCP-04 | `received_at` accepts a date (no time component); values with a time component are rejected. |
| AC-RCP-05 | All registered bales start with status `in_warehouse`. |
| AC-RCP-06 | If any bale in the batch fails validation, the entire batch is not persisted. |
| AC-RCP-07 | Weight validation enforces: gross > 0, tare > 0, tare < gross. |
| AC-RCP-08 | Business identifiers are normalized before persistence. |

### 12.2 Inventory and Query

| ID | Criterion |
|---|---|
| AC-INV-01 | The aggregate summary respects all active filters conjunctively. |
| AC-INV-02 | A query with no matching results returns zero metrics, not an error. |
| AC-INV-03 | Individual query requires both `shipment_number` and `bale_number`. |
| AC-INV-04 | An existing bale returns full detail including calculated net weight. |
| AC-INV-05 | A non-existing composite identity returns a "not found" result. |

### 12.3 Delivery

| ID | Criterion |
|---|---|
| AC-DLV-01 | A bale in `in_warehouse` can be transitioned to `delivered`. |
| AC-DLV-02 | A bale already in `delivered` cannot be delivered again; the attempt is rejected with a conflict response. |
| AC-DLV-03 | Only the value `delivered` is accepted as a target status; no other value is permitted. |
| AC-DLV-04 | Concurrent delivery attempts for the same bale result in exactly one success. |
| AC-DLV-05 | The transition is enforced through domain logic, not direct string manipulation. |

### 12.4 Data Integrity

| ID | Criterion |
|---|---|
| AC-INT-01 | Net weight is never persisted — it is always derived from gross minus tare. |
| AC-INT-02 | Decimal precision is preserved end-to-end (input, persistence, calculation, output). |
| AC-INT-03 | All writes are transactional — partial persistence never occurs. |

---

## 13. Open Items and Pending Decisions

| # | Item | Owner | Impact | Status |
|---|---|---|---|---|
| 1 | **Delivery actors:** Should delivery record responsible actors (who delivers, who receives)? | Product | Affects audit trail completeness | Open |
| 2 | **Reversal capability:** When should controlled reversal (`delivered → in_warehouse`) be implemented? What authorization and audit requirements apply? | Product | Affects state machine design and correction policy | Open |
| 3 | **Post-registration correction:** How should errors in already-registered batches be corrected? (typos in bale_number, wrong weights, etc.) | Product | Affects edit policy, audit requirements, and correction window rules | Open |
| 4 | **Multi-bale delivery atomicity:** Should delivery of multiple bales in one operation be atomic (all-or-nothing) or individual? | Product | Affects future multi-bale delivery command design | Open |
| 5 | **Transport fields:** Should truck number, license plate, or driver be added to the batch header? | Product | Affects reception contract | Open |
| 6 | **Provider catalog:** Should `provider_name` reference a managed supplier catalog or remain free text? | Product | Affects data quality and validation | Open |
| 7 | **Material type catalog:** Should `material_type` reference a managed catalog or remain free text with normalization? | Product | Affects data quality and validation | Open |
| 8 | **Batch size upper bound:** Is 100 bales per batch a hard business rule or an implementation safeguard? | Product | Affects validation rules and error messaging | Open |

---

## References

- [Warehouse Area PRD](./overview.md) — area-level overview and all subdomain scope
- [Warehouse Domain Map](../../domain/warehouse.md) — domain model and boundaries
- [Ubiquitous Language](../../domain/ubiquitous-language.md) — canonical naming contract
- [Warehouse Schema](../../../backend/docs/database/warehouse-schema.md) — physical schema documentation
- [Backend Specification](../../../backend/docs/features/bale-management.md) — technical backend spec (derives from this PRD)
- [Frontend Specification](../../../frontend/docs/features/bale-management.md) — technical frontend spec (derives from this PRD)
