---
document_type: adr
status: active
implementation: not-started
scope: domain/operations
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# ADR-002: Separate Bounded Contexts for Yarn Spinning and Lot Processing

## Status

Active

## Context

The Operations Unit in Colibri Hub encompasses two distinct production processes:

1. **Yarn Spinning** — transforms raw material (fiber bales) into yarn through carding, drawing, roving, and spinning stages. Identity is a production run or bobbin lot.
2. **Lot Processing** — tracks downstream processing of yarn into finished products (dyeing, winding, packaging). Identity is a processing batch with quality checkpoints.

Both operate on materials that originate in the Warehouse context, but they have fundamentally different:

- **Identities**: spinning runs vs. processing batches
- **Timelines**: spinning is continuous-flow; lot processing is batch-discrete
- **Record semantics**: spinning tracks machine parameters and fiber blend; lot processing tracks treatment steps and quality grades

The question is whether to model these as one "Operations" bounded context or as two separate contexts.

## Decision

We will model Yarn Spinning and Lot Processing as separate bounded contexts, each with its own domain model, aggregate roots, and repository interfaces.

- **Yarn Spinning** context owns: production runs, machine allocations, fiber blends, bobbin output
- **Lot Processing** context owns: processing batches, treatment steps, quality inspections, packaging records

Communication between them uses domain events or explicit integration patterns, not shared aggregates.

## Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
|-------------|------|------|-----------------|
| Single "Operations" bounded context | Simpler initial model, fewer integration points | Conflates two distinct lifecycles, forces shared aggregate design, couples deployment and evolution | Different identities, timelines, and record semantics mean a single model would require constant disambiguation. The tactical cost of separation is lower than the ongoing complexity of a unified model that doesn't reflect reality. |

## Consequences

**Positive:**

- Each context evolves independently — spinning can change without affecting lot processing
- Domain language is unambiguous within each context (no "batch" meaning two different things)
- Clearer ownership boundaries for teams or modules
- Easier to test in isolation

**Negative:**

- Requires explicit integration between contexts (events, anti-corruption layer)
- Initial setup has more boilerplate (two sets of ports, adapters, repositories)

**Neutral:**

- Both contexts still depend on Warehouse for raw material identity (upstream dependency)

## References

- [Context map](../context-map.md)
- [Domain — ubiquitous language](../../domain/ubiquitous-language.md)
