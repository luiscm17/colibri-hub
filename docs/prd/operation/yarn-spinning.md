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

Yarn Spinning (Hilatura) is the Operation capability that transforms raw material received from Warehouse into yarn of a specific yarn count (título) through five productive sections arranged in continuous sequential flow. Its recorded output is skein production. Lot Processing independently records physical lot assembly.

The capability sits between two contexts:

- **Upstream — Warehouse.** Raw-material deliveries arrive authorized from Warehouse. A delivery does not create any association between bales and lots, products, or identities.
- **Lot Processing.** Lot Processing independently records physical lot assembly. Skeins produced in Yarn Spinning carry no lot attribution.

| Capability or Context | Relationship |
| --- | --- |
| Warehouse (upstream) | Delivers authorized raw material and the information needed to process it. Delivery does not link bales to lots, products, or production identities. |
| Lot Processing | Independently records physical lot assembly, lot-stage history, final lot quality evaluation, and finished-product handoff. |
| Access Control | Governs who may administer profiles, record, correct, and consult through configurable actions and scopes; it does not own Quality physical parameters, units, methods, calculations, or tolerances. |
| Shared Reference Data | Supplies shared catalogs consumed read-only: employees, shifts, yarn counts, sections, machines, and machine groups. |

**Identity and context boundary.** Inside Yarn Spinning there is no lot, no lot code, no production identity, and no production run. Continuity of records is built from section × machine × business date × shift × yarn count. Physical lot assembly, lot-stage history, final lot quality evaluation, and the finished-product handoff are outside this capability and belong to Lot Processing. Yarn Spinning and Lot Processing record independent business facts: neither context writes, reserves, consumes, or reconciles the other context's source records. Their real-world process relationship creates no transactional availability, allocation, reservation, consumption, or double-use-prevention rule in Yarn Spinning. Raw-material custody and supplies remain Warehouse capabilities.

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
| Foreman / recorder | Authenticated capture actor | Submits an authorized capture or correction; the system attributes that act to the authenticated session. |
| Quality Control | Process-quality executor | Performs process-quality tests across all sections. |
| Inventory | Material-flow function | Tracks material flow between sections and records material movements between them. |
| System | Automated | Calculates derived weights, enforces constraints, attributes capture timestamps, and maintains the append-only correction history. |

> **Note on responsibilities:** This document defines business capabilities, not authorizations. Which function performs each recording, validation, or correction action is determined exclusively by access policy configuration (see [Access Control](../access-control.md)). No recording assignment is fixed in this PRD.

Two further clarifications bound the actor model:

- Machine operators manipulate production equipment and are not direct system users.
- Packaging and dyeing personnel do not participate in Yarn Spinning; their involvement begins in Lot Processing.
- Material-flow views held by the inventory function derive from the production records of this capability; this capability never maintains a parallel duplicate capture of the same production facts.
- Each record names the operational shift supervisor selected for the capture header and attributes the capture to the authenticated foreman / recorder session. The foreman / recorder attribution is derived by the system, not selected or sent by the client; it is an audit attribution, not an additional operational responsibility slot.

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
- **Deterministic outcomes.** A completed capture session accounts for every in-scope machine: a machine with no production contributes zero to calculations (an omitted or zero-valued row is treated as zero), and the capture UI requires each in-scope machine to be acknowledged before submission. No machine in scope is left undetermined ([DIS-08](#51-production-discharge-dis)).
- **Optimistic concurrency.** When two capture attempts target the same continuity key, the first save prevails and the competing attempt receives `409`; the current stored record is available for review through the authorized current-record read. Silent overwriting never occurs.

---

## 5. Production Records

Yarn Spinning maintains five record families plus one cross-cutting correction history. Families do not apply uniformly: each section records only the families listed for it in [§4](#4-the-five-productive-sections).

Conventions common to every family:

- **Business date** — calendar day of production, entered by the recorder; no time component.
- **Shift** — one of the three-turn rotation A / B / C; part of the record's capture context.
- **System capture timestamp** — registered automatically by the system; never entered by users.
- **Shared catalogs** — employees, shifts, yarn counts, sections, machines, and machine groups are consumed read-only from shared reference data.
- **Numerical operational data** — when a numerical value applies to a record, it is captured or calculated as a non-negative known value; it is never null, blank, or unknown. Zero represents a known zero quantity, never an absent capture.

### 5.1 Production Discharge (DIS)

**Nature of the record.** A production discharge is an individually recorded machine-level output event within a shift. Machine, business date, shift, yarn count, and material type classify the event but do not uniquely identify it: repeated discharges with equal dimensions remain distinct business facts. Recording is granular per discharge: one machine can have several discharges in one shift — of the same or different yarn count — or none. Although discharges occur across the shift, all of them for a shift are captured together at shift close; the system still preserves each discharge's own capture moment as metadata.

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Machine | catalog value (section machines) | Yes | Machine that produced the discharge |
| Business date | calendar date (no time component) | Yes | Production date entered by the recorder |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Supervisor | catalog value (employees) | Yes | Supervisor of the shift |
| Foreman / recorder attribution | authenticated session | Yes | Foreman (encargado) submitting the capture. The system derives this attribution automatically from the authenticated session; it is never selected or sent by the client. |
| Yarn count | catalog value (título) | Yes | Yarn count in effect for this discharge, maintained as shared reference data; its characteristics (material type, process-specific notations) belong to the yarn count identity, not to this record |
| Material type | text, short code | No | Material type of the referenced yarn count (e.g., HB/N/Fantasía/OTRO); an attribute of the yarn count identity, not a separate catalog |
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
| DIS-01 | A production discharge associates exactly one machine, one business date, one shift, and one yarn count, with its material type when applicable. |
| DIS-02 | Net weight is always system-calculated: gross cart weight minus total spindle tares minus cart weight. Direct net-weight entry is rejected. |
| DIS-03 | Only FIN-type machines record production discharges in Preparation; a discharge for a PSJ-type machine is invalid. |
| DIS-04 | A machine may have several discharges per shift — of the same or different yarn count — or none; zero discharges is a valid recorded outcome. |
| DIS-05 | Yarn count and material type may change during a shift; each discharge carries the values in effect for that discharge. |
| DIS-06 | Spindle tare weight is recorded in grams; the system converts it consistently when calculating net weight. All cart and weight values use kilograms. |
| DIS-07 | A shift-close capture session persists completely or not at all, across every record family included in the session; partial persistence never occurs. |
| DIS-08 | A completed capture session accounts for every in-scope machine. A machine that produced nothing is represented by a zero-valued row (or omitted and treated as zero); its production is never left undetermined. The capture UI requires each in-scope machine to be acknowledged before submission. |
| DIS-09 | The operational shift supervisor is entered once at the shift/section header and applied to every discharge row in that capture. Foreman / recorder attribution is derived once from the authenticated session and applied by the system to every discharge row; neither identity is repeated per discharge row, and the client never sends the foreman identity. |

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
| Yarn count | catalog value (título) | Yes | Yarn count of the skeins produced; its characteristics belong to the yarn count identity |
| Material type | text, short code | No | Material type of the referenced yarn count (e.g., HB/N/Fantasía/OTRO); an attribute of the yarn count identity, not a separate catalog |
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
| SKN-05 | Madejeras does not assemble lots inside Yarn Spinning; it records skein production independently of the physical lot assembly recorded by Lot Processing. A skeining record creates no availability, allocation, reservation, consumption, or double-use-prevention rule in Yarn Spinning. |

### 5.3 Progress (PRG)

**Nature of the record.** The progress record is a per-machine summary registered at shift close. It consolidates in one record what entered the machine, what was discharged, and the closing quantity physically remaining on the machine. That closing output becomes the following shift's opening input. Unlike production (granular per discharge), progress is one record per continuity key.

Progress applies to Preparation (PSJ-type machines only), Ring Spinning, and Twisting. Bobbin Winding and Madejeras have no progress record.

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Machine | catalog value (section machines) | Yes | Machine being controlled |
| Business date | calendar date (no time component) | Yes | Date entered by the recorder |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Supervisor | catalog value (employees) | Yes | Supervisor of the shift |
| Recorded by | attribution from the authenticated session | Yes | Person performing the capture; attributed automatically from the authenticated session |
| Yarn count | catalog value (título) | Yes | Yarn count of the summarized work; its characteristics belong to the yarn count identity |
| Input weight | numeric (decimal precision), in kilograms | Yes | Opening material on the machine; determined from continuity, or zero when no predecessor exists (PRG-04) |
| Sample gross weight | numeric (decimal precision), in grams | Conditional | Gross weight of one sample spindle or package, where spindle sampling applies |
| Sample tare weight | numeric (decimal precision), in grams | Conditional | Tare of that sample spindle or package |
| Operative spindle count | whole number | Conditional | Total operative spindles, where spindle sampling applies |
| Discharged weight | numeric (decimal precision), in kilograms | Calculated | Sum of authoritative net weights of the shift's production discharges; zero when there are none (PRG-03) |
| Output weight | numeric (decimal precision), in kilograms | Yes | Sole closing quantity physically remaining on the machine at shift close; becomes the following shift's opening input when continuity applies |
| Worked hours | numeric, in hours | No | Hours the machine operated; supports productivity metrics |
| Consistency notes | free text | No | Reconciliation remarks or operational exceptions |

#### Rules

| ID | Rule |
| --- | --- |
| PRG-01 | One progress record exists per machine × shift × business date × yarn count; a duplicate for the same key is rejected. |
| PRG-02 | Only Preparation, Ring Spinning, and Twisting have progress records; no progress record exists for Bobbin Winding or Madejeras. |
| PRG-03 | Discharged weight equals the sum of authoritative net weights of that machine's production discharges in the shift, and is zero when the shift has none. |
| PRG-04 | Input weight equals the output weight registered by the immediately preceding logical shift for the same section, machine, and yarn-count identity. Logical shifts progress A → B → C → next-business-day A. A different yarn-count identity is a new stream with no predecessor, so its derived input is zero; this is normal continuity derivation, not a user-entered override. |
| PRG-05 | Output weight is the sole closing quantity physically remaining on the machine and is estimated by spindle sampling wherever sampling applies (see [§6](#6-progress-tracking-rules)). |
| PRG-06 | The discharged weight consolidated in a progress record must reconcile with the shift's recorded discharge totals. A difference within the configured reconciliation tolerance is accepted with a mandatory consistency note; a difference beyond the tolerance rejects the record. The tolerance is an operational parameter maintained through the application by holders of the corresponding access-policy permission. |
| PRG-07 | Net process production equals output weight plus discharged weight minus input weight. Input weight minus output weight is not waste; waste is recorded independently under the WST family. |

### 5.4 Process Quality (QUA)

**Nature of the record.** The process quality record captures in-process quality control under one active Yarn Spinning Process Quality measurement-profile version. The profile defines the applicable method, physical parameters, units, capture mode, approved calculations, derived results, and tolerances for the selected section, machine where applicable, and yarn count where applicable.

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Section | catalog value (sections) | Yes | Section evaluated |
| Machine | catalog value (section machines) | Conditional | Machine evaluated; optional for section-level random checks |
| Business date | calendar date (no time component) | Yes | Date of the control |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Yarn count | catalog value (título) | Conditional | Yarn count evaluated, when the test targets one; its characteristics belong to the yarn count identity |
| Material type | text, short code | Conditional | Material type of the referenced yarn count (e.g., HB/N/Fantasía/OTRO); an attribute of the yarn count identity, not a separate catalog |
| Inspector | catalog value (employees) | Yes | Employee performing the control |
| Measurement profile and version | Yarn Spinning profile identity | Yes | Active profile version applied to the control |
| Method and capture mode | profile-defined | Yes | Applicable Quality method and how its values are captured (see [§7](#7-process-quality-measurement-profiles-and-methods)) |
| Raw parameter values | profile-defined measurements | Yes | Values in the profile-defined parameters, units, and ordering; retained exactly as captured |
| Sample count | whole number | Sample method | Profile-configured number of ordered measurements, from 10 through 15 inclusive |
| Derived results | profile-defined results | As configured | Results calculated only through the profile's approved operations from retained raw values |
| Tolerance outcome | profile-defined | As configured | Applicable tolerance limits and the resulting review outcome |
| Observations | free text | No | Quality context or exceptions |

#### Rules

| ID | Rule |
| --- | --- |
| QUA-01 | Process Quality measurement profiles belong to Yarn Spinning. Access Control only authorizes profile administration, activation, capture, and correction; it does not define profile content. |
| QUA-02 | A profile version declares its section applicability and may further restrict machines and yarn counts. It defines parameter labels, physical units, capture mode, approved calculation operations, derived results, and tolerances. A profile may reference shared units, sections, machines, yarn counts, and employees without becoming Shared Reference Data. |
| QUA-03 | A control uses exactly one active, applicable profile version. A retired version blocks new capture but its records remain readable. Profile changes create a new effective version and never reinterpret an existing control. |
| QUA-04 | Sample profiles retain the configured ordered measurements. Their sample count is from 10 through 15 inclusive. Preparation normally uses 10 samples and exposes readonly `x_average` and `x_percentage_error` results. |
| QUA-05 | The initial approved Preparation operation for `x_percentage_error` is relative standard error: sample standard deviation divided by the square root of sample count, divided by sample average, expressed as a percentage. When the sample average is zero, the outcome is safely defined as unavailable rather than an invented numeric value. |
| QUA-06 | Profile administrators select only backend-approved calculation operations through the application; arbitrary formula expressions are not permitted. Capture preview is informative; the system validates and recalculates the authoritative results and tolerances. |
| QUA-07 | Process quality in Yarn Spinning is distinct from lot quality; final lot evaluation belongs to Lot Processing. |
| QUA-08 | Bobbin Winding Machine Register remains captured at the machine-shift cut. Random controls preserve their method applicability. Both are profile-driven, including their parameters, units, calculations, and tolerances. |
| QUA-09 | Correcting a Quality record retains its original profile version and recalculates only under that version; it never substitutes a newer active profile. |

### 5.5 Waste (WST)

**Nature of the record.** The waste record captures real waste for a section, weighed by machine group rather than by individual machine. Real-waste semantics are defined in [§8](#8-real-waste).

#### Attributes

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Section | catalog value (sections) | Yes | Section where the waste originated |
| Machine group | catalog value (machine groups) | Yes | Group of machines weighed together |
| Business date | calendar date (no time component) | Yes | Date entered by the recorder |
| Shift | catalog value (A, B, C) | Yes | Turn of the record's capture context |
| Waste weight | numeric (decimal precision), in kilograms | Yes | Weight recorded for the machine group |
| Recorded by | attribution from the authenticated session | Yes | Person performing the capture; attributed automatically from the authenticated session |
| Observations | free text | No | Context or exceptions, including Madejeras reprocessing notes |

#### Rules

| ID | Rule |
| --- | --- |
| WST-01 | Waste is weighed and recorded by machine group; individual machines are never weighed separately for waste. |
| WST-02 | Each waste record represents real waste independently weighed for its machine group and shift. |
| WST-03 | Out-of-specification skeins in Madejeras are reprocessing material returned to an earlier stage; they are never recorded as waste. |
| WST-04 | Waste corrections follow the same correction policy as every other record family (see [§9](#9-corrections-policy)). |

### 5.6 Corrections (COR)

**Nature of the record.** Every record family admits controlled correction when a data-entry error exists. A correction updates the record's current values in place so the record reflects the latest corrected state, and in the same operation appends an immutable entry to a separate, append-only correction history that preserves the complete before-and-after values and the original capture timestamp. The correction history is never overwritten or deleted ([COR-02](#56-corrections-cor)); the original capture timestamp is never altered ([COR-06](#56-corrections-cor)). Each correctable record belongs to exactly one family (production discharge, skeining production, progress, process quality, or waste) and is addressed for correction by its family and record id. The policy governing when correction is allowed is defined in [§9](#9-corrections-policy).

#### Rules

| ID | Rule |
| --- | --- |
| COR-01 | Every correction stores, for each changed business record, the authenticated correcting actor, the correction timestamp, a mandatory reason, and the complete before-and-after values. Audit evidence is per changed business record, not per interface field or generic multi-record event. |
| COR-02 | The correction history is append-only; existing entries are never overwritten or deleted. |
| COR-03 | Yarn Spinning validates the correction reason and evidence and enforces its administrative correction window. Within that window, a correction requires Access Control's general `Edit` action in the applicable business scope. |
| COR-04 | Outside that window, a correction requires Access Control's general `Edit Outside the Operational Window` action in the applicable business scope. |
| COR-05 | Production discharge, skeining production, and progress corrections use their applicable section scope. Process Quality and Waste corrections use their own transversal scopes, not section scopes. Organizational position grants no correction authority by itself. |
| COR-06 | Corrections never alter the original capture timestamp of the corrected record. |
| COR-07 | The correction policy applies uniformly to production discharge, skeining production, progress, process quality, and waste records. |
| COR-08 | Correcting a progress input or output never automatically changes a later record. The system warns when continuity records may be affected; any later correction is manual and independently traceable under this policy. |
| COR-09 | A correction affecting more than one business record may be applied atomically; each changed record retains its own correction evidence under COR-01. |

---

## 6. Progress Tracking Rules

Progress tracking expresses, in business terms, how a machine's shift is measured and reconciled. It applies only to Preparation, Ring Spinning, and Twisting ([PRG-02](#53-progress-prg)).

Because weighing every spindle is impractical ([§4](#4-the-five-productive-sections)), quantities that are not discharged in carts are estimated by **spindle sampling**:

1. One spindle or package is weighed as a sample: its gross weight minus its tare gives the sample's net content.
2. All spindles are assumed to carry the same content weight.
3. The sample net weight is multiplied by the machine's total operative spindle count to estimate the closing output weight remaining on the machine.

Three continuity rules bind progress to the rest of the record system:

1. **Input continuity.** The predecessor is the immediately preceding logical shift in the A → B → C → next-business-day A sequence for the same section, machine, and yarn-count identity. Its output weight becomes input weight. A different yarn-count identity starts a new stream with no predecessor, so its derived opening input is zero; this is normal continuity derivation, not a user-entered override ([PRG-04](#53-progress-prg)). The chain of input-to-output values forms the continuous material thread across shifts.
2. **Discharge reconciliation.** The discharged weight consolidated in the progress record must coincide with the sum of the net weights of that machine's production discharges in the shift ([PRG-03](#53-progress-prg), [PRG-06](#53-progress-prg)). A shift with zero discharges reconciles at zero.
3. **Production measurement.** Output weight is the sole closing in-machine quantity. Net process production equals closing output weight plus discharged weight minus opening input weight. The difference between input weight and output weight is not waste; independently weighed real waste remains the WST-family fact. Worked hours convert net process production into productivity (kilograms per hour).

Progress therefore serves four purposes: cross-validation of discharge detail, net process production measurement, productivity measurement per machine, and visibility of each section's in-process status.

---

## 7. Process Quality Measurement Profiles and Methods

Process quality control operates in all five sections. A Yarn Spinning measurement-profile version configures each applicable control without imposing one fixed record schema across sections.

| Section | Method | What is measured |
| --- | --- | --- |
| Preparación (Preparation) | Sample | Ordered profile-defined measurements; `x_average` and `x_percentage_error` are readonly derived displays |
| Continuas (Ring Spinning) | Sample | Active profile defines all parameters, units, capture mode, calculations, results, and tolerances; CV%, tenacity, and elongation are not mandatory columns |
| Bobinados (Bobbin Winding) | Machine register | Profile-driven machine-register parameters at the machine-shift cut |
| Retorcido (Twisting) | Random | Random tests at lower frequency than Preparation and Ring Spinning |
| Madejeras (Skeining) | Random | Random tests; systematic in-process evaluation happens at lot level downstream |

Method facts:

- **Profile lifecycle.** Authorized Yarn Spinning profile administrators create and activate effective versions. A version retains its complete definition for historical interpretation. Retirement prevents new capture only.
- **Sample.** The profile defines ordered raw measurements and results. Preparation retains 10–15 configured samples and the approved derived displays described in QUA-04 and QUA-05.
- **Machine register and Random.** Their existing applicability remains intact, while each profile defines the captured parameters and results rather than a fixed global set.

For section methods that use machine-level controls, the selected machines are random or flexible within the relevant section. Process quality therefore covers every section without requiring a record for every machine.

One exclusion sentence bounds this section's reach: special nomenclatures such as -AT, -FT, -VARR, and -D belong to Lot Processing stages, never to machines or to Yarn Spinning records; process quality here only records the findings that may later inform those stage-level designations.

---

## 8. Real Waste

Waste in Yarn Spinning means only real material loss, independently weighed and recorded by section, machine group, and shift ([WST-01](#55-waste-wst), [WST-02](#55-waste-wst)). Machines are weighed together in machine groups; the record identifies the group, not the individual machine.

Reprocessing boundary: skeins outside specification in Madejeras are reprocessing material. They return to an earlier stage of the process and are never recorded as waste ([WST-03](#55-waste-wst)). This keeps the waste metric faithful to true material loss and protects the downstream reprocessing path.

---

## 9. Corrections Policy

Operational records may be corrected when a data-entry error exists, under a uniform policy for all five record families ([COR-07](#56-corrections-cor)).

The policy rests on four pillars:

1. **Append-only evidence.** A correction updates the affected operational record's current values in place and appends complete evidence — authenticated correcting actor, timestamp, reason, and full before-and-after values — for each changed business record to an immutable correction history. Audit evidence is not attached to individual interface fields or treated as a generic whole-grid event. The history is never erased or overwritten ([COR-01](#56-corrections-cor), [COR-02](#56-corrections-cor)), and the original capture timestamp is preserved ([COR-06](#56-corrections-cor)). A multi-record correction may be atomic, while retaining evidence for each changed record ([COR-09](#56-corrections-cor)).
2. **Administrative window.** Yarn Spinning owns validation of correction validity and evidence and enforces an administrative window that opens at capture and closes after a duration defined by an operational parameter maintained through the application by holders of the corresponding access-policy permission. No duration value is fixed in this capability.
3. **Access Control authorization.** Within the window, correction requires Access Control's general `Edit` action in the applicable business scope. Beyond the window, it requires Access Control's general `Edit Outside the Operational Window` action in that scope. This PRD does not define roles or an RBAC catalog.
4. **Applicable business scope.** Production discharge, skeining production, and progress corrections use their applicable section scope. Process Quality and Waste use their own transversal scopes, not section scopes. Organizational position does not confer correction authority ([COR-05](#56-corrections-cor)).

Original capture timestamps survive every correction ([COR-06](#56-corrections-cor)): the system preserves when a fact was first recorded independently of when it was last corrected.

**Continuity after correction.** Correcting a progress input or output does not automatically change later records. The system warns about continuity records that may be affected; any later correction remains manual and independently traceable ([COR-08](#56-corrections-cor)).

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
| Net process production | kg | Closing output weight plus discharged weight minus opening input weight |
| Productivity | kg/h | Net process production divided by worked hours, per machine and section |
| Effective hours | h | Worked hours recorded per machine in the shift |

### Quality metrics

| Metric | Unit | Definition |
| --- | --- | --- |
| Profile-defined result | profile-defined unit | Authorized aggregation of a named result, only where the applied profile supports it |
| Controls outside tolerance | count or % | Profile-aware count or share of controls whose retained tolerance outcome is outside tolerance |

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

| ID | Criterion |
| --- | --- |
| AC-NUM-01 | Every applicable required numerical operational value is a non-negative known value. Zero is accepted only as a known zero quantity and never as a missing, blank, null, or unknown value. |

### 11.1 Production Discharge

| ID | Criterion |
| --- | --- |
| AC-DIS-01 | A production discharge can be recorded with machine, business date, shift, operational shift supervisor, yarn count, gross weight, operative spindle count, spindle tare weight, and cart weight completed; the system attributes the capture to the authenticated foreman / recorder without accepting that identity from the client. |
| AC-DIS-02 | Net weight always equals gross cart weight minus total spindle tares minus cart weight, and direct net-weight entry is rejected. |
| AC-DIS-03 | A production discharge for a PSJ-type machine in Preparation is rejected. |
| AC-DIS-04 | Multiple discharges for one machine in one shift coexist, including discharges with different yarn counts, and a shift with zero discharges is valid. |
| AC-DIS-05 | GIVEN a machine changes yarn count during a shift, WHEN each discharge is recorded, THEN each discharge carries the yarn count and material type in effect for that discharge. |
| AC-DIS-06 | A shift-close capture session persists completely or not at all; a failed validation leaves no partial records. |
| AC-DIS-07 | A completed capture session accounts for every in-scope machine; a machine that produced nothing is represented by a zero-valued row (or treated as zero), and the capture UI requires its acknowledgement before submission. |
| AC-DIS-08 | GIVEN two production discharges have the same machine, business date, shift, yarn count, and material type, WHEN both output events are recorded, THEN both remain distinct business facts. |

### 11.2 Skeining Production

| ID | Criterion |
| --- | --- |
| AC-SKN-01 | A Madejeras production record captures skein count and estimated unit weight without spindles, spindle tares, or cart weight. |
| AC-SKN-02 | Estimated total weight always equals skein count × estimated unit weight, calculated by the system. |
| AC-SKN-03 | The operator name is stored as an informative free-text reference and creates no association with an employee catalog identity. |
| AC-SKN-04 | A skeining record stores the estimated unit weight entered at capture, and its estimated total weight always equals skein count × that unit weight, calculated by the system. |
| AC-SKN-05 | A skeining record remains independent of physical lot assembly: it creates no availability, allocation, reservation, consumption, or double-use-prevention rule in Yarn Spinning. |

### 11.3 Progress

| ID | Criterion |
| --- | --- |
| AC-PRG-01 | One progress record exists per machine, shift, business date, and yarn count; a duplicate for the same key is rejected. |
| AC-PRG-02 | Progress can be recorded only for Preparation, Ring Spinning, and Twisting. |
| AC-PRG-03 | Discharged weight equals the sum of the machine's authoritative discharge net weights in the shift and is zero when there are none. |
| AC-PRG-04 | Input weight equals the output weight of the immediately preceding logical shift in the A → B → C → next-business-day A sequence for the same section, machine, and yarn-count identity. A different yarn-count identity has no predecessor and therefore derives input weight as zero; this is not a user-entered override. |
| AC-PRG-05 | Output weight is the sole closing quantity physically remaining on the machine; where spindle sampling applies, its estimate derives from one weighed sample spindle applied to the full operative spindle count. |
| AC-PRG-06 | A progress record whose discharged weight differs from recorded discharge totals within the configured reconciliation tolerance is accepted only with a mandatory consistency note; a difference beyond the tolerance is rejected. |
| AC-PRG-07 | Net process production equals closing output weight plus discharged weight minus opening input weight. Input weight minus output weight is not recorded or reported as waste; waste remains an independently weighed WST-family fact. |

### 11.4 Process Quality

| ID | Criterion |
| --- | --- |
| AC-QUA-01 | Process quality controls cover every Yarn Spinning section without requiring a record for every machine; where a method uses machine-level controls, machines may be selected randomly or flexibly from the relevant section. |
| AC-QUA-02 | A Sample-method control captures the configured number of ordered measurements for its applicable profile version, from 10 through 15 inclusive, and calculates only that version's designated results. |
| AC-QUA-03 | A Quality capture retains the applied profile and version, its raw values, derived results, units, and tolerances; later profile changes do not reinterpret it, and a correction recalculates under its original version. |
| AC-QUA-04 | A Preparation sample capture retains its ordered 10–15 measurements and shows readonly `x_average` and `x_percentage_error`; when its average is zero, percentage error is safely unavailable rather than numeric. |
| AC-QUA-05 | Ring Spinning, Bobbin Winding Machine Register, and Random controls render and validate only their active profile definitions; Ring Spinning does not require CV%, tenacity, or elongation columns. |
| AC-QUA-06 | Profile administration offers only backend-approved calculation operations; arbitrary formula entry is rejected, and the authoritative service recalculates results. |
| AC-QUA-07 | No nomenclature assignment exists among Yarn Spinning quality records. |

### 11.5 Waste

| ID | Criterion |
| --- | --- |
| AC-WST-01 | A waste record captures real waste independently weighed by section, machine group, business date, and shift. |
| AC-WST-02 | An out-of-specification skein outcome in Madejeras cannot be recorded as waste. |

### 11.6 Corrections

| ID | Criterion |
| --- | --- |
| AC-COR-01 | Every correction stores the authenticated correcting actor, correction timestamp, mandatory reason, and complete before-and-after values. |
| AC-COR-02 | Correction history is append-only; no entry is ever overwritten or removed. |
| AC-COR-03 | A correction within the administrative window requires Access Control's general `Edit` action in the applicable business scope; outside the window, it requires `Edit Outside the Operational Window` in that scope. |
| AC-COR-04 | Corrections never alter the original capture timestamp of the corrected record. |
| AC-COR-05 | GIVEN a correction is attempted, WHEN the user lacks the effective permission for the record family and scope, THEN the correction is rejected regardless of the user's organizational position. |
| AC-COR-06 | A correction updates the affected operational record in place and preserves append-only audit evidence for each changed business record, rather than for an interface field or generic multi-record event. |
| AC-COR-07 | GIVEN a progress input or output is corrected, WHEN later continuity records may be affected, THEN the system warns of those records and does not change them automatically; each later correction is manual and independently traceable. |
| AC-COR-08 | Process Quality and Waste corrections are authorized in their own transversal scopes, not section scopes. |

---

## References

- [Operation Area Overview](./overview.md) — area-level scope, actors, and cross-cutting Operation rules
- [Yarn Spinning Domain Map](../../domain/operation/yarn-spinning.md) — bounded-context domain model
- [Lot Processing Domain Map](../../domain/operation/lot-processing.md) — downstream domain consuming skein output
- [Ubiquitous Language](../../domain/ubiquitous-language.md) — canonical naming contract
