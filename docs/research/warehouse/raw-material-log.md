---
document_type: research
status: active
implementation: partial
scope: warehouse/raw-material
authority: evidence
owner: product
last_reviewed: 2026-07-27
---

# Raw Material Reception — Current DB

> **Purpose:** Understand what data is recorded when raw material arrives from a supplier, based on real Excel files (`CAMION 01-2026 HB.xlsx`, `RESUMEN MAT. PRIMA 2026.xlsx`) and knowledge of the current physical receipt.
>
> **Outcome:** Ground truth for the data model in `docs/domain/warehouse.md`.
>
> **Scope:** Strictly what happens at **reception** — when the truck arrives and bales enter the warehouse.
> Downstream processes (enrichment, emission to production, bale delivery) are noted as references only.

---

## 1. Physical flow

```
Supplier truck arrives ──► Physical receipt (document) ──► Bales unloaded ──► Weighing ──► DB registration
```

There are **two distinct things** at reception:

1. **Physical document** — a receipt-like list that comes with the truck. It lists all bales delivered to the warehouse.
2. **DB registration** (the CAMION Excel file) — what the warehouse fills into the system. Mirrors the physical document but may add system-generated data (lot code, entry number, etc.).

---

## 2. The physical receipt (documento físico)

The supplier delivers a document similar to a **receipt** that lists every bale in the shipment. Each bale entry includes:

| Field | Description |
|---|---|
| **Provider** | Sudamericana de Fibras (Typically) |
| **Receiption Date** | date |
| **Client ID** | 2000000161 (Illampu Textiles ID) |
| **No. Pedido Cliente** | e.g. 20002417 |
| **No. de entrega** | e.g. 80008182 |
| **Material** | e.g. HB, CICLAN, N, etc |
| **Type** | e.g. 1.6, 3.3, 4.1, etc |
| **No. Partida** | e.g. 60701 |
| **Bale number** | ID identifier (e.g., 1727, 1728...) |
| **Net weight (kg)** | Individual bale weight |
| **Tara weight (kg)** | bag wieght typically 1.90 kg |
| **Gross Weight (kg)** | individual bale weight |
| **Observations** | Any notes about the bale's condition |

This is the source document. The warehouse then enters this data into the system.

---

## 3. The DB registration (CAMION Excel)

The file `CAMION NN-GGGG <TYPE>.xlsx` is what the warehouse fills into the DB. Relevant sheets for raw material reception:

### 3.1 FARDOS sheet — Bale packing list

| Field | Example | Notes |
|---|---|---|
| **Truck ID** | `CAMION 01-2026` | Format: `CAMION NN-GGGG` |
| **Reception date** | 2025-12-06 | When the truck was received |
| **Total bales** | 86 | Count of bales received |
| **Partida number** | 50704 | External reference number from the supplier |
| **Bale number** | 1727–2025 | ID bale identifier from the physical receipt |
| **Net weight per bale** | ~220–226 kg | Varies per bale, recorded individually |
| **Delivery date** | 2026-01-14 | (Downstream) When delivered to production |
| **Delivered kilos** | 221.6 | (Downstream) Quantity delivered to production |

**Key:** The bale is the central entity at reception. Each bale has its own identity (`baleNumber`) and weight. The bale numbers follow a **global sequential namespace** — they are NOT per truck. For example, CAMION 01-2026 uses numbers 1727–2025.

After reception, bales remain in storage and are delivered to production gradually.

### 3.2 RESUMEN sheet — Summary

| Field | Example | Notes |
|---|---|---|
| **Entry date** | 2025-12-06 | Date of reception |
| **Partida number** | 50901 / 10104 | Reference numbers from supplier |
| **Raw material arrived** | 19,310.2 kg | Total net weight (sum of all bales) |
| **Estimated lots** | `(total - waste) / 204.4` | ~86 lots, where 204.4 kg is the standard per-lot production weight (this is a production planning estimate, not stored at reception) |

### 3.3 Other sheets in the CAMION file

The CAMION file also contains sheets for **PRODUCTO TERM** (finished product), **DESPERDICIOS** (daily waste), and detailed item breakdowns. These are **not** raw material reception data — they belong to downstream production tracking.

---

## 4. The lot code: `NN-GGGG-NNN`

The lot code is generated at reception. It will later accompany the material through production and finished product.

### 4.1 Current format

| Part | Meaning | Example |
|---|---|---|
| `NN` | Distributor truck sequence number | `01`, `02`, `03` ... `58` |
| `GGGG` | Management year (last 2 digits) | `26` (2026) |
| `NNN` | Sequential item number within (truck × year) | `001`, `005`, `086` |

### 4.2 Code duplication problem

From the SIC JAC system data (finished product inventory), **76 codes are duplicated** — same `NN-GGGG-NNN` assigned to different material types (HB vs ALPACA/SM N vs SM):

```
code       description                    type
03-26-01   FUCSIA 3039 2/13               ALPACA / SM N
03-26-01   CELESTE 7034 2/32              HB
```

The root cause: the code format does **not** include the fiber/material type, so different material streams within the same truck compete for the same sequential numbers.

### 4.3 Proposed fix

The lot code must be globally unique. Two approaches:

**Option A: Add material type to existing format**

```
GGGG-MMMMM-NNNN
```

| Part | Meaning | Example |
|---|---|---|
| `GGGG` | Full year | `2026` |
| `MMMMM` | Material type | `HB` (Hila de Bisagra), `AN` (Alpaca/SM N), `SM` (Semi-mate), `CI` (Ciclan) |
| `NNNN` | Global correlative per year | `0001`, `0002`... |

**Option B: Surrogate key + display code**

- DB primary key: UUID or bigserial (guaranteed unique)
- Human-readable display code: `NN-GGGG-NNN` (auto-generated, for reference only)

---

## 5. What the data model needs for reception

### 5.1 Truck Reception (header)

Created once when the truck arrives:

| Field | Description | Source |
|---|---|---|
| `receptionNumber` | Auto-generated, sequential per year | System |
| `truckCode` | Distributor truck ID (e.g., `01`, `02`) | Physical receipt / supplier |
| `materialType` | Fiber type (HB, TIPO N, S/MATE, CICLAN, etc.) | Physical receipt |
| `supplierId` | FK → Supplier catalog | Supplier |
| `invoiceNumber` | Supplier invoice / receipt number | Physical receipt |
| `partidaNumber` | External reference number | Physical receipt |
| `receptionDate` | When the truck arrived | Warehouse |
| `totalGrossKg` | Gross weight (bales + packaging) | Scale |
| `totalNetKg` | Sum of individual bale net weights | Calculated |
| `authorizedBy` | Person who authorized reception | Warehouse |
| `receivedBy` | Warehouse assistant who received | Warehouse |
| `observations` | Any notes about the reception | Warehouse |

### 5.2 Bale (fardo)

Each bale in the truck is recorded individually:

| Field | Description | Source |
|---|---|---|
| `baleNumber` | Global sequential bale identifier | Physical receipt |
| `receptionId` | FK → TruckReception | System |
| `netWeightKg` | Individual bale weight | Scale / receipt |
| `observations` | Bale condition notes (damaged, partial, etc.) | Warehouse |

### 5.3 Lot (identity only)

The lot code is generated at reception, but **not enriched** until later (enrichment phase):

| Field | Description |
|---|---|
| `code` | Unique lot identifier (format TBD) |
| `receptionId` | FK → TruckReception |
| `status` | `received` (initial state) |

---

## 6. Material types catalog (from reception data)

Based on real incoming trucks recorded in `RESUMEN MAT. PRIMA 2026.xlsx`:

| Material type | Description | Examples from data |
|---|---|---|
| `HB` | Hila de Bisagra (standard) | CAMION 01 HB, 02 HB... |
| `HB 3,3` | HB finer count | CAMION 03 HB 3,3 |
| `TIPO N 4,1` | Type N fiber | CAMION 03 TIPO "N" 4,1 |
| `S/MATE HB` | Semi-mate HB | CAMION 06 S/MATE HB |
| `S/MATE N` | Semi-mate Type N | CAMION 06 S/MATE "N" 2,2 |
| `CICLAN` | Recycled fiber blend | CICLAN (various trucks) |
| `TOPS ALPACA` | Alpaca tops | TOPS S/FINA ALPACA, TOPS S/FINA ALPACA CLARO, TOPS S/FINA ALPACA OSCURO |
| `TOPS OVEJA` | Sheep tops | TOPS OVEJA |
| `NEGRO` | Black colored fiber | CAMION 32 NEGRO 3,6 |

This catalog is needed for lot code generation and must be stable.

---

## 7. Post-reception (reference only)

For context, what happens AFTER reception is outside this document's scope:

1. **Enrichment** — Order data is added to the lot: client, requested color, title, type N/CH.
2. **Emission to production** — MP leaves warehouse for the operation area.
3. **Bale delivery** — Bales are consumed gradually, tracked in `ENTREGA DE FARDOS` daily log.

---

*Generated from: `docs/reference/warehouse/raw/CAMION 01-2026 HB.xlsx`, `docs/reference/warehouse/raw/RESUMEN MAT. PRIMA 2026.xlsx`, `docs/research/warehouse/sic-jac-reports.md`*
