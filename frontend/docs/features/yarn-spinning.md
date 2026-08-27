---
document_type: technical-spec
status: draft
implementation: not-started
scope: operation/yarn-spinning
authority: explanatory
owner: frontend
last_reviewed: 2026-08-27
replaces: null
---

# Technical Specification — Frontend Yarn Spinning (Hilatura)

> **Normative PRD:** [Yarn Spinning](../../../docs/prd/operation/yarn-spinning.md)
>
> This document is a **frontend technical specification** (explanatory). Business rules, state
> definitions, identity constraints, and acceptance criteria are defined in the normative PRD linked
> above. Any business rule referenced here is explanatory context only — the PRD is authoritative.
>
> The **wire schema** (endpoint field names, types, and validation) is owned by the complementary
> backend yarn-spinning technical specification, which is to be created. This spec describes the
> frontend capability architecture and the user experience, and references the PRD and the backend
> spec for field-level semantics.

**Product:** Colibri Hub
**Context:** Operation
**Type:** Technical Specification — Frontend
**Status:** Draft
**Implementation:** Not started
**Complementary spec:** Backend yarn-spinning technical specification — *to be created*
**Date:** 2026-08-27

---

## 1. Overview

The frontend implements the Yarn Spinning (Hilatura) capability as a single, capability-oriented
module under the operation context. Its centerpiece is the **shift-close section capture workspace**:
a per section × shift × business-date workspace where **Production Discharge (DIS)**, **Progress
(PRG)**, and **Skeining (SKN)** are captured in a per-machine spreadsheet-style grid and submitted
atomically for that section. **Process Quality (QUA)** and **Waste (WST)** are NOT part of that
workspace; they are separate transversal capture surfaces with their own independent submits and
RBAC scopes. Around the capture workspace it provides per-section dashboards, a transversal
consolidated dashboard, and a controlled correction experience consistent with the access-control
permission model.

The capability consumes read-only shared reference data (catalogs), never embeds catalog values, and
renders every calculated weight read-only. It hides or disables routes and actions according to the
user's *effective* permissions and assumes no fixed role such as Supervisor or Quality Control.

All eight Hilatura sidebar entries already exist in the application navigation configuration and route
registration, each pointing at a placeholder and protected by a scope requirement. No capture grid,
dashboard, permission-gated action, or correction surface exists yet.

---

## 2. Architecture & component boundaries

The capability is composed by the application shell; it does **not** import shell internals
(routing/layout). Its shared surface is deliberately small and limited to:

- a **common grid** component (spreadsheet capture base: shell, toolbar, renderers, editors),
- **common UI components**,
- the **access-control** capability (route protection by scope, effective-permission evaluation,
  correction-requirement catalog),
- the shared **HTTP client**.

Within the capability, the architecture is organized first by ownership, with a narrow public
contract (an API module that owns endpoint calls + request/response mapping, and a set of domain
view models) kept separate from presentation internals. Pages and presentational components depend
only on that public contract; they never reach into each other's internals. Components never call
`fetch` directly.

Conceptual building blocks (not an exhaustive code inventory):

- **Section capture workspace** — the shift-close capture experience for one section; orchestrates
  load, edit, and atomic submit of the section's in-scope families, plus conflict and work-preservation
  state.
- **Transversal capture surfaces** — the Quality and Waste capture experiences, each its own surface
  with independent scope and submit.
- **Dashboards** — per-section metrics and the transversal consolidated metrics, both read-only and
  filter-driven.
- **Correction surface** — a modal experience for in-place correction with before/after review,
  mandatory reason, and an audit warning.
- **Catalog consumption** — read-only loading of sections, machines, yarn counts (carrying material type and the process-specific notations `notation_spinning` / `notation_lot`), machine
  groups, employees, and shifts.
- **Decimal arithmetic** — a shared string-based, BigInt-scaled helper reused across capabilities
  (promoted from the existing bales implementation so spinning does not depend on bales internals).

---

## 3. Pages and routes

The eight Hilatura sidebar entries already exist in the navigation configuration and are protected by
scope requirements. Per the project's frontend feature-spec convention and the collapsed
information architecture already present in navigation, **each section is a single route that combines
its dashboard (read-scoped, default) and its capture workspace (active capture) in one experience**,
rather than separate nav sub-items.

| Sidebar entry | Route | Required scope (see Access Control §6) |
| --- | --- | --- |
| Preparación | `/spinning/preparation` | `yarn_spinning.section.preparation` (read) |
| Ring spinning | `/spinning/ring-spinning` | `yarn_spinning.section.ring_spinning` (read) |
| Bobinado | `/spinning/bobbin-winding` | `yarn_spinning.section.bobbin_winding` (read) |
| Retorcido | `/spinning/twisting` | `yarn_spinning.section.twisting` (read) |
| Madejas | `/spinning/skeining` | `yarn_spinning.section.skeining` (read) |
| Calidad de proceso | `/spinning/quality` | `yarn_spinning.process_quality` (read/write) |
| Desperdicio | `/spinning/waste` | `yarn_spinning.waste` (read/write) |
| Consolidado | `/spinning/consolidated` | `transversal.consolidated_dashboard` (read) |

Quality and Waste are **separate transversal capture surfaces** with their own scopes, not sub-forms
of a section workspace. Route visibility is provided by the application's route protection bound to
the scope catalog; the capability additionally gates **actions** (submit, add/delete row, paste,
correct) using effective-permission evaluation and never assumes a literal role name.

All routes are lazily loaded; no placeholder pages remain after implementation.

---

## 4. Capture experience

### 4.1 Backend is authoritative

The frontend validates format and completeness (required fields, decimal format, duplicates within
the current grid). It does **not** decide: global uniqueness, net-weight truth, state transitions,
concurrency, or persistence rules. The backend owns every business rule.

### 4.2 The grid is an operational tool

The common grid component delivers spreadsheet-like interaction in DIS/PRG/SKN: keyboard navigation,
paste from a spreadsheet, inline editing, frozen columns, virtualization, and summary rows — mirroring
the mature bales capture convention already in the codebase.

### 4.3 Atomic per capture surface, deterministic outcome

Each capture surface submits in its own transaction; partial persistence never occurs within a
surface. The **section production capture is atomic for the families that section records** (DIS/SKN/PRG
as applicable per the domain applicability matrix). Process Quality and Waste are separate atomic
submits on their own transversal endpoints. Every in-scope machine is accounted for in the capture: a machine with no production is represented by a zero-valued row (or omitted and treated as zero), never left undetermined. The capture UI requires each in-scope machine to be acknowledged before submission.

### 4.4 Permission-driven visibility and actions

Route visibility comes from route protection bound to the scope catalog. Actions are gated by
effective-permission evaluation. No UI branch assumes a literal role name.

### 4.5 Work preservation

No user-entered data is cleared by remote validation errors, conflicts, network failures, or 500
responses. Data is cleared only by explicit user action or after a successful operation is
acknowledged.

### 4.6 Section capture workspace

The shift-close **section capture workspace** is the primary capture mode. Its context (business date
+ shift) is provided by the shared shift/date selector held in session context; it is not part of the
top bar and never changes authorization.

- **DIS / PRG / SKN grids** — per (machine, yarn count, material type) editable spreadsheet, where material type is resolved from the selected yarn count. A single machine
  can contribute several rows across different yarn counts in one shift (per PRD DIS-04); non-numeric
  titles such as "Fantasía"/"OTRO" are valid catalog entries. Which grids appear depends on the
  section's applicability matrix: Preparación shows DIS (FIN only) + PRG (PSJ only), SKN N/A;
  Continuas/Bobinados/Retorcido show DIS (+ PRG for Continuas/Retorcido, no PRG for Bobinados); Madejeras shows SKN only.
- **Submit** — sends the section's production families (DIS/SKN/PRG as applicable) in **one
  transaction**. On success the whole section production is recorded; on failure nothing persists.

Process Quality (QUA) and Waste (WST) are NOT part of this workspace. They are separate transversal
capture surfaces — `/spinning/quality` and `/spinning/waste` — each with its own submit and
independent scope.

**Capture completeness (UI):** the workspace lists every in-scope machine for the section/shift and requires each to be acknowledged before submission. A machine with no production is represented by a zero-valued row (or omitted and treated as zero); there is no separate persisted "affirmative zero" state. While the capture is in progress, the UI marks machines not yet acknowledged so the recorder can confirm the session is complete; after submission every in-scope machine is either present or implied zero — "never captured" exists only during an open (in-progress) capture.

**Optimistic concurrency:** the capture carries a continuity key (section × business date × shift). If
a second submit targets an already-persisted key, the backend returns a conflict with the current
stored state. The UI renders a **conflict banner** showing the stored values for review and offers
reload / re-base, never silent overwrite.

**Spreadsheet-style capture** behaviors (DIS/PRG/SKN grids, built on the common grid):

- Rows keyed by a stable client id; a trailing continuation row is auto-maintained so the grid always
  has an empty row to type into.
- Keyboard navigation, add/delete row (delete disabled for persisted rows), and duplicate-row
  prefill from a selected row.
- Material type is displayed from the selected yarn count (an attribute of the yarn count entity); no separate material-type catalog is loaded.
- Paste from spreadsheet (TSV), bounds-checked against capacity and editable columns.
- Inline validation per cell (format, range, required, numeric) blocking submit while invalid.
- Calculated totals at the grid bottom.
- Select editors for catalog columns.
- Decimal values handled as strings through the shared decimal module.

### 4.7 Per-family forms (business-level)

Field and calculation rules follow the PRD attribute tables; the backend remains authoritative. The
UI only validates for feedback. Key business behaviors:

- **DIS (Production Discharge):** net weight is computed read-only (gross cart weight − total spindle
  tares − cart weight). Per the PRD canonical unit contract, gross/cart weights are in **kg** and spindle
  tare in **g**; the UI labels each field's unit and transports all decimals as strings — no hardcoded
  kg/g conversion in the client. A discharge row is keyed by (machine, yarn count, material type) within a
  shift, so one machine contributes several rows across yarn counts (PRD DIS-04). A PSJ machine in
  Preparación is rejected. **Supervisor and foreman** are shift-level capture attributes: captured once
  at the capture header (the form header) via the employee catalog, not per row, and applied to the whole
  section capture; the backend records the acting
  user.
- **SKN (Skeining):** skein count × unit weight (entered at capture, grams) yields a read-only estimated
  total weight; no spindles/tare/cart; operator name is free text with no employee link.
- **PRG (Progress):** per-machine; input weight prefilled from the prior shift's output for the same
  machine + yarn count; spindle sampling inputs; discharged weight is a read-only sum of the shift's
  discharge nets; reconciliation against discharge totals beyond tolerance blocks submit (mandatory
  consistency note within tolerance).
- **QUA (Process Quality):** separate transversal surface, dynamic by method (Sample / Machine register
  / Random) per the PRD; computed statistics (average, standard deviation, CV%, derived tenacity/
  elongation) are read-only.
- **WST (Waste):** separate transversal surface; theoretical waste = real + accumulated, read-only;
  out-of-spec skeins are not waste (offer a reprocessing path instead).
- **Unit contract (UI):** every weight field is labeled with its PRD-canonical unit — gross/cart weights
  in kg; spindle tare, sample weights, and skein unit weight in g; progress weights in kg. The UI never
  mixes grams and kilograms within a single field, follows the PRD canonical units, and keeps all
  decimals as strings with no hardcoded conversion in the client.
- **Bobinado is discharge-only:** the section records DIS and not PRG, matching the applicability matrix
  (Bobinados have no progress block).

**Live computed read-only columns** render in the capture grids and recompute client-side on every
  edit, mirroring sheet formulas. The UI never accepts them as input; the backend value is
  authoritative on submit/response.

---

## 5. Permission model & UI behavior

The capability reuses the **access-control** capability (see `backend/docs/features/access-control.md`,
§6 Scope taxonomy, for the authoritative scope definitions). The Yarn Spinning capability **references**
those scopes; it does not redefine them.

Required scopes:

- `yarn_spinning.section.<section>` — per-section production capture, dashboards, and corrections.
- `yarn_spinning.process_quality` — transversal Quality capture and corrections.
- `yarn_spinning.waste` — transversal Waste capture and corrections.
- `transversal.consolidated_dashboard` — consolidated dashboard (read-only).

UI behavior:

- **Route visibility** is driven by route protection bound to the scope catalog (read permission).
- **Action gating** (submit, add/delete row, paste, correct) is driven by effective-permission
  evaluation; no literal role name is assumed.
- **Corrections** require effective `edit` (inside the operational window) or `edit_outside_window`
  (outside it) in the record family's scope. A domain rule may still prohibit correction even with
  the action.
- **Effective permission computation** (role × scope × action, with transversal overrides) is owned by
  access-control; the spinning UI only consumes the result.

---

## 6. Frontend-to-backend contract

The wire schema (field names, types, validation) is defined by the backend yarn-spinning technical
specification. This section states the **endpoint surface and the architectural decisions** bound to
it; it does not enumerate request/response attributes.

| Operation | Method | Path | Frontend usage |
| --- | --- | --- | --- |
| Read-only catalogs | `GET` | catalog endpoints (sections, machines, yarn counts — which carry material type and the `notation_spinning`/`notation_lot` designations, machine groups, employees, shifts) | Reference data for grids/forms |
| Section production capture (atomic) | `POST` | `/spinning/sections/{section}/production` | Shift-close section workspace submit (DIS+SKN+PRG as the section records) |
| Process Quality capture (transversal) | `POST` | `/spinning/process-quality` | Transversal Quality capture (scope `yarn_spinning.process_quality`) |
| Waste capture (transversal) | `POST` | `/spinning/waste` | Transversal Waste capture (scope `yarn_spinning.waste`) |
| Get capture records | `GET` | `/spinning/records?section=&business_date=&shift_code=&family=production\|process_quality\|waste` | Correction / edit context for the requested family |
| Section metrics | `GET` | `/spinning/sections/{section}/metrics?business_date=&shift_code=&...` | Per-section dashboard |
| Consolidated metrics | `GET` | `/spinning/consolidated/metrics?business_date=&shift_code=&section=&yarn_count_id=&period=` | Consolidated dashboard |
| Correction | `PATCH` | `/spinning/{family}/{record_id}` | In-place update of the record (flat table) |

Endpoints follow the repository's RESTful style. Decimal weights travel as **strings** end-to-end.
The frontend defines the shape it consumes; the **backend owns enforcement** of every business rule.

**Architectural decisions bound to this contract:**

1. **Atomic per-section production capture.** The `{section}` path segment is the RBAC scope; the body
   echoes the section for convenience. The continuity key (section × business_date × shift_code) is the
   natural composite key on the flat family records — no separate session entity exists. The body contains
   ONLY the production families the section records; QUA and WST are NOT part of this capture.
2. **Families absent for a section are omitted from the body** (NOT sent as `null`). E.g., a Preparación
   submit sends discharges + progress only; a Madejeras submit sends skeins only; Bobinados sends
   discharges only. A machine with no row is treated as zero — capture completeness requires acknowledging every in-scope machine, and an omitted or absent row is treated as zero.
3. **Unified correction/read endpoint.** A single `GET /spinning/records?...&family=...` replaces
   per-family GET routes; the `family` parameter selects the record set (production / process_quality /
   waste). It returns 404 if nothing was captured for the key.
4. **Transversal captures are separate.** Process Quality and Waste use their own POST endpoints and
   scopes; they are not sub-forms of the section workspace.
5. **Corrections use `PATCH` in-place** on the family's flat table. The backend writes an **append-only
   audit row** in the SAME transaction; the frontend sends only new values + mandatory reason + an
   optimistic-concurrency token. No separate correction endpoint is called by the frontend. This is
   reconciled with the PRD (§5.6/§9): the PRD now permits in-place update of the record's current values
   plus an append-only correction history and preserved original capture timestamp, so the in-place
   model is aligned with the normative PRD.

---

## 7. Decimal handling

All weight and quantity fields are maintained as **strings** throughout the frontend.

Rules:

- No `input type="number"`.
- No `parseFloat` for final calculations.
- No storing weights as JavaScript `number`.
- No automatic rounding or exponential notation.

Local calculations (net weight, estimated total weight, theoretical waste, totals, reconciliation
tolerance checks) use a BigInt-based scaled-integer utility (validate format → normalize scale →
operate with scaled integers → format result as string). The spinning module reuses the shared
string-based, BigInt-scaled decimal helper (promoted to a common module so capabilities do not depend
on each other's internals).

---

## 8. Error handling

- **Inline validation (grid):** per-row feedback map; errors render inline, totals alert in the status
  bar; submit blocked while any populated row is invalid.
- **Backend validation (422):** field errors are mapped back to the offending grid row/column or form
  field (e.g., net-weight mismatch, PSJ discharge, missing reconciliation note).
- **Optimistic concurrency conflict (capture, 409):** conflict banner shows stored state; user
  reloads/re-bases; no silent overwrite.
- **Optimistic concurrency conflict (correction, 409):** correction surface warns the record changed;
  user re-opens from latest state.
- **Permission (403):** action disabled/hidden up front via effective-permission evaluation; if a stale
  enabled state slips through, the error is shown as a non-retryable notice.
- **Correction audit warning:** the correction surface surfaces the in-place update + append-only
  audit-row nature before confirm.
- All API errors are normalized through the shared HTTP client's error type.

---

## 9. Accessibility, responsive, performance

- **Accessibility:** WCAG 2.1 AA for primary flows. Keyboard-operable actions, visible focus, modal
  focus trap/return, grid ARIA (labels, selection, editors), errors linked via `aria-describedby`,
  loading `aria-busy`, results `aria-live`, global errors `role="alert"`, "go to first error" focus,
   not color-dependent, minimum contrast. Conflict banner and capture-completeness indicator (unacknowledged in-scope machines) exposed to assistive tech.
- **Responsive:** desktop/tablet priority for grids and dashboards; controlled horizontal scroll on
  mobile (no row-to-card conversion); frozen columns; reachable shift/date selector and section tabs.
- **Performance:** fluid editing with up to 100 machine rows; memoized columns, stable row keys, pure
  validators, active virtualization; dashboards cancel previous requests on filter change; section
  capture uses a single POST per surface (no per-row requests).

---

## 10. Out of scope

- Backend DTO definitions and validation (owned by the backend yarn-spinning technical specification).
- RBAC scope taxonomy and permission-model internals (owned by `access-control.md`).
- Correction-requirement catalog entries and role/scope assignment (owned by the access-control
  capability).
- Operational-parameter administration UI (reconciliation tolerance, quality tolerance limits, sampling
  plan, late-capture window) — the spinning UI only *consumes* configured values.
- Data migration of existing production records (out of scope for this capability).
- Production target / objective capture. These are
  operational-planning artifacts, not per-shift captured records; the spinning UI only *consumes* any
  configured target as a read-only reference, never captures it.
- Date storage. The capture uses the shared business-date selector; no serial date representation is
  used.

---

## 11. Open questions / decisions

**Decisions already made (recorded for traceability):**

1. **Capture split — Quality/Waste transversal.** QUA and WST are transversal captures with their own
   endpoints, pages, and independent scopes; the per-section production capture contains ONLY the
   families that section records (DIS/SKN/PRG per the domain matrix). The `capture-sessions` aggregate
   was removed as overengineering — RBAC already scopes per section and each section page is its own
   capture surface.
2. **Corrections: in-place + append-only audit (reconciled with PRD).** Corrections update the record in
   place plus an append-only correction history in one transaction, preserving the original capture
   timestamp. PRD §5.6/§9 were adjusted to permit this; Design B is now aligned with the normative PRD.
3. **Spec location.** This file (`frontend/docs/features/yarn-spinning.md`) is the intended home, per the
   frontend feature-spec convention (mirroring `bale-management.md`).
 4. **Affirmative zero removed as over-modeling.** An empty cell is simply zero; there is no explicit persisted "affirmative zero" outcome or endpoint. Capture completeness (acknowledge every in-scope machine before submit) replaces it; a missing/zero row is treated as zero. PRD DIS-08 / AC-DIS-07 adjusted accordingly.
5. **`sample_values` stored as JSON with server-computed aggregates.** The QUA wire sends raw `sample_values`; the backend computes the measured properties (CV%, tenacity, elongation) and stores the raw values (e.g., a `sample_values` JSON column), not only aggregates. Reconciled with the data dictionary (which stored only aggregates).

**Genuine open questions (need a backend/contract decision):**

 4. **Capture completeness (resolved).** Every in-scope machine must be acknowledged before submission; a machine with no production is represented by a zero-valued row (or omitted and treated as zero). There is no separate persisted "affirmative zero" outcome or endpoint — the earlier "affirmative zero" modeling was removed as over-modeling. The UI marks unacknowledged machines only while the capture is in progress.
5. **`sample_values` storage shape (resolved).** The capability records the individual sample values (PRD QUA, Sample method). The wire sends the raw `sample_values` array; the backend computes the measured properties (average, standard deviation, CV%, derived tenacity/elongation) from them and stores the raw values (e.g., a `sample_values` JSON column), not only aggregates. The frontend sends raw values plus the computed statistics it already renders read-only for feedback.
6. **Dictionary vs PRD mismatch — SKN unit weight.** The data dictionary implies a title-specific weight
   parameter (e.g., 500g vs 600g) while the PRD states the unit weight is entered at capture, not a
   parameter. Reconcile semantics.
7. **Yarn count is an entity, not a row attribute.** `material_type` (and the process-specific notations `notation_spinning`/`notation_lot`) belong to the `yarn_counts` identity, not to discharge/skein records; the data dictionary must model `yarn_counts` accordingly (backend spec formalizes). Separate known omissions: waste machine
   group stored as free text not a catalog id; PRG sampling inputs absent from progress records. The
   data dictionary must reconcile with the PRD.
8. **Operational-parameters consumption.** Reconciliation tolerance, quality tolerance limits, sampling
   plan/sample count, and late-capture window duration are consumed as configured reference data.
 9. **Correction cap policy (resolved).** Rely on `version` + optimistic-concurrency conflict; no fixed edit cap; the model relies on optimistic concurrency. Field stays `version`; do not rename to `edit_version`.
 10. **Foreman/encargado capture (resolved).** The capture UI collects a foreman via the employee catalog alongside the supervisor; both are captured once at the capture header (shift-level, not per row) and recorded as explicit attributes (PRD §5.1, DIS-09). The backend records the acting user.
 11. **RM/bales waste scope gap (resolved).** The separate raw-material (RM/bales) waste store is out of scope for the new process-waste family; bales waste belongs to the Warehouse context. Flagged and confirmed out of scope.
 12. **Data migration.** Strip the existing yarn-count `'` text prefix and map free-text
     machine group to catalog ids before linking to catalogs.
13. **Non-numeric material types (resolved).** The yarn count's `material_type` attribute accepts non-numeric values such as "Fantasía" and "OTRO" (fantasy/other) alongside standard codes (HB/N); these are attributes of the `yarn_counts` entity, not a separate material-type catalog. The UI must not assume numeric material types.
 14. **Discharge identity includes yarn count (resolved).** A discharge is keyed by (machine, yarn count,
     material type) within a shift, not by machine alone — consistent with PRD DIS-01/DIS-04. The PRD §5.1 was clarified accordingly.
