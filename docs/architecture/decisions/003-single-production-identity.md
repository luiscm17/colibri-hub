---
document_type: adr
status: active
implementation: not-started
scope: global
authority: normative
owner: architecture
last_reviewed: 2026-08-01
---

# ADR-003: Single Business Lot with Context-Owned Representations

## Status

Active

## Context

The enterprise uses the term **Lot** throughout the complete production cycle.
The system, however, separates that cycle across bounded contexts with different
responsibilities:

- Warehouse defines what must be produced and manages the product before and
  after productive processing.
- Operation processes that requirement and owns the operational history.

The same physical lot crosses both contexts. It must retain one stable,
human-readable code without forcing Warehouse and Operation to share one
aggregate or write each other's records.

The architecture must therefore answer two related questions:

1. Which context assigns the business `lot_code`?
2. How does each context represent the same lot while preserving its own model
   and write authority?

The current Bale Management capability does not associate delivered bales with
a Finished Product, Production Identity, or `lot_code`. Bale-to-lot genealogy is
therefore not part of this decision.

## Decision

The system models one business lot through two context-owned representations:

| Context | Representation | Responsibility |
| --- | --- | --- |
| Warehouse | `Finished Product` | Defines the production requirement, assigns the unique `lot_code`, and later manages reception, availability, custody, dispatch, and returns |
| Lot Processing within Operation | `Production Identity` | Represents the same requirement inside Operation and anchors physical assembly, stage history, quality facts, and Quality Send |

The following rules apply:

1. Warehouse creates the Finished Product requirement before Lot Processing
   begins and assigns one globally unique `lot_code`.
2. Lot Processing creates or resolves exactly one Production Identity from that
   requirement.
3. The Warehouse Finished Product and Operation Production Identity have a
   `1:1` relationship and represent the same business and physical lot.
4. Both representations retain the same `lot_code`; Operation must not assign a
   parallel business code.
5. Context-local technical identifiers may differ. They do not replace the
   shared `lot_code` or imply another business lot.
6. Inventory assembles the physical set of skeins under the existing Production
   Identity and `lot_code`. Assembly starts the Lot Processing stage history; it
   does not create another identity.
7. Quality Send transfers the completed operational result to Warehouse under
   the same `lot_code`. Warehouse reception continues the existing Finished
   Product lifecycle and does not create another Finished Product.
8. Warehouse writes only Warehouse-owned requirement and inventory facts. Lot
   Processing writes only Operation-owned identity, processing, waste, quality,
   and handoff facts.
9. Cross-context dashboards and details may project authorized data from both
   representations, but a projection does not transfer source-record ownership.

Identity flow:

```text
Warehouse Finished Product requirement
    1:1, same lot_code
Operation Production Identity
    physical assembly and Lot Processing history
Quality Send
    same lot_code
Warehouse reception and inventory lifecycle
```

## Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
| --- | --- | --- | --- |
| Warehouse owns Production Identity and Operation references the same aggregate | Simple conceptual identity and direct reuse of one record | Makes an Operation concept part of the Warehouse model, weakens bounded-context ownership, and encourages cross-context writes | Production Identity is the Operation representation of the requirement, not a Warehouse capability |
| Each context assigns an independent lot code and correlates them later | Strong local autonomy | Codes may diverge, users must reconcile two business identities, and end-to-end consultation becomes fragile | The enterprise recognizes one lot and requires one visible code throughout the cycle |
| One shared aggregate spans Warehouse and Operation | Avoids an explicit context mapping | Couples lifecycles, permissions, persistence, and change rules across contexts | Each context owns different facts and must evolve without sharing write authority |

## Consequences

### Positive

- Users follow one `lot_code` across Warehouse and Operation.
- The system reflects the enterprise's single-lot concept without collapsing
  bounded contexts.
- Warehouse and Lot Processing retain independent domain models and write
  ownership.
- Physical reception, processing history, and Warehouse inventory can be
  presented as one authorized lifecycle.
- Operation cannot accidentally fork the business identity.

### Negative

- The integration must enforce the `1:1` mapping and idempotent creation or
  resolution of Production Identity.
- Read models that show the complete lifecycle must combine context-owned data
  while applying authorization to every projected field.
- Failures at the Warehouse-to-Operation handoff can delay the start of new Lot
  Processing work and require observable retry or reconciliation behavior.

### Neutral

- Each context may use its own internal identifier in addition to the shared
  `lot_code`.
- Yarn Spinning remains independent from Production Identity. It produces
  skeins that Inventory later assembles under the existing Operation
  representation.
- No bale-to-lot association is introduced by this decision.

## Architectural Invariants

1. A `lot_code` is globally unique.
2. One Finished Product maps to exactly one Production Identity, and vice versa.
3. Crossing a context boundary never creates another business lot or replaces
   the `lot_code`.
4. A context cannot overwrite source records owned by another context.
5. Inventory assembly cannot start without the applicable Finished Product
   requirement and resolved Production Identity.
6. Quality Send and Warehouse reception reference the same Finished Product,
   Production Identity mapping, and `lot_code`.
7. Authorization-sensitive projections omit data for scopes the caller cannot
   read.

## References

- [Product overview](../../prd/product-overview.md)
- [Warehouse Finished Product PRD](../../prd/warehouse/finished-product.md)
- [Operation overview](../../prd/operation/overview.md)
- [Lot Processing PRD](../../prd/operation/lot-processing.md)
- [Lot Processing Records](../../prd/operation/lot-processing-records.md)
- [Bale Management PRD](../../prd/warehouse/bale-management.md)
- [Context map](../context-map.md)
