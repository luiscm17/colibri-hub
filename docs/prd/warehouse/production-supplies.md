---
document_type: prd
status: active
scope: warehouse/production-supplies
authority: normative
owner: product
last_reviewed: 2026-08-01
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
- **Dashboard and filtered queries** for stock and movement history.

Production supplies are consumable materials required by the production process. They do not share the unique lot history of finished product — they have their own stock traceability.

### Relationship to Other Capabilities

| Capability | Relationship |
| --- | --- |
| Bale Management | Separate capability; raw material (bales) is not a supply |
| Finished Product | Separate Warehouse capability; supplies are not tracked as part of a Finished Product or its `lot_code` |
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
| --- | --- | --- |
| Warehouse Personnel | Operational executor | Registers receptions, consumption exits, and returns |
| Production Supervisor | Authorizer | Authorizes consumption by Production (per policy) |
| System | Automated | Generates timestamps, enforces constraints |

> **Note on permissions:** Actor assignments are configurable by access policy (see `docs/prd/access-control.md`).

---

## 4. Supply Categories

| Category | Typical Unit of Measure | Examples |
| --- | --- | --- |
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
| --- | --- | --- |
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

## 8. Supplies Dashboard and Query Capabilities

### 8.1 Purpose

The Supplies workspace provides a dashboard and filtered movement history so authorized users can consult stock without entering a registration flow.

### 8.2 Minimum Query Views

- Current stock by supply item, category, and natural unit of measure.
- Receptions, consumption exits, and supplier returns for a selected period.
- Movement detail by movement number.
- History filtered by business date, category, item, movement type, supplier or destination, and unit of measure.

Filters refine an authorized query and are not permissions. Quantities with different units of measure must not be added into a misleading universal total.

### 8.3 Permission Behavior

- `Read` permits dashboard, stock, movement-detail, and history consultation for the authorized Supplies scope.
- `Write` permits the authorized supply-movement registrations.
- `Edit` and `Edit Outside the Operational Window` govern corrections.
- Actions are independent. `Write` does not grant `Read` implicitly.
- The backend enforces data access; hiding a component in the UI is not sufficient authorization.

---

## 9. Cross-Cutting Rules (Applicable)

1. **Business date vs system timestamp:** The business date is the calendar date entered by the actor. The registration timestamp is system-generated. These are distinct.
2. **Correction with audit:** If an error is made, the record may be corrected with full audit trail.
3. **Operational window:** Correction rights follow the independent `Edit` and `Edit Outside the Operational Window` actions defined by access policy.
4. **Permissions are configurable:** Current actor assignments are operational practice, not rigid.

---

## 10. Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-SUP-01 | A supply movement can be registered with all required fields in a single operation. |
| AC-SUP-02 | Each movement type (reception, consumption, return) is recorded distinctly. |
| AC-SUP-03 | The unit of measure is specific to the supply item, not forced to a universal unit. |
| AC-SUP-04 | Consumption movements require authorization per policy. |
| AC-SUP-05 | All business dates accept calendar dates (no time component). |
| AC-SUP-06 | All registration timestamps are system-generated. |
| AC-SUP-07 | Stock traceability is independent from the lot history of bales or finished product. |
| AC-SUP-08 | A user with `Read` for Supplies can consult the dashboard and authorized history without receiving registration rights. |
| AC-SUP-09 | Dashboard totals do not combine quantities expressed in incompatible units of measure. |

---

## References

- [Bale Management PRD](./bale-management.md) — raw-material bale lifecycle (separate capability)
- [Finished Product PRD](./finished-product.md) - Finished Product lifecycle (separate capability)
- [Warehouse Area PRD](./overview.md) — area-level overview
- [Access Control](../access-control.md) — permission policies
