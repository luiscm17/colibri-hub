---
document_type: prd
status: active
implementation: partial
scope: warehouse
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Warehouse Area Overview

> **Part of:** Production Directorate — Colibri Hub
> **Dependencies:** [`docs/prd/product-overview.md`](../product-overview.md) (Master PRD)
> **Domain model:** [`docs/domain/warehouse.md`](../../domain/warehouse.md)

## 1. Purpose

The Warehouse unit manages physical custody and traceability of raw materials, finished products, and production supplies. It is responsible for recording all stock movements (entries and exits), maintaining inventory accuracy, and providing production identity that accompanies lots throughout their lifecycle.

This document defines the area-level scope, responsibilities, and capabilities. Detailed business rules and requirements for each capability are maintained in their own PRDs.

## 2. Scope

The Warehouse area covers:

- Reception, custody, and emission of raw material bales
- Definition of production identity (lot code, client, color, title)
- Reception of finished product from Operations, storage, and dispatch
- Management of production supplies (dyes, chemicals, packaging, spare parts, lubricants, cones, tubes, etc.)
- Stock movement history and auditability
- Periodic stock closings (monthly, annual, extraordinary)

### Out of scope

- The 6 productive stages and their state machine (→ [Operation Overview](../operation/overview.md))
- Process quality control and special PT nomenclatures (→ Operation)
- Real and accumulated waste (→ Operation / Production Manager)
- Invoicing, accounting, and fiscal books
- Detailed data model and API design (→ `docs/domain/`)

## 3. Organizational Context

The Warehouse unit reports to the **Production Directorate** through the **Production Manager**.

```text
Production Directorate
├── Production Manager
│   ├── Warehouse Unit
│   │   └── Warehouse Unit Manager
│   │       └── Operational Assistants
│   └── Operations Unit
│       └── Supervisors (1 per shift)
```

### Roles

| Role | System Responsibilities |
| --- | --- |
| **Warehouse Unit Manager** | Supervises RM reception, emissions to Operations, PT verification, and stock control. Reports to Production Manager. |
| **Operational Assistant** | Executes physical movements: reception, verification, bagging, and dispatch. |

> Permission assignment is cross-cutting and defined in [`docs/prd/access-control.md`](../access-control.md).

## 4. Capabilities

Each capability is documented in its own PRD with detailed business rules, flows, and acceptance criteria:

| Capability | Description | PRD |
| --- | --- | --- |
| **Bale Management** | Raw material reception, bale identity, inventory, and emission to Operations | [`bale-management.md`](bale-management.md) |
| **Production Identity** | Lot code definition, client/color/title assignment, independent of physical bale reception | [`production-identity.md`](production-identity.md) |
| **Finished Product** | PT reception from Operations, operational availability, presentation, dispatch, and returns | [`finished-product.md`](finished-product.md) |
| **Production Supplies** | Supply categories, reception, consumption, returns, and per-category units of measure | [`production-supplies.md`](production-supplies.md) |

### Cross-cutting concerns

- **Movement history and change tracking** — stock movements are editable under policy; every correction preserves actor, timestamp, reason, and before/after values
- **Stock closings** — monthly, annual, and extraordinary closings freeze movements and compute balances using `(Previous Balance + Entries) − Exits = Balance`
- **Configurable permissions** — registration, validation, authorization, and correction capabilities can be reassigned without altering functional flows

## 5. Operating Principles

1. **Bale reception ≠ production identity.** Physical RM reception and lot identity definition are distinct business acts.
2. **Mandatory traceability.** Every lot maintains an auditable history from definition through final dispatch, shared between Warehouse and Operations under a single identity.
3. **Balance consistency.** System stock must match physical stock; discrepancies require documented adjustments.
4. **Each domain writes its own history.** Warehouse records its movements without interfering with Operations data. The lot history is unified but composed from contributions of both domains.
5. **Two PT exit channels.** Finished product exits either by direct sale to client or by transfer to Marketing/Sales.
6. **Configurable permissions.** Authorization assignments (who registers, validates, authorizes, corrects) can change by organizational policy without redesigning Warehouse processes.

## 6. Dependencies

### Warehouse depends on

| Dependency | Reason |
| --- | --- |
| [Operation Overview](../operation/overview.md) | Receives PT from Operations; reads lot productive data |
| [`docs/prd/access-control.md`](../access-control.md) | Permission and authorization model |
| Master PRD ([`docs/prd/product-overview.md`](../product-overview.md)) | Data capture model, organizational principles |

### Other areas depend on Warehouse

| Dependent | Reason |
| --- | --- |
| **Operations** | Receives RM bales emitted by Warehouse; returns PT to Warehouse |
| **Marketing/Sales** | Receives PT transfers for unit sales |
| **Production Manager** | Consumes stock reports, authorizes emissions and PT exits |

## 7. Domain Boundary

| Domain | Writes | Does Not See |
| --- | --- | --- |
| **Warehouse** | Bale reception, production identity definition, emission to Operations, PT reception, exits, returns | The 6 productive stages, quality, real waste |
| **Operations** | 6 lot stages, quality, nomenclatures, real waste | Internal Warehouse stock movements, clients, balances |

The lot history is unique, but each domain writes and queries only its own information under the same production identity.
