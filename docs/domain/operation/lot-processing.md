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
| `currentStage` | Current stage in the lifecycle | Updated as lot advances |
| `qualityClassification` | Final quality verdict | Set by Quality at stage 6 |
| `isClosed` | Whether the lot completed Operation | True when delivered to Warehouse |

**Lifecycle stages:** `En_Almacen → En_Inventario → En_Tintoreria → En_Secado → En_Devanado → En_Embolsado → En_Calidad → En_Almacen_PT`

---

### 2.2 StageRecord

Records a lot's passage through one stage. Each lot has exactly 6 records, one
per stage, created sequentially.

| Attribute | Description |
|---|---|
| `lot` | Reference to the Lot |
| `stageType` | Which stage (Inventory, Dyeing, Drying, Winding, Bagging, Quality) |
| `sequenceNumber` | Stage order (1-6), enforces sequential flow |
| `entryTimestamp` | When the lot physically entered this stage |
| `entryShift` | Shift when the lot was received |
| `entryResponsible` | Person who received the lot |
| `entrySupervisor` | Supervisor on duty at entry |
| `exitTimestamp` | When the lot physically left this stage |
| `exitShift` | Shift when the lot was delivered |
| `exitResponsible` | Person who delivered the lot |
| `exitSupervisor` | Supervisor on duty at exit |
| `stageData` | Stage-specific technical data (see [section 3](#3-stage-specific-data-by-stagetype)) |
| `observations` | 0..N observations recorded during this stage |

**Rules:**

- `entryTimestamp` must be >= previous stage's `exitTimestamp`
- Stage N+1 cannot be created until Stage N has an `exitTimestamp`
- Once `exitTimestamp` is set, stage data is immutable
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
- Observations are append-only once the stage is closed

---

### 2.4 QualityClassification

The final quality verdict assigned by Quality Control at stage 6.

| Attribute | Description |
|---|---|
| `lot` | Reference to the Lot |
| `classification` | One of: `Standard`, `WithNomenclature`, `WithObservations`, `Rejected` |
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
| `WithObservations` | Documented defects that don't prevent use but affect quality |
| `Rejected` | Significant defects preventing first-quality commercialization |

**Nomenclatures:**

- `AT` — Alta torsión (high twist)
- `FT` — Fuera de tabla (off-spec)
- `VARR` — Con varilla (with rod)
- `D` — Degradado (downgraded)

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
they are **value objects** — a fixed catalog, not user-extensible.

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

1. **Sequential progression:** Stage N must be closed (have `exitTimestamp`) before
   Stage N+1 can be created.
2. **No backtracking:** Once a lot advances to the next stage, it cannot return
   to a previous stage.
3. **Immutability:** Once a StageRecord is closed (`exitTimestamp` is set), its
   `stageData` and `observations` cannot be modified. Corrections are new Observations.
4. **Mandatory delivery:** Every lot that completes the 6 stages is delivered
   to Warehouse with full documentation, regardless of quality classification.
5. **Quality is documentation, not a gate:** Quality classifies the final product,
   but does not block delivery.

---

## 6. Related Documents

- `docs/prd/operation/lot-processing.md` — Source PRD
- `docs/prd/operation.md` — Operation unit PRD
- `docs/prd/warehouse.md` — Warehouse PRD (defines lot code)
