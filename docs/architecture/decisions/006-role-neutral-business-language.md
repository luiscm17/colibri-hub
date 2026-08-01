---
document_type: adr
status: active
implementation: not-applicable
scope: global
authority: normative
owner: architecture
last_reviewed: 2026-08-01
---

# ADR-006: Role-Neutral Business Language Across System Boundaries

## Status

Active

## Context

Some business acts are currently performed by a particular section or position,
but that assignment may change without changing the meaning of the act. Naming a
capability, lifecycle phase, handoff, or business record after the current actor
would make the system model depend on an organizational arrangement rather than
on durable business meaning.

The finished-product handoff illustrates the problem. Quality Control currently
performs the final operational work and participates in making the completed lot
available to Warehouse. The durable fact, however, is that Operation releases a
completed Finished Product for Warehouse verification. Another authorized actor
may assume that responsibility without creating a new business process.

Authorization language, business language, and interface labels also answer
different questions:

- authorization determines whether an actor may perform an action in a scope;
- business language states what happens to the business object;
- interface labels explain the available interaction to the user.

Treating these vocabularies as interchangeable would either reduce meaningful
business acts to generic authorization terms or embed temporary interface copy
and staff assignments in the domain.

## Decision

Colibri Hub uses role-neutral business language for capabilities, business acts,
handoffs, lifecycle phases, records, and cross-context contracts.

The following rules apply:

1. A durable business fact is named for what happens, not for the position or
   section that currently performs it.
2. Current actors remain documented in PRDs as business responsibilities, but
   they do not determine the canonical name of the act.
3. Authorization actions determine whether a user may act in a business scope;
   they do not replace the business meaning of the authorized act.
4. Interface labels may use the clearest wording for the user's task, but those
   labels do not define domain or cross-context terminology.
5. Lifecycle phases describe the condition of the business process, not the
   organizational unit expected to act next.
6. A change in staff assignment or configurable role must not require a change
   to the business identity, lifecycle, or handoff contract.
7. The ubiquitous language is the bridge between canonical business terms and
   implementation vocabulary. Core documentation uses business vocabulary only.

For the Operation-to-Warehouse boundary, the canonical business act is
**release for reception**, within the broader **finished-product handoff**. It is
not named after Quality Control. The handoff may be pending verification,
require resolution, or be received. These conditions describe the handoff and
remain valid regardless of which authorized actor performs each interaction.

## Alternatives Considered

| Alternative | Benefits | Costs | Reason Rejected |
| --- | --- | --- | --- |
| Name business acts after the current responsible section | Familiar wording for current staff | Couples durable concepts to a changeable organizational assignment | Responsibility may change while the business act remains the same |
| Use only generic authorization actions as business names | Small and uniform action vocabulary | Loses business intent, rules, and audit meaning | Authorization answers whether an actor may act, not what business fact occurs |
| Use interface labels as canonical system terms | Copy appears consistent with visible controls | User-facing wording changes with language and interaction design | Interface copy is not a stable domain contract |

## Consequences

### Positive

- Organizational changes do not redefine the business process.
- Authorization remains configurable without weakening domain meaning.
- PRDs, architecture documents, and interfaces can evolve at their appropriate
  levels while sharing one stable business vocabulary.
- Audit history describes the business act and separately records the actor who
  performed it.

### Negative

- Existing documents that use actor-coupled terms must be aligned.
- Teams must distinguish current responsibility from canonical business naming
  during analysis and review.

### Neutral

- PRDs may continue to state that Quality Control is the current business actor
  for final inspection or release, provided that assignment is descriptive and
  does not rename the underlying capability.
- Interface labels such as “Register issue”, “Record response”, or “Register
  reception” remain valid contextual wording.

## References

- [Documentation Principles](../../dev-guide/documentation-principles.md)
- [Ubiquitous Language](../../domain/ubiquitous-language.md)
- [ADR-003](003-single-production-identity.md)
- [Context Map](../context-map.md)
- [Lot Processing PRD](../../prd/operation/lot-processing.md)
- [Finished Product PRD](../../prd/warehouse/finished-product.md)
- [UI Requirements](../../prd/ui-requirements.md)
