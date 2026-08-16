---
document_type: pattern
status: active
scope: frontend/patterns
authority: explanatory
owner: frontend
---

# Editable Batch Grid

An editable batch grid supports efficient entry and correction of many records
while preserving row identity, user input, and actionable outcomes. This pattern
defines observable behavior, not a component library or source-code structure.

Adoption requires equivalent batch-entry and recovery needs; superficial tabular
similarity is not sufficient.

## 1. Problem

Operators need spreadsheet-like throughput without losing the safeguards of an
application form. Editing, pasting, validation, submission, and partial outcomes
must behave as one coherent interaction rather than as unrelated cells.

## 2. Applicability

Use this pattern when:

- users create or amend multiple structurally similar records in one task;
- keyboard continuity and bulk paste materially improve throughput;
- validation must identify row- and field-specific corrections; and
- submission may return outcomes for individual rows.

Do not use it for read-only tabular comparison, heterogeneous records, isolated
single-record forms, or workflows where each record requires substantial
independent context or confirmation.

## 3. Forces

- High entry speed must coexist with explicit validation and understandable
  feedback.
- Local row identity must survive sorting, editing, retries, and server response
  mapping.
- Virtualization or large datasets must not break focus or accessible context.
- Bulk operations must not hide which values changed or discard valid work.
- Backend policy remains authoritative even when the grid provides early local
  feedback.

## 4. Observable Contract

### 4.1 Keyboard And Editing

- A keyboard user can reach the grid, understand the active cell, enter and exit
  edit mode, move between relevant cells, and reach actions outside the grid.
- Navigation and editing keystrokes are predictable and do not trap focus.
- Committing an edit preserves the entered value and advances focus only when
  that movement is expected and announced by context.
- Cancelling an in-progress edit restores the last committed value.
- Read-only, disabled, and editable cells are distinguishable without relying on
  color alone.

### 4.2 Paste

- Pasted rectangular data maps from the active origin across eligible rows and
  columns in a deterministic order.
- The user can review affected values before submission.
- Unsupported shape, overflow, parsing, or read-only destinations produce an
  actionable outcome rather than silent truncation or corruption.
- A paste is handled as one user operation for validation and recovery; valid
  unaffected data is preserved when part of it fails.

### 4.3 Validation

- Empty, incomplete, valid, and invalid rows remain distinguishable according to
  the adopting feature's rules.
- Validation identifies every relevant row and field, provides a human-readable
  reason, and exposes an efficient path to correction.
- When submission is blocked, focus moves to the first actionable error while a
  summary makes the full error set discoverable.
- Duplicate or cross-row constraints identify all involved rows, not only the
  last value entered.
- Backend validation outcomes map back to the submitted row identity and field
  without depending on the grid's current visual order.

### 4.4 Focus

- Focus remains visible and stable through edits, validation, scrolling, row
  insertion or removal, and asynchronous outcomes.
- If the focused row or cell disappears, focus moves to a logical surviving
  target and the change is understandable.
- Programmatic movement never depends on an element being currently visible in a
  virtualized viewport.

### 4.5 Preservation And Recovery

- Recoverable validation, authorization, concurrency, network, and service
  failures preserve safe user-entered data.
- Retrying does not require re-entry of unaffected values.
- Data is cleared only by an explicit user action or a feature-defined successful
  outcome that has been clearly communicated.
- Destructive bulk actions identify their scope and provide an appropriate
  confirmation or recovery path.

### 4.6 Submission And Partial Outcomes

- Submission uses an immutable snapshot that binds each payload item to stable
  local row identity.
- Editing that would invalidate response mapping is prevented or isolated while
  a submission is in flight.
- Duplicate submission is prevented while the same snapshot is pending.
- Success, rejection, and indeterminate outcomes are distinguishable per row
  when the backend contract supports partial results.
- Successful rows follow the feature-defined post-submit state; failed or
  unconfirmed rows retain their data and actionable feedback.
- A summary communicates the batch outcome without replacing row-level detail.

### 4.7 Accessibility

- The interaction exposes grid, row, column, cell, editability, selection, and
  validation semantics appropriate to its behavior.
- Assistive technology receives row and column context even when content is
  virtualized or visually reordered.
- Instructions explain non-standard keyboard and paste behavior before it is
  needed.
- Status and validation changes are announced without excessive repetition.
- Focus, selection, validation, and outcome states remain perceivable without
  color alone.

The [Accessibility Guidelines](../accessibility.md) remain authoritative for
transversal requirements. The [Testing Strategy](../testing/strategy.md) owns
validation levels and automation boundaries.

## 5. Allowed Variations

Adopting features may vary:

- editable fields, row shape, defaults, and catalog-backed choices;
- whether rows can be inserted, removed, reordered, selected, or copied;
- validation timing, provided feedback is not disruptive and submission checks
  remain authoritative;
- single-request, chunked, or per-row transport, subject to the same identity and
  preservation contract;
- summary content, aggregation, frozen context, and responsive presentation; and
- post-success row retention, locking, replacement, or removal.

Variations must preserve the observable contract or explicitly document why a
requirement does not apply.

## 6. Feature Obligations

Each adopting feature specification defines:

- why batch editing is appropriate for that workflow;
- row identity, fields, defaults, and editability;
- local completeness, format, duplicate, and cross-row rules;
- paste shape, parsing, overflow, and confirmation behavior;
- exact payload and mapping to backend validation or partial outcomes;
- submission concurrency and retry behavior;
- post-success and partial-success treatment;
- feature-specific accessible names, instructions, and announcements; and
- scenario coverage for its material risks and chosen variations.
