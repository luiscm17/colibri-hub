---
document_type: adr
status: active
implementation: implemented
scope: warehouse/bales
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# ADR-005: Reception as Application Action, Not Domain Aggregate

## Status

Active

## Context

When raw material bales arrive at the warehouse, the system records a "reception" event that captures the shipment, supplier, transport details, and the individual bales received.

There are two modeling approaches:

1. **Reception as a domain aggregate** — an entity with its own lifecycle, identity, state transitions, and invariants
2. **Reception as an application action** — a use case that creates other domain entities (RawMaterialBatch + Bale aggregates) without being an entity itself

The key observation is that a reception, once recorded, has no lifecycle of its own. It does not transition states, it is not queried independently, and it has no invariants that evolve over time. It is a one-time creation event.

## Decision

Reception is modeled as an application-layer action (use case), not as a domain aggregate.

The reception use case:

1. Validates input (shipment number, supplier, bales)
2. Creates a `RawMaterialBatch` aggregate (the shipment record)
3. Creates `Bale` aggregates associated with the batch
4. Persists both in a single transaction
5. Returns the batch identifier

There is no `Reception` entity, no `ReceptionRepository`, and no reception lifecycle. The `RawMaterialBatch` and its `Bale` children are the domain artifacts that persist and evolve.

## Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
|-------------|------|------|-----------------|
| Reception as domain aggregate | Explicit modeling of the reception event, could support reception-level queries and state | Adds an entity with no lifecycle (never transitions, never updates after creation), introduces a repository and identity for something that is conceptually a command, over-engineers a one-shot action | Reception has no post-creation behavior. Making it an aggregate means maintaining an entity that is created once and never touched again. The batch and bales themselves carry all the meaningful state. |

## Consequences

**Positive:**

- Simpler domain model — fewer aggregates to maintain
- No phantom entity cluttering the repository layer
- The application layer clearly expresses intent: "register a batch with bales"
- Easier to test — the use case is a function, not an entity lifecycle

**Negative:**

- If future requirements add reception-level behavior (e.g., reception approval workflow, partial reception), this decision would need to be revisited
- Querying "all receptions" requires querying batches by creation context rather than a dedicated reception table

**Neutral:**

- The `RawMaterialBatch` effectively serves as the reception record for traceability purposes

## References

- [Bale management PRD](../../prd/warehouse/bale-management.md)
- [Backend bale management spec](../../../backend/docs/features/bale-management.md)
