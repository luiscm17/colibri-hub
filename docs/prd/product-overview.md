---
document_type: product-overview
status: active
scope: global
authority: normative
owner: product
last_reviewed: 2026-08-01
---

# Colibri Hub - Product Overview

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
- Costing methodology (excluded from this system; requires a separate capability definition)

## 3. Business Areas

| Area | Responsibility | Detailed PRD |
| ------ | --------------- | -------------- |
| **Warehouse** | Raw material custody, production identity assignment, finished product inventory, production supplies (dyes, packaging) | [`warehouse/overview.md`](./warehouse/overview.md) |
| **Operation - Yarn Spinning** | 5 sections (Preparation, Ring Frames, Winding, Twisting, Skeining), production by machine/shift/yarn count, quality sampling, waste | [`operation/overview.md`](./operation/overview.md) |
| **Operation - Lot Processing** | 6 sequential stages: Inventory -> Dyeing -> Drying -> Winding -> Bagging -> Quality. Full lot traceability | [`operation/overview.md`](./operation/overview.md) |
| **Access Control** | Role-based authorization decoupled from organizational hierarchy. Permissions combine a general action (Read, Write, Edit, Edit Outside the Operational Window, or Manage Access) with an explicit business scope | [`access-control.md`](./access-control.md) |
| **Shared Reference Data** | Yarn counts catalog (`yarn_counts`) used across Warehouse, Operation, and Lot Processing | - |

## 4. Actors

| Actor | Role in the system |
| ------- | ------------------- |
| **Production Manager** | Central user. Authorizes raw material issuance, supervises both units via dashboards, validates operational coherence, directs consolidation |
| **Production Secretary** | Collects shift data from Operation, assists in consolidation and follow-up |
| **Warehouse Unit Manager** | Operates receptions, issuances, verifications, and inventory control |
| **Warehouse Operatives** | Register physical movements (reception, verification, packaging, dispatch) |
| **Shift Supervisors** (x3) | Each responsible for their shift exclusively. Consolidate production, quality, lots, incidents, and novelties at shift end |
| **Supervisor-dependent staff** | Quality Control, Inventory, Dyer, Bagging - register section events per assigned permissions |
| **Administration** | Read-only consumer of consolidated production data; prepares reports for Management |
| **Management** | Receives final consolidated reports; not a direct system user |
| **Machine Operators** | Do not use the system. Their production is registered by supervisors |

> [!NOTE]
> These are business actors and responsibilities, not hardcoded RBAC
> roles. "Machine Operator" specifically identifies the person who manipulates
> production equipment and is not currently a direct system user. Configurable
> RBAC roles or presets use non-ambiguous references such as Manager, Director,
> Unit Head, Section Responsible, and, where applicable, Secretary. The generic
> role name "Operator" is avoided.
>
> Detailed responsibility rules live in the relevant capability PRDs. Effective
> authorization is defined only through configurable roles and explicit
> action-and-scope permissions in [`access-control.md`](./access-control.md).

## 5. Data Capture Model

| Aspect | Detail |
| -------- | -------- |
| **Shifts** | 3 sequential shifts (morning, afternoon, night). Only one operates at a time |
| **Physical capture** | During the shift, operators produce and annotate on paper/auxiliary forms |
| **Digital capture** | At shift end, the responsible person registers all shift data in a single session |
| **Concurrency** | No simultaneous registration between shifts - each registers after the prior one finishes |
| **Timestamps** | Reflect when events physically occurred, not when they were digitized |
| **Controlled editing** | Registered data can be corrected within the operational window under RBAC policy. Every correction preserves actor, timestamp, reason, and before/after values. Identity fields and consumed events cannot be altered. |

## 6. Transversal Rules

1. **Authorization is decoupled from hierarchy.** Business job titles and
   reporting lines do not grant access by themselves. Configurable roles combine
   the general actions Read, Write, Edit, Edit Outside the Operational Window,
   and Manage Access with explicit business scopes. Business acts such as
   register, validate, approve, or consolidate retain their domain meaning, but
   they are not independent general RBAC actions. The owning PRD identifies the
   action and scope required for each protected operation. Policy is defined in
   [`access-control.md`](./access-control.md).

2. **Read supports scoped consultation.** Read authorizes consultation within an
   explicit business scope. The same action may be presented through a dashboard,
   table, detail view, report, or another query-oriented interface. Presentation
   format does not create a separate permission.

3. **Section and consolidated dashboards have different scopes.** A section
   dashboard summarizes information for its section and may offer filters such as
   date or shift. The consolidated dashboard is a transversal view that may
   combine information from several sections, business contexts, or plant areas.
   It is not owned exclusively by Yarn Spinning. Access to section dashboards
   does not automatically grant access to the consolidated dashboard, and
   consolidated Read access grants no Write or Edit permission in the represented
   contexts.

4. **Filters are query criteria, not authorization.** Date, shift, section, and
   similar filters refine the information displayed. Labels such as Shift Summary
   or Daily Summary describe filtered dashboard queries and are not independent
   capabilities, actions, or scopes.

5. **Data captured at source.** Whoever generates or controls the data registers
   it directly - no reconstruction from parallel spreadsheets.

6. **End-to-end traceability.** Every raw material lot maintains an auditable
   history of its journey: sections, dates, incidents. History is never deleted.

7. **Controlled editing and audit.** Critical records (warehouse movements,
   production, authorizations, lot events) are never deleted. Allowed
   corrections preserve complete historical traceability.

8. **Shift continuity.** The next shift can query previous shift data without
   loss or duplication. The system supports handoff between sequential shifts.

9. **Designed for uncertainty.** Processes not yet fully defined (supplies
   detail, costing) can be added without restructuring existing modules.

10. **Transmission to Administration is a system output.** Consolidated
   information is built from operational data, not manually assembled.

## 7. Architecture and Context Boundaries

The system is organized into bounded contexts aligned with business areas.
For context ownership, dependencies, aggregate families, and inter-context
handoffs, see:

- [`../architecture/system-overview.md`](../architecture/system-overview.md)
- [`../architecture/context-map.md`](../architecture/context-map.md) _(Phase 3)_

## 8. Related Documents

| Document | Purpose |
| ---------- | --------- |
| [`warehouse/overview.md`](./warehouse/overview.md) | Warehouse area scope and capabilities |
| [`operation/overview.md`](./operation/overview.md) | Operation area scope and capabilities |
| [`access-control.md`](./access-control.md) | Authorization policy |
| [`../domain/ubiquitous-language.md`](../domain/ubiquitous-language.md) | Domain glossary |
| [`../architecture/system-overview.md`](../architecture/system-overview.md) | System architecture |
