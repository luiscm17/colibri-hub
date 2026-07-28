---
document_type: domain
status: active
implementation: not-started
scope: operation/lot-processing
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# Domain Model: Lot Processing

> **Part of:** Operation Unit — Colibri Hub
> **Source:** `docs/prd/operation/lot-processing.md`
> **Next:** DB Schema → API Design → Tasks

---

## 1. Bounded Context

This domain model lives within the **Operation** bounded context. The Lot is the
central entity that crosses domain boundaries via its unique code `NN-GGGG-NNN`,
but each domain owns its own data.

```
┌──--───────────────────────────────────────────┐
│               OPERATION                       │
│                                               │
│  Lot ─── 6 StageRecords (ordered)             │
│            ├── StageData (varies by stage)     │
│            └── 0..N Observations               │
│  Lot ─── 0..1 QualityClassification            │
│                                               │
│  Reads from Warehouse: code, title, color,     │
│  client, specifications                        │
└─────────────────────────────────────────────┘
         │                    ▲
         │ code + specs       │ quality + observations
         ▼                    │
┌─────────────────────────────────────────────┐
│               WAREHOUSE                       │
│  Owns: lot identity, stock movements,         │
│  PT disposition                               │
└─────────────────────────────────────────────┘
```

**Shared catalogs** (referenced but owned elsewhere):

- Employee (responsible, supervisor)
- Shift (A, B, C)
- Machine (for Devanado equipment check)
- Title (hilado type)

---

## 2. Entities

### 2.1 Lot

The central entity. Represents a set of skeins that share the same title, color,
and client, tracked through 6 sequential stages.

| Attribute | Description | Notes |
|---|---|---|
| `codeId` | Unique identifier `NN-GGGG-NNN` | Assigned by Warehouse, read-only in Operation |
| `yarnCount` | Yarn thickness designation (e.g. 2/18) | From Warehouse specifications |
| `color` | Target color for dyeing | From Warehouse, applied by Dyehouse |
| `colorId` |    |    |
| `client` | Destination client | From Warehouse |
| `clientId` |   |  |
| `specifications` | Order details from Warehouse | Read-only reference |
| `currentStage` | Current stage in the lifecycle | **Derived** from the last StageRecord that exists |
| `qualityClassification` | Final quality verdict | Set by Quality at stage 6 |
| `isClosed` | Whether the lot completed Operation | True when Warehouse registers PT reception |

**Lifecycle stages:** `En_Almacen → En_Inventario → En_Tintoreria → En_Secado → En_Devanado → En_Embolsado → En_Calidad → En_Almacen_PT`

---

### 2.2 StageRecord

Records a lot's passage through one stage. Each record is created when the
responsible operator **finishes** their work and saves the stage data. The act
of saving IS the state transition — it implicitly makes the lot available for
the next stage.

| Attribute | Description |
|---|---|
| `lot` | Reference to the Lot |
| `stageType` | Which stage (Inventory, Dyeing, Drying, Winding, Bagging, Quality) |
| `sequenceNumber` | Stage order (1-6), enforces sequential flow |
| `businessDate` | Calendar date when the work occurred (user input, no time component) |
| `shift` | Shift when the work was performed (A, B, C) |
| `responsible` | Person who performed and registered the work |
| `supervisor` | Supervisor on duty |
| `stageData` | Stage-specific technical data (see [section 3](#3-stage-specific-data-by-stagetype)) |
| `observations` | 0..N observations recorded during this stage |
| `createdAt` | System timestamp (date+time) — when the record was saved. This is the lot's transition moment. |

**Rules:**

- A StageRecord for stage N can only be created if a StageRecord for stage N-1 already exists
- The `createdAt` of each StageRecord serves as the timestamp of the lot's transition to the next stage
- Each stage adds NEW data — it never modifies data from previous stages
- The responsible can edit ONLY their own StageRecord, within the operational correction window, with full audit trail
- Outside the window, only SysAdmin can edit
- StageData structure varies by stageType

---

### 2.3 Observation

Documents an incident or defect found during a stage.

| Attribute | Description |
|---|---|
| `stageRecord` | Reference to the parent StageRecord |
| `category` | Predefined category for this stage type (see [section 4](#4-observation-categories-per-stage-type)) |
| `details` | Optional free-text context |

**Rules:**

- Category is mandatory when an observation exists
- Details is optional
- Categories are predefined per stage type (dropdown)
- Observations are append-only; existing observations are not deleted

---

### 2.4 QualityClassification

The final quality verdict assigned by Quality Control at stage 6.

| Attribute | Description |
|---|---|
| `lot` | Reference to the Lot |
| `classification` | One of: `Standard`, `WithNomenclature`, `Flagged` |
| `nomenclature` | Optional special designation |
| `visualDefects` | List of visual defects found |
| `internalDefects` | List of internal defects found |
| `inspectedBy` | Quality inspector |
| `inspectionDate` | When the inspection was completed |

**Classifications:**

| Value | Meaning |
|---|---|
| `Standard` | No defects or minor defects within tolerance |
| `WithNomenclature` | Special designation affecting classification/value |
| `Flagged` | Documented defects or conditions requiring decisions within Operation or informing delivery conditions to Warehouse |

**Nomenclatures:**

- `AT` — Alta torsión (high twist)
- `FT` — Fuera de tabla (off-spec)
- `VARR` — Con varilla (with rod)
- `D` — Degradado (downgraded)

---

### 2.5 QualitySendNote

When a lot is in "Espera Validación Almacén" state (after Quality Send), users
from Operation can add notes documenting problems that were fixed, corrections
that were applied, or conditions under which the lot is being delivered.

| Attribute | Description |
|---|---|
| `lot` | Reference to the Lot |
| `noteText` | Free-text description of what was fixed or what condition exists |
| `author` | User who wrote this note |
| `createdAt` | System timestamp (date+time) when the note was written |

**Rules:**

- Notes are **append-only** — once written, a note is never edited or deleted
- Multiple notes can exist for the same lot (a thread of updates)
- Each note has its own author and timestamp
- Notes serve as evidence that issues were addressed before Warehouse acceptance
- Warehouse reads these notes when deciding whether to accept the lot

---

## 3. Stage-Specific Data (by StageType)

Each stage type carries its own technical data structure. These are **value objects**
embedded within their respective StageRecord — they have no identity of their own.

### 3.1 InventoryData

| Attribute | Description |
|---|---|
| `title` | Yarn title for this lot (from specifications) |
| `skeinCount` | Number of skeins in the lot |
| `totalWeight` | Total weight of the lot (kg) |

### 3.2 DyeingData

| Attribute | Description |
|---|---|
| `skeinCount` | Number of skeins received |
| `netWeight` | Net weight entering the dyeing process (kg) |
| `vatNumber` | Vat identifier (e.g. T-03) |
| `temperature` | Process temperature |
| `materialType` | Material type (HB, N, etc.) |

### 3.3 DryingData

| Attribute | Description |
|---|---|
| `skeinCount` | Number of skeins entering drying |
| `totalWeight` | Total weight of the lot after dyeing (kg) |

### 3.4 WindingData

Covers both Devanado (cones) and Ovillado (skeins for retail).

| Attribute | Description |
|---|---|
| `format` | `Cone` or `Skein` (determines whether Devanado or Ovillado) |
| `skeinsProcessed` | Number of skeins converted |
| `unitsProduced` | Number of cones or retail skeins produced |
| `wasteKg` | Waste generated during conversion (kg) |

### 3.5 BaggingData

| Attribute | Description |
|---|---|
| `bagsUsed` | Number of bags used |
| `unitsPerBag` | Cones or retail skeins per bag |
| `wasteKg` | Waste generated during bagging (kg) |

### 3.6 QualityData

| Attribute | Description |
|---|---|
| `visualDefects` | List of visual defect categories found |
| `internalDefects` | List of internal defect categories found |
| `nomenclature` | Optional nomenclature assigned (AT, FT, VARR, D) |
| `classification` | Final classification |
| `inspector` | Quality inspector |

---

## 4. Observation Categories (per stage type)

These are the predefined categories available per stage. In the domain model,
they are **value objects** — a closed enumeration defined within Lot Processing, not user-extensible.

| StageType | Categories |
|---|---|
| **Inventory** | Insufficient skeins / Weight out of range / Incomplete emission data |
| **Dyeing** | Redye (off-color) / Temperature out of range / Contaminated vat / Wrong material |
| **Drying** | Weight out of range / Excessive moisture |
| **Winding** | Damaged cones / Wrong title / Uncalibrated equipment / Excessive waste |
| **Bagging** | Damaged bags / Wrong label / Count mismatch |
| **Quality** | Double tone / Staining / Rod / Damaged skeins / Tails / Flames / Low twist / High twist / Mix / Purge / Paraffin / Card / Double end / Bad splices / Splice count / Contamination |

---

## 5. Key Business Rules (enforced by the domain)

1. **Registration IS transition:** Saving a StageRecord automatically makes the
   lot available for the next stage. There is no separate "advance" action.
2. **Sequential progression:** A StageRecord for stage N can only be created if
   a StageRecord for stage N-1 already exists for this lot.
3. **No backtracking:** Once a lot has a StageRecord for stage N, it cannot
   return to a previous stage.
4. **State is derived:** The lot's current stage is inferred from which
   StageRecords exist — not from a manually-set field.
5. **Each stage owns its data:** A stage never modifies data from a previous
   stage. Each StageRecord adds a new layer of information.
6. **Editable within window:** The responsible can correct their own StageRecord
   within the operational time window (e.g. 24-48h). Full audit trail required.
   Outside the window, only SysAdmin can edit.
7. **Mandatory delivery:** Every lot that completes the 6 stages is delivered
   to Warehouse with full documentation, regardless of quality classification.
8. **Quality is documentation, not a gate:** Quality classifies the final product
   and documents conditions, but does not block delivery to Warehouse.
9. **Quality Send is deliberate:** After Quality completes its StageRecord, a
   separate Quality Send action marks the lot as ready for Warehouse acceptance.
10. **Subsanation notes are append-only:** When a lot is "Observed" and awaiting
    Warehouse acceptance, users add notes documenting what was fixed or what
    conditions exist. Notes are never edited or deleted — only new notes are
    appended, each with author and timestamp.

---

## 6. Related Documents

- `docs/prd/operation/lot-processing.md` — Source PRD
- `docs/prd/operation/overview.md` — Operation unit PRD
- `docs/prd/warehouse/overview.md` — Warehouse PRD (defines lot code)
