# Frontend Yarn Spinning Specification

## Purpose

Provide accessible, responsive Yarn Spinning workflows while preserving the planned backend contract as a future integration. The frontend MUST NOT implement business calculations, persistence, API behavior, or access-control policy.

## Requirements

### Requirement: Section Workspaces

The system MUST provide five route-composed section workspaces, including Skeining. Each workspace SHALL preserve visible business-date, shift, and capture context, separate Skeining from Lot Processing, and present production and applicable Progress as one section-close submission intent. Until its real API exists, every server-dependent read or submit MUST show an explicit unavailable-integration state and MUST NOT fabricate an outcome.

#### Scenario: Open a section workspace
- GIVEN a user reaches a Yarn Spinning section destination
- WHEN the workspace renders
- THEN it shows its capture context and unavailable-integration state
- AND it does not show a locally confirmed record or calculation

#### Scenario: Identify Skeining
- GIVEN a user opens the Skeining workspace
- WHEN its capture experience is displayed
- THEN it identifies Skeining as a Yarn Spinning workflow
- AND it does not expose Lot Processing behavior

### Requirement: Progress Continuity Presentation

The system MUST reserve a Progress continuity presentation for the planned backend response. It SHALL identify predecessor-derived input, editable predecessor suggestions, no-predecessor zero, stale configuration, and read failure without deriving continuity locally.

#### Scenario: Display unavailable continuity
- GIVEN a user begins applicable Progress capture
- WHEN continuity integration is unavailable
- THEN the draft remains available
- AND the interface explains that continuity cannot be retrieved

#### Scenario: Prevent stale continuity display
- GIVEN the Progress identity changes during a pending continuity read
- WHEN an older response would arrive
- THEN it MUST NOT replace the newer identity context

### Requirement: Process Quality Experiences

The system MUST provide independent Process Quality profile configuration and capture surfaces. It SHALL present profile version, configured fields or ordered samples, units, readonly results, and tolerance status only from the future server contract; it MUST NOT provide arbitrary formulas or locally confirm results.

#### Scenario: Open Quality capture
- GIVEN a user enters Process Quality capture
- WHEN the profile API is unavailable
- THEN the interface shows an explicit unavailable-integration state
- AND no profile fields or result values are invented

#### Scenario: Preserve a Quality draft
- GIVEN a user has entered raw Quality values
- WHEN a recoverable integration failure occurs
- THEN entered values and profile context remain available

### Requirement: Waste Experience

The system MUST provide an independent Waste capture and review experience for real weighed waste by machine group and shift. It MUST NOT classify theoretical, accumulated, or reprocessing values as waste, calculate waste, or confirm a record without the backend.

#### Scenario: Open Waste capture
- GIVEN a user opens Waste capture
- WHEN its integration is unavailable
- THEN the interface explains the unavailable state
- AND it does not display a fabricated waste result

### Requirement: Reporting and Record Reads

The system MUST provide section and consolidated dashboard and current-record read surfaces with retained reporting filters. It SHALL distinguish loading, empty, populated, stale, failure, and unavailable integration states, and MUST show only future backend-returned metric values, units, and availability.

#### Scenario: View a dashboard without an API
- GIVEN a user selects reporting context
- WHEN the dashboard API is unavailable
- THEN selected filters remain visible
- AND the dashboard states that current results are unavailable

#### Scenario: Read records with no results
- GIVEN a record-read response contains no records
- WHEN the result is rendered
- THEN the interface shows an empty state
- AND it does not present absence as zero

### Requirement: Correction, History, and Recovery

The system MUST provide correction and history review surfaces that preserve local drafts through recoverable failures and conflicts. A conflict SHALL retain local work and require a future current-record read before any retry; the UI MUST NOT overwrite information silently or make downstream changes automatically.

#### Scenario: Recover a correction conflict
- GIVEN a correction draft encounters a conflict
- WHEN the conflict state is displayed
- THEN the draft remains available with recovery guidance
- AND no retry or downstream change occurs automatically

#### Scenario: View history without an API
- GIVEN a user opens record history
- WHEN the history integration is unavailable
- THEN the interface shows an explicit unavailable-integration state

### Requirement: Accessible Responsive Interaction

The system MUST make draft, validation, status, unavailable, and recovery states keyboard-operable and programmatically announced. It SHALL retain essential context, inputs, completion status, and review actions on constrained viewports through reachable controls and controlled overflow.

#### Scenario: Operate an unavailable state by keyboard
- GIVEN a keyboard user reaches an unavailable server-dependent action
- WHEN focus moves to its state and recovery control
- THEN focus is visible and status is announced

#### Scenario: Use a constrained viewport
- GIVEN a section workspace is displayed on a small viewport
- WHEN capture or review content overflows
- THEN essential context and controls remain reachable
