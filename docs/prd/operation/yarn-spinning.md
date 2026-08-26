---
document_type: prd
status: draft
scope: operation/yarn-spinning
authority: normative
owner: product
last_reviewed: 2026-08-25
replaces: null
---

# Yarn Spinning

> **Authority:** This is the single normative source for all Yarn Spinning business rules.
> Backend specifications, frontend specifications, and domain documents derive from this PRD.
> Technical specifications may not redefine business rules documented here.

---

## 1. Business Scope

Yarn Spinning (Hilatura) is the Operation capability that transforms raw material received from Warehouse into yarn of a specific yarn count (título) through five productive sections arranged in continuous sequential flow. Its recorded output is skein production, which Lot Processing consumes to assemble the physical lot.

The capability sits between two contexts:

- **Upstream — Warehouse.** Raw-material deliveries arrive authorized from Warehouse. A delivery does not create any association between bales and lots, products, or identities.
- **Downstream — Lot Processing.** The capability hands off skein output so Lot Processing can assemble the physical lot under an existing production identity. Skeins produced in Yarn Spinning carry no lot attribution.

| Capability or Context | Relationship |
| --- | --- |
| Warehouse (upstream) | Delivers authorized raw material and the information needed to process it. Delivery does not link bales to lots, products, or production identities. |
| Lot Processing (downstream) | Receives skein output for physical lot assembly under an existing production identity and lot code. |
| Access Control | Governs who may record, correct, and consult through configurable actions and scopes. |
| Shared Reference Data | Supplies shared catalogs consumed read-only: employees, shifts, yarn counts, sections, machines, and machine groups. |

**Identity boundary.** Inside Yarn Spinning there is no lot, no lot code, no production identity, and no production run. Continuity of records is built from section × machine × business date × shift × yarn count. Physical lot assembly, lot-stage history, final lot quality evaluation, and the finished-product handoff are outside this capability and belong to Lot Processing. Raw-material custody and supplies remain Warehouse capabilities.

The capability covers five record concerns: production discharges, skeining production, progress, process quality, and waste, plus the correction policy that governs all of them.

---

## 2. Problem Statement

Spinning production is currently recorded in manual spreadsheets maintained per section and per function. This practice fails the business in four ways:

1. **Traceability.** Production continuity lives in disconnected files organized by person and shift, so reconstructing what a machine produced on a given date requires manual assembly.
2. **Reconciliation.** The control that discharged weight must match recorded progress is checked by hand; discrepancies between discharge detail and shift summaries surface late or never.
3. **Correction integrity.** Edits to already-recorded data happen silently, without a preserved actor, reason, or before-and-after evidence, so corrected figures cannot be distinguished from originals.
4. **Capture quality.** Repetitive per-machine matrices invite entry errors, calculated weights are recomputed manually, and catalog values (machines, yarn counts, employees) are hardcoded copies that drift apart.

The business needs a single record system that captures production per machine, shift, and yarn count; derives every calculated weight automatically; reconciles discharge detail against progress summaries; and makes every correction visible, attributed, and reversible in evidence while remaining irreversible in history.

---

## 3. Stakeholders and Actors

| Actor | Role | Interaction |
| --- | --- | --- |
| Shift Supervisor | Operational supervisor | Supervises shift production, verifies data coherence, and consults consolidated shift information across sections. |
| Quality Control | Process-quality executor | Performs process-quality tests across all sections. |
| Inventory | Material-flow function | Tracks material flow between sections and records material movements between them. |
| System | Automated | Calculates derived weights, enforces constraints, attributes capture timestamps, and maintains the append-only correction history. |

> **Note on responsibilities:** This document defines business capabilities, not authorizations. Which function performs each recording, validation, or correction action is determined exclusively by access policy configuration (see [Access Control](../access-control.md)). No recording assignment is fixed in this PRD.

Two further clarifications bound the actor model:

- Machine operators manipulate production equipment and are not direct system users.
- Packaging and dyeing personnel do not participate in Yarn Spinning; their involvement begins in Lot Processing.
- Material-flow views held by the inventory function derive from the production records of this capability; this capability never maintains a parallel duplicate capture of the same production facts.
- Each record attributes its capture to the authenticated session and names the shift supervisor; no additional responsibility slots exist.

---

## 4. The Five Productive Sections

Material flows through five sections in fixed order. Each section keeps its Spanish plant name alongside its canonical English term:

| # | Section | Machine types | Production record | Progress record | Production unit |
| --- | --- | --- | --- | --- | --- |
| 1 | Preparación (Preparation) | PSJ-type machines (Pasaje) and FIN-type machines (Finisor) | Production discharge — FIN-type machines only | Yes — PSJ-type machines only | Net weight in kilograms; roving count where captured |
| 2 | Continuas (Ring Spinning) | Spinning frames | Production discharge | Yes | Net weight; operative spindle count |
| 3 | Bobinados (Bobbin Winding) | Winders | Production discharge | No | Net weight; operative spindle count |
| 4 | Retorcido (Twisting) | Twisters | Production discharge | Yes | Net weight; operative spindle count |
| 5 | Madejeras (Skeining) | Skeining machines | Skeining production | No | Skein count and estimated total weight |

Machine facts:

- Preparation hosts PSJ-type machines that only record progress and FIN-type machines that produce. Machine codes are business identifiers drawn from the machine catalog (shared reference data); no specific code is fixed in this capability.
- Machines hold between roughly 20 and 200 spindles depending on section and machine type. Weighing each spindle individually is impractical, which is why the operative spindle count and per-spindle tare drive the weight calculations in [§5](#5-production-records) and [§6](#6-progress-tracking-rules).

**Capture context.** Production physically occurs throughout the shift, but digital capture happens at shift close in batch sessions. Every record distinguishes three time references: the business date and shift entered by the recorder, and the system capture timestamp registered automatically. The shift belongs to the record's capture context; assignment of people to shifts follows staff rotation administered outside this capability.

First-time capture of a record after its shift has closed is allowed only within an administrative late-capture window. The window's duration is an operational parameter maintained through the application by holders of the corresponding access-policy permission. Capturing beyond that window follows the override authority defined in [§9](#9-corrections-policy); no duration value is fixed in this capability.

Three guarantees bind every capture session:

- **Session integrity.** A capture session persists completely or not at all across every record family it touches; partial persistence never occurs ([DIS-07](#51-production-discharge-dis)).
- **Deterministic outcomes.** A completed capture session leaves no machine in scope undetermined: a machine without production is recorded with an affirmative zero outcome, distinguishable from a machine whose shift was never captured ([DIS-08](#51-production-discharge-dis)).
- **Optimistic concurrency.** When two capture attempts target the same continuity key, the first save prevails and the second is rejected together with the current stored state for review; silent overwriting never occurs.

---

## 5. Production Records

Yarn Spinning maintains five record families plus one cross-cutting correction history. Families do not apply uniformly: each section records only the families listed for it in [§4](#4-the-five-productive-sections).

Conventions common to every family:

- **Business date** — calendar day of production, entered by the recorder; no time component.
- **Shift** — one of the three-turn rotation A / B / C; part of the record's capture context.
- **System capture timestamp** — registered automatically by the system; never entered by users.
- **Shared catalogs** — employees, shifts, yarn counts, sections, machines, and machine groups are consumed read-only from shared reference data.

### 5.1 Production Discharge (DIS)

**Nature of the record.** A production discharge is the granular record of one machine-level output event within a shift. Recording is granular per discharge: one machine can have several discharges in one shift — of the same or different yarn count — or none. Although discharges occur across the shift, all of them for a shift are captured together at shift close; the system still preserves each discharge's own capture moment as metadata.

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Machine | catalog value (section machines) | Yes | Machine that produced the discharge |
| Business date | calendar date (no time component) | Yes | Production date entered by the recorder |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Supervisor | catalog value (employees) | Yes | Supervisor of the shift |
| Recorded by | attribution from the authenticated session | Yes | Person performing the capture; attributed automatically from the authenticated session |
| Yarn count | catalog value (título) | Yes | Yarn count in effect for this discharge, maintained as shared reference data; no count value or notation form is fixed in this capability |
| Yarn count variant | text, short code (yarn-count-variant catalog) | No | Variety of the yarn count produced; the variant set is maintained as shared reference data, no value fixed in this capability |
| Gross weight | numeric (decimal precision), in kilograms | Yes | Weight of the full cart or container holding the discharge |
| Operative spindle count | whole number | Yes | Number of operative spindles that produced the discharge |
| Spindle tare weight | numeric (decimal precision), in grams | Yes | Package weight per spindle used in the net-weight calculation |
| Cart weight | numeric (decimal precision), in kilograms | Yes | Weight of the empty cart or container |
| Net weight | numeric (decimal precision), in kilograms | Calculated | System-calculated; never accepted as input (see DIS-02) |
| Roving count | whole number | No | Preparation-specific roving (mecha) count when captured |
| Observations | free text | No | Operational context or exceptions |

#### Rules

| ID | Rule |
| --- | --- |
| DIS-01 | A production discharge associates exactly one machine, one business date, one shift, and one yarn count, with its variant when applicable. |
| DIS-02 | Net weight is always system-calculated: gross cart weight minus total spindle tares minus cart weight. Direct net-weight entry is rejected. |
| DIS-03 | Only FIN-type machines record production discharges in Preparation; a discharge for a PSJ-type machine is invalid. |
| DIS-04 | A machine may have several discharges per shift — of the same or different yarn count — or none; zero discharges is a valid recorded outcome. |
| DIS-05 | Yarn count and variant may change during a shift; each discharge carries the values in effect for that discharge. |
| DIS-06 | Spindle tare weight is recorded in grams; the system converts it consistently when calculating net weight. All cart and weight values use kilograms. |
| DIS-07 | A shift-close capture session persists completely or not at all, across every record family included in the session; partial persistence never occurs. |
| DIS-08 | A completed capture session records an explicit zero outcome for every in-scope machine that produced nothing; the absence of discharge records alone never represents a declared zero. |

### 5.2 Skeining Production (SKN)

**Nature of the record.** The skeining production record captures Madejeras output. Madejeras production is operator-dependent, not machine-cycle-dependent: the primary magnitude is the number of skeins produced. The record uses no spindles, no spindle tares, and no cart weight.

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Machine | catalog value (Madejeras machines) | Yes | Machine that produced the skeins |
| Business date | calendar date (no time component) | Yes | Production date entered by the recorder |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Supervisor | catalog value (employees) | Yes | Supervisor of the shift |
| Recorded by | attribution from the authenticated session | Yes | Person performing the capture; attributed automatically from the authenticated session |
| Yarn count | catalog value (título) | Yes | Yarn count of the skeins produced |
| Yarn count variant | text, short code (yarn-count-variant catalog) | No | Variety of the yarn count produced; the variant set is maintained as shared reference data, no value fixed in this capability |
| Skein count | whole number | Yes | Number of skeins produced |
| Estimated unit weight | numeric (decimal precision), in grams | Yes | Weight per skein entered at capture for this record; reflects the physical presentation produced (see SKN-03) |
| Estimated total weight | numeric (decimal precision), in kilograms | Calculated | Skein count × estimated unit weight, system-calculated |
| Operator name | free text | No | Informative reference to the operator; carries no identity claim (SKN-04) |
| Observations | free text | No | Operational context, including weight-basis clarifications |

#### Rules

| ID | Rule |
| --- | --- |
| SKN-01 | Skeining production applies only to Madejeras and never uses spindles, spindle tares, or cart weight. |
| SKN-02 | Estimated total weight always equals skein count × estimated unit weight, converted to kilograms by the system; it is never entered directly. |
| SKN-03 | The estimated unit weight is entered at capture for each skeining record. It reflects the physical presentation produced in the shift — single skein or bundled basis — which belongs to floor practice and varies independently of the yarn count; it is neither a fixed value nor an application-maintained parameter. |
| SKN-04 | The operator name is an informative free-text reference. It asserts no employment identity and references no employee catalog entry. |
| SKN-05 | Madejeras does not assemble lots inside Yarn Spinning; it produces skeins of a defined weight for the downstream assembly performed by Lot Processing. |

### 5.3 Progress (PRG)

**Nature of the record.** The progress record is a per-machine summary registered at shift close. It consolidates in one record what entered the machine, what was discharged, what remains in the machine, and what continues to the next shift or section. Unlike production (granular per discharge), progress is one record per continuity key.

Progress applies to Preparation (PSJ-type machines only), Ring Spinning, and Twisting. Bobbin Winding and Madejeras have no progress record.

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Machine | catalog value (section machines) | Yes | Machine being controlled |
| Business date | calendar date (no time component) | Yes | Date entered by the recorder |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Supervisor | catalog value (employees) | Yes | Supervisor of the shift |
| Recorded by | attribution from the authenticated session | Yes | Person performing the capture; attributed automatically from the authenticated session |
| Yarn count | catalog value (título) | Yes | Yarn count of the summarized work |
| Input weight | numeric (decimal precision), in kilograms | Yes | Material entering the machine; equals the previous shift's registered output (PRG-04) |
| Sample gross weight | numeric (decimal precision), in grams | Conditional | Gross weight of one sample spindle or package, where spindle sampling applies |
| Sample tare weight | numeric (decimal precision), in grams | Conditional | Tare of that sample spindle or package |
| Operative spindle count | whole number | Conditional | Total operative spindles, where spindle sampling applies |
| In-machine weight | numeric (decimal precision), in kilograms | Conditional | Material still on the machine, estimated by material balance; mainly Ring Spinning and Twisting |
| Discharged weight | numeric (decimal precision), in kilograms | Calculated | Sum of net weights of the shift's production discharges; zero when there are none (PRG-03) |
| Output weight | numeric (decimal precision), in kilograms | Yes | Material remaining on the machine at shift close that continues forward; becomes the next shift's input |
| Worked hours | numeric, in hours | No | Hours the machine operated; supports productivity metrics |
| Consistency notes | free text | No | Reconciliation remarks or operational exceptions |

#### Rules

| ID | Rule |
| --- | --- |
| PRG-01 | One progress record exists per machine × shift × business date × yarn count; a duplicate for the same key is rejected. |
| PRG-02 | Only Preparation, Ring Spinning, and Twisting have progress records; no progress record exists for Bobbin Winding or Madejeras. |
| PRG-03 | Discharged weight equals the sum of net weights of that machine's production discharges in the shift, and is zero when the shift has none. |
| PRG-04 | Input weight equals the output weight registered by the preceding shift for the same machine. |
| PRG-05 | In-machine and output weights are estimated by spindle sampling wherever sampling applies (see [§6](#6-progress-tracking-rules)). |
| PRG-06 | The discharged weight consolidated in a progress record must reconcile with the shift's recorded discharge totals. A difference within the configured reconciliation tolerance is accepted with a mandatory consistency note; a difference beyond the tolerance rejects the record. The tolerance is an operational parameter maintained through the application by holders of the corresponding access-policy permission. |

### 5.4 Process Quality (QUA)

**Nature of the record.** The process quality record captures in-process quality control for a section and machine within a shift. The measured values depend on the method bound to the section (matrix in [§7](#7-process-quality-methods)).

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Section | catalog value (sections) | Yes | Section evaluated |
| Machine | catalog value (section machines) | Conditional | Machine evaluated; optional for section-level random checks |
| Business date | calendar date (no time component) | Yes | Date of the control |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Yarn count | catalog value (título) | Conditional | Yarn count evaluated, when the test targets one |
| Yarn count variant | text, short code (yarn-count-variant catalog) | Conditional | Variety of the evaluated yarn count; the variant set is maintained as shared reference data, no value fixed in this capability |
| Inspector | catalog value (employees) | Yes | Employee performing the control |
| Method | catalog value (control method) | Yes | Control method bound to the section; the method set is maintained as shared reference data, no method fixed in this capability (see [§7](#7-process-quality-methods)) |
| Sample count | whole number | Sample method | Number of samples taken, following the sampling configuration for the section (see QUA-03) |
| Individual sample values | numeric measurements | Sample method | Value measured on each sample |
| Measured properties | numeric results | Sample method | Consistency (CV%), tenacity, and elongation as calculated properties of the samples |
| Body | numeric result | Machine register method | Imperfections per unit of length reported by the machine |
| Kilometers | numeric result | Machine register method | Kilometers processed by the machine |
| Cuts per bobbin | numeric result | Machine register method | Cut frequency per bobbin reported by the machine |
| Result summary | free text | Random method | Results of the tests performed; varies with the test |
| Out-of-tolerance indicator | yes/no | No | Quick review flag when results exceed the configured tolerance limits (see QUA-06) |
| Observations | free text | No | Quality context or exceptions |

#### Rules

| ID | Rule |
| --- | --- |
| QUA-01 | Process quality evaluates every section and machine of Yarn Spinning, without exception. |
| QUA-02 | Controls use exactly one of the three methods, and the method is bound to the section per the matrix in [§7](#7-process-quality-methods). |
| QUA-03 | Sample-method controls take the sample count defined by the sampling configuration maintained through the application by holders of the corresponding access-policy permission; no sample count is embedded in capture behavior. |
| QUA-04 | Process quality in Yarn Spinning is distinct from lot quality; final lot evaluation belongs to Lot Processing. |
| QUA-05 | Machine-register controls in Bobbin Winding are captured at the machine-shift cut; a different capture cut requires an explicit revision of this capability. |
| QUA-06 | Tolerance limits for measured properties are configured reference data maintained through the application by holders of the corresponding access-policy permission; no limit value is embedded in capture behavior. |

### 5.5 Waste (WST)

**Nature of the record.** The waste record captures real waste for a section, weighed by machine group rather than by individual machine. Waste classification semantics are defined in [§8](#8-waste-classification).

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Section | catalog value (sections) | Yes | Section where the waste originated |
| Machine group | catalog value (machine groups) | Yes | Group of machines weighed together |
| Business date | calendar date (no time component) | Yes | Date entered by the recorder |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Waste type | one of: real, accumulated | Yes | Classification per [§8](#8-waste-classification) |
| Waste weight | numeric (decimal precision), in kilograms | Yes | Weight recorded for the machine group |
| Recorded by | attribution from the authenticated session | Yes | Person performing the capture; attributed automatically from the authenticated session |
| Observations | free text | No | Context or exceptions, including Madejeras reprocessing notes |

#### Rules

| ID | Rule |
| --- | --- |
| WST-01 | Waste is weighed and recorded by machine group; individual machines are never weighed separately for waste. |
| WST-02 | Waste is classified as real or accumulated; both classes follow the classification semantics of [§8](#8-waste-classification). |
| WST-03 | Theoretical waste always equals real waste plus accumulated waste and is calculated by the system, never stored as a direct input. |
| WST-04 | Out-of-specification skeins in Madejeras are reprocessing material returned to an earlier stage; they are never recorded as waste. |
| WST-05 | Waste corrections follow the same correction policy as every other record family (see [§9](#9-corrections-policy)). |

### 5.6 Corrections (COR)

**Nature of the record.** Every record family admits controlled correction when a data-entry error exists. Corrections never modify records in place: each correction appends an entry to a separate, append-only correction history, leaving the sequence of prior entries intact. The policy governing when correction is allowed is defined in [§9](#9-corrections-policy).

#### Rules

| ID | Rule |
| --- | --- |
| COR-01 | Every correction stores the correcting actor, the correction timestamp, a mandatory reason, and the complete before-and-after values. |
| COR-02 | The correction history is append-only; existing entries are never overwritten or deleted. |
| COR-03 | Operational-role corrections are allowed only within the administrative window defined in [§9](#9-corrections-policy). |
| COR-04 | Outside that window, correction is reserved to the designated administrative override role configured through access policy. |
| COR-05 | Every correction requires the effective permission for the record family and section scope; organizational position grants nothing by itself. |
| COR-06 | Corrections never alter the original capture timestamp of the corrected record. |
| COR-07 | The correction policy applies uniformly to production discharge, skeining production, progress, process quality, and waste records. |

---

## 6. Progress Tracking Rules

Progress tracking expresses, in business terms, how a machine's shift is measured and reconciled. It applies only to Preparation, Ring Spinning, and Twisting ([PRG-02](#53-progress-prg)).

Because weighing every spindle is impractical ([§4](#4-the-five-productive-sections)), quantities that are not discharged in carts are estimated by **spindle sampling**:

1. One spindle or package is weighed as a sample: its gross weight minus its tare gives the sample's net content.
2. All spindles are assumed to carry the same content weight.
3. The sample net weight is multiplied by the machine's total operative spindle count to estimate the machine-level quantity (material in the machine or continuing as output).

Three continuity rules bind progress to the rest of the record system:

1. **Input continuity.** The input weight of a shift is the output weight registered by the preceding shift for the same machine ([PRG-04](#53-progress-prg)). The chain of input-to-output values forms the continuous material thread across shifts.
2. **Discharge reconciliation.** The discharged weight consolidated in the progress record must coincide with the sum of the net weights of that machine's production discharges in the shift ([PRG-03](#53-progress-prg), [PRG-06](#53-progress-prg)). A shift with zero discharges reconciles at zero.
3. **Loss visibility.** The difference between input weight and output weight exposes the material lost in the section, and worked hours convert production into productivity (kilograms per hour).

Progress therefore serves four purposes: cross-validation of discharge detail, waste estimation per section, productivity measurement per machine, and visibility of each section's in-process status.

---

## 7. Process Quality Methods

Process quality control operates in all five sections. Frequency and method vary by section; systematic sampling alternates with random testing and machine-reported counters:

| Section | Method | What is measured |
| --- | --- | --- |
| Preparación (Preparation) | Sample | Samples evaluate consistency of preparation output |
| Continuas (Ring Spinning) | Sample | Sampling per the configured sampling plan; consistency (CV%), tenacity, elongation |
| Bobinados (Bobbin Winding) | Machine register | No samples; the machine reports body (imperfections per unit of length), kilometers processed, and cuts per bobbin |
| Retorcido (Twisting) | Random | Random tests at lower frequency than Preparation and Ring Spinning |
| Madejeras (Skeining) | Random | Random tests; systematic in-process evaluation happens at lot level downstream |

Method facts:

- **Sample** produces individual sample values plus the measured properties: CV% (coefficient of variation, a consistency measure), tenacity, and elongation.
- **Machine register** records counter data reported by winding machines rather than laboratory samples.
- **Random** records the results of whichever test the control applies; results vary per test.

One exclusion sentence bounds this section's reach: special nomenclatures such as -AT, -FT, -VARR, and -D belong to Lot Processing stages, never to machines or to Yarn Spinning records; process quality here only records the findings that may later inform those stage-level designations.

---

## 8. Waste Classification

Waste in Yarn Spinning follows a two-component classification:

1. **Real waste** is material loss captured during the process, per section and shift, weighed by machine group ([WST-01](#55-waste-wst), [WST-02](#55-waste-wst)).
2. **Accumulated waste** is material retained for management under current plant policy; it does not enter the routine per-shift weighing capture.

From both components the system derives one aggregate:

3. **Theoretical waste equals real waste plus accumulated waste.** It is always calculated by the system and never stored as a direct input ([WST-03](#55-waste-wst)).

Weighing practice: machines are weighed together in machine groups; the record identifies the group, not the individual machine.

Reprocessing boundary: skeins outside specification in Madejeras are reprocessing material. They return to an earlier stage of the process and are never recorded as waste ([WST-04](#55-waste-wst)). This keeps the waste metric faithful to true material loss and protects the downstream reprocessing path.

---

## 9. Corrections Policy

Operational records may be corrected when a data-entry error exists, under a uniform policy for all five record families ([COR-07](#56-corrections-cor)).

The policy rests on four pillars:

1. **Append-only evidence.** A correction appends a complete evidence entry — actor, timestamp, reason, and full before-and-after values — and never erases history ([COR-01](#56-corrections-cor), [COR-02](#56-corrections-cor)).
2. **Administrative window.** Operational roles may correct records only within an administrative window that opens at capture and closes after a duration defined by an operational parameter maintained through the application by holders of the corresponding access-policy permission. No duration value is fixed in this capability.
3. **Override authority.** Beyond the window, correction is reserved to a designated administrative override role. That authority exists only as configured through access policy; it is never implied by a person's organizational position, and no position name is fixed for it in this document.
4. **Permission-gated execution.** Within or beyond the window, a correction executes only when the user holds the effective permission for the record family and section scope ([COR-05](#56-corrections-cor)).

Original capture timestamps survive every correction ([COR-06](#56-corrections-cor)): the system preserves when a fact was first recorded independently of when it was last corrected.

---

## 10. Metrics and Reporting

The recorded families feed section dashboards and the supervisory consolidated view. Metric definitions below are business definitions only.

### Production metrics

| Metric | Unit | Definition |
| --- | --- | --- |
| Total discharged | kg | Sum of production-discharge net weights in the period, by machine, yarn count, and section |
| Discharge count | count | Number of production discharges in the period; exposes discharge frequency |
| Average per discharge | kg | Total discharged divided by discharge count; consistency control |

### Progress metrics

| Metric | Unit | Definition |
| --- | --- | --- |
| Productivity | kg/h | Discharged weight divided by worked hours, per machine and section |
| Progress waste | kg | Input weight minus output weight; material loss in the section |
| Relative waste | % | Progress waste divided by input weight |
| Effective hours | h | Worked hours recorded per machine in the shift |

### Quality metrics

| Metric | Unit | Definition |
| --- | --- | --- |
| Average consistency | CV% | Mean coefficient of variation across sample tests |
| Samples outside tolerance | % | Share of samples exceeding the configured tolerance limits |
| Average body | result | Mean imperfection level reported in Bobbin Winding |
| Cuts per bobbin | result | Cut frequency reported in Bobbin Winding |

### Waste metrics

| Metric | Unit | Definition |
| --- | --- | --- |
| Real waste | kg | Sum of real waste recorded in the period |
| Waste rate | % | Real waste divided by total production, per section and machine group |

### Cross-cutting views

| View | Definition |
| --- | --- |
| Production versus planning | Actual production against the planned baseline, with deviation alerts. Specific per-yarn-count baselines (kilogram-per-day targets) are excluded from this capability; planning baselines belong to the area level defined in the [Operation Area Overview](./overview.md). |
| Spindle utilization | % | Operative spindles against total machine spindles; capacity utilization |
| Shift consolidated | Combined production, quality, and waste view for the supervisor's daily consultation |

**Boundary declaration.** These entries define what each metric means for the business. Calculation detail — formulas, period handling, and filter semantics — is defined in the corresponding technical specification.

---

## 11. Acceptance Criteria

### 12.1 Production Discharge

| ID | Criterion |
| --- | --- |
| AC-DIS-01 | A production discharge can be recorded with machine, business date, shift, supervisor, yarn count, gross weight, operative spindle count, spindle tare weight, and cart weight completed. |
| AC-DIS-02 | Net weight always equals gross cart weight minus total spindle tares minus cart weight, and direct net-weight entry is rejected. |
| AC-DIS-03 | A production discharge for a PSJ-type machine in Preparation is rejected. |
| AC-DIS-04 | Multiple discharges for one machine in one shift coexist, including discharges with different yarn counts, and a shift with zero discharges is valid. |
| AC-DIS-05 | GIVEN a machine changes yarn count during a shift, WHEN each discharge is recorded, THEN each discharge carries the yarn count and variant in effect for that discharge. |
| AC-DIS-06 | A shift-close capture session persists completely or not at all; a failed validation leaves no partial records. |
| AC-DIS-07 | A completed capture session distinguishes a machine that produced nothing, recorded as an affirmative zero outcome, from a machine whose shift was never captured. |

### 12.2 Skeining Production

| ID | Criterion |
| --- | --- |
| AC-SKN-01 | A Madejeras production record captures skein count and estimated unit weight without spindles, spindle tares, or cart weight. |
| AC-SKN-02 | Estimated total weight always equals skein count × estimated unit weight, calculated by the system. |
| AC-SKN-03 | The operator name is stored as an informative free-text reference and creates no association with an employee catalog identity. |
| AC-SKN-04 | A skeining record stores the estimated unit weight entered at capture, and its estimated total weight always equals skein count × that unit weight, calculated by the system. |

### 12.3 Progress

| ID | Criterion |
| --- | --- |
| AC-PRG-01 | One progress record exists per machine, shift, business date, and yarn count; a duplicate for the same key is rejected. |
| AC-PRG-02 | Progress can be recorded only for Preparation, Ring Spinning, and Twisting. |
| AC-PRG-03 | Discharged weight equals the sum of the machine's discharge net weights in the shift and is zero when there are none. |
| AC-PRG-04 | Input weight equals the output weight registered by the preceding shift for the same machine. |
| AC-PRG-05 | The output estimate derives from one weighed sample spindle applied to the full operative spindle count. |
| AC-PRG-06 | A progress record whose discharged weight differs from recorded discharge totals within the configured reconciliation tolerance is accepted only with a mandatory consistency note; a difference beyond the tolerance is rejected. |

### 12.4 Process Quality

| ID | Criterion |
| --- | --- |
| AC-QUA-01 | Process quality controls can be recorded for every section and machine in Yarn Spinning. |
| AC-QUA-02 | Sample-method controls capture individual sample values and the measured properties: consistency (CV%), tenacity, and elongation. |
| AC-QUA-03 | Machine-register controls in Bobbin Winding capture body, kilometers, and cuts per bobbin. |
| AC-QUA-04 | Random-method controls capture the results of the tests performed as a free summary. |
| AC-QUA-05 | No nomenclature assignment exists among Yarn Spinning quality records. |

### 12.5 Waste

| ID | Criterion |
| --- | --- |
| AC-WST-01 | A waste record captures section, machine group, business date, shift, weight, and waste type. |
| AC-WST-02 | Theoretical waste always equals real waste plus accumulated waste and is never stored as a direct input. |
| AC-WST-03 | An out-of-specification skein outcome in Madejeras cannot be recorded as waste. |

### 12.6 Corrections

| ID | Criterion |
| --- | --- |
| AC-COR-01 | Every correction stores the correcting actor, correction timestamp, mandatory reason, and complete before-and-after values. |
| AC-COR-02 | Correction history is append-only; no entry is ever overwritten or removed. |
| AC-COR-03 | A correction by an operational role outside the administrative window is rejected unless executed under the designated administrative override authority. |
| AC-COR-04 | Corrections never alter the original capture timestamp of the corrected record. |
| AC-COR-05 | GIVEN a correction is attempted, WHEN the user lacks the effective permission for the record family and scope, THEN the correction is rejected regardless of the user's organizational position. |

---

## References

- [Operation Area Overview](./overview.md) — area-level scope, actors, and cross-cutting Operation rules
- [Yarn Spinning Domain Map](../../domain/operation/yarn-spinning.md) — bounded-context domain model
- [Lot Processing Domain Map](../../domain/operation/lot-processing.md) — downstream domain consuming skein output
- [Ubiquitous Language](../../domain/ubiquitous-language.md) — canonical naming contract
