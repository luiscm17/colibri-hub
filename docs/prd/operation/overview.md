---
document_type: prd
status: active
implementation: not-started
scope: operation
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Operation Unit — Area Overview

> **Area PRD** for the Operation Unit within the Production Directorate.
>
> This document defines the scope, actors, capabilities, and relationships
> of the Operation area. Detailed business rules for each productive process
> live in their own PRDs:
>
> - [Yarn Spinning](./yarn-spinning.md) — 5 productive sections (continuous flow)
> - [Lot Processing](./lot-processing.md) — Per-lot lifecycle (dyeing through delivery)

---

## 1. Scope

The Operation Unit is responsible for transforming Raw Material (MP) received
from the Warehouse into Finished Product (PT) ready for physical verification
and subsequent delivery back to Warehouse.

It covers the entire productive operation of the textile plant:

| Process | Nature | Granularity |
|---------|--------|-------------|
| **Yarn Spinning** | Continuous sequential flow | Machine × shift × yarn title |
| **Lot Processing** | Independent per-lot lifecycle | Lot |
| **Process Quality** | Cross-cutting quality control | All sections and machines |
| **Waste** | Cross-cutting waste registration | Machine group × section |

### Boundaries

| Boundary | Detail |
|----------|--------|
| **Input** | Complete bales received from Warehouse, plus production identity (`production_identity_id`, `lot_code`, title, color, client/destination) defined by Warehouse. |
| **Output** | Processed lots approved by Quality and delivered to Warehouse for PT physical verification. |
| **Excluded** | MP/PT/supplies inventory management, valuation, costing, accounting closes (Warehouse and Administration responsibility). |

---

## 2. Actors

All operational roles within the Operation Unit are assigned **per shift**.
Each shift has its own Supervisor and dependent roles.

| Actor | Reports to | Scope |
|-------|-----------|-------|
| **Supervisor** | Production Manager | Full responsibility for MP processing during shift; coordinates operational staff; consolidates production records. Does not act as direct registrar unless explicitly enabled by access policy. |
| **Quality Control** | Supervisor | Quality testing across ALL plant sections and machines. Approves lots for Warehouse delivery. Registers production/progress for Preparation and Ring Spinning. |
| **Inventory** | Supervisor | Physical lot assembly under Warehouse-defined identity; tracking through delivery. Registers production/progress for Twisting and Skeining. Registers real waste across all sections. Receives daily MP from Warehouse. |
| **Dyeing Personnel** | Supervisor | Operates the dyeing process within the lot lifecycle. |
| **Packaging** | Supervisor | Coordinates and registers winding, balling, and packaging operations. Reports to Supervision. |

> **Configurable permissions:** Role-to-capability assignments reflect current
> or expected operations. The organization may reassign registration, validation,
> or approval at any section or stage through the cross-cutting access policy
> defined in `docs/prd/access-control.md`.

---

## 3. Capabilities

### 3.1 Yarn Spinning (Continuous Flow)

Transforms raw material through 5 sequential sections into skeins:

1. Preparation
2. Ring Spinning (Continuas)
3. Winding (Bobinados)
4. Twisting (Retorcido)
5. Skeining (Madejeras)

Detailed section rules, quality parameters, and production records are defined
in [yarn-spinning.md](./yarn-spinning.md).

### 3.2 Lot Processing (Per-Lot Lifecycle)

Takes skeins produced by Yarn Spinning and processes them through:

1. Inventory (lot assembly)
2. Dyeing (Tintorería)
3. Drying (Secado)
4. Winding/Balling (Devanado)
5. Packaging (Embolsado)
6. Quality (lot approval)

Detailed stage rules, state machine, and delivery criteria are defined
in [lot-processing.md](./lot-processing.md).

### 3.3 Process Quality

Quality Control performs testing across ALL sections and machines of the plant.
Frequency and method vary by section (systematic in Preparation and Ring Spinning,
random in Twisting and Skeining, machine-record in Winding).

### 3.4 Waste Registration

Waste is registered by machine group (not individual machine) across all sections.
Distinguishes between real waste (registered during process) and accumulated waste
(managed by Production).

### 3.5 Production Planning

The Production Manager plans MP processing based on orders and a fixed monthly
base production (~60 000 kg/month). The system supports planned vs. actual
production visibility and deviation alerts.

### 3.6 Daily Shift Report

At shift end, the Supervisor consults a consolidated report covering production
by section, lot status, quality, and waste. This feeds the daily report sent
to Administration by the Production Manager.

---

## 4. Relationships

| Related Area | Relationship |
|--------------|-------------|
| **Warehouse** | Provides MP + production identity at input; receives approved PT at output. Warehouse defines lot identity (`production_identity_id`, `lot_code`); Operation never generates its own identities. |
| **Access Control** | Governs which roles can register, validate, or approve at each section/stage. Operation documents current assignments; Access Control enables reassignment without process redesign. |
| **Production Manager** | Supervises both Warehouse and Operation units. Authorizes MP emissions, plans production priorities, consolidates information for Administration. |
| **Administration** | Receives consolidated daily production reports. Owns valuation and costing (outside Operation scope). |

---

## 5. Subdomain Map

| Subdomain | PRD | Status |
|-----------|-----|--------|
| Yarn Spinning (5 sections) | [yarn-spinning.md](./yarn-spinning.md) | Active |
| Lot Processing (6 stages + state machine) | [lot-processing.md](./lot-processing.md) | Active |
| Process Quality | Included in yarn-spinning.md | Active |
| Waste | Distributed across both detail PRDs | Active |
| Lot Quality | Included in lot-processing.md | Active |

---

## 6. Deferred Decisions

| Decision | Status |
|----------|--------|
| _(none at this time)_ | — |
