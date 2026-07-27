---
document_type: technical-spec
status: active
implementation: partial
scope: frontend/patterns
authority: explanatory
owner: frontend
last_reviewed: 2026-07-27
---

# Data Grid Pattern — react-data-grid

> Reusable patterns for editable grids using react-data-grid in the Colibri Hub frontend.
> Applicable to any domain that requires spreadsheet-like data entry (Warehouse, Spinning, Lots, Reports).

---

## 1. Library Overview

react-data-grid v7 is the standard grid component for tabular inline editing in Colibri Hub.

- Single dependency, zero external deps, tree-shakeable.
- Provides native copy-paste (Ctrl+C / Ctrl+V from/to Excel).
- Built-in keyboard navigation (Tab, Enter, Escape, Arrow keys).
- Summary rows for column aggregations.
- Column freezing for horizontal scroll scenarios.

---

## 2. Keyboard Navigation

react-data-grid exposes built-in keyboard interactions:

| Key | Behavior |
| --- | --- |
| Tab / Shift+Tab | Move to next/previous cell |
| Enter | Enter edit mode on focused cell |
| Escape | Cancel current cell edit |
| Arrow keys | Directional navigation between cells |
| Ctrl+C | Copy selected cell(s) |
| Ctrl+V | Paste clipboard content into grid |

These behaviors are native to react-data-grid and require no additional implementation.

---

## 3. Copy-Paste from External Sources

react-data-grid v7 supports clipboard copy-paste natively. Users can:

- Copy a range of cells from Excel or Google Sheets.
- Paste directly into the grid; values map column-by-column.
- Copy from the grid back to a spreadsheet.

No custom event handlers are required for basic copy-paste. For advanced transformations (e.g., parsing pasted values), intercept the `onPaste` event at the grid level.

---

## 4. Inline Cell Editors

Each editable column declares a `renderEditCell` renderer. Editors are Mantine components adapted to fit within a cell:

| Editor Type | Base Component | Notes |
| --- | --- | --- |
| Text editor | `<TextInput>` | No border, no label, cell-sized padding |
| Number editor | `<TextInput pattern="[0-9]*\\.?[0-9]*">` | String-based to preserve decimal precision; avoid `type="number"` |
| Select editor | `<Select>` | Dropdown populated from catalog data |

### 4.1 Editor Implementation Pattern

```typescript
import type { RenderEditCellProps } from 'react-data-grid'

function TextCellEditor<R>({ row, column, onRowChange, onClose }: RenderEditCellProps<R>) {
  return (
    <TextInput
      autoFocus
      value={row[column.key as keyof R] as string}
      onChange={(e) => onRowChange({ ...row, [column.key]: e.target.value })}
      onBlur={() => onClose(true)}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose(false)
        if (e.key === 'Enter') onClose(true)
      }}
      styles={{ input: { border: 'none', padding: '8px 12px' } }}
    />
  )
}
```

### 4.2 Decimal Precision Rule

For numeric fields that require exact decimal representation (weights, measurements):

- Store and edit as **strings** during the editing lifecycle.
- Never use `type="number"` on inputs — browsers round and reformat.
- Convert to numeric types only at the serialization boundary (payload construction).

---

## 5. Column Configuration

Columns are defined using the `Column<R>[]` type from react-data-grid:

```typescript
import type { Column } from 'react-data-grid'

const columns: Column<RowType>[] = [
  { key: 'fieldName', name: 'Display Label', editor: customEditor },
  { key: 'readOnlyField', name: 'Computed', editable: false },
]
```

### 5.1 Frozen Columns

For grids with many columns, freeze identifier columns so they remain visible during horizontal scroll:

```typescript
{ key: 'identifier', name: 'ID', frozen: true }
```

---

## 6. Row Management

### 6.1 Adding Rows

Insert new empty rows at the end of the dataset. Each row must have a stable local identifier (UUID or incremental ID) for React key reconciliation and error mapping.

### 6.2 Removing Rows

Allow removing selected rows. Ensure:

- Selection state is tracked (checkbox column or row click).
- Removal does not alter the relative order of remaining valid rows.
- A confirmation is shown when removing multiple rows.

### 6.3 Empty vs. Partial Rows

Distinguish between:

- **Empty row**: All editable fields are blank — ignored on submission.
- **Partial row**: Some fields filled, some missing — flagged as invalid, not discarded.
- **Valid row**: All required fields present and passing validation.

---

## 7. Row Validation

Validation runs at submission time (not on every keystroke) with optional inline feedback:

### 7.1 Validation Strategy

1. On "Save" action, iterate all rows.
2. Skip entirely empty rows.
3. For partial/valid rows, validate each required cell.
4. Collect all errors per row and per cell.
5. Focus the first invalid cell for user correction.

### 7.2 Visual Error Feedback

- Mark invalid cells with a highlight (border color or background).
- Show a brief error message per cell (tooltip or inline text).
- Provide a row-level status indicator summarizing the row state.
- Never use color alone — combine with icons or text for accessibility.

### 7.3 Duplicate Detection

For columns with uniqueness constraints (within the grid dataset):

- Compare all values in the constrained column.
- Mark ALL duplicate cells (not just the second occurrence).
- Report duplicates in the validation summary.

---

## 8. Summary Row

react-data-grid supports a `summaryRows` prop for aggregate displays at the grid footer:

```typescript
const summaryRows = [
  {
    id: 'summary',
    totalRows: validRows.length,
    totalWeight: validRows.reduce((sum, r) => sum + parseFloat(r.weight || '0'), 0),
  },
]
```

Use summary rows for:

- Row counts (total, valid, invalid).
- Numeric aggregates (sums, averages).
- The summary must remain visible when scrolling through many rows.

---

## 9. Theme Integration (RDGThemeWrapper)

A reusable wrapper component in `common/components/` maps Mantine design tokens to react-data-grid CSS variables. This ensures the grid respects the application's light/dark mode.

| RDG Variable | Mantine Token (Light) | Mantine Token (Dark) |
| --- | --- | --- |
| `--rdg-color` | `--mantine-color-text` | `--mantine-color-text` |
| `--rdg-background-color` | `--mantine-color-body` | `--mantine-color-body` |
| `--rdg-header-background-color` | `--mantine-color-gray-0` | `--mantine-color-dark-7` |
| `--rdg-row-hover-background-color` | `#E5FCFA` (brand-50) | `rgba(16, 89, 85, 0.4)` |
| `--rdg-selection-color` | `#14E3D9` (brand-400) | `#14E3D9` (brand-400) |
| `--rdg-border-color` | `--mantine-color-gray-3` | `--mantine-color-dark-4` |
| `--rdg-font-size` | `14px` | `14px` |
| `--rdg-cell-padding` | `8px 12px` | `8px 12px` |

Place `RDGThemeWrapper` in `common/components/` so any feature using react-data-grid inherits consistent theming.

---

## 10. Submission Pattern

For grids that submit data to the backend as a batch:

### 10.1 Snapshot Strategy

1. On submit, create an immutable snapshot of the current grid state.
2. Block further edits during the request (disable grid interaction).
3. Use the snapshot to map backend error responses (e.g., `bales.2.field`) back to the original row by index.

### 10.2 Error Mapping from Backend

When the backend returns field-level errors referencing array indices:

```typescript
// Backend error: { field: "items.2.weight", message: "must be positive" }
// Map index 2 → rowId from snapshot → highlight cell in grid
```

### 10.3 Data Preservation

- Never clear the grid on error — user data must survive failed submissions.
- Clear only on explicit user action after a successful response.
- Provide retry capability without re-entering data.

---

## 11. Accessibility

- Maintain full keyboard navigation (Tab, Enter, Arrows).
- Ensure visible focus indicators on active cells.
- Provide accessible labels for all editor inputs.
- Communicate errors and states through text/icons, not color alone.
- Use `aria-label` or `aria-describedby` for cell editors.

---

## 12. Reusable Component Placement

| Component | Location | Reuse Scope |
| --- | --- | --- |
| RDGThemeWrapper | `common/components/` | All grids in the application |
| TextCellEditor | `common/components/editors/` | Any text-editable grid |
| NumberCellEditor | `common/components/editors/` | Any numeric-editable grid |
| SelectCellEditor | `common/components/editors/` | Any dropdown-editable grid |
| Feature-specific columns | `features/<domain>/components/` | Domain-specific only |
