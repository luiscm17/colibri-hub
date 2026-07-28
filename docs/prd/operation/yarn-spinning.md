---
document_type: prd
status: active
scope: operation/yarn-spinning
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Hilatura (`Yarn Spinning`)

> **Domain PRD — Hilatura (`Yarn Spinning`)**
>
> Continuous spinning process that transforms raw material into yarn
> of a specific yarn count through 5 production sections.
>
> Belongs to the Operation unit. For general context, actors, and
> cross-cutting rules, see [Operation Overview](./overview.md).
>
> **Next:** `docs/domain/operation/yarn-spinning.md` (Domain Model)

---

## 1. Purpose and Scope

### 1.1 Purpose

Document the **Hilatura (`Yarn Spinning`)** process,
a continuous and sequential flow that transforms raw-material bales received from
Warehouse into yarn of a specific yarn count, ready for output as skeins
from Madejeras (Skeining) and subsequent use in Lot Processing. In
this process, the lot does not yet exist as a physical entity and no lot code
is used.

### 1.2 Scope

Covers the 5 production sections, their production records, progress records,
process quality, and waste:

| Section                       | Production | Progress           | Quality            | Waste |
| ----------------------------- | ---------- | ------------------ | ------------------ | ----- |
| Preparación (Preparation)     | ✓          | ✓ (input/output)   | ✓ (samples)        | ✓     |
| Continuas (Ring Spinning)     | ✓          | ✓ (input/output)   | ✓ (samples)        | ✓     |
| Bobinados (Bobbin Winding)    | ✓          | —                  | ✓ (body/km/cuts)   | ✓     |
| Retorcido (Twisting)          | ✓          | ✓ (input/output)   | ✓ (random)         | ✓     |
| Madejeras (Skeining)          | ✓          | —                  | ✓ (random)         | ✓     |

**Not included:**

- The subsequent lot processing (Lot Processing, documented in `lot-processing.md`)
- Lot quality (final evaluation before handoff to Warehouse, in `lot-processing.md`)
- Supply or raw-material management (Warehouse responsibility)

### 1.3 Dependencies

| Process                                        | Relationship                                                              |
| ---------------------------------------------- | ------------------------------------------------------------------------- |
| **Warehouse (input)**                          | Delivers the raw material and the information needed for its processing   |
| **Lot Processing (output)**                    | Receives the produced skeins for subsequent lot assembly                  |

---

## 2. The 5 Sections

### 2.1 Process Flow

```
Raw material (bales)
  │
  ▼
PREPARACIÓN (Preparation)
  │  Machines: PSJ (Preparación A/B) + FIN (Finisor A/B)
  │  Records: FIN produce, PSJ only progress
  ▼
CONTINUAS (Ring Spinning)
  │  Machines: spinning frames
  │  Records: net weight, spindle count
  ▼
BOBINADOS (Bobbin Winding)
  │  Machines: winders
  │  Records: net weight, spindle count (no progress)
  ▼
RETORCIDO (Twisting)
  │  Machines: twisters
  │  Records: net weight, spindle count (managed by Inventory)
  ▼
MADEJERAS (Skeining)
  │  Production: skeins (not spindles)
  │  Exit point toward the next process
  ▼
  LOT PROCESSING
```

### 2.2 Section Summary

| #   | Section                         | Machine type         | Production unit        | Has progress | Who records prod. | Who records progress |
| --- | ------------------------------- | -------------------- | ---------------------- | ------------ | ----------------- | -------------------- |
| 1   | **Preparación (Preparation)**   | PSJ (A/B), FIN (A/B) | kg (net), roving count | Yes          | Quality           | Quality              |
| 2   | **Continuas (Ring Spinning)**   | Spinning frames      | kg (net), spindle count | Yes         | Quality           | Quality              |
| 3   | **Bobinados (Bobbin Winding)**  | Winders              | kg (net), spindle count | No          | Quality           | —                    |
| 4   | **Retorcido (Twisting)**        | Twisters             | kg (net), spindle count | Yes         | Inventory         | Inventory            |
| 5   | **Madejeras (Skeining)**        | Skeining machines    | skein count, net weight | No          | Inventory         | —                    |

> **Note:** The current recording assignment in Bobinados (Bobbin Winding) falls on Quality,
> although it may be reassigned by access policy.

---

## 3. Production Records

### 3.1 Record Nature

The production record is **granular, per production discharge**. A single machine
can have multiple production discharges in one shift (of the same or different yarn count),
or it can have none.

**Granularity:** 1 production discharge × 1 machine × 1 shift × 1 date × 1 yarn count.

**Recording moment:** Although production discharges physically occur throughout
the shift (e.g., 8:00 AM, 10:30 AM, 1:00 PM), the digital recording of **all**
of them is performed at the end of the shift (e.g., 2:00 PM) in a single capture session.
The system captures the actual timestamp of each production discharge, but it is not a real-time
system. See [section 2.4 of the master PRD](../product-overview.md#5-data-capture-model).

### 3.2 Spindle Count

Each machine has between 20 and 200 spindles (depending on the section and machine type).
It is not practical to weigh each spindle individually. Therefore, the **number of
operative spindles** is a fundamental data point. The weight calculation varies by record
type:

| Record type | Weight calculation |
|---|---|
| **Progress (input/output/accumulated)** | 1 spindle is weighed as a sample (gross − tare for that spindle), all spindles are assumed to have the same weight, and the result is multiplied by the total number of spindles. |
| **Production discharge (granular production)** | The full cart/bin/drum is weighed (total gross weight). Net is calculated as: **gross_total − (spindle_tare × spindle_count) − cart_weight**. |

> In production discharges, net weight is not simply gross − tare of a
> container, because each production discharge contains the output of multiple spindles
> and is transported in a cart that has its own weight.

### 3.3 Data Recorded per Production Discharge

#### Preparación (Preparation), Continuas (Ring Spinning), Bobinados (Bobbin Winding), Retorcido (Twisting)

For each production discharge the following is recorded:

- **Machine** that produced
- **Shift** and **date**
- **Shift supervisor**
- **Yarn count** produced (e.g., 2/18, 2/32). May differ from the initial yarn count
  of the shift if there was a change.
- **Total gross weight** of the production discharge (cart or full container)
- **Tare per spindle** (for adjusted calculation)
- **Number of operative spindles** on the machine
- **Cart/container weight** used to transport the production discharge
- **Current assignment:** Quality in Preparación (Preparation), Continuas (Ring Spinning), and Bobinados (Bobbin Winding); Inventory in Retorcido (Twisting)

#### Madejeras (Skeining)

For each production discharge the following is recorded:

- **Machine** that produced
- **Shift** and **date**
- **Shift supervisor**
- **Yarn count**
- **Number of skeins** produced
- **Estimated unit weight** per bundle (1 bundle = 10 skeins ~ 5 kg; in some cases the skein must weigh 600 g instead of 500 g per yarn-count requirement)
- **Current assignment:** Inventory

> [!NOTE] Madejeras (Skeining)
> Production is operator-dependent, not machine-cycle-dependent.
> The primary metric is the number of skeins produced. It does not use spindles or tare.
> Total weight is estimated as: skeins × unit weight. In Yarn Spinning, Madejeras (Skeining)
> does not yet assemble lots: it only produces skeins of a given weight for the
> next process.

### 3.4 Production Rules

1. **Net weight always calculated:** The system calculates net weight by applying the
   corresponding formula (with spindles and cart for production discharge; with proportional
   sampling for progress). Direct net weight entry is not accepted.
2. **Only FIN machines produce in Preparación (Preparation):** FIN-A and FIN-B are the
   only machines that record production in Preparación (Preparation). PSJ machines only record progress.
3. **Madejeras (Skeining) does not use spindles or tare:** Madejeras (Skeining) records skeins produced
   (numeric value) and estimated unit weight. The spindle-based calculation does not apply.
4. **Multiple production discharges per shift:** A machine can have several production discharges
   in one shift, or none. Each production discharge is an independent record.
5. **Yarn count change during the shift:** A machine can change yarn count
   within the same shift, or work with different yarn counts simultaneously
   on different spindles. Each production discharge carries its corresponding yarn count.
6. **No lot in Yarn Spinning:** In this process, the lot does not yet exist
   as a physical entity and no lot code is recorded. The output of Yarn Spinning is
   skeins and production records per section/machine/shift/yarn count.
7. **Controlled editing with audit trail:** Operational records may
   be corrected when a data entry error exists, but every edit must leave
   a complete audit trail of the change, including user, date, previous values,
   new values, and reason for correction.
8. **Operational correction window:** Editing may be allowed during a
   defined window after the shift (for example 24 or 48 hours, according to
   current policy).
9. **Restricted editing outside the window:** Once the operational correction
   window expires, only the **SysAdmin** role may edit the record,
   maintaining the same mandatory audit trail.

---

## 4. Progress Records

### 4.1 Record Nature

The progress record is a **report/summary** per machine, shift, and yarn count.
Unlike production (granular per production discharge), the progress record consolidates
in a single record:

- What **entered** the machine/section as raw material
- What **was produced** (sum of the shift's production discharges)
- What **exits** as product toward the next section

That is, the progress record is a **sum of the production detail** plus the
input and output data of the process.

**Weight calculation in progress:** Unlike production discharges (which are weighed
by full cart), in progress records the input and output weight is calculated
**by spindle sampling**: 1 spindle is weighed, its tare is subtracted, and the result is multiplied
by the total number of spindles on the machine. All spindles are assumed to
have the same weight.

### 4.2 Sections with Progress

Only 3 sections record progress:

| Section | Who records | Data recorded |
|---|---|---|
| **Preparación (Preparation)** | Quality | Input weight, total discharged weight (sum of production discharges), output weight |
| **Continuas (Ring Spinning)** | Quality | Input weight, net weight in machine, total discharged weight, spindle count, hours worked, output weight |
| **Retorcido (Twisting)** | Inventory | Input weight, net weight in machine, total discharged weight, spindle count, hours worked, output weight |

**Bobinados (Bobbin Winding) and Madejeras (Skeining) do not record progress.**

### 4.3 Granularity

Each progress record represents: **1 machine × 1 shift × 1 date × 1 yarn count**.

### 4.4 Purpose of Progress Records

Progress records enable:

- **Cross-validation:** The total discharged weight (from progress) must match
  the sum of individual production discharges.
- **Waste calculation:** The difference between input weight and output weight reveals
  losses in the section.
- **Productivity:** kg/hour per machine and section.
- **Process status:** Knowing how much material each section is processing.

---

## 5. Process Quality

### 5.1 Responsible Party

**Quality** is responsible for process quality control in ALL
sections of Hilatura (`Yarn Spinning`), without exception. Frequency and method vary
by section.

### 5.2 Methods by Section

| Section         | Method                     | Description                                                                                       |
| --------------- | -------------------------- | ------------------------------------------------------------------------------------------------- |
| **Preparación (Preparation)** | Samples           | Samples are taken from Preparación A and B to evaluate consistency                                |
| **Continuas (Ring Spinning)** | Samples (12/machine/type) | 12 samples per machine and yarn type. Evaluates CV%, tenacity, elongation              |
| **Bobinados (Bobbin Winding)** | Body/km/cuts      | No samples are taken. Machine data is recorded: body, kilometers, cuts per bobbin                 |
| **Retorcido (Twisting)** | Random             | Random tests. Lower frequency than in Preparación (Preparation) and Continuas (Ring Spinning)     |
| **Madejeras (Skeining)** | Random             | Random tests. Madejeras (Skeining) does not have systematic process quality (evaluated at lot level) |

### 5.3 Data Recorded

For each quality control the following is captured:

- **Section, machine, and shift** evaluated
- **Sample type:** according to the yarn count evaluated (HB, N, CH, etc.)
- **Test results:** vary by method:
  - *Samples:* individual values for each sample, CV%, tenacity
  - *Body/km/cuts:* data recorded by the machine
  - *Random:* results of the tests performed
- **Who records** (Quality)

### 5.4 Quality Rules

1. **All sections are evaluated:** No exceptions. Quality tests
   all machines in all sections.
2. **Variable frequency:** Preparación (Preparation) and Continuas (Ring Spinning) have systematic sampling.
   Retorcido (Twisting) and Madejeras (Skeining) have random sampling. Bobinados (Bobbin Winding) uses machine
   recording instead of samples.
3. **Special nomenclatures:** As a result of process quality and lot
   quality, Quality may assign nomenclatures to the finished product according to current policy.
   This applies to the complete product that will later be delivered to the
   next process, not to individual machines.
4. **Separate records:** Process quality in Hilatura (`Yarn Spinning`) is distinct and
   independent from lot quality (final evaluation in Lot Processing).

---

## 6. Waste

### 6.1 Responsible Party

**Inventory** records the real waste from ALL sections and machines
in the plant, including Hilatura (`Yarn Spinning`).

### 6.2 Data Recorded

For each waste record the following is captured:

- **Section** and **machine group** (weighed together)
- **Shift** and **date**
- **Weight** of the waste
- **Type:** real or accumulated
- **Who records** (Inventory)

### 6.3 Waste Rules

1. **Waste by machine group:** Machines are physically weighed together.
   They are not weighed machine by machine.
2. **Real waste vs accumulated waste:** Real waste is recorded by
   Inventory. Accumulated waste is managed by Production. The sum
   of both is called "theoretical waste."
3. **Madejeras (Skeining) — exceptional waste:** Skeins outside
   specification are not recorded as conventional waste. They return
   to an earlier stage of the process for reprocessing.
4. **Controlled waste editing:** If a data entry error exists, the
   record may be corrected with a complete audit trail of who edited, when,
   what changed, and why.
5. **Temporal restriction:** Waste correction follows the same
   operational window defined for production records. Outside that
   window, only **SysAdmin** may edit.

---

## 7. Actors and Responsibilities

| Actor                      | Role in Hilatura (`Yarn Spinning`)                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Supervisor**             | Supervises shift production. Responsible for the plant and personnel. Verifies data coherence.                          |
| **Quality Control**        | Performs quality tests in ALL sections and machines. Currently records production and progress for Preparación (Preparation), Continuas (Ring Spinning), and Bobinados (Bobbin Winding). |
| **Inventory**              | Records production and progress for Retorcido (Twisting) and Madejeras (Skeining). Records real waste for all sections. |
| **Embolsado (Bagging)**    | Does not directly participate in Hilatura (`Yarn Spinning`). Their involvement begins in Lot Processing.                |
| **Dyeing Personnel**       | Does not participate in Hilatura (`Yarn Spinning`).                                                                     |

---

## 8. Functional Requirements

### 8.1 Production

| ID       | Requirement                                                                                                                           |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| YS-PR-01 | The system must allow recording production by machine, shift, date, and yarn count for each section.                                   |
| YS-PR-02 | The system must calculate net weight automatically (gross − tare).                                                                     |
| YS-PR-03 | The system must validate that only FIN (A/B) machines record production in Preparación (Preparation).                                  |
| YS-PR-04 | The system must allow Madejeras (Skeining) recording with skeins and unit weight, not gross weight/tare.                               |
| YS-PR-05 | The system must support a configurable assignment of who records per section. Current operation assigns Quality for Preparación (Preparation), Continuas (Ring Spinning), and Bobinados (Bobbin Winding); and Inventory for Retorcido (Twisting) and Madejeras (Skeining). |
| YS-PR-06 | The system must allow the Supervisor to query shift production across all sections.                                                     |

### 8.2 Progress

| ID       | Requirement                                                                                                                            |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| YS-AV-01 | The system must allow recording progress (input/output) by machine, shift, date, and yarn count for Preparación (Preparation), Continuas (Ring Spinning), and Retorcido (Twisting). |
| YS-AV-02 | The system must calculate the input − output difference to detect waste in each section.                                                |
| YS-AV-03 | Bobinados (Bobbin Winding) and Madejeras (Skeining) must not have a progress form.                                                     |

### 8.3 Process Quality

| ID       | Requirement                                                                                                                                           |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| YS-QL-01 | The system must allow recording quality controls by machine, shift, and section.                                                                       |
| YS-QL-02 | The system must support the 3 quality methods: samples (Preparación, Continuas), body/km/cuts (Bobinados), and random (Retorcido, Madejeras).          |
| YS-QL-03 | The system must allow recording special nomenclatures for the finished product at the lot level (not per machine).                                     |
| YS-QL-04 | Quality must be able to query the quality history of any machine and section.                                                                          |

### 8.4 Waste

| ID       | Requirement                                                                                                                                        |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| YS-WS-01 | The system must allow recording waste by machine group, not by individual machine.                                                                  |
| YS-WS-02 | The system must distinguish between real waste (recorded by Inventory) and theoretical waste (real + accumulated).                                   |
| YS-WS-03 | The system must handle the special case of Madejeras (Skeining): skeins outside specification are not recorded as waste; they are marked for reprocessing. |

### 8.5 Cross-Cutting

| ID       | Requirement                                                                                                                |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| YS-TR-01 | The system must allow controlled editing of production, progress, quality, and waste records when a data entry error exists, preserving a complete audit trail of the change. |
| YS-TR-02 | The system must record for each correction: editing user, date/time, previous values, new values, and reason for the change. |
| YS-TR-03 | The system must validate that the user has the corresponding permission according to the current access policy for each record type. |
| YS-TR-04 | The system must allow editing by operational roles only within a defined window after the shift (for example 24 or 48 hours). |
| YS-TR-05 | Once the operational correction window expires, only the **SysAdmin** role may edit Yarn Spinning records.                   |
| YS-TR-06 | The Supervisor must be able to view a consolidated summary of production, progress, quality, and waste for their shift.      |

---

## 9. Metrics and Reports

From the recorded data (production, progress, quality, and waste),
the system must calculate the following metrics for each section's dashboard
and the Supervisor's consolidated view.

### 9.1 Production Metrics

| Metric | Unit | Purpose |
|---|---|---|
| **Total discharged** | kg | Sum of all production discharges in the period (shift/day/week) by machine, yarn count, and section |
| **Number of discharges** | — | Number of production discharges performed in the period. Helps detect discharge frequency |
| **Average per discharge** | kg | Total discharged / number of discharges. Consistency control |

### 9.2 Progress Metrics

| Metric | Unit | Purpose |
|---|---|---|
| **Productivity** | kg/h | Total weight discharged / hours worked. Per machine and section |
| **Waste** | kg | Input weight − output weight. Material loss in the section |
| **Relative waste** | % | (input − output) / input × 100 |
| **Effective hours** | h | Hours recorded per machine in the shift |

### 9.3 Quality Metrics

| Metric | Purpose |
|---|---|
| **Average CV%** | Yarn consistency in sample tests |
| **Samples outside tolerance** | Percentage of samples that do not pass established limits |
| **Average body** | Imperfection level in Bobinados (Bobbin Winding) |
| **Cuts per bobbin** | Cut frequency in Bobinados (Bobbin Winding) |

### 9.4 Waste Metrics

| Metric | Unit | Purpose |
|---|---|---|
| **Real waste** | kg | Sum of waste recorded by Inventory in the period |
| **Waste rate** | % | Real waste / total produced × 100. Per section and machine group |

### 9.5 Cross-Cutting Metrics

| Metric | Purpose |
|---|---|
| **Production vs planning** | Compares actual production against the planned baseline (see [section 3.5 of operation overview](./overview.md#35-production-planning)). Alerts if there is significant deviation. **Note:** Specific baselines per yarn count (kg/day targets) are a valid business rule excluded from this capability. |
| **Spindle utilization** | Operative spindles / total machine spindles. Percentage of utilized capacity |
| **Shift consolidated** | Production, quality, and waste aggregated by Supervisor for their daily report |

> **Note:** Detailed formulas, temporal filters (overlap with previous shift),
> and specific calculation logic will be documented in the metrics specification
> or in the domain design, not in this PRD.

---

## 10. Glossary

| Term                      | Definition                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Finisor**               | Finisor machines in Preparación (Preparation). The only machines that record production in that section.                         |
| **Pasaje**                | Preparación A/B machines (PSJ). Only record progress (input/output), not production.                                            |
| **Yarn count**            | Designation of yarn thickness (e.g., 2/18, 2/32, 4/9). Produced during Hilatura (`Yarn Spinning`).                              |
| **Spindle**               | Production unit in spinning machines (Continuas, Bobinados, Retorcido).                                                         |
| **Skein**                 | Production unit in Madejeras (Skeining). Yarn is presented as skeins (loose hanks), not cones.                                  |
| **Body**                  | Quality measurement in Bobinados (Bobbin Winding). Records imperfections per unit of length.                                    |
| **CV%**                   | Coefficient of variation — measure of yarn consistency in quality tests.                                                         |
| **Special nomenclature**  | Quality suffix or mark that may later be associated with the finished product in the subsequent process. Assigned by Quality.    |
| **Real waste**            | Waste recorded by Inventory during the process, by machine group.                                                               |
| **Theoretical waste**     | Sum of real waste + accumulated waste.                                                                                          |
