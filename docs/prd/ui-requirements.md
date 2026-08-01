---
document_type: prd
status: active
scope: global/ui
authority: normative
owner: product
last_reviewed: 2026-08-01
---

# Colibri Hub - UI Requirements

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
   shared context, and each screen incorporates them as needed in dashboards,
   forms, and queries. They are not part of the global top bar and do not change
   the user's authorization.

3. **Spreadsheet-style capture is the primary mode for repetitive data.**
   Yarn Spinning production discharges per machine and certain quality records
   require multi-row entry in a session. The UI must prioritize keyboard
   navigation, rapid entry, and inline feedback.

4. **Guided forms correspond to rich business objects.**
   Receptions, production identity, Warehouse movements, and lot stage records
   have complex structure and conditional fields.

5. **Controlled editing is visible, not silent.** The user must know whether a
   record is editable, whether a correction reason is required, and when the
   operational window is closed.

6. **Authorization uses effective permissions, not fixed roles.** Each permission
   combines a general action with an explicit business scope. The UI may hide or
   disable routes and actions according to effective permissions, but it must
   never assume that a specific business actor such as Supervisor or Quality
   Control is the only actor that can perform an operation. UI visibility never
   replaces backend authorization.

7. **Product states are displayed as separate dimensions.**
   Quality, Warehouse availability, and physical presentation are distinct
   concepts and must appear as separate fields or badges, not as a single
   compound state.

8. **Dashboards present scoped Read queries.** A dashboard is a presentation of
   information, not a separate RBAC action. Section dashboards and the
   transversal consolidated dashboard have distinct business scopes. Date,
   shift, section, and similar selectors are filters; they are not permissions
   or independent capabilities.

---

## 2. Global Layout

The layout is organized into three permanent zones:

- **Top bar:** system identity, navigation toggle, theme, and current user.
- **Sidebar:** routes available according to the user's effective permissions.
- **Main content:** the active dashboard, query, form, table, or detail view.

### 2.1 Top bar

| Element | Behavior |
| --- | --- |
| Logo / system name | Link to the user's default authorized route |
| Sidebar toggle | Button to collapse or expand navigation |
| Theme toggle | Light or dark mode |
| Current user | Name and avatar; profile and logout menu |

### 2.2 Sidebar

Main navigation is organized by business context. Each context may expand into
sub-items, and the active section is visually highlighted. A route is displayed
only when the user has the effective permissions required to access at least one
of its supported operations. Hiding or displaying a route never grants access;
the backend remains the final authorization authority.

- **Warehouse**
  - Bale reception
  - Production identity
  - Delivery to Production
  - Finished-product reception
  - Classification / availability
  - Outbound movements and returns
  - Supplies
  - Stock and history

- **Preparation**
  - Dashboard by section
  - Production discharges and Progress records

- **Ring Spinning (Continuas)**
  - Dashboard by section
  - Production discharges and Progress records

- **Winding (Bobinados)**
  - Dashboard by section
  - Production discharges and Progress records

- **Twisting (Retorcido)**
  - Dashboard by section
  - Production discharges and Progress records

- **Skeining (Madejeras)**
  - Dashboard by section
  - Production discharges and Progress records

- **Process quality**
- **Waste**

- **Lot Processing**
  - Lot queue
  - Lot detail

- **Dashboards and reports**
  - Consolidated dashboard
  - Production vs plan
  - Lot traceability

- **Admin**
  - Master data
  - Access Control
    - Users
    - Roles
    - Presets
    - Business scopes
    - Access audit

Access Control navigation requires the effective `Manage Access` action. The
consolidated dashboard is shown only to users with `Read` in its transversal
business scope. Section dashboard navigation follows `Read` permission in the
corresponding section scope.

### 2.3 Main content

The variable area where the active screen is rendered supports:

- List or table view with filters
- Data capture form
- Record detail
- Section or consolidated dashboard with interactive filters

---

## 3. Screens by Context

### 3.1 Warehouse

#### Bale reception

Registration of raw-material intake from supplier.

- See [Bale Management PRD](./warehouse/bale-management.md) section 7 for reception fields.
- Table of received bales with filterable history
- Each bale is a row; multiple bales can be registered per batch

#### Production identity

Definition of the unique lot identity before it physically exists.

> Business rules for this capability are defined in [Production Identity PRD](./warehouse/production-identity.md). This section defines only cross-cutting UI patterns.

- Form with: `lot_code`, `production_identity_id`, yarn count, color,
  customer/destination, and order specifications
- List of defined identities with their state, such as pending delivery

#### Delivery to Production

Registration of raw-material departure from Warehouse to Production.

- Bale selector limited to complete bales not previously delivered

See [Bale Management PRD](./warehouse/bale-management.md) section 12 for delivery rules.

#### Finished-product reception

Reception of finished product from Operations.

> Business rules for this capability are defined in [Finished Product PRD](./warehouse/finished-product.md). This section defines only cross-cutting UI patterns.

- List of lots awaiting Warehouse receipt after being sent by Quality
- Lot detail with operation data in read-only mode
- Physical verification with documentation of inconsistencies, if any
- Reception confirmation

#### Classification / availability

Management of the operational state of finished product in Warehouse.

> Business rules for this capability are defined in [Finished Product PRD](./warehouse/finished-product.md). This section defines only cross-cutting UI patterns.

- Lot selector
- Separate fields for:
  - Quality state inherited from Operations and displayed read-only
  - Warehouse availability: available, flagged, available with condition,
    defective, or delivered
  - Physical presentation: bag, bulk, cone, or ball
- State change history

#### Outbound movements and returns

Registration of direct sales, transfers to Commercialization, and returns.

> Business rules for this capability are defined in [Finished Product PRD](./warehouse/finished-product.md). This section defines only cross-cutting UI patterns.

- Movement type selector
- Form by type: customer, quantity in kg, invoice, and date
- Return references the original sale
- Authorization state and responsible actor visible according to the current
  domain policy; the UI must not hardcode Production Manager as the only actor
  who may authorize the operation

#### Supplies

Management of production supplies such as dyes, chemicals, and packaging.

> Business rules for this capability are defined in [Production Supplies PRD](./warehouse/production-supplies.md). This section defines only cross-cutting UI patterns.

- Configurable categories
- Reception, consumption, and return by category
- Stock table by category

#### Stock and history

Balance and movement queries.

> Business rules for this capability are defined in [Warehouse Overview](./warehouse/overview.md). This section defines only cross-cutting UI patterns.

- Filters by subdomain, date, lot, and other available criteria
- Calculated balance: previous + inbound - outbound
- Movement history by lot or item

---

### 3.2 Yarn Spinning

> Business rules for Yarn Spinning capabilities are defined in [Yarn Spinning PRD](./operation/yarn-spinning.md). This section defines only cross-cutting UI patterns.

#### Dashboard by section

Interactive production summary within an authorized section scope.

- Cards, charts, or tables for the selected section: Preparacion (Preparation),
  Continuas (Ring Spinning), Bobinados (Bobbin Winding), Retorcido (Twisting),
  or Madejeras (Skeining)
- Metrics available for the section, such as total discharged, productivity in
  kg/h, quality information, and waste
- Filters by business date, shift, and other section criteria
- Access requires `Read` in the corresponding section scope
- Selecting a date or shift refines the query and does not change authorization

#### Production discharges

Spreadsheet-style capture of production discharges per machine.

- Editable table where each row is a production discharge:
  machine, yarn count, gross weight, number of spindles, tare per spindle,
  cart weight, and automatically calculated net weight
- Madejeras (Skeining) has distinct rows for skeins and unit weight
- Supports adding multiple rows in a session
- Inline validation: net weight greater than zero and spindles greater than zero
- Calculated totals at the bottom

#### Progress records

Per-machine summary at shift end.

- Form per machine: input, output, discharged weight as the sum of shift
  discharges, and hours worked
- Gross sample weight and tare for output calculation
- Applies only to Preparacion (Preparation), Continuas (Ring Spinning), and
  Retorcido (Twisting). Bobinados (Bobbin Winding) and Madejeras (Skeining)
  do not have progress records

#### Process quality

Quality control records by section and machine.

- Section and machine selector
- Dynamic fields by method:
  - **Samples:** Preparacion and Continuas; individual values and CV%
  - **Machine record:** Bobinados; body, km, and cuts
  - **Random:** Retorcido and Madejeras; test result
- Quality control history by machine

#### Waste

Waste recording by machine group.

- Section and machine group selector
- Weight and type: real or accumulated
- Madejeras out of specification is not recorded as waste; it is marked for
  reprocessing

Produced skeins available for lot assembly are not an independent capability or
sidebar page. When required by the Inventory stage, the lot assembly flow may
present the eligible skeins as contextual source data according to the relevant
domain rules and effective permissions.

---

### 3.3 Lot Processing

> Business rules for Lot Processing capabilities are defined in [Lot Processing PRD](./operation/lot-processing.md). This section defines only cross-cutting UI patterns.

#### Lot queue

List of active lots organized by current stage.

- Table with lot code, yarn count, current stage, responsible business actor,
  and last update
- Filters by stage, yarn count, date, and other available criteria
- Selecting a lot opens its detail

#### Lot detail

Unified view of the complete lot history.

- Vertical timeline with the 6 stages
- Each stage shows the responsible business actor, date and shift, technical
  data, and observations
- The active stage is highlighted and allows entry or editing only when domain
  rules and effective permissions allow it
- Completed stages are displayed read-only unless controlled correction is
  permitted
- Button to register advancement to the next stage when authorized

#### Stage registration

Each stage has its own specialized form. All share:

- Business date and shift
- Responsible business actor and supervisor
- Stage-specific technical data
- Issue category selector as an optional field
- Optional free-text observations

**Inventory stage - lot assembly:**

- Yarn count inherited from the production identity
- Eligible skein selection
- Skein quantity and total weight

**Dyeing - color application:**

- Skeins received, net weight, vat number, and temperature

**Drying - moisture removal:**

- Skeins entered and total weight

**Winding / Ball Winding - conversion to final format:**

- Format: cone or ball
- Skeins processed, units produced, and waste in kg

**Bagging - packaging:**

- Bags used, units per bag, and waste in kg

**Quality stage - final inspection:**

- Visual and internal defects as categorized checkboxes
- Special nomenclature, if applicable
- Final classification: standard, with nomenclature, or flagged
- Confirmation of Quality Send to Warehouse

---

### 3.4 Dashboards and Reports

#### Consolidated dashboard

Transversal interactive view for users responsible for supervising or consulting
information across plant areas.

- May combine authorized information from multiple sections and business contexts
- Supports available filters such as date, shift, section, yarn count, or period
- May include production versus plan, active lot status, accumulated waste,
  quality indicators, and significant deviation alerts
- Access requires `Read` in the transversal consolidated dashboard scope
- Access does not grant `Write` or `Edit` in any represented context
- Labels such as Shift Summary or Daily Summary describe filtered states of this
  dashboard and are not separate pages or permissions

#### Production vs plan

Comparison by yarn count and period.

- Bar chart or table with planned versus actual production
- Filters by yarn count and date range
- Main metric: kg produced versus kg planned

#### Lot traceability

Complete lot journey across business contexts.

- Timeline from definition in Warehouse to current state
- Warehouse and Operations data combined in a read-only view
- Access follows `Read` permission in the business scope defined for this query

---

### 3.5 Access Control Administration

> Business rules are defined in [Access Control PRD](./access-control.md). These
> screens are available only with the effective `Manage Access` action.

#### Users

- Consult users and their active state
- Assign or remove one or more configurable roles
- Preview effective-permission changes before confirmation

#### Roles

- Create, inspect, edit, activate, or deactivate configurable roles
- Assign explicit permissions expressed as a general action and business scope
- Show the users affected by a role change before confirmation

#### Presets

- Consult and maintain reusable role templates
- Create an independent role by copying a preset
- Make clear that later preset changes do not silently change existing roles

#### Business scopes

- Consult registered business scopes and their active state
- Prevent the interface from presenting nonexistent or inactive scopes as valid
  authorization targets

#### Access audit

- Query append-only records of changes to users, roles, presets, assignments,
  permissions, and scopes
- Display the individual actor, date and time, reason when required, previous
  state, and new state

---

## 4. UI Patterns

### 4.1 Spreadsheet-style capture

For Yarn Spinning production discharges, progress records, and waste.

- Table with dynamically addable rows
- Keyboard navigation with Tab, Enter, and arrow keys
- Cells with inline validation on blur
- Automatically calculated totals at the bottom
- Add row and Delete row buttons
- Paste from external clipboard

### 4.2 Lot timeline

For visualizing Lot Processing history.

- Vertical line with nodes for each stage
- Nodes displayed as completed, active, or pending
- Selecting a completed node expands its detail
- The active node shows the registration form when authorized

### 4.3 Guided form

For Warehouse and stage records.

- Single step or multiple sections on one page
- Required fields marked
- Validation on submit rather than on every field
- Summary before confirmation when the record is critical

### 4.4 Controlled editing

For correction of existing records.

- Visual indicator of editable or not editable state
- Within the domain's operational window, correction requires effective `Edit`
  permission in the corresponding business scope
- Outside that window, correction requires effective
  `Edit Outside the Operational Window` permission in that scope
- A domain rule may prohibit correction even when a user has an action in the
  corresponding scope
- Correction modal with:
  - Previous values visible
  - Editable fields
  - Correction reason when required by the domain
  - Confirmation with audit warning

### 4.5 Shift and date selector

Session context component. Each screen places it where appropriate next to a
form, dashboard, or section heading. It is not part of the global top bar.

- Shift selector with A, B, C, and all when the current query supports it
- Business date picker with a shortcut for today
- Changes update the screens that use these values through shared session context
- Changes refine operational or query context and never modify effective permissions

---

## 5. Global UI States

| State | Scope | Purpose |
| --- | --- | --- |
| `activeShift` | Session | Active shift for capture and queries |
| `businessDate` | Session | Active business date |
| `currentUser` | Session | Authenticated user with effective permissions |
| `sidebarCollapsed` | Local UI | Sidebar state |
| `filters` | Per screen | Active filters such as section, yarn count, date, or shift |
