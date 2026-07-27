---
document_type: product-overview
status: active
implementation: partial
scope: global
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Colibri Hub — Product Overview

## 1. Purpose

Colibri Hub systematizes production management for a textile spinning plant,
replacing parallel Excel spreadsheets and paper forms with a single digital
system that captures, traces, and consolidates operational data.

The system serves the **Production Directorate** (Warehouse Unit + Operation
Unit) under the supervision of the Production Manager, and delivers consolidated
information to **Administration** as the formal liaison toward **Management**.

## 2. Scope

### What the system covers

- Raw material reception, storage, and controlled issuance to Operation
- Yarn spinning across 5 productive sections and 3 sequential shifts
- Lot processing through 6 sequential stages with full traceability
- Finished product verification and inventory
- Quality control with statistical sampling and special nomenclatures
- Waste tracking (real and accumulated)
- Consolidated reporting for Administration

### What is explicitly out of scope

- Commercialization and sales
- Direct Management operations (receives consolidated reports only)
- Costing methodology (deferred — placeholder for future definition)

## 3. Business Areas

| Area | Responsibility | Detailed PRD |
|------|---------------|--------------|
| **Warehouse** | Raw material custody, production identity assignment, finished product inventory, production supplies (dyes, packaging) | [`warehouse/overview.md`](./warehouse/overview.md) |
| **Operation — Yarn Spinning** | 5 sections (Preparation, Ring Frames, Winding, Twisting, Skeining), production by machine/shift/yarn count, quality sampling, waste | [`operation/overview.md`](./operation/overview.md) |
| **Operation — Lot Processing** | 6 sequential stages: Inventory → Dyeing → Drying → Winding → Bagging → Quality. Full lot traceability | [`operation/overview.md`](./operation/overview.md) |
| **Access Control** | Role-based authorization decoupled from organizational hierarchy. Permissions for registration, validation, approval, consolidation, and query | [`access-control.md`](./access-control.md) |
| **Shared Reference Data** | Yarn counts catalog (`yarn_counts`) used across Warehouse, Operation, and Lot Processing | — |

## 4. Actors

| Actor | Role in the system |
|-------|-------------------|
| **Production Manager** | Central user. Authorizes raw material issuance, supervises both units via dashboards, validates operational coherence, directs consolidation |
| **Production Secretary** | Collects shift data from Operation, assists in consolidation and follow-up |
| **Warehouse Unit Manager** | Operates receptions, issuances, verifications, and inventory control |
| **Warehouse Operatives** | Register physical movements (reception, verification, packaging, dispatch) |
| **Shift Supervisors** (×3) | Each responsible for their shift exclusively. Consolidate production, quality, lots, incidents, and novelties at shift end |
| **Supervisor-dependent staff** | Quality Control, Inventory, Dyer, Bagging — register section events per assigned permissions |
| **Administration** | Read-only consumer of consolidated production data; prepares reports for Management |
| **Management** | Receives final consolidated reports; not a direct system user |
| **Machine Operators** | Do not use the system. Their production is registered by supervisors |

> **Note:** Detailed permission matrices and capability-specific actor
> responsibilities live in the relevant capability PRDs and in
> [`access-control.md`](./access-control.md).

## 5. Data Capture Model

| Aspect | Detail |
|--------|--------|
| **Shifts** | 3 sequential shifts (morning, afternoon, night). Only one operates at a time |
| **Physical capture** | During the shift, operators produce and annotate on paper/auxiliary forms |
| **Digital capture** | At shift end, the responsible person registers all shift data in a single session |
| **Concurrency** | No simultaneous registration between shifts — each registers after the prior one finishes |
| **Timestamps** | Reflect when events physically occurred, not when they were digitized |
| **Immutability** | Once registered, data is not modified. Corrections are new records with traceability to the original |

## 6. Transversal Rules

1. **Authorization is decoupled from hierarchy.** Permissions (register, validate,
   approve, consolidate, query) can be reassigned without redesigning business
   processes. Policy defined in [`access-control.md`](./access-control.md).

2. **Data captured at source.** Whoever generates or controls the data registers
   it directly — no reconstruction from parallel spreadsheets.

3. **End-to-end traceability.** Every raw material lot maintains an auditable
   history of its journey: sections, dates, incidents. History is never deleted.

4. **Controlled editing and audit.** Critical records (warehouse movements,
   production, authorizations, lot events) are never deleted. Allowed
   corrections preserve complete historical traceability.

5. **Shift continuity.** The next shift can query previous shift data without
   loss or duplication. The system supports handoff between sequential shifts.

6. **Designed for uncertainty.** Processes not yet fully defined (supplies
   detail, costing) can be added without restructuring existing modules.

7. **Transmission to Administration is a system output.** Consolidated
   information is built from operational data, not manually assembled.

## 7. Architecture and Context Boundaries

The system is organized into bounded contexts aligned with business areas.
For context ownership, dependencies, aggregate families, and inter-context
handoffs, see:

- [`../architecture/system-overview.md`](../architecture/system-overview.md)
- [`../architecture/context-map.md`](../architecture/context-map.md) _(Phase 3)_

## 8. Risks and Open Items

| Item | Risk | Impact |
|------|------|--------|
| Supplies detail (Dyeing + Packaging) | Defined but not implemented | Warehouse module must cover all 4 subdomains |
| Commercialization integration | Out of scope, but finished product feeds their process | Define boundary and output format |
| Production Manager bottleneck | If system demands too much interaction | Dashboard UX must be immediate, not demanding |
| Adoption | Users come from Excel and paper | UX must prioritize simplicity |
| Historical migration | Data in Excel, papers, various spreadsheets | Requires separate plan |

## 9. Related Documents

| Document | Purpose |
|----------|---------|
| [`warehouse/overview.md`](./warehouse/overview.md) | Warehouse area scope and capabilities |
| [`operation/overview.md`](./operation/overview.md) | Operation area scope and capabilities |
| [`access-control.md`](./access-control.md) | Authorization policy |
| [`../domain/ubiquitous-language.md`](../domain/ubiquitous-language.md) | Domain glossary |
| [`../architecture/system-overview.md`](../architecture/system-overview.md) | System architecture |
