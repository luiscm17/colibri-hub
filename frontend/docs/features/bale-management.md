---
document_type: technical-spec
status: active
implementation: partial
scope: warehouse/bales
authority: explanatory
owner: frontend
last_reviewed: 2026-07-28
---

# Technical Specification — Frontend Bale Management

> **Normative PRD:** [Bale Management](../../../docs/prd/warehouse/bale-management.md)
>
> This document is a **frontend technical specification**. Business rules, state definitions,
> identity constraints, and acceptance criteria are defined in the normative PRD linked above.
> Any business rule referenced here is explanatory context only — the PRD is authoritative.

**Product:** Colibri Hub  
**Context:** Warehouse  
**Type:** Technical Specification — Frontend  
**Status:** Partially implemented  
**Technical baseline:** Repository `luiscm17/colibri-hub`, branch `main`  
**Complementary spec:** [Backend bale management](../../../backend/docs/features/bale-management.md)  
**Date:** 2026-07-28

---

## 1. Executive summary

The frontend implements the bale management capability through three dedicated pages:

1. **Bale Reception** — Spreadsheet-style grid for registering a complete raw-material batch (1–100 bales) in a single atomic operation.
2. **Bale Stock** — Aggregated metrics with filters and individual bale lookup by business identity.
3. **Delivery to Production** — Spreadsheet-style grid for recording which bales were delivered, submitted as a single batch request.

All three pages use `react-data-grid` for data entry (Reception and Delivery) and Mantine for layout, forms, feedback, and metrics (Stock). The backend is authoritative for all business decisions; the frontend validates format and completeness only.

---

## 2. Technology stack

| Area | Technology |
| --- | --- |
| Framework | React 19 |
| Language | TypeScript 6 |
| Build | Vite 8 |
| UI | Mantine 9 (Core, Form, Hooks, Notifications) |
| Grid | `react-data-grid` 7.0.0-beta.61 |
| Navigation | React Router 7 |
| Icons | Tabler Icons React |
| Styles | CSS Modules + Mantine tokens |
| Quality | TypeScript build + ESLint |

### 2.1 Constraints

No additional libraries for: UI, grids, global state, server state, dates, decimals, forms, or modals. The implementation exploits React, Mantine, React Router, and `react-data-grid` exclusively.

---

## 3. Pages and routes

| Page | Route | Responsibility |
| --- | --- | --- |
| Bale Reception | `/warehouse/bales/reception` | Register a complete raw-material batch |
| Bale Stock | `/warehouse/bales` | Show aggregated metrics and lookup individual bales |
| Delivery to Production | `/warehouse/bales/delivery` | Record batch delivery of bales to Production |

Navigation under Warehouse sidebar:

```text
Warehouse
├── Bale Reception
├── Bale Stock
└── Delivery to Production
```

All routes use `React.lazy`. No placeholder pages.

---

## 4. API contract consumed

| Operation | Method | Path | Frontend usage |
| --- | --- | --- | --- |
| Register batch | `POST` | `/api/v1/warehouse/bales` | Reception page |
| Stock summary | `GET` | `/api/v1/warehouse/bales` | Stock page metrics |
| Bale detail | `GET` | `/api/v1/warehouse/bales/{shipment_number}/{bale_number}` | Stock page lookup |
| Batch delivery | `POST` | `/api/v1/warehouse/bales/deliver` | Delivery page |

Full contract details are defined in the [backend technical specification](../../../backend/docs/features/bale-management.md).

---

## 5. UX principles

### 5.1 One surface per task

Reception, stock visibility, and delivery are separate pages. They are not combined into a single screen.

### 5.2 The grid is an operational tool

`react-data-grid` is used in Reception and Delivery for spreadsheet-like interaction: keyboard navigation, paste from Excel, inline editing, frozen columns, virtualization, and summary rows.

### 5.3 Backend is authoritative

The frontend validates format and completeness (required fields, decimal format, duplicates within the current grid). It does NOT decide: global uniqueness, bale availability, state transitions, concurrency, or persistence rules.

### 5.4 Work preservation

No user-entered data is cleared by: remote validation errors, conflicts, network failures, or 500 responses. Data is cleared only by explicit user action or after a successful operation is acknowledged.

---

## 6. Bale Reception

### 6.1 Objective

Register a complete raw-material batch and all its bales through a single atomic operation, using a spreadsheet-style editable grid.

### 6.2 Layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Bale Reception                             [Clear draft]     │
├─────────────────────────────────────────────────────────────┤
│ [Shipment number] [Reception date] [Provider]                │
├─────────────────────────────────────────────────────────────┤
│ [Add] [Remove] [Clear]        12 valid · 2 with errors       │
├─────────────────────────────────────────────────────────────┤
│ # | Bale | Material | Dtex | Gross | Tare | Net | Status     │
├─────────────────────────────────────────────────────────────┤
│ Summary row: count · gross · tare · net · errors             │
├─────────────────────────────────────────────────────────────┤
│                                    [Register batch]          │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Header

| Field | Control | Rule |
| --- | --- | --- |
| Shipment number | Mantine `TextInput` | Required, max 10, uppercase |
| Reception date | `TextInput type="date"` | Required, no time component |
| Provider | Mantine `TextInput` | Required, trimmed on submit |

No other fields (invoice, truck, driver, lot code, global material).

### 6.4 Grid row model

```typescript
interface ReceptionGridRow {
  rowId: string
  baleNumber: string
  materialType: string
  dtex: string
  grossWeightKg: string
  containerWeightKg: string
  netWeightKg: string          // computed: gross - tare
  validationStatus: 'empty' | 'partial' | 'valid' | 'invalid'
}
```

### 6.5 Grid columns

| Column | Editable | Rule |
| --- | ---: | --- |
| Selection | No | Multi-row deletion |
| # | No | Visual order |
| Bale number | Yes | Frozen, required, unique within batch |
| Material type | Yes | Required, uppercase |
| Dtex | Yes | Decimal string > 0 |
| Gross weight | Yes | Decimal string > 0 |
| Container weight | Yes | Decimal string > 0 and < gross |
| Net weight | No | Gross minus tare (computed) |
| Status | No | Row validation indicator |

### 6.6 Paste from Excel

Expected column order: `Bale number | Material type | Dtex | Gross weight | Tare`

- Paste starts at the selected cell.
- Rows are added as needed (max 100 non-empty).
- Computed cells do not accept paste.
- Values are preserved as strings.
- Paste triggers validation and recalculation.
- A range exceeding the limit is rejected entirely.

### 6.7 Row management

- Start with 5 empty rows.
- Maintain a continuation row.
- Empty rows do not count toward the 100-bale limit.
- Partial rows are preserved (not discarded).
- Bulk delete and full clear require confirmation.
- Row order does not change after deletion.
- `rowId` is never reused.

### 6.8 Validation

| Status | Meaning |
| --- | --- |
| `empty` | All fields blank |
| `partial` | Some fields filled, some missing |
| `valid` | All fields pass rules |
| `invalid` | Format or relationship error |

All duplicate bale numbers (after normalization) are marked — not just the second occurrence.

### 6.9 Summary row

Visible at all times (via `summaryRows`):

- Rows with content / valid / with errors
- Total gross weight (valid rows only)
- Total tare (valid rows only)
- Total net weight (valid rows only)

### 6.10 Submission flow

1. Validate header.
2. Validate grid (reject partial/invalid rows).
3. Require at least one valid bale.
4. Focus first invalid cell if errors exist.
5. Create immutable snapshot.
6. Open confirmation modal (shipment, date, provider, count, weights).
7. On confirm: block editing, show "Registering N bales...", POST.
8. On 201: show result modal (shipment, date, provider, bale_count). Clear only on explicit action.
9. On error: preserve everything, map errors to header or cells, allow retry.

### 6.11 Error mapping

| Backend error | Frontend representation |
| --- | --- |
| `duplicate_shipment_number` | Mark header field + modal |
| `bales.N.field` | Map via snapshot to `rowId` → mark cell |
| `duplicate_bale_number` | Mark all involved cells |
| `domain_validation_error` | Global modal, data intact |
| Network/timeout/500 | Generic modal, allow retry |

---

## 7. Bale Stock

### 7.1 Objective

Provide aggregated visibility into bale stock and allow locating a specific bale by its business identity — without loading an exhaustive list.

### 7.2 Filters

| Filter | Control |
| --- | --- |
| Received from | `TextInput type="date"` |
| Received to | `TextInput type="date"` |
| Shipment number | `TextInput` |
| Status | Mantine `Select` |
| Provider | `TextInput` |
| Material type | `TextInput` |
| Dtex | `TextInput` (decimal) |

Behavior:

- Filters applied via explicit button (not on keystroke).
- Separate draft filters from applied filters.
- Show active filters as `Pill` or `Badge`.
- "Clear" resets to unfiltered summary.
- Validate `received_from <= received_to`.

### 7.3 HTTP control

- `AbortController` per query.
- Cancel previous request on new filter application.
- Ignore stale responses.
- Maintain previous data during refresh.
- Allow retry on failure.

### 7.4 Metrics

Six cards via Mantine `SimpleGrid`:

- Total bales
- In warehouse
- Delivered
- Total net weight
- In-warehouse net weight
- Delivered net weight

Responsive: 3 columns desktop, 2 tablet, 1 mobile. Zero is a valid result (not treated as error).

### 7.5 Individual bale lookup

Two required fields: shipment number + bale number. Search triggered by button.

States: initial → loading → found → not found → network error.

Detail shows: shipment, bale number, reception date, provider, material, dtex, gross weight, tare, net weight, status, delivery date (if delivered).

Labels:

| Backend | UI |
| --- | --- |
| `in_warehouse` | In Warehouse |
| `delivered` | Delivered |

---

## 8. Delivery to Production

### 8.1 Objective

Record a batch delivery of bales to Production using a spreadsheet-style grid. The operator reads bale identities from physical labels and enters them into the grid. A single POST submits the entire delivery session.

### 8.2 Layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Delivery to Production                                       │
├─────────────────────────────────────────────────────────────┤
│ Delivery date: [2026-07-28]                                  │
├─────────────────────────────────────────────────────────────┤
│ [Add rows] [Remove selected] [Clear]       5 filled          │
├─────────────────────────────────────────────────────────────┤
│ # | Shipment | Bale   | Result                               │
│ 1 | PART-001 | F-01   |                                      │
│ 2 | PART-001 | F-02   |                                      │
│ 3 | PART-002 | F-03   |                                      │
│ 4 |          |        |                                      │
│ 5 |          |        |                                      │
├─────────────────────────────────────────────────────────────┤
│ 3 bales to deliver                  [Deliver]                │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Grid row model

```typescript
interface DeliveryGridRow {
  rowId: string
  shipmentNumber: string
  baleNumber: string
  result: 'pending' | 'delivered' | 'already_delivered' | 'not_found' | 'error' | null
  resultMessage: string | null
}
```

### 8.4 Grid columns

| Column | Editable | Rule |
| --- | ---: | --- |
| # | No | Visual order |
| Shipment number | Yes | Frozen, required |
| Bale number | Yes | Required |
| Result | No | Filled after POST response |

### 8.5 Interaction

- Grid starts with 5 empty rows.
- Operator fills shipment + bale per row (reads from physical label).
- Paste from Excel supported: two columns (shipment | bale).
- Empty rows are ignored on submit.
- Local duplicate detection (same shipment+bale after normalization) marks both rows.
- No pre-resolution against backend — the operator does not need to verify before submitting.

### 8.6 Delivery date

- Required field above the grid.
- Business date (no time component, no UTC conversion).
- Applied to all bales in the request.
- Defaults to today's date.

### 8.7 Submission flow

1. Validate delivery date is present.
2. Collect non-empty rows.
3. Require at least one row.
4. Reject local duplicates (mark both rows, block submit).
5. Open confirmation modal: date, count, list of identities, irreversibility warning.
6. On confirm: block editing, POST `/deliver`.
7. On response: map per-bale results to the grid's Result column.

### 8.8 Result display

After the POST response, each row shows its per-bale result:

| Backend status | Grid display |
| --- | --- |
| `delivered` | ✓ Delivered |
| `already_delivered` | ✗ Already delivered |
| `not_found` | ✗ Not found |

Summary below the grid: "N delivered · M failed"

### 8.9 Post-delivery actions

- Rows with errors remain editable for correction and retry.
- Successfully delivered rows become read-only (or removable).
- "New delivery session" clears the grid.
- "Go to stock" navigates to the stock page.

### 8.10 Error handling

| Error level | Behavior |
| --- | --- |
| Request-level 422 (invalid date, duplicates, empty) | Modal with message, data preserved |
| Per-bale failures in 207 response | Mapped to Result column per row |
| Network/timeout | Generic modal, allow retry, data preserved |
| 500 | Generic modal, data preserved |

---

## 9. Decimal handling

Fields `dtex`, `grossWeightKg`, and `containerWeightKg` are maintained as strings throughout.

Rules:

- No `input type="number"`.
- No `parseFloat` for final calculations.
- No storing weights as JavaScript `number`.
- No automatic rounding or exponential notation.

Local calculations (net weight, totals) use a BigInt-based scaled integer utility:

1. Validate decimal format.
2. Normalize scale.
3. Operate with scaled integers via `BigInt`.
4. Format result as string.

Must support: addition, subtraction, comparison.

---

## 10. Shared grid components

Location: `frontend/src/common/grid/`

| Component | Responsibility |
| --- | --- |
| `DataGridThemeWrapper` | Apply Mantine tokens to react-data-grid |
| `TextCellEditor` | Compact text editor |
| `DecimalCellEditor` | String-based decimal editor |
| `CellErrorIndicator` | Accessible per-cell error |
| `RowStatusCell` | Validation or process status indicator |
| `GridToolbar` | Row actions (add, remove, clear) |

Shared components must not know Warehouse-specific concepts.

---

## 11. Feature architecture

```text
frontend/src/features/warehouse/bales/
├── api/
│   ├── baleApi.ts
│   ├── baleApi.types.ts
│   ├── baleApi.mappers.ts
│   └── baleApi.errors.ts
├── components/
│   ├── reception/
│   ├── stock/
│   └── delivery/
├── hooks/
│   ├── useBaleReception.ts
│   ├── useBaleStockSummary.ts
│   ├── useBaleDetail.ts
│   └── useBaleDelivery.ts
├── model/
│   ├── reception.types.ts
│   ├── stock.types.ts
│   ├── delivery.types.ts
│   ├── validation.ts
│   └── decimal.ts
├── pages/
│   ├── BaleReceptionPage.tsx
│   ├── BaleStockPage.tsx
│   └── BaleDeliveryPage.tsx
├── styles/
└── index.ts
```

Responsibilities:

- `pages/` — composition and layout
- `components/` — presentational
- `hooks/` — state management and HTTP lifecycle
- `api/` — transport, contracts, mappers
- `model/` — types, validation, pure calculations
- `styles/` — CSS Modules

Components must not call `fetch` directly.

---

## 12. HTTP client

Common HTTP utilities for the feature:

- Configurable base URL.
- JSON serialization/deserialization.
- `AbortSignal` support.
- Timeout via `AbortController`.
- Error normalization to typed discriminated union.
- No secrets in `VITE_*`.
- No payload logging in production.

Feature API:

```typescript
registerBatch(request, signal?)
getStockSummary(filters, signal?)
getBaleDetail(shipmentNumber, baleNumber, signal?)
deliverBales(request, signal?)
```

Mapping: UI uses `camelCase`, API uses `snake_case`. Explicit mappers in both directions. UI types are never reused as API DTOs.

---

## 13. Local state design

### 13.1 Reception

Separate: header, rows, selection, local errors, remote errors, snapshot, submit state, result.

### 13.2 Stock

Separate: filter draft, applied filters, metrics, query state, detail criteria, detail result.

### 13.3 Delivery

Separate: delivery date, rows, local duplicate errors, submit state, per-row results.

No global context for the feature. Each page manages its own state via hooks.

---

## 14. Accessibility

Target: WCAG 2.1 AA for primary flows.

- All actions keyboard-operable.
- Visible focus indicators.
- Modals with focus trap and return.
- "Go to first error" focuses the cell.
- Grids with `aria-label`.
- Selected rows with `aria-selected`.
- Editors with accessible labels.
- Errors linked via `aria-describedby`.
- Loading with `aria-busy`.
- Results with `aria-live`.
- Global errors with `role="alert"`.
- Not color-dependent.
- Minimum 4.5:1 text contrast, 3:1 for controls.

---

## 15. Responsive

### 15.1 Reception and Delivery

- Desktop/tablet priority.
- Controlled horizontal scroll on mobile.
- Do not convert rows to cards.
- Maintain frozen columns.
- Keep toolbar and primary action button accessible.

### 15.2 Stock

- Fully responsive.
- Filters: 1, 2, or 4 columns.
- Metrics: 1, 2, or 3 columns.
- Detail stacked on mobile.

---

## 16. Performance

Reception:

- Fluid editing with 100 rows.
- Memoized columns.
- Stable `rowKeyGetter`.
- Stable editors.
- Pure validators.
- Active virtualization.

Stock:

- No request per keystroke.
- Cancel previous requests.
- Maintain data during refresh.

Delivery:

- Fluid with up to 50 rows.
- Single POST (no per-row requests).
- Result mapping is synchronous after response.

---

## 17. Quality gates

Mandatory:

```bash
pnpm build
pnpm lint
```

Manual validation:

- Reception: 1 and 100 bales, paste 100 rows, keyboard navigation, duplicates, partial rows, 409/422/500, network failure, retry, light/dark.
- Stock: no filters, individual and combined filters, zero results, cancelled query, detail found and not found.
- Delivery: fill 15 rows manually, paste identities, local duplicates, submit, partial results (delivered + not_found + already_delivered), retry failed, light/dark.

---

## 18. Acceptance criteria

| ID | Criterion |
| --- | --- |
| AC-01 | Reception header contains only shipment number, date, and provider. |
| AC-02 | Reception grid supports up to 100 bales with keyboard and paste. |
| AC-03 | Only complete rows are serialized; partial rows block submission; empty rows are ignored. |
| AC-04 | Decimals are sent as strings; net weight is not part of the request. |
| AC-05 | Confirmation modal shown before registration; result modal shown after 201. |
| AC-06 | Cell-level errors shown in grid; global errors shown in modal. |
| AC-07 | User-entered data is preserved on failure. |
| AC-08 | Stock page shows six aggregated metrics and applies filters conjunctively. |
| AC-09 | Bale lookup requires shipment number and bale number; presents detail or 404. |
| AC-10 | Delivery grid allows filling shipment + bale per row with paste support. |
| AC-11 | Delivery requires a business date and at least one non-empty row. |
| AC-12 | Delivery submits a single POST batch and shows per-bale results. |
| AC-13 | Failed rows are correctable and retriable; successful rows become read-only. |
| AC-14 | Navigation uses dedicated routes (no placeholder pages). |
| AC-15 | Loading, empty, error, and success states are distinguishable and accessible. |
| AC-16 | Build and lint pass without errors. |
| AC-17 | Light and dark themes are consistent. |

---

## 19. Implementation sequence

1. **Foundation** — Feature structure, HTTP client, API types, error normalization, grid wrapper, editors, decimal utility.
2. **Reception** — Header, columns, paste, row management, validation, summary, confirmation, POST, error mapping.
3. **Stock** — Route, filters, hook with abort, metric cards, states.
4. **Bale detail** — Compound lookup form, detail presentation, 404 handling.
5. **Delivery** — Grid, paste, duplicate detection, date field, confirmation, POST, per-bale result mapping.
6. **Navigation and accessibility** — Lazy routes, sidebar, breadcrumbs, focus, ARIA, contrast.
7. **Hardening** — 100-row paste, real errors, slow network, light/dark, responsive, build/lint, backend integration.

---

## 20. Definition of done

The capability is considered done when:

- All three pages exist and function against real backend endpoints.
- Reception registers up to 100 bales with keyboard, paste, and validation.
- Errors are identified per cell; calculations preserve decimal precision.
- User data survives failures.
- Stock shows aggregated metrics without exhaustive listing.
- Bale detail uses business identity (shipment number + bale number).
- Delivery uses a grid for identity entry and submits a single batch POST.
- Per-bale delivery results are shown; failed rows are retriable.
- Navigation and messages are accessible.
- Light and dark modes are consistent.
- No libraries outside the approved stack are introduced.
- `pnpm build` and `pnpm lint` complete without errors.
- All four backend endpoints work in real integration.
