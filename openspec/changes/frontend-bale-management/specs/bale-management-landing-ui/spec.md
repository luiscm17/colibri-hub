# Bale Management Landing UI Specification

## Purpose

Provide a static, accessible Spanish entry point for Bale Management workflows.

## Requirements

### Requirement: Accessible workflow navigation

The system MUST render `/warehouse/bales` as a Spanish, light/dark-compatible module landing page with exactly three keyboard- and assistive-technology-accessible navigation cards: Reception, Stock, and Delivery. Each card MUST reach, respectively, `/warehouse/bales/reception`, `/warehouse/bales/stock`, or `/warehouse/bales/delivery`.

#### Scenario: Operator chooses a workflow

- GIVEN the operator opens `/warehouse/bales`
- WHEN the landing page renders
- THEN exactly the three Spanish workflow cards are available and each reaches its explicit child route

#### Scenario: Keyboard or assistive-technology navigation

- GIVEN the landing page is rendered in either color scheme
- WHEN an operator navigates cards by keyboard or assistive technology
- THEN each card has a discernible Spanish name, visible focus, and non-color-only feedback

### Requirement: Static module boundary

The system MUST NOT make backend requests or display metrics or operational data on the landing page. It MUST NOT integrate authorization or vary card visibility by authorization state.

#### Scenario: Landing page loads without data access

- GIVEN the operator opens `/warehouse/bales`
- WHEN the page completes its initial render
- THEN no backend request is made and no metric or operational-data content is shown

#### Scenario: Authorization is unavailable

- GIVEN no authorization integration is configured
- WHEN the landing page renders
- THEN the same three workflow cards remain available without authorization-dependent behavior
