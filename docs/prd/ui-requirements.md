---
document_type: prd
status: active
scope: global/ui
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Colibri Hub — UI Requirements

> User interface requirements for the textile production management system.
> This document defines which screens, navigation, and UI patterns the system
> needs, without prescribing technologies or API contracts.

---

## 1. UI Principles

1. **Each business context is an independent navigation section.**
   Warehouse, Yarn Spinning, and Lot Processing appear as separate areas because
   their concepts, timelines, and users are distinct.

2. **The business date and shift are session state.** Most data capture occurs at
   shift close, not in real time. The shift and business date are provided via
   shared context, and each screen incorporates them as needed (dashboard, forms,
   reports). They are not part of the global chrome (top bar).

3. **Spreadsheet-style capture is the primary mode for repetitive data.**
   Yarn Spinning (production discharges per machine) and certain quality records
   require multi-row entry in a session. The UI must prioritize keyboard
   navigation, rapid entry, and inline feedback.

4. **Guided forms correspond to rich business objects.**
   Receptions, production identity, Warehouse movements, and lot stage records
   have complex structure and conditional fields.

5. **Controlled editing is visible, not silent.** The user must know whether a
   record is editable, whether a correction reason is required, and when the
   operational window is closed.

6. **Authorization is expressed as capabilities, not fixed roles.** The UI may
   hide or disable actions based on permissions, but must never assume that a
   specific role (Supervisor, Quality) is the only one that can perform X.

7. **Product states are displayed as separate dimensions.**
   Quality, Warehouse availability, and physical presentation are distinct
   concepts and must appear as separate fields or badges, not as a single
   compound state.

---

## 2. Global Layout

The layout is organized into three permanent zones:

```
┌─────────────────────────────────────────────────┐
│  Top bar                                         │
│ [☰] [Logo]                  [🌙] [User ▼]    │
├──────────┬──────────────────────────────────────┤
│ Sidebar  │  Main content area                    │
│          │                                       │
│ Warehouse│  (active route)                       │
│ Spinning │                                       │
│ Lots     │                                       │
│ Reports  │                                       │
│ Admin    │                                       │
│          │                                       │
└──────────┴──────────────────────────────────────┘
```

### 2.1 Top bar

| Element | Behavior |
|---|---|
| Logo / system name | Link to dashboard or default route |
| Sidebar toggle | Button to collapse/expand navigation |
| Theme toggle | Light / dark mode |
| Current user | Name + avatar. Profile/logout menu |

### 2.2 Sidebar

Main navigation organized by bounded context. Each context may expand
sub-items. The active section is visually highlighted.

- **Warehouse**
  - Bale reception
  - Production identity
  - Delivery to Production
  - Finished-product reception
  - Classification / availability
  - Outbound movements and returns
  - Supplies
  - Stock and history

- **Yarn Spinning**
  - Dashboard by section
  - Production discharges
  - Progress records
  - Process quality
  - Waste
  - Skein availability
  - Shift summary

- **Lot Processing**
  - Lot queue
  - Lot detail

- **Reports**
  - Daily summary
  - Production vs plan
  - Lot traceability

- **Admin**
  - Master data

### 2.3 Main content

Variable area where the active screen is rendered. Supports:
- List/table view with filters
- Data capture form
- Record detail
- Dashboard with metrics

---

## 3. Screens by Context

### 3.1 Warehouse

#### Bale reception

Registration of raw-material intake from supplier.

- See [Bale Management PRD](./warehouse/bale-management.md) §7 for reception fields.
- Table of received bales with filterable history
- Each bale is a row. Multiple bales can be registered per batch

#### Production identity

Definition of the unique lot identity before it physically exists.

> Business rules for this capability are defined in [Production Identity PRD](./warehouse/production-identity.md). This section defines only cross-cutting UI patterns.

- Form with: `lot_code`, `production_identity_id`, yarn count, color,
  customer/destination, order specifications
- List of defined identities with their state (pending delivery, etc.)

#### Delivery to Production

Registration of raw-material departure from Warehouse to Production.

- Bale selector (only complete bales, not previously delivered)

See [Bale Management PRD](./warehouse/bale-management.md) §12 for delivery rules.

#### Finished-product reception

Reception of finished product from Operations.

> Business rules for this capability are defined in [Finished Product PRD](./warehouse/finished-product.md). This section defines only cross-cutting UI patterns.

- List of lots awaiting Warehouse receipt (sent by Quality)
- Lot detail with operation data (read-only)
- Physical verification: document inconsistencies if any
- Reception confirmation

#### Classification / availability

Management of the operational state of finished product in Warehouse.

> Business rules for this capability are defined in [Finished Product PRD](./warehouse/finished-product.md). This section defines only cross-cutting UI patterns.

- Lot selector
- Separate fields for:
  - Quality state (inherited from Operations, read-only)
  - Warehouse availability (available, flagged, available with
    condition, defective, delivered)
  - Physical presentation (bag, bulk, cone, ball)
- State change history

#### Outbound movements and returns

Registration of direct sales, transfers to Commercialization, and returns.

> Business rules for this capability are defined in [Finished Product PRD](./warehouse/finished-product.md). This section defines only cross-cutting UI patterns.

- Movement type selector
- Form by type: customer, quantity (kg), invoice, date
- Return references the original sale
- Visible authorization (requires Production Manager)

#### Supplies

Management of production supplies (dyes, chemicals, packaging, etc.).

> Business rules for this capability are defined in [Production Supplies PRD](./warehouse/production-supplies.md). This section defines only cross-cutting UI patterns.

- Configurable categories
- Reception, consumption, and return by category
- Stock table by category

#### Stock and history

Balance and movement queries.

> Business rules for this capability are defined in [Warehouse Overview](./warehouse/overview.md). This section defines only cross-cutting UI patterns.

- Filters by subdomain (raw material, finished product, supplies), date, lot
- Calculated balance: previous + inbound − outbound
- Movement history by lot or item

---

### 3.2 Yarn Spinning

> Business rules for Yarn Spinning capabilities are defined in [Yarn Spinning PRD](./operation/yarn-spinning.md). This section defines only cross-cutting UI patterns.

#### Dashboard by section

Production summary view by section, shift, and date.

- Cards or table by section (Preparación (Preparation), Continuas (Ring Spinning),
  Bobinados (Bobbin Winding), Retorcido (Twisting), Madejeras (Skeining))
- Metrics by section: total discharged, productivity (kg/h), waste
- Shift and date selector (uses the session context)

#### Production discharges

Spreadsheet-style capture of production discharges per machine.

- Editable table where each row is a production discharge:
  Machine, yarn count, gross weight, No. spindles, tare per spindle,
  cart weight, net weight (calculated automatically)
- Madejeras (Skeining) has distinct rows: skeins, unit weight
- Supports adding multiple rows in a session
- Inline validation: net > 0, spindles > 0
- Calculated totals at the bottom

#### Progress records

Per-machine summary at shift end.

- Form per machine: input, output, discharged weight (sum of shift
  discharges), hours worked
- Gross sample weight and tare for output calculation
- Applies only to Preparación (Preparation), Continuas (Ring Spinning),
  and Retorcido (Twisting) (Bobinados (Bobbin Winding) and Madejeras (Skeining)
  do not have progress records)

#### Process quality

Quality control records by section and machine.

- Section and machine selector
- Dynamic fields by method:
  - **Samples** (Preparación (Preparation), Continuas (Ring Spinning)): individual values, CV%
  - **Machine record** (Bobinados (Bobbin Winding)): body, km, cuts
  - **Random** (Retorcido (Twisting), Madejeras (Skeining)): test result
- Quality control history by machine

#### Waste

Waste recording by machine group.

- Section, machine group selector
- Weight, type (real / accumulated)
- Madejeras (Skeining) out of specification: not recorded as waste,
  marked for reprocessing

#### Skein availability

View of produced skeins available for lot assembly.

- Table by yarn count: skein quantity, total weight
- Filter by production date

#### Shift summary

Shift production summary for the Supervisor.

- Total production by section
- Quality: controls performed, results
- Total waste
- Printable or exportable view

---

### 3.3 Lot Processing

> Business rules for Lot Processing capabilities are defined in [Lot Processing PRD](./operation/lot-processing.md). This section defines only cross-cutting UI patterns.

#### Lot queue

List of active lots organized by current stage.

- Table with: lot code, yarn count, current stage, responsible operator,
  last update
- Filters by stage, yarn count, date
- Click on a lot opens its detail

#### Lot detail

Unified view of the complete lot history.

- Vertical timeline with the 6 stages
- Each stage shows: responsible operator, date/shift, technical data,
  observations
- The active (current) stage is highlighted and allows editing/entry
- Completed stages are read-only
- Button to register advancement to the next stage

#### Stage registration

Each stage has its own specialized form. All share:

- Business date and shift
- Responsible operator and supervisor
- Stage-specific technical data
- Issue category selector (optional)
- Detail field for observations (optional free text)

**Inventory stage** — lot assembly:
- Yarn count (inherited), skein quantity, total weight

**Dyeing** — color application:
- Skeins received, net weight, vat number, temperature

**Drying** — moisture removal:
- Skeins entered, total weight

**Winding / Ball Winding** — conversion to final format:
- Format (cone / ball), skeins processed, units produced,
  waste in kg

**Bagging** — packaging:
- Bags used, units per bag, waste in kg

**Quality stage** — final inspection:
- Visual and internal defects (categorized checkboxes)
- Special nomenclature (if applicable)
- Final classification: standard, with nomenclature, flagged
- Confirmation of Quality Send to Warehouse

---

### 3.4 Reports

#### Daily summary

Production Manager view with the day's production.

- Production by section vs. plan
- Active lot status
- Accumulated waste
- Significant deviation alerts

#### Production vs plan

Comparison by yarn count and period.

- Bar chart or table: planned vs actual
- Filter by yarn count, date range
- Main metric: kg produced vs kg planned

#### Lot traceability

Complete lot journey cross-context.

- Timeline from definition in Warehouse to current state
- Warehouse and Operations data combined in a read-only view

---

## 4. UI Patterns

### 4.1 Spreadsheet-style capture

For Yarn Spinning — production discharges, progress records, waste.

- Table with dynamically addable rows
- Keyboard navigation (Tab, Enter, arrows)
- Cells with inline validation on blur
- Automatically calculated totals at the bottom
- "Add row" and "Delete row" buttons
- Paste from external clipboard

### 4.2 Lot timeline

For Lot Processing — visual history.

- Vertical line with nodes for each stage
- Nodes: completed (check), active (highlighted), pending (dimmed)
- Click on completed node expands detail
- Active node shows the registration form

### 4.3 Guided form

For Warehouse and stage records.

- Single step or multi-section on one page
- Required fields marked
- Validation on submit, not on every field
- Summary before confirmation when the record is critical

### 4.4 Controlled editing

For correction of existing records.

- Visual indicator of editable / not editable
- Correction modal with:
  - Previous values visible
  - Editable fields
  - Required correction reason field
  - Confirmation with audit warning

### 4.5 Shift and date selector

Session context component. Each screen places it where appropriate
(next to forms, in dashboard, or in section headers). It is not part of
the global chrome.

- Shift: dropdown with A/B/C and "all" option
- Business date: date picker with shortcut for "today"
- Changes update all screens that use these values through a shared
  session context

---

## 5. Global UI States

| State | Scope | Purpose |
|---|---|---|
| `activeShift` | Session | Active shift for capture and queries |
| `businessDate` | Session | Active business date |
| `currentUser` | Session | Authenticated user with capabilities |
| `sidebarCollapsed` | Local UI | Sidebar state |
| `filters` | Per screen | Active filters (section, yarn count, date, etc.) |
