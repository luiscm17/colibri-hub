# Frontend Yarn Spinning Specification

## Purpose

Provide accessible Yarn Spinning capture, review, correction, and reporting workflows. The frontend MUST preserve server authority for outcomes, calculations, persistence, and authorization.

## Requirements

### Requirement: Section Production Discharge Grids

The system MUST compose applicable section production as repeatable spreadsheet-style Production Discharge grids, not a generic form. Each row SHALL represent one distinct discharge event, including repeated machine-and-yarn-count discharges. Grids MUST support keyboard entry, appropriate paste, inline validation, and visible pending, invalid, complete, and acknowledged-no-production row states. In Preparation, Production Discharge MUST apply only to FIN machines.

#### Scenario: Capture repeated discharges
- GIVEN an applicable section grid is open
- WHEN a user enters two discharges with the same machine and yarn count
- THEN both rows remain separate events with their own validation state

#### Scenario: Paste invalid production data
- GIVEN a user pastes values into production rows
- WHEN a pasted value is incomplete or malformed
- THEN the affected row shows inline validation without confirming an outcome

### Requirement: Applicable Progress Summary Grid

The system MUST provide one distinct unique per-machine-and-yarn-count Progress summary grid only for Preparation PSJ, Ring Spinning, and Twisting. It MUST NOT expose Progress for Bobbin Winding or Skeining, calculate or aggregate Progress locally, or treat Progress as a discharge-event grid. The grid SHALL show only server-derived continuity and editable predecessor suggestions.

The frontend-complete boundary is limited to rendering the fixed gateway roster for the applicable sections. The backend remains authoritative for canonical machine × shift × business-date × yarn-count identity, predecessor continuity, stale-response handling, discharge reconciliation, tolerance decisions, and persistence; no frontend state may claim those outcomes.

#### Scenario: Render applicable Progress
- GIVEN a user opens Ring Spinning
- WHEN the section workspace renders
- THEN one Progress summary grid is available beside applicable production capture

#### Scenario: Change Progress identity
- GIVEN a continuity request is pending
- WHEN the machine or yarn count changes
- THEN an obsolete response MUST NOT replace the current grid context

### Requirement: Skeining Production Boundary

The system MUST provide Skeining as a separate Yarn-Spinning production grid. It MUST NOT expose Progress or Lot Processing behavior.

#### Scenario: Open Skeining
- GIVEN a user opens the Skeining workspace
- WHEN its capture surface renders
- THEN it shows only Skeining production and no Progress or Lot Processing controls

### Requirement: Independent Waste Grid

The system MUST provide Waste as an independent editable grid for real weighed waste by machine group and shift. It MUST NOT calculate waste or classify theoretical, accumulated, or reprocessing values as waste.

#### Scenario: Edit Waste independently
- GIVEN a section capture is in progress
- WHEN a user enters Waste rows
- THEN those rows remain independent from production and Progress capture

### Requirement: Profile-Driven Process Quality

The system MUST provide independent Process Quality configuration and capture. A Sample profile SHALL render its configured ordered 10–15 measurements in a React Data Grid with units, validation, readonly results, and tolerance status from the server contract. Other Quality methods MUST remain profile-driven and MUST NOT be represented as grids unless their profile requires it.

#### Scenario: Capture a Sample profile
- GIVEN an authorized Sample profile provides 10–15 measurements
- WHEN Quality capture renders
- THEN the measurements appear in their supplied order in a React Data Grid

#### Scenario: Open unavailable Quality
- GIVEN the profile integration is unavailable
- WHEN a user enters Quality capture
- THEN the interface shows unavailability without inventing fields or results

### Requirement: Server-Confirmed and Recoverable States

The system MUST show explicit unavailable-integration states for unavailable server-dependent reads and submits, preserving drafts where recoverable. It MUST NOT fabricate successful records, continuity, calculations, metrics, or authorization outcomes. Dashboards and record reads SHALL retain filters and distinguish loading, empty, populated, stale, failure, and unavailable states; correction conflicts MUST retain local work and require a current-record read before retry.

Frontend evidence for an unavailable submit is limited to retaining the local draft and displaying no success state. It does not prove submission, record creation, validation acceptance, authorization, or any backend outcome.

#### Scenario: Submit while integration is unavailable
- GIVEN a user has a valid local capture draft
- WHEN its submit integration is unavailable
- THEN the draft remains available and no success is displayed

#### Scenario: Render empty reporting
- GIVEN a record read returns no records
- WHEN the result is displayed
- THEN it shows an empty state and not a zero metric

### Requirement: Accessible Responsive Operation

The system MUST make grid editing, validation, status, unavailable, and recovery states keyboard-operable, visibly focused, and programmatically announced. It SHALL preserve essential context and reachable grid controls through controlled overflow on constrained viewports.

#### Scenario: Operate a narrow grid by keyboard
- GIVEN a keyboard user views a constrained workspace
- WHEN capture columns overflow
- THEN inputs, validation, status, and recovery controls remain reachable
