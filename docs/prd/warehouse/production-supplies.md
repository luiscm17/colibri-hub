---
document_type: prd
status: active
implementation: not-started
scope: warehouse/production-supplies
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Production Supplies — Normative PRD

> **Authority:** This is the single normative source for production supplies management business rules within Warehouse.
> Technical specifications derive from this PRD and may not redefine business rules documented here.

---

## 1. Business Scope

This PRD defines the business rules for **production supplies management** within the Warehouse context of Colibri Hub:

- **Reception** of supplies from suppliers.
- **Consumption** tracking when Production uses supplies.
- **Returns** of supplies to suppliers.

Production supplies are consumable materials required by the production process. They do not share the unique lot history of finished product — they have their own stock traceability.

### Relationship to Other Capabilities

| Capability | Relationship |
|---|---|
| Bale Management | Separate capability; raw material (bales) is not a supply |
| Production Identity | No direct relationship; supplies are not tracked per production identity |
| Finished Product | No direct relationship |
| Lot Processing (Operations) | Consumer of supplies; consumption events originate from Production |

---

## 2. Problem Statement

Production requires various consumable supplies (dyes, chemicals, packaging materials, spare parts, lubricants, cones, tubes). Warehouse must:

1. Track supply reception from suppliers.
2. Record consumption by Production with proper authorization.
3. Handle returns to suppliers when needed.
4. Maintain stock visibility per supply category with appropriate units of measure.

Without supply traceability, the business cannot control consumption costs, detect waste, or manage supplier relationships.

---

## 3. Stakeholders and Actors

| Actor | Role | Interaction |
|---|---|---|
| Warehouse Personnel | Operational executor | Registers receptions, consumption exits, and returns |
| Production Supervisor | Authorizer | Authorizes consumption by Production (per policy) |
| System | Automated | Generates timestamps, enforces constraints |

> **Note on permissions:** Actor assignments are configurable by access policy (see `docs/prd/access-control.md`).

---

## 4. Supply Categories

| Category | Typical Unit of Measure | Examples |
|---|---|---|
| Colorantes (dyes) | kg, liters | Reactive dyes, acid dyes |
| Químicos (chemicals) | kg, liters | Auxiliaries, pH regulators, softeners |
| Embalaje (packaging) | units, rolls, meters | Bags, wrapping film, labels |
| Repuestos (spare parts) | units | Mechanical components, needles |
| Lubricantes (lubricants) | liters, kg | Machine oils, greases |
| Conos (cones) | units | Winding cones of various sizes |
| Tubos (tubes) | units | Cardboard or plastic tubes |

> **Important:** The unit of measure depends on the supply item and must not be forced to kilograms when it does not correspond. Each item carries its own natural unit.

---

## 5. Movement Types

### 5.1 Reception from Supplier

Entry of supplies into Warehouse stock from an external supplier.

### 5.2 Consumption by Production

Exit of supplies from Warehouse stock for use by Production. This reduces Warehouse inventory.

### 5.3 Return to Supplier

Exit of supplies from Warehouse back to the original supplier (defective material, excess, contractual return).

---

## 6. Supply Movement Data

### 6.1 Common Movement Attributes

| Attribute | Required | Description |
|---|---|---|
| Movement number | Yes | Unique identifier for this movement |
| Movement type | Yes | Reception, consumption, or return |
| Business date | Yes | Calendar date of the movement |
| Supply category | Yes | One of the defined categories |
| Item or reference | Yes | Specific supply item identifier |
| Supplier or destination | Yes | Supplier (for reception/return) or Production (for consumption) |
| Quantity | Yes | Amount in the item's unit of measure |
| Unit of measure | Yes | Natural unit for the item (kg, liters, units, meters, rolls) |
| Responsible who delivers or receives | Yes | Actor executing the physical movement |
| Authorizer | When applicable | Required for consumption; per policy |
| Observations | No | Free-text notes |

### 6.2 Technical Data (Automatic)

| Attribute | Source | Description |
|---|---|---|
| Registration timestamp | System | Date and time the record was created |

---

## 7. Boundary Rules

1. Supplies do **not** share the unique lot history of finished product or production identities.
2. Supplies **do** require their own stock and consumption traceability.
3. The unit of measure is **per item**, not universal — it must not be forced to a single unit.
4. Authorization for consumption exits follows the current policy (normally Production Supervisor or designated responsible).

---

## 8. Cross-Cutting Rules (Applicable)

1. **Business date vs system timestamp:** The business date is the calendar date entered by the actor. The registration timestamp is system-generated. These are distinct.
2. **Correction with audit:** If an error is made, the record may be corrected with full audit trail.
3. **Operational window:** Corrections by operational roles within the policy-defined window. Outside the window, only SysAdmin may edit.
4. **Permissions are configurable:** Current actor assignments are operational practice, not rigid.

---

## 9. Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-SUP-01 | A supply movement can be registered with all required fields in a single operation. |
| AC-SUP-02 | Each movement type (reception, consumption, return) is recorded distinctly. |
| AC-SUP-03 | The unit of measure is specific to the supply item, not forced to a universal unit. |
| AC-SUP-04 | Consumption movements require authorization per policy. |
| AC-SUP-05 | All business dates accept calendar dates (no time component). |
| AC-SUP-06 | All registration timestamps are system-generated. |
| AC-SUP-07 | Stock traceability is independent from the lot history of bales or finished product. |

---

## 10. Open Items and Pending Decisions

| # | Item | Owner | Impact | Status |
|---|---|---|---|---|
| 1 | **Supply catalog:** Should supply items reference a managed catalog or remain free text? | Product | Affects data quality and reporting | Open |
| 2 | **Stock levels and alerts:** Should the system maintain running stock levels per item and trigger alerts? | Product | Affects inventory visibility | Open |
| 3 | **Batch/lot tracking for supplies:** Should certain supplies (e.g., dyes, chemicals) track supplier batch numbers for quality traceability? | Product | Affects traceability depth | Open |

---

## References

- [Bale Management PRD](./bale-management.md) — raw-material bale lifecycle (separate capability)
- [Production Identity PRD](./production-identity.md) — production identity definition
- [Finished Product PRD](./finished-product.md) — PT management
- [Warehouse Area PRD](./overview.md) — area-level overview
- [Access Control](../access-control.md) — permission policies
