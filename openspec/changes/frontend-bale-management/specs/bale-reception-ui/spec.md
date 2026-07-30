# Bale Reception UI Specification

## Purpose

Enable Warehouse personnel to register one complete raw-material batch through an accessible, Spanish spreadsheet workflow.

## Requirements

### Requirement: Canonical reception access

The system MUST expose reception at `/warehouse/bales/reception` with Spanish user-visible copy, including `Guardar` and `Limpiar`, and MUST NOT expose `/warehouse/reception`. It MUST remain usable in light and dark themes and by keyboard and assistive technology.

#### Scenario: Operator opens reception

- GIVEN the operator navigates to the reception route
- WHEN the page renders in either color scheme
- THEN Spanish labels, visible focus, and non-color-only feedback are available

#### Scenario: Legacy route is requested

- GIVEN `/warehouse/reception` is requested
- WHEN routing resolves the path
- THEN the reception page is not served or redirected from that legacy route

### Requirement: Spreadsheet capture and decimal integrity

The system MUST support 1–100 non-empty bales for one batch, keyboard navigation, continuation rows, and paste beginning at the selected editable cell. It MUST retain dtex and weight values as immutable decimal strings, calculate net weight without direct entry or rounding, and reject an over-limit paste without partial insertion.

#### Scenario: Paste extends the grid

- GIVEN a selected editable cell and fewer than 100 non-empty rows
- WHEN the operator pastes compatible spreadsheet values
- THEN values populate from that cell, required rows continue, and calculated cells are not overwritten

#### Scenario: Paste exceeds capacity

- GIVEN the paste would create more than 100 non-empty bales
- WHEN the operator pastes the range
- THEN the entire paste is rejected and existing rows remain unchanged

### Requirement: Atomic reception feedback and preservation

The system MUST locally identify incomplete, invalid, or duplicate normalized bale rows and block submission until a valid header and at least one bale exist. On submission it MUST request confirmation, submit one atomic batch, and preserve the draft on any unavailable-backend, transport, validation, or conflict failure. Popups MUST be concise; indexed remote field errors MUST identify the matching header or grid cell. `Limpiar` MUST clear only page-local state and MUST NOT call the backend; the only persistent reception actions MUST be `Guardar` and `Limpiar`.

#### Scenario: Indexed failure is returned

- GIVEN a confirmed reception submission with an immutable row order
- WHEN the backend returns an indexed field error or a conflict
- THEN the affected field or cell is identified, a concise Spanish summary is announced, and all draft data remains editable

#### Scenario: Operator clears the page

- GIVEN a populated reception draft
- WHEN the operator confirms `Limpiar`
- THEN header, grid, and local errors reset without a backend request
