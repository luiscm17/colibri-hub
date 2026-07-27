---
document_type: adr
status: active
implementation: implemented
scope: domain/warehouse
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# ADR-003: Single Production Identity Defined by Warehouse

## Status

Active

## Context

Lots of raw material and finished product must be traceable across the entire system — from reception in Warehouse, through Yarn Spinning, to Lot Processing and final dispatch. This requires a stable production identity that all contexts can reference.

The question is: which context owns and defines the production identity?

Options:

1. Each context defines its own identity and maps to others via correlation
2. Warehouse defines the canonical identity; downstream contexts reference it

The system needs to support:

- Traceability audits (which bales went into which yarn lot)
- Inventory reconciliation across contexts
- Consistent lot codes in reports and labels

## Decision

The Warehouse context defines `production_identity_id` and `lot_code` as the canonical production identity. Downstream contexts (Yarn Spinning, Lot Processing) reference this identity and append their own history records, but they do not redefine or fork the identity.

Identity flow:

```text
Warehouse (defines) → Yarn Spinning (references, appends) → Lot Processing (references, appends)
```

Each downstream context may add context-specific attributes (e.g., spinning parameters, treatment records) linked to the Warehouse-defined identity, but the identity itself — its code, its creation timestamp, its batch association — is immutable once defined by Warehouse.

## Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
|-------------|------|------|-----------------|
| Each context defines its own identity | Maximum autonomy per context, no upstream dependency for identity creation | Breaks end-to-end traceability, requires complex correlation mappings, lot codes may diverge across contexts, audit becomes a reconciliation problem | Traceability is a core business requirement. Distributed identity creation makes it impossible to answer "which bales produced this yarn lot?" without fragile cross-context joins. |

## Consequences

**Positive:**

- Single, unambiguous lot code across the entire system
- Traceability queries are straightforward (follow the identity)
- Reports and labels reference one consistent code
- Downstream contexts are simpler — they consume identity, they don't create it

**Negative:**

- Warehouse becomes a dependency for identity creation — downstream contexts cannot create production records without a Warehouse-issued identity
- If Warehouse is unavailable, downstream cannot start new production lots (acceptable given Warehouse is always online in this system)

**Neutral:**

- Downstream contexts still own their domain-specific attributes and lifecycle events

## References

- [Bale management PRD](../../prd/warehouse/bale-management.md)
- [Context map](../context-map.md)
