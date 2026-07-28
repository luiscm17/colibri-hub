---
document_type: prd
status: active
scope: warehouse/production-identity
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Production Identity Definition — Normative PRD

> **Authority:** This is the single normative source for production identity definition business rules within Warehouse.
> Technical specifications derive from this PRD and may not redefine business rules documented here.

---

## 1. Business Scope

This PRD defines the business rules for **production identity definition** within the Warehouse context of Colibri Hub:

- **Definition** of a unique identity for a planned production unit.
- **Assignment** of client, color, title, and classification to that identity.
- **Lifecycle continuity** of the identity across Warehouse and Operations.

Production identity definition is a distinct business act, separated from bale reception and from bale delivery. It establishes the naming and tracking basis that Operations will continue.

### Relationship to Other Capabilities

| Capability | Relationship |
|---|---|
| Bale Management | Separate act; delivery of bales does not link them to a production identity |
| Finished Product | Downstream; PT returns under the same identity defined here |
| Lot Processing (Operations) | Continues the identity; must not create a parallel identity for the same flow |
| Supplies | No direct relationship |

---

## 2. Problem Statement

When Warehouse plans a production unit, it must define a unique identity that will persist throughout the entire production lifecycle — from planning through Operations processing to finished-product return. Without a controlled identity definition act:

1. Operations might create parallel identifiers for the same flow.
2. Traceability between raw material, production, and finished product is lost.
3. Client attribution and production objectives become ambiguous.

---

## 3. Stakeholders and Actors

| Actor | Role | Interaction |
|---|---|---|
| Warehouse Personnel | Operational executor | Normally registers the identity definition |
| Production Manager | Authorizer / Definer | Defines or authorizes the identity and its parameters |
| System | Automated | Generates timestamps, enforces constraints |

> **Note on permissions:** The registering actor is configurable by access policy (see `docs/prd/access-control.md`). This PRD does not fix permissions rigidly to roles.

---

## 4. Boundary Rules

1. This act is **separate** from the physical reception of bales.
2. It does **not** select, assign, or link bales to the production identity — bale delivery remains an independent act.
3. The identity defined here becomes the basis of continuity for the lot history with Operations.
4. Operations must **not** create a parallel identity for the same production flow.

---

## 5. Business Data

### 5.1 Data Captured at Definition

| Attribute | Required | Description |
|---|---|---|
| Production identifier (lot code) | Yes | Unique identifier for the production unit |
| Target title | Yes | Objective title for the production |
| Required color | Yes | Color specification for the production |
| Client or destination | Yes | Client or target for the production output |
| Type, variant, or classification | When applicable | Additional classification |
| Requirements or order observations | No | Free-text notes about the order |
| Business date of definition | Yes | Calendar date when the identity was defined |
| Responsible who defines or authorizes | Yes | Actor who performs or authorizes the definition |

### 5.2 Technical Data (Automatic)

| Attribute | Source | Description |
|---|---|---|
| Registration timestamp | System | Date and time the record was created in the system |

### 5.3 Data Semantics

- The **business date of definition** is a calendar date entered by the responsible actor. It is not the same as the system registration timestamp.
- The **production identifier** must be globally unique within the system. Its format and naming rules are defined by operational convention.

---

## 6. Identity Naming Rules and Constraints

| Rule | Description |
|---|---|
| Uniqueness | The production identifier (lot code) must be unique across the system |
| Assignment | Defined by Warehouse with authorization from the Production Manager |
| Continuity | Once defined, this identity persists through the entire production lifecycle |
| No reassignment | A production identity cannot be reassigned to a different production flow |
| No duplication | Operations must not create a separate identity for the same flow |

---

## 7. Continuity of the Lot History

From the moment a production identity is defined:

1. A **unique identity** exists that Operations must continue.
2. Warehouse and Operations maintain a **shared lot history**, but each domain writes only the portion under its responsibility.
3. Operations does not recreate or redefine the identity — it extends the history.
4. When finished product returns to Warehouse, it returns under **the same identity** defined here.

### 7.1 Domain Write Separation

| Domain | Writes |
|---|---|
| Warehouse | Identity definition, client, color, title, classification, definition date |
| Operations | Processing events, quality data, route-sheet facts, production completion |

Neither domain overwrites the other's contributions to the shared history.

---

## 8. Cross-Cutting Rules (Applicable)

1. **Business date vs system timestamp:** The business date of definition is the actor-entered calendar date; the registration timestamp is system-generated. These are distinct and must not be confused.
2. **Correction with audit:** If an error is made in the identity definition, the record may be corrected, but only with full audit trail (actor, timestamp, reason, before/after values).
3. **Operational window:** Operational roles may correct within the policy-defined window. Outside that window, only SysAdmin may edit.
4. **Permissions are configurable:** The current registerer and authorizer assignments are operational practice, not rigid permissions.

---

## 9. Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-PID-01 | A production identity can be defined with all required fields in a single operation. |
| AC-PID-02 | The production identifier must be globally unique; a duplicate produces a clear conflict response. |
| AC-PID-03 | The definition is independent from bale reception — no bale linkage is required or recorded. |
| AC-PID-04 | The business date of definition accepts a date (no time component). |
| AC-PID-05 | The registration timestamp is generated automatically by the system. |
| AC-PID-06 | Once defined, the identity is available for Operations to continue the lot history. |

---

---

## References

- [Bale Management PRD](./bale-management.md) — raw-material bale lifecycle (separate capability)
- [Finished Product PRD](./finished-product.md) — PT management under the same identity
- [Warehouse Area PRD](./overview.md) — area-level overview
- [Access Control](../access-control.md) — permission policies
- [Lot Processing Records](../operation/lot-processing-records.md) — Operations continuation of the lot history
