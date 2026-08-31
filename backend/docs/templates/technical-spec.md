# Backend Capability Technical Specification

> Use this template for a durable specification of one backend bounded context. It describes public behavior, ownership, and observable guarantees. It does not record delivery history, current implementation state, source structure, storage design, or migration details.

```yaml
---
document_type: technical-spec
status: <draft|active|superseded|archived>
scope: <bounded-context/capability>
authority: explanatory
owner: backend
last_reviewed: <YYYY-MM-DD>
replaces: <path|null>
---
```

## Purpose and Bounded-Context Boundary

<!-- State the business purpose, owned language and invariants, and what belongs outside this bounded context. -->

## Authorities and Precedence

<!-- Link the governing PRD and shared policy authorities. State which authority prevails for business rules, authorization, API conventions, and errors. -->

## Architectural References

<!-- Link durable shared authorities rather than copying their rules. -->

- [Backend Architecture Overview](../architecture/overview.md)
- [Technology Baseline](../../../docs/architecture/technology-baseline.md)
- [API Conventions](../api/conventions.md)
- [Error Contract](../api/errors.md)
- [Testing Strategy](../testing/strategy.md)

## Responsibilities and Exclusions

<!-- Define what this context owns, consumes, and deliberately does not own. -->

## Semantic Operations and Outcomes

<!-- Describe each business operation, its preconditions, authoritative outcomes, and meaningful failures. Do not repeat the PRD's business-rule rationale. -->

## Public API Contract

<!-- Document all public routes, methods, request and response schemas, field names, types, units, validation, calculated values, pagination, and error semantics required by consumers. -->

### Route Catalog

<!-- Use a table with operation, method, path, authorization, and purpose. -->

### Request and Response Schemas

<!-- Use JSON examples and/or field tables. Mark intentionally incomplete portions as "Contract detail pending" without implying an implementation state. -->

### Contractual Errors

<!-- Link the shared error envelope and state capability-specific observable error outcomes. -->

## Cross-Context Contracts

<!-- Describe ownership, read-only reference data, timing, compatibility expectations, and consumer references. -->

## Authorization Integration

<!-- Reference Access Control as the authority. State server-derived authorization requirements and denial outcomes without redefining its policy. -->

## Consistency, Concurrency, and Correction Guarantees

<!-- State atomicity, concurrency, correction evidence, recovery behavior, and caller-visible guarantees. Keep unresolved policy deliberately unresolved. -->

## Security and Observability

<!-- Describe protected boundaries, data-disclosure limits, and outcome signals without exposing internal mechanisms. -->

## Observable Verification

<!-- List externally demonstrable behaviors that prove the contract and collaboration boundaries. -->

## Out of Scope

<!-- State adjacent responsibilities and intentionally deferred work. -->
