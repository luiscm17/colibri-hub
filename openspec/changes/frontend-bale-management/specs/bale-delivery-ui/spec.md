# Bale Delivery UI Specification

## Purpose

Enable Warehouse personnel to record whole-bale deliveries through a resilient Spanish spreadsheet workflow.

## Requirements

### Requirement: Canonical delivery entry

The system MUST expose delivery at `/warehouse/bales/delivery` with Spanish user-visible copy and an accessible, light/dark-compatible spreadsheet grid. It MUST accept a business delivery date and 1–50 non-empty composite identities, support keyboard navigation, continuation rows, and paste from the selected editable cell.

#### Scenario: Operator enters delivery identities

- GIVEN the delivery page has an editable selected cell
- WHEN the operator types or pastes shipment and bale values
- THEN rows continue as needed and the grid remains keyboard-operable

#### Scenario: Too many identities are pasted

- GIVEN a paste would exceed 50 non-empty identities
- WHEN the operator applies the paste
- THEN the paste is rejected without changing the existing draft

### Requirement: Delivery validation and protected submission

The system MUST require a date, at least one complete identity, and unique normalized composite identities before submission. It MUST show an irreversible-delivery confirmation and submit all eligible rows in one request. Request serialization MUST include no frontend-local `rowId`. Empty rows MUST be ignored; incomplete or duplicate rows MUST be identified and block submission.

#### Scenario: Duplicate identity is entered

- GIVEN two non-empty rows normalize to the same shipment and bale identity
- WHEN the operator attempts delivery
- THEN both rows are identified and no request is sent

#### Scenario: Valid delivery is confirmed

- GIVEN valid rows and a business date
- WHEN the operator confirms the irreversible action
- THEN one delivery request contains the entered normalized identities and shared date without frontend-local `rowId` values

### Requirement: Per-row outcomes, retry, and draft preservation

The system MUST retain and visibly lock each successful delivery row with an accessible success indication. Server delivery results MUST contain no frontend-local `rowId`; the system MUST correlate each result by its normalized `shipment_number` + `bale_number` composite business identity to the matching local row and preserve that local row's `rowId` when updating it. Rows reported as not found or already delivered MUST remain visible, editable, and retryable. Request-level validation, unavailable-backend, transport, and server failures MUST preserve every draft row and show a concise Spanish popup summary. A page clear MUST reset only local state and MUST NOT call the backend.

#### Scenario: Mixed delivery results arrive

- GIVEN a submitted delivery contains multiple identities
- WHEN the response reports successes and failures
- THEN every result without a frontend-local `rowId` is correlated by normalized `shipment_number` + `bale_number` to its local row, each updated row retains its local `rowId`, successful rows are locked, failed rows stay editable, and a concise delivered/failed summary is announced

#### Scenario: Delivery request fails

- GIVEN a populated delivery draft
- WHEN the backend is unavailable or returns a request-level failure
- THEN no row is discarded, the failure is retryable, and the operator may correct rows
