# Yarn EPR — Context Boundaries and Ownership

> Pre-architecture artifact.
> This document defines domain boundaries and ownership decisions that must be stable before [Architecture](./ARCHITECTURE.md) is rewritten.

---

## 1. Purpose

This document exists to lock the **business boundaries**, **ownership rules**, and
**handoff language** before deeper architecture work starts.

It is intentionally **pre-technical**:

- it defines **who owns what meaning**
- it defines **where a concept starts and stops**
- it prevents [Architecture](./ARCHITECTURE.md) from mixing contexts, records, and responsibilities

It does **not** define database schema, APIs, or internal code structure.

---

## 2. Recommended bounded contexts

| Context | Why it exists | Core boundary |
|---|---|---|
| **Warehouse** | Owns raw-material batch registration, Bale custody/lifecycle, stock movements, production identity setup, and finished-product handling | Stops at warehouse-issued identity and warehouse-managed stock lifecycle |
| **Yarn Spinning** | Owns continuous spinning production records before Inventory assembles a lot | Stops at skein output and section/shift/machine records |
| **Lot Processing** | Owns the operational stage history appended after Inventory assembles the lot | Stops when Quality Send hands the lot back to Warehouse |
| **Access Control** | Owns authorization policy, scopes, and configurable permissions | Does not own business workflow semantics |
| **Shared Reference Data** | Owns the canonical shared yarn-count catalog | Does not own operational records |

**Recommendation:** treat **Yarn Spinning** and **Lot Processing** as separate contexts inside the broader **Operation Unit**, not one generic “Operation” model. They have different identities, timelines, and record semantics.

---

## 3. Context definitions

### 3.1 Warehouse

- **Core responsibility:** manage physical custody and documentary control of raw material, finished product, and production supplies; define the production identity that later travels across contexts.
- **Owns:** `RawMaterialBatch` shipment grouping; independent **Bale** identity, custody, and lifecycle; the receiving application action; production identity definition; delivery to Production; finished-product reception; warehouse availability/disposition; physical presentation; stock movements; stock balances; supply movements.
- **Does not own:** spinning production records; lot-stage progression; process quality execution; lot-stage waste; final production-stage decisions inside Operation.
- **Inbound dependencies:** Access Control; Shared Reference Data; Quality's sent-lot documentation from Lot Processing.
- **Outbound contracts / shared identifiers:** technical production identity, visible lot code, yarn count, color requirement, client/destination, and emitted quantity linkage needed by downstream contexts.

### 3.2 Yarn Spinning

- **Core responsibility:** record continuous yarn production before Inventory assembles a lot.
- **Owns:** production discharges; section progress records; process quality in spinning sections; spinning waste; skein output from Madejeras (Skeining).
- **Does not own:** warehouse stock; production identity assignment rules; Inventory assembly; lot timeline; final finished-product reception.
- **Inbound dependencies:** Access Control; Shared Reference Data; warehouse-issued production identity as external planning/reference context.
- **Outbound contracts / shared identifiers:** yarn count produced; skein availability; section/shift/machine production records; operational readiness for lot assembly.

### 3.3 Lot Processing

- **Core responsibility:** own the operational stage history appended after Inventory assembles the Warehouse-defined lot and carry it until Quality Send.
- **Owns:** lot stage records; lot timeline; lot-stage notes/exceptions; stage waste; final quality documentation for delivery; handoff back to Warehouse.
- **Does not own:** warehouse stock balances; warehouse availability/disposition; spinning-section records; permission policy; reference catalog governance.
- **Inbound dependencies:** warehouse-issued production identity and specifications; skein output from Yarn Spinning; Access Control; Shared Reference Data.
- **Outbound contracts / shared identifiers:** same technical production identity, visible lot code, operational lot stage history, Quality Send evidence, Lot Processing-owned quality state, delivery conditions, and physical presentation.

### 3.4 Access Control

- **Core responsibility:** govern who may read, register, validate, approve, correct, or administer data in each scope.
- **Owns:** roles, permissions, scopes, exceptions, and auditability of permission changes.
- **Does not own:** who is operationally responsible in the business sense; record semantics; workflow state; domain invariants.
- **Inbound dependencies:** organizational actors and scopes defined by business contexts.
- **Outbound contracts / shared identifiers:** permission assignments by action + scope; authorization decisions; auditable permission history.

### 3.5 Shared Reference Data

- **Core responsibility:** provide the canonical yarn-count values reused across contexts.
- **Owns:** the canonical `yarn_counts` catalog.
- **Does not own:** users, transactional records, lot timelines, stock balances, or permission decisions.
- **Inbound dependencies:** business governance for yarn-count curation.
- **Outbound contracts / shared identifiers:** stable yarn-count IDs and values reused by Warehouse, Yarn Spinning, and Lot Processing.

---

## 4. Explicit boundary decisions

### 4.1 Single lot identity

Warehouse defines the single lot through its technical `production_identity_id` and visible `lot_code`, including yarn count, color, customer/destination, and request data. Inventory records the assembled weight and skein count, and each later Lot Processing stage appends its own history to that same lot.

### 4.2 Warehouse vs Yarn Spinning vs Lot Processing

- **Warehouse** receives **bales**, not production lots.
- A `RawMaterialBatch`, identified by `ShipmentNumber`, groups one or more bales
  and shared receipt evidence. It is not a production lot.
- Reception is an application action, not a `Reception` or `BaleReception`
  aggregate. Each `Bale` owns its independent lifecycle.
- **Yarn Spinning** transforms material continuously and does **not** own a lot entity or lot timeline.
- **Lot Processing** starts when Inventory assembles skeins and from then on owns the lot timeline.
- The lot history delivered back to Warehouse belongs to a broader **cross-context traceability chain**, not a new warehouse-only record detached from production. Lot Processing owns the operational stage history; Warehouse owns the warehouse-side records that continue the same business identity.

### 4.3 Access Control as a policy context

Access Control must stay a **policy context**, not a hidden business owner.

- It may decide **who can record** a stage.
- It must **not redefine what the stage is**.
- It may change recorder/validator/approver assignments.
- It must **not freeze today’s job-role mapping into the domain model**.

### 4.4 Shared Reference Data

Shared Reference Data is a support context, not a dumping ground for business logic.

- keep the canonical yarn-count list and identifiers here
- keep operational meaning in the owning business context
- do not move lot rules, stock rules, or permission rules into catalogs

---

## 5. Aggregate / record ownership

| Aggregate / record family | Owning context | Ownership note |
|---|---|---|
| Raw-material batch registration | Warehouse | Application action registers one complete `RawMaterialBatch` and one or more `Bale` aggregates in one transaction; persistence shape does not define this ownership |
| Bale custody and delivery | Warehouse | Bale owns independent identity and `IN_WAREHOUSE` to `IN_PRODUCTION` transition; delivery records `delivered_at` and rejects repetition |
| Lot identity definition | Warehouse | Defines the single lot before Inventory records its assembly facts |
| MP emission to production | Warehouse | Stock movement plus production handoff |
| Warehouse supply movement | Warehouse | Independent from production lot history |
| Spinning production discharge | Yarn Spinning | Machine/shift/yarn-count record |
| Spinning progress | Yarn Spinning | Section summary, not lot history |
| Spinning process quality | Yarn Spinning | Section/machine quality, not lot-final quality |
| Spinning waste | Yarn Spinning | Continuous-process waste |
| Skein output availability | Yarn Spinning | Output contract for lot assembly |
| Lot stage record | Lot Processing | Unified lot history across stages |
| Lot-stage note / inconvenience | Lot Processing | Attached to stage history |
| Lot-stage waste | Lot Processing | Part of lot history |
| Final lot quality state and send | Lot Processing | Quality sends the validated lot and documents its delivery condition |
| PT reception from Operation | Warehouse | Warehouse accepts the same lot through its own receipt after verification; it does not change the operational history |
| PT availability / disposition | Warehouse | Separate from the Lot Processing-owned quality state, which Warehouse does not snapshot |
| PT physical presentation | Warehouse | Separate dimension from quality/disposition |
| PT sale / transfer / return | Warehouse | Warehouse stock lifecycle after reception |
| Permission policy and scope rules | Access Control | Cross-cutting authorization only |
| Canonical users and technical roles | Access Control | Authorization identity and technical RBAC roles |
| Yarn counts | Shared Reference Data | Canonical `yarn_counts` references only |

---

## 6. Cross-context handoff summary

```mermaid
flowchart LR
    W[Warehouse]
    YS[Yarn Spinning]
    LP[Lot Processing]
    AC[Access Control]
    SRD[Shared Reference Data]
    ALL[All business contexts]

    W -->|Production identity and material availability| YS
    W -->|Shared production identity, specifications, and lot code| LP
    YS -->|Skein output and readiness for Inventory assembly| LP
    LP -->|Quality Send provides validated lot history, quality state, and delivery conditions| W
    AC -->|Authorization decisions by action and scope| ALL
    SRD -->|Stable catalog identifiers and shared reference values| ALL
```

| From | To | Handoff |
|---|---|---|
| Warehouse | Yarn Spinning | Production identity and material availability for execution |
| Yarn Spinning | Lot Processing | Skein output and readiness for Inventory assembly |
| Warehouse | Lot Processing | Shared production identity, specifications, and lot code |
| Lot Processing | Warehouse | One Quality Send leaves the same lot awaiting Warehouse validation; Warehouse later accepts it once through its own receipt for the same `production_identity_id` after physical verification |
| Access Control | All business contexts | Authorization decisions by action and scope |
| Shared Reference Data | All business contexts | Stable catalog identifiers and shared reference values |

**Important:** no handoff changes ownership retroactively. A receiving context may reference prior data, but it must only write its own part.

---

## 7. Top architecture mistakes to avoid

1. **Modeling Warehouse reception of bales as if the production lot already exists.**
2. **Treating Yarn Spinning and Lot Processing as one aggregate model with one timeline.**
3. **Letting Warehouse own production-stage records after the lot returns.**
4. **Using Supervisor as the default recorder in the domain model.** Supervisor is the operational lead/consolidator, not the mandatory registrar.
5. **Hard-coding current job roles into authorization rules.** RBAC must stay configurable.
6. **Collapsing quality state, warehouse availability/disposition, and physical presentation into one status field.**
7. **Designing for strict append-only when the PRD requires controlled edits with audit trail.**
8. **Using Shared Reference Data as a home for business workflow rules.**
9. **Turning this boundary document into schema or API design too early.**

---
