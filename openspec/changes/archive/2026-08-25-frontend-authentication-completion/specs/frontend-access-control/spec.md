# Delta for Frontend Access Control

## ADDED Requirements

### Requirement: Authentication Semantic Consumption
Access MUST consume Authentication conditions without owning sessions or credentials. It SHALL not request while unresolved, ended, replacement-required, or unavailable; it MAY bootstrap only after current `authenticated`. Access MUST resolve return intent without duplicate bootstrap or navigation.

#### Scenario: Eligible handoff
- GIVEN current `load_access` handoff
- WHEN Access initializes
- THEN it bootstraps once and resolves a permitted destination

#### Scenario: Ineligible transition
- GIVEN Authentication becomes unavailable or replacement-required
- WHEN Access receives the condition
- THEN it clears prior Access and makes no bootstrap request
