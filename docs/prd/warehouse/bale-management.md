---
document_type: prd
status: active
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
4. A controlled process for recording bale deliveries to Production (date tracked; actor tracking requires a separate requirement).

Without this capability, stock discrepancies, lost traceability, and uncontrolled material flow create operational risk.

---

## 3. Stakeholders and Actors

| Actor | Role | Interaction |
|---|---|---|
| Warehouse Personnel | Operational executor | Registers receptions, executes and records deliveries |
| Warehouse Unit Manager | Operational supervisor | Oversees reception quality, authorizes corrections |
| Production Manager | Authorizer | Authorizes deliveries to Production |
| System | Automated | Generates timestamps, enforces constraints, calculates derived values |

> **Note on permissions:** These actors describe operational practice. The assignment of who registers, validates, authorizes, or corrects is configurable by access policy (see `docs/prd/access-control.md`). This PRD does not fix permissions rigidly to roles.

---

## 4. Identity Rules

### 4.1 Raw-Material Batch Identity

A **raw-material batch** represents a supplier shipment grouping one or more bales.

| Rule | Description |
|---|---|
| Identifier | Shipment number |
| Uniqueness | Globally unique across all batches |
| Format | Text, maximum 10 characters after normalization |
| Normalization | Uppercase; applied before persistence and comparison |

### 4.2 Bale Identity

A **bale** is an independently identified raw-material unit with its own lifecycle.

| Rule | Description |
|---|---|
| Identifier within batch | Bale number |
| Uniqueness | Unique within the parent batch; the same canonical bale number is valid in different batches |
| Format | Text, maximum 10 characters after normalization |
| Normalization | Uppercase; applied before persistence and comparison |
| Business-visible identity | Shipment number + bale number (composite) |

### 4.3 Identity Invariants

1. A bale always belongs to exactly one raw-material batch.
2. The composite identity (shipment number + bale number) uniquely identifies a bale across the entire system.
3. Bale number alone is insufficient for identification — it may repeat across batches.
4. Technical identifiers are never exposed as primary identity to business users.

---

## 5. Attributes

### 5.1 Raw-Material Batch Attributes

| Attribute | Format | Required | Description |
|---|---|---|---|
| Shipment number | text, up to 10 characters | Yes | Globally unique batch identifier |
| Reception date | calendar date (no time component) | Yes | Business date of reception (see §5.3) |
| Provider name | text | Yes | Supplier name |

### 5.2 Bale Attributes

| Attribute | Format | Required | Description |
|---|---|---|---|
| Bale number | text, up to 10 characters | Yes | Bale identifier within batch |
| Material type | text, up to 20 characters | Yes | Raw-material classification; normalized to uppercase |
| Dtex | numeric (decimal precision) | Yes | Linear density; finite, greater than zero |
| Gross weight | numeric (decimal precision), in kilograms | Yes | Gross weight; finite, greater than zero |
| Container weight | numeric (decimal precision), in kilograms | Yes | Tare/container weight; finite, greater than zero, less than gross weight |
| Status | one of the defined states | Yes | Lifecycle state: In Warehouse or Delivered |

### 5.3 Reception Date Semantics

- The reception date is a **business date** — the calendar date when the physical reception occurred.
- It does not carry a time component.
- It does not represent when the system record was created (that is a separate technical concern: the system registration timestamp).

---

## 6. Weight Model

### 6.1 Weight Attributes

| Weight | Business name | Source | Persistence |
|---|---|---|---|
| Gross weight | gross weight | User-provided at reception | Persisted |
| Tare weight | container weight | User-provided at reception | Persisted |
| Net weight | net weight | Calculated | Derived, not persisted |

### 6.2 Calculation Rules

1. **Net weight equals gross weight minus tare weight** (net weight = gross weight − container weight).
2. Net weight is always calculated, never accepted as direct input from users or external systems.
3. Gross weight must be strictly greater than tare weight (ensuring net weight is always positive).
4. All weights use kilograms as the unit of measure.
5. All weight values are decimal with arbitrary precision — no premature rounding.

### 6.3 Aggregation Rules

When computing aggregate weights (e.g., inventory summary):

1. The system groups bales by batch for aggregate queries.
2. When no bales match the filter criteria, aggregate weights are zero (not null).
3. Aggregates respect the same filter conjunction as counts (see §11).

---

## 7. Reception Flow

### 7.1 Business Act

Reception is the act of recording the physical arrival of raw material from a supplier. The system registers a raw-material batch and its bales — it does not model a separate Reception entity. See [ADR-005](../../architecture/decisions/005-reception-as-application-action.md) for implementation approach.

### 7.2 Steps

1. Warehouse personnel identify the incoming shipment and determine the shipment number.
2. The operator registers one complete raw-material batch with all its bales in a single operation.
3. The system validates all data before persisting.
4. The system creates the batch header and all bale records in one atomic transaction.
5. All bales are registered with initial status In Warehouse.
6. The system returns a confirmation with batch summary.

### 7.3 Reception Rules

| ID | Rule |
|---|---|
| RCP-01 | A reception registers exactly one raw-material batch and one or more bale records. |
| RCP-02 | The entire reception is atomic — if any bale fails validation, the entire batch is rejected. |
| RCP-03 | The reception contract accepts 1–100 bales per request. This is an operational safeguard, not an intrinsic business limit. |
| RCP-04 | The shipment number must not already exist in the system. |
| RCP-05 | Within the batch, all bale number values must be unique. |
| RCP-06 | The system creates the batch record before its bale records and returns a unique batch identifier. |
| RCP-07 | Adding bales to an already-registered batch requires a separate correction capability (explicit, audited). |
| RCP-08 | Business identifiers (shipment number, bale number, material type) are normalized (uppercase) before persistence. |

### 7.4 Transport Fields

Transport information (truck number, license plate, driver) is **not part of the bale management capability**. Adding transport fields requires an explicit separate requirement.

---

## 8. States and Transitions

### 8.1 Canonical State Names

| State | Display (English) | Display (Spanish) | Meaning |
|---|---|---|---|
| In Warehouse | In Warehouse | En almacén | Bale is under Warehouse custody |
| Delivered | Delivered | Entregado | Bale has been delivered to and used by Production |

### 8.2 Transition Rules

```text
┌──────────────┐          deliver           ┌──────────────┐
│ In Warehouse │ ────────────────────────► │   Delivered  │
└──────────────┘                           └──────────────┘
```

| ID | Rule |
|---|---|
| ST-01 | A newly created bale always starts in In Warehouse. |
| ST-02 | The only permitted transition is In Warehouse → Delivered. |
| ST-03 | A bale in Delivered cannot transition to any other state. |
| ST-04 | There are no additional states beyond these two. |
| ST-05 | The system enforces the valid-transition constraint on every state change. |
| ST-06 | Two concurrent delivery attempts for the same bale must result in exactly one success; the other receives a conflict. |

### 8.3 Reversibility

The delivery transition is **irreversible**. No reversal mechanism exists. A controlled reversal requires a separate capability following the standard correction policy (audited, authorized, reason documented).

---

## 9. Delivery Meaning

Delivered means that the bale has been **delivered to and used by Production**. In practice, delivery and consumption are treated as the same event — once a bale leaves Warehouse, it is considered used. The system models this as a binary, irreversible fact.

- Delivery is a **checklist-style operation**: the user marks which bales were delivered and when.
- There is no intermediate state between In Warehouse and Delivered.
- No approval workflow, contract, or intermediary is modeled.
- Delivery does not link the bale to a production identity or lot code.

### 9.1 Delivery Rules

| ID | Rule |
|---|---|
| DLV-01 | A bale is always delivered whole — partial delivery is not supported. |
| DLV-02 | The delivery target is always Production — no other destination is required or persisted. |
| DLV-03 | A bale can be delivered only once. A repeat delivery attempt must be rejected. |
| DLV-04 | Delivery records the delivery date — a business date (calendar day, no time component) entered by the user representing when the physical delivery occurred. |
| DLV-05 | Delivery does not link the bale to a production identity or lot code. |
| DLV-06 | The delivery act changes the bale's lifecycle state; it does not create a separate movement record. |
| DLV-07 | No authorization workflow is modeled. The real-world authorization process is acknowledged but excluded from this capability. |

### 9.2 Delivery Exclusions

The following are excluded from this capability. Each requires an explicit separate requirement:

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
| In-warehouse bale count | Count of filtered bales with status In Warehouse |
| Delivered bale count | Count of filtered bales with status Delivered |
| Total net weight (kg) | Sum of net weights for all filtered bales |
| In-warehouse net weight (kg) | Sum of net weights for filtered bales in warehouse |
| Delivered net weight (kg) | Sum of net weights for filtered delivered bales |

### 10.3 Summary Rules

| ID | Rule |
|---|---|
| INV-01 | Net weight is always derived from gross weight minus container weight. |
| INV-02 | When no bales match the filters, all counts are zero and all weights are zero (not null, not an error). |
| INV-03 | When a status filter is applied, the total represents only that subset and the other status counter is zero. |
| INV-04 | Net weight for summary purposes is calculated as gross weight minus container weight per bale. |

---

## 11. Query Capabilities

### 11.1 Aggregate Query (Summary)

Filters all combine by conjunction (AND): a bale must satisfy all provided filters.

| Filter | Format | Semantics |
|---|---|---|
| Received from | date | Inclusive lower bound on reception date |
| Received to | date | Inclusive upper bound on reception date |
| Shipment number | text | Exact match after normalization |
| Status | one of the defined states | In Warehouse or Delivered |
| Provider name | text | Case-insensitive exact match, trimmed |
| Material type | text | Exact match after normalization |
| Dtex | numeric (decimal) | Exact decimal match |

All filters are optional. When both date bounds are provided, received from must not be after received to.

### 11.2 Individual Bale Query (Detail)

A single bale is queried by its composite business identity:

- **Required:** shipment number AND bale number
- **Semantics:** Values are normalized before lookup
- **Result:** Full bale detail including batch-level attributes, bale attributes, calculated net weight, and current status
- **Not found:** A missing combination produces a "not found" result without revealing whether the batch exists

### 11.3 Query Non-Goals

- There is no paginated list of all bales.
- There is no full-text search.
- There is no query by system-generated unique identifier (the internal identifier is used only for write operations after discovery).

---

## 12. Acceptance Criteria

### 12.1 Reception

| ID | Criterion |
|---|---|
| AC-RCP-01 | A complete batch with 1–100 bales can be registered in one atomic operation (operational safeguard, not an intrinsic business limit). |
| AC-RCP-02 | Shipment number must be globally unique; a duplicate produces a clear conflict response. |
| AC-RCP-03 | Bale number must be unique within the batch; a duplicate within the same registration is rejected. |
| AC-RCP-04 | Reception date accepts a date (no time component); values with a time component are rejected. |
| AC-RCP-05 | All registered bales start with status In Warehouse. |
| AC-RCP-06 | If any bale in the batch fails validation, the entire batch is not persisted. |
| AC-RCP-07 | Weight validation enforces: gross > 0, tare > 0, tare < gross. |
| AC-RCP-08 | Business identifiers are normalized before persistence. |

### 12.2 Inventory and Query

| ID | Criterion |
|---|---|
| AC-INV-01 | The aggregate summary respects all active filters conjunctively. |
| AC-INV-02 | A query with no matching results returns zero metrics, not an error. |
| AC-INV-03 | Individual query requires both shipment number and bale number. |
| AC-INV-04 | An existing bale returns full detail including calculated net weight. |
| AC-INV-05 | A non-existing composite identity returns a "not found" result. |

### 12.3 Delivery

| ID | Criterion |
|---|---|
| AC-DLV-01 | A bale in In Warehouse can be transitioned to Delivered. |
| AC-DLV-02 | A bale already in Delivered cannot be delivered again; the attempt is rejected with a conflict response. |
| AC-DLV-03 | Only the state Delivered is accepted as a target status; no other value is permitted. |
| AC-DLV-04 | Concurrent delivery attempts for the same bale result in exactly one success. |
| AC-DLV-05 | The system enforces the valid-transition constraint on every delivery attempt. |
| AC-DLV-06 | GIVEN a delivery is being recorded, WHEN the user submits the form, THEN the system requires a delivery date as a business date (calendar day, no time component) entered by the user (validates DLV-04). |

### 12.4 Data Integrity

| ID | Criterion |
|---|---|
| AC-INT-01 | Net weight is never persisted — it is always derived from gross minus tare. |
| AC-INT-02 | Decimal precision is preserved end-to-end (input, persistence, calculation, output). |
| AC-INT-03 | All writes are transactional — partial persistence never occurs. |

---

## References

- [Warehouse Area PRD](./overview.md) — area-level overview and all subdomain scope
- [Warehouse Domain Map](../../domain/warehouse.md) — domain model and boundaries
- [Ubiquitous Language](../../domain/ubiquitous-language.md) — canonical naming contract
- [Warehouse Schema](../../../backend/docs/database/warehouse-schema.md) — physical schema documentation
- [Backend Specification](../../../backend/docs/features/bale-management.md) — technical backend spec (derives from this PRD)
- [Frontend Specification](../../../frontend/docs/features/bale-management.md) — technical frontend spec (derives from this PRD)
