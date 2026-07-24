# Yarn EPR — Backend Architecture

> Backend design reference aligned with the current PRDs and the boundary decisions in
> [Architecture](./ARCHITECTURE.md) and
> [Context Boundaries and Ownership](./context-boundaries-and-ownership.md).
>
> Detailed backend technical design now lives in
> [Backend Technical Design Baseline](./backend/backend-technical-design.md).
> Conceptual persistence rules now live in
> [Persistence Design Principles](./backend/persistence-design-principles.md).
> Applied Supabase migrations are authoritative for the implemented Warehouse
> schema; [Warehouse DB Dictionary](../db/warehouse-dictionary.md) explains the
> current mapping. DBML remains a lower-level design artifact.
> This document remains the higher-level backend view.

---

## 1. Purpose

This document translates the current product and boundary decisions into a
backend-oriented design view.

It exists to define:

- the backend contexts that should remain separate
- the kinds of aggregates and record families each context is likely to own
- the invariants and handoffs that must shape application services and ports
- the dependency direction between contexts

It does **not** define:

- database tables or SQL design
- endpoint shapes in detail
- frontend workflow behavior
- infrastructure choices beyond the contracts the backend will likely need

---

## 2. Backend design principles

1. **Boundaries follow the current domain map.** Backend modules must align with
   **Warehouse**, **Yarn Spinning**, **Lot Processing**, **Access Control**, and
   **Shared Reference Data**.
2. **Warehouse defines the single lot identity.** Inventory records assembly
   facts and later Lot Processing stages append their history to that same identity.
3. **Yarn Spinning and Lot Processing must stay separate.** They do not share
   the same aggregate root, timeline, or record semantics.
4. **Business records support controlled edits with audit trail.** The backend
   must not assume strict append-only behavior for critical business records;
   within the operational correction window, edits follow scoped RBAC/policy,
   and outside that window only SysAdmin may edit.
5. **Recorder assignment is policy-driven.** The domain must not hard-code
   Supervisor as the default recorder.
6. **Warehouse state dimensions stay separate.** Quality state,
   availability/disposition, and physical presentation are different concerns.
7. **Access Control is a policy context.** It authorizes actions and scopes; it
   does not own business workflow meaning.

---

## 3. Suggested per-context internal structure

Each backend context can follow the same logical shape:

```text
<context>/
├── domain/          # aggregates, value objects, domain services, invariants
├── application/     # use cases / commands / queries / orchestration
├── ports/           # repository, policy, external read-model, integration contracts
└── adapters/        # persistence, HTTP, messaging, auth, external integrations
```

This is a **logical structure**, not a final filesystem contract. The important
rule is conceptual isolation between contexts.

Code-facing names should follow the aliases defined in
[Architecture](./ARCHITECTURE.md).

---

## 4. Context map for the backend

```mermaid
flowchart LR
    AC[Access Control\nPolicy + RBAC]
    SRD[Shared Reference Data\nYarn counts]
    W[Warehouse\nRaw-material batches + Bale custody + stock lifecycle]
    YS[Yarn Spinning\nContinuous production records]
    LP[Lot Processing\nStage history for the Warehouse-defined lot]

    AC --> W
    AC --> YS
    AC --> LP
    SRD --> W
    SRD --> YS
    SRD --> LP
    W --> YS
    W --> LP
    YS --> LP
    LP --> W
```

---

## 5. Context: Warehouse

### Purpose

Own raw-material batch registration, independent Bale custody/lifecycle, stock
movements, production identity definition, finished-product reception, and
downstream warehouse lifecycle decisions.

### Core aggregates / record families

- **RawMaterialBatch** — shipment grouping identified by `ShipmentNumber`
- **Bale** — independently identified aggregate and custody/lifecycle owner
- **Raw-material receiving action** — application orchestration that registers one complete batch and one or more bales in one transaction
- **Production Identity Definition** — documentary/commercial identity later
  reused across contexts
- **Material Emission to Production** — stock movement and production handoff
- **Finished Product Reception** — warehouse re-entry under the same identity
- **PT Operational Classification** — warehouse availability/disposition and
  handling decisions
- **PT Exit / Return Records** — sale, transfer, return, and similar warehouse
  lifecycle records
- **Supply Movement Records** — non-lot warehouse stock for production inputs

### Important invariants / business rules

- Raw material is received as **bales**, not as a production lot.
- `RawMaterialBatch` is not a production lot; it groups one or more bales and
  shared shipment evidence.
- Reception is an application action, not a domain aggregate. The current
  collective POST registers the complete batch; omitted bales are not silently appended later.
- A Bale delivery records `delivered_at`, rejects repeat delivery, and changes
  custody from `IN_WAREHOUSE` to `IN_PRODUCTION`; it does not mean processed.
- Production identity is defined **after** raw-material reception as bales, as a separate business
  act.
- Warehouse owns the single lot identity; Lot Processing owns the operational
  records appended to it.
- Finished-product reception continues the same production identity and visible
  lot code without collapsing Warehouse ownership into Lot Processing history.
- Warehouse must keep these dimensions separate:
  - quality state reported by Operation
  - warehouse availability/disposition
  - physical presentation / storage form
- Warehouse can document inconsistencies during PT reception; that is not the
  same as rewriting Operation history.
- Critical warehouse records support controlled edits with full audit trail.
- Header/detail persistence and historical `reception_id` names may remain for
  compatibility without dictating domain aggregate boundaries.

### Likely ports / contracts

- `WarehouseRecordRepository`
- `ProductionIdentityRepository`
- `StockBalanceReadPort`
- `WarehouseAuthorizationPolicyPort`
- `LotProcessingDeliveryReadPort`
- `AuditTrailWriterPort`
- `PeriodClosurePolicyPort`

### Consumes from other contexts

- **Access Control**: action + scope authorization
- **Access Control**: canonical users for audit references
- **Shared Reference Data**: yarn counts
- **Lot Processing**: delivery condition, lot quality state, delivery history,
  delivered quantities/physical presentation
- **Yarn Spinning**: no direct ownership dependency; usually only indirect
  planning/reference effects through Warehouse identity and Lot Processing output

---

## 6. Context: Yarn Spinning

### Purpose

Own continuous production records before Inventory assembles a lot.

### Core aggregates / record families

- **Production Discharge Records** by machine / shift / yarn count
- **Progress Records** for sections that summarize input-output flow
- **Process Quality Records** for section/machine quality control
- **Spinning Waste Records** by machine group / section
- **Skein Output Availability** as the business output that feeds lot assembly

### Important invariants / business rules

- Yarn Spinning has **no lot aggregate** and **no lot timeline**.
- Its continuity is organized by section, machine, shift, business date, and
   yarn count — not by lot-stage history.
- The backend must model Madejeras (Skeining) output as skein availability for Inventory assembly,
  not as the start of a lot-stage history.
- Net weights and derived production values should be computed/validated by
  domain rules rather than treated as arbitrary user-entered facts.
- Waste and quality belong to the spinning context even if recorder assignment is
  configurable by policy.
- Supervisor is a supervisory actor, not the default recorder in the domain
  model.
- Critical operational records support controlled edits with audit trail and
  policy-based correction windows.

### Likely ports / contracts

- `ProductionRecordRepository`
- `ProgressRecordRepository`
- `ProcessQualityRepository`
- `WasteRecordRepository`
- `SkeinAvailabilityReadModelPort`
- `YarnSpinningAuthorizationPolicyPort`
- `AuditTrailWriterPort`

### Consumes from other contexts

- **Access Control**: who may register, validate, approve, or correct records
- **Access Control**: canonical users for audit references
- **Shared Reference Data**: yarn counts
- **Warehouse**: production identity, yarn-count/color/client/specification context,
  and material availability references

---

## 7. Context: Lot Processing

### Purpose

Own the operational stage history from Inventory assembly through Quality Send back
to Warehouse.

### Core aggregates / record families

- **Lot Stage Record** — the main record family for Inventory stage, Dyeing, Drying,
  Winding, Ball Winding, Bagging, and Quality stage
- **Stage Note / Inconvenience Records**
- **Stage Waste Records**
- **Delivery-to-Warehouse Record** with lot condition and handoff metadata

### Important invariants / business rules

- Warehouse defines the single lot identity before production; Inventory records its
  assembly facts, and Lot Processing owns the stage history appended to it.
- Each Lot Processing intervention should use its stage's dedicated record model
  rather than artificial receipt/delivery pairs:
  - inherited data from Warehouse or the previous stage
  - locally verified data
  - stage-generated data
  - stage notes/exceptions, waste, and output condition
- The lot history is sequential by stage, but a lot may have multiple legitimate
  records in the same stage, business date, or shift. These history attributes
  must not be used as a uniqueness key.
- No lot history should be flattened into generic “Operation” records.
- The Quality stage documents the lot condition for delivery; Warehouse later decides its
  own operational disposition.
- Critical stage records support controlled edits with audit trail; within the
  operational correction window, edits follow scoped RBAC/policy, and outside
  that window only SysAdmin may edit.

### Likely ports / contracts

- `LotStageRecordRepository`
- `LotStageSequencePolicyPort`
- `SkeinAvailabilityPort`
- `WarehouseIdentityReadPort`
- `LotProcessingAuthorizationPolicyPort`
- `AuditTrailWriterPort`
- `WarehouseDeliveryPort`

### Consumes from other contexts

- **Access Control**: stage-level authorization and correction permissions
- **Access Control**: canonical users for audit references
- **Shared Reference Data**: yarn counts
- **Warehouse**: production identity, lot code, yarn count, color, client/destination,
  and order specifications
- **Yarn Spinning**: skein output availability and readiness for lot assembly

---

## 8. Context: Access Control

### Purpose

Own configurable RBAC policy, scopes, permission assignments, and permission
auditability across the system.

### Core aggregates / record families

- **System Role / Capability Definition**
- **Permission Assignment**
- **Scope Definition**
- **Assignment Exception / Override**
- **Permission Change Audit Record**

### Important invariants / business rules

- Access Control is a **policy context**, not a workflow owner.
- It may answer who can register, validate, approve, correct, or administer in a
  scope; it must not redefine the business meaning of those actions.
- Organizational roles and system permissions are related but not equivalent.
- Recorder/validator/approver assignments must remain configurable.
- Exceptions must be explicit and auditable.

### Likely ports / contracts

- `AuthorizationDecisionPort`
- `PermissionAssignmentRepository`
- `ScopeRepository`
- `PermissionAuditRepository`
- `UserRoleMappingReadPort`

### Consumes from other contexts

- **Access Control owns canonical users and technical roles.**
- **Business contexts**: action names, protected resources, and scopes that need
  authorization

---

## 9. Context: Shared Reference Data

### Purpose

Provide the canonical yarn-count catalog and stable yarn-count identities reused
by multiple contexts.

### Core aggregates / record families

- **Yarn Count**

### Important invariants / business rules

- Shared Reference Data owns canonical yarn counts, not transactional meaning.
- It must not absorb warehouse rules, lot rules, or permission logic.
- Changes to reference data should remain auditable because they affect multiple
  contexts.

### Likely ports / contracts

- `YarnCountQueryPort`
- `YarnCountValidationPort`
- `YarnCountRepository`

### Consumes from other contexts

- Governance decisions about yarn-count curation

---

## 10. Single lot identity

The backend must use the Warehouse-defined production identity as the single lot
identity across both contexts.

| Concern | Owner | Backend meaning |
|---|---|---|
| **Lot identity** | **Warehouse** | Cross-context `productionIdentityId` defined after raw-material reception as bales and before production execution |
| **Operational stage history** | **Lot Processing** | Inventory assembly and later stage facts linked directly to `productionIdentityId` |

### Design consequence

- Warehouse should expose lot identity data for downstream use.
- Lot Processing should append stage records directly under that identity.
- Yarn Spinning should reference the upstream production context when needed, but
  it should not pretend to own or progress a lot aggregate.

```mermaid
flowchart LR
    F[Raw-material reception as bales\nWarehouse] --> ID[Production identity defined\nWarehouse]
    ID --> YS[Yarn Spinning\ncontinuous records only]
    ID --> INV[Inventory stage\nLot Processing]
    YS --> INV
    INV --> LOT[Stage history begins\nunder the same lot identity]
```

---

## 11. Controlled edits and audit trail

The backend should adopt a consistent correction model across contexts.

### Required behavior

- Critical business records are **not deleted silently**.
- Allowed corrections update business truth while preserving historical
  traceability.
- Within the operational correction window, edits follow scoped RBAC/policy.
- Outside that window, only SysAdmin may edit.
- The audit trail should preserve at least:
  - who changed the record
  - when it changed
  - previous values
  - new values
  - reason for correction
  - applicable authorization context

### Architecture consequence

Each business context should own:

- its own correction rules
- its own editable time-window policy when applicable
- its own audit emission or audit persistence contract

The system should therefore avoid a blanket append-only assumption in backend
design and avoid burying correction semantics inside infrastructure only.

The system may expose a broader cross-context traceability view, but that must
not collapse ownership: Lot Processing owns stage history during operation, and
Warehouse owns its own records.

---

## 12. Dependency direction and context interaction

### High-level rule

Supporting contexts point inward; business contexts depend on policy and
reference services, while peer business handoffs happen only through explicit
contracts.

```mermaid
flowchart TD
    AC[Access Control]
    SRD[Shared Reference Data]
    W[Warehouse]
    YS[Yarn Spinning]
    LP[Lot Processing]

    AC --> W
    AC --> YS
    AC --> LP
    SRD --> W
    SRD --> YS
    SRD --> LP
    W --> YS
    W --> LP
    YS --> LP
    LP --> W
```

### Interaction summary

| From | To | Why |
|---|---|---|
| Access Control | All business contexts | authorization decisions by action and scope |
| Shared Reference Data | Warehouse, Yarn Spinning, Lot Processing | canonical yarn-count IDs and validation |
| Warehouse | Yarn Spinning | production identity and material context |
| Warehouse | Lot Processing | production identity, specifications, and shared lot-code reference |
| Yarn Spinning | Lot Processing | skein output availability for Inventory assembly |
| Lot Processing | Warehouse | processed lot delivery, quality state, and handoff condition |

### Architectural constraint

No context should write directly into another context's internal record model.
Cross-context collaboration should happen through ports, published views, or
integration contracts that preserve ownership.

---

## 13. Related documents

- [Architecture](./ARCHITECTURE.md)
- [Backend Technical Design Baseline](./backend/backend-technical-design.md)
- [Persistence Design Principles](./backend/persistence-design-principles.md)
- [Warehouse DBML](../db/warehouse.dbml)
- [Context Boundaries and Ownership](./context-boundaries-and-ownership.md)
- [Master PRD](../prd.md)
- [Access Control PRD](../prd/access-control.md)
- [Operation PRD](../prd/operation.md)
- [Yarn Spinning PRD](../prd/operation/yarn-spinning.md)
- [Yarn Spinning Records](../prd/operation/yarn-spinning-records.md)
- [Lot Processing PRD](../prd/operation/lot-processing.md)
- [Lot Processing Records](../prd/operation/lot-processing-records.md)
- [Warehouse PRD](../prd/warehouse.md)
- [Warehouse Records](../prd/warehouse/warehouse-records.md)
