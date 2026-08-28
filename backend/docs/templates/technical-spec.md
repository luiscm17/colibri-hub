# Backend Capability Technical Specification

> Use this template for a durable, explanatory specification owned by one backend bounded context. Link the PRD that is authoritative for business rules; describe stable semantics and boundaries, not delivery history or a catalog of technical artifacts.

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

## Authorities

<!-- Link the governing PRD and other authoritative policy. Explain precedence when they differ. -->

## Architectural References

<!-- Required. Link these durable authorities; do not duplicate them. -->

- [Backend Architecture Overview](../architecture/overview.md)
- [Technology Baseline](../../../docs/architecture/technology-baseline.md)
- [API Conventions](../api/conventions.md)
- [Error Contract](../api/errors.md)
- [Migration Strategy](../database/migrations.md)
- [Testing Strategy](../testing/strategy.md)

<!-- These documents own framework and platform conventions, HTTP conventions, error envelopes, migration policy, and verification levels. This specification adds only capability-specific consequences. -->

## Responsibilities and Exclusions

<!-- Define the business responsibilities this context owns and the adjacent responsibilities it deliberately does not own. -->

## Dependency Direction

<!-- Explain which business policies remain independent and how dependencies point toward them. Identify meaningful boundary crossings. -->

## Semantic Operations and Outcomes

<!-- Describe the business operations, preconditions, invariant-preserving outcomes, and meaningful failures without copying transport payloads. -->

## Cross-Context Contracts

<!-- Describe semantic commitments exchanged with other contexts, including ownership, timing, and compatibility expectations. -->

## Authorization Integration

<!-- Reference Access Control as the authority. State when authorization is required and what business outcome follows a denial. -->

## Consistency, Transactions, Concurrency, and Failure Guarantees

<!-- State guarantees, boundaries, recovery behavior, and what callers may rely on when concurrent work or failures occur. -->

## Security and Observability

<!-- Describe security-relevant boundaries and the signals needed to understand outcomes without exposing protected information. -->

## Observable Verification

<!-- List behavior that can demonstrate the stated semantics, guarantees, and collaboration boundaries. -->

## Optional: Material Architectural Decisions

<!-- Include only decisions that materially affect domain ownership, dependency direction, or cross-context guarantees. -->

## Out of Scope

<!-- State adjacent responsibilities and future work this bounded context intentionally does not own. -->
