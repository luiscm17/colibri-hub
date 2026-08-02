---
document_type: domain
status: active
scope: warehouse
authority: normative
owner: architecture
last_reviewed: 2026-08-01
---

# Warehouse Domain Map

## Purpose

Warehouse owns physical custody and documentary control for raw-material bales,
Finished Products, and production supplies. It manages each lifecycle within
its own boundary and consumes only the authorized information needed from other
contexts.

Warehouse owns the Finished Product from requirement definition onward. Lot
Processing owns the contextual Production Identity used by Operation. Both
represent the same business and physical lot through a one-to-one relationship
and one lot code.

## Authority

Warehouse owns:

- raw-material batch registration and independent bale identity;
- bale custody and whole-bale delivery to Production;
- Finished Product requirement definition and the unique lot code;
- physical verification during the finished-product handoff;
- Warehouse handoff issues;
- Finished Product reception and custody;
- Warehouse availability, physical presentation, stock, dispatch, and returns;
- production-supplies receipts, issues, adjustments, balances, and consultation;
- correction history for Warehouse-owned records.

Warehouse consumes authorized Lot Processing information such as productive
completion, Operation quality state, delivery conditions, release for reception,
and issue responses. It does not overwrite or duplicate the source records.

Access Control determines whether an actor may perform an action in a scope.
Business positions and current responsibilities do not grant authority by
themselves.

## Core Concepts

| Concept | Warehouse meaning |
| --- | --- |
| Raw-material batch | Supplier-shipment grouping identified by shipment number and containing one or more bales |
| Bale | Independently identified raw-material unit with its own custody lifecycle |
| Receiving action | Business act that registers one complete raw-material batch and its bales |
| Delivery to Production | Whole-bale custody transfer from Warehouse to Production |
| Finished Product | Warehouse representation of one business lot from requirement definition through reception, custody, dispatch, and possible return |
| Lot code | Globally unique business reference assigned with the Finished Product requirement and shared with Operation |
| Finished-product handoff | Cross-context coordination from Operation release for reception until Warehouse reception |
| Handoff issue | Warehouse record of a discrepancy requiring correction, remedy, or clarification before reception |
| Finished-product reception | Warehouse record that physical verification is complete and custody has transferred to Warehouse |
| Availability state | Warehouse decision about readiness for storage, reservation, release, or distribution |
| Physical presentation | Physical form in which Warehouse receives or stores the Finished Product |
| Supply | Warehouse-managed production input with its own receipt, issue, adjustment, and stock history |

## Raw-Material Bale Lifecycle

Bales follow a simple one-directional custody lifecycle:

| Condition | Meaning |
| --- | --- |
| In Warehouse | Bale remains under Warehouse custody |
| Delivered | Bale has been physically transferred to Production and is treated as used |

The transition from In Warehouse to Delivered occurs once. Delivery is for the
whole bale and does not associate that bale with a Finished Product, Production
Identity, or lot code.

## Finished Product Requirement

Warehouse defines what must be produced before Lot Processing begins. The
requirement establishes the Finished Product, unique lot code, target yarn
count, color, client or destination, classification, and applicable
specifications.

Completing the requirement makes it available to Operation automatically. No
separate approval, send, or acceptance is required at this boundary. Operation
creates or resolves one Production Identity for the same requirement and keeps
the supplied lot code.

Requirement definition does not mean that finished physical stock already
exists in Warehouse.

## Finished-Product Handoff

After productive completion, an authorized Operation actor performs release for
reception. The business act is role-neutral even when Quality Control currently
performs it.

Warehouse then verifies the physical product against the authorized
requirement, productive completion, Operation quality state, delivery
conditions, and applicable quantities.

### Successful verification

When the physical product and authorized information agree, Warehouse records
Finished Product reception. Reception completes the handoff and places the
product under Warehouse custody.

### Discrepancy before reception

When the information and physical product do not agree, Warehouse records a
handoff issue instead of reception. The issue describes what must be corrected,
remedied, or clarified.

The issue is not rejection or non-approval. The product must still be delivered
to Warehouse. Operation records an issue response and the same handoff returns
to pending verification. Warehouse verifies again and may record reception or
another issue.

Issues and responses may repeat until reception. They form one chronological,
append-only history and never create another release, Finished Product,
Production Identity, or lot code.

## Finished Product After Reception

After reception, Warehouse:

1. records the physical presentation;
2. classifies Warehouse availability independently from the Operation quality
   state;
3. manages custody and stock;
4. records dispatch through an applicable business channel;
5. records a return only in relation to a prior dispatch.

Operation quality, Warehouse availability, and physical presentation are
separate dimensions. Warehouse reads Operation quality as context and does not
replace it with a Warehouse decision.

## Business Rules

1. Warehouse Finished Product and Operation Production Identity maintain a
   one-to-one relationship and one lot code.
2. Each context writes only its own source records.
3. Bale delivery does not create bale-to-lot genealogy.
4. Completing a Finished Product requirement makes it available to Operation
   without a separate approval or acceptance.
5. Release for reception starts one finished-product handoff.
6. Warehouse records either a handoff issue or reception after verification.
7. Operation response returns the same handoff to pending verification.
8. Handoff issue and response cycles may repeat.
9. Reception is recorded once and is the only act that completes the handoff.
10. No rejection or non-approval outcome exists for the mandatory delivery.
11. Availability classification requires prior reception.
12. Corrections preserve actor, time, reason, and prior and resulting
    information under the applicable authorization policy.
13. Current business actors do not define fixed authorization roles or canonical
    names for business acts.

## Boundaries and Non-Goals

- Warehouse does not own Yarn Spinning records, Lot Processing stages,
  Operation waste, Operation quality, or Production Identity.
- The handoff does not reopen or reverse a productive stage.
- Handoff issues and responses are not an independent messaging capability.
- A transversal view may present authorized information from several contexts
  without transferring ownership of source records.
- This map does not prescribe interfaces, storage, functions, classes,
  components, or implementation technology.

## References

- [Bale Management PRD](../prd/warehouse/bale-management.md)
- [Finished Product PRD](../prd/warehouse/finished-product.md)
- [Production Supplies PRD](../prd/warehouse/production-supplies.md)
- [Lot Processing Domain Map](operation/lot-processing.md)
- [Context Map](../architecture/context-map.md)
- [ADR-003](../architecture/decisions/003-single-production-identity.md)
- [ADR-006](../architecture/decisions/006-role-neutral-business-language.md)
