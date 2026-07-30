# Bale Stock UI Specification

## Purpose

Provide accessible, filtered stock visibility and composite-identity bale lookup without an exhaustive bale list.

## Requirements

### Requirement: Canonical stock access and presentation

The system MUST expose stock at `/warehouse/bales/stock` with Spanish user-visible copy. Metrics, filters, lookup results, loading, errors, and focus feedback MUST remain distinguishable in light and dark themes and accessible by keyboard and assistive technology.

#### Scenario: Operator opens stock

- GIVEN the operator navigates to the stock route
- WHEN the page renders in either color scheme
- THEN controls have Spanish labels and status feedback is not conveyed by color alone

#### Scenario: A request is loading

- GIVEN a stock request is pending
- WHEN the page updates its request state
- THEN the loading state is programmatically communicated without disabling unrelated navigation

### Requirement: Filtered summary and composite lookup

The system MUST apply only explicitly submitted optional filters as a conjunction and show six stock metrics for the applied result. It MUST validate date-range order before querying. A zero-valued response MUST be shown as valid stock data. Detail lookup MUST require both shipment number and bale number and present either the returned business detail or a distinct not-found state.

#### Scenario: Filters return no matches

- GIVEN valid applied filters with no matching bales
- WHEN the summary response contains zero metrics
- THEN all six zero values are shown as a successful result

#### Scenario: Composite lookup misses

- GIVEN both lookup identity fields are supplied
- WHEN the backend reports the composite identity as absent
- THEN a Spanish not-found state is shown without implying which identity part exists

### Requirement: Current-response and failure handling

The system MUST cancel superseded summary or detail requests, ignore stale responses, retain prior successful summary data while a replacement request is pending, and provide a concise Spanish retryable failure state when the backend is unavailable or fails.

#### Scenario: A newer filter request replaces an older one

- GIVEN a summary request is pending
- WHEN the operator applies different valid filters
- THEN the prior request is aborted or its response ignored, and only the newer result may update metrics

#### Scenario: Backend is unavailable

- GIVEN a summary or detail request cannot complete
- WHEN the failure is received
- THEN existing successful summary data remains visible where applicable and a retryable concise error is announced
