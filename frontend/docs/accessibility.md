---
document_type: technical-spec
status: draft
implementation: not-started
scope: frontend/accessibility
authority: explanatory
owner: frontend
last_reviewed: 2026-07-27
---

# Frontend Accessibility Guidelines

Accessibility requirements and implementation guidelines for the Colibri Hub frontend application. Target conformance: **WCAG 2.1 Level AA**.

> **Note:** Full WCAG validation requires manual testing with assistive technologies (screen readers, switch devices) and expert accessibility review. Automated checks catch approximately 30–50% of potential issues.

---

## 1. Keyboard Navigation

All interactive elements must be operable via keyboard alone.

- Every focusable element must have a visible focus indicator
- Tab order must follow a logical reading sequence (no positive `tabIndex` values)
- Modal dialogs must trap focus while open and return focus on close
- Custom components (dropdowns, date pickers) must support standard keyboard patterns:
  - `Enter`/`Space` to activate
  - `Escape` to dismiss
  - Arrow keys for option navigation where applicable
- Skip-to-content link must be present as the first focusable element

### Data Grid Specifics

The editable data grid (react-data-grid) requires additional keyboard support:

- Arrow keys navigate between cells
- `Enter` activates cell editing
- `Escape` cancels in-progress edits
- `Tab` moves to the next editable cell within a row

---

## 2. Color Contrast

Mantine's theme system provides baseline contrast compliance, but custom overrides must be verified.

- Text on background must meet a minimum contrast ratio of **4.5:1** (normal text) or **3:1** (large text)
- Interactive element boundaries must meet **3:1** against adjacent colors
- Status indicators (success, error, warning) must not rely solely on color — use icons or text labels as secondary indicators
- Custom theme tokens extending Mantine defaults must be checked against WCAG contrast requirements

---

## 3. ARIA Labeling

### General Requirements

- Every form input must have an associated `<label>` element or `aria-label`/`aria-labelledby` attribute
- Icon-only buttons must include `aria-label` describing the action
- Loading states must use `aria-busy="true"` on the affected region
- Dynamic content updates must use `aria-live` regions (polite for non-urgent, assertive for errors)

### Data Grid ARIA

The data grid component requires explicit ARIA attributes because its structure diverges from native HTML tables:

- Grid container: `role="grid"` with `aria-label` describing the dataset
- Row headers: `role="rowheader"` on identifying cells (e.g., bale number)
- Column headers: `role="columnheader"` with sort state via `aria-sort`
- Editable cells: `aria-readonly="false"` when in edit mode
- Selection state: `aria-selected` on selected rows
- Row count: `aria-rowcount` reflecting total rows (including off-screen for virtual scroll)

### Notifications

- Toast notifications (Mantine notifications) should use `role="status"` for info/success and `role="alert"` for errors
- Notification content must be concise and actionable

---

## 4. Screen Reader Considerations

- Page titles must update on route changes (reflect current view)
- Headings must follow a logical hierarchy (`h1` → `h2` → `h3`, no skipped levels)
- Decorative images use `alt=""` (empty alt); informative images use descriptive alt text
- Tables and grids must expose row/column context to assistive technology
- Form validation errors must be programmatically associated with the invalid field via `aria-describedby`
- Route transitions should announce the new page context (e.g., via a visually hidden live region)

---

## 5. Implementation Priorities

| Priority | Area | Rationale |
| --- | --- | --- |
| High | Keyboard navigation in data grid | Core workflow; power users rely on keyboard |
| High | Form validation error association | Blocks task completion for screen reader users |
| Medium | Color contrast verification | Mantine provides decent defaults; custom tokens need audit |
| Medium | ARIA on notification toasts | Affects real-time feedback for non-sighted users |
| Low | Skip-to-content link | Important for navigation-heavy pages; less critical for single-view app |

---

## 6. Testing Approach

- Automated: axe-core integration in component tests catches structural violations
- Manual: periodic screen reader walkthroughs (VoiceOver on macOS, NVDA on Windows)
- Review: accessibility audit before major feature releases

See [Testing Strategy](testing/strategy.md) for tooling details.
