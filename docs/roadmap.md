---
document_type: roadmap
status: active
implementation: not-applicable
scope: global
authority: explanatory
owner: product
last_reviewed: 2026-07-27
---

# Product Roadmap

This is a living navigation from Phase 2 priorities to candidate capabilities, their future specs and tasks, and focused layer-specific branches or pull requests. It is not a completion gate, strict schedule, architecture replacement, or implementation prescription.

## How To Use This Roadmap

1. Start with the relevant milestone and candidate capability.
2. Create or refine its spec and tasks against the source precedence below.
3. Deliver focused backend, frontend, or devops work through the appropriate branch and pull request.

One shared capability may be delivered through separate focused backend, frontend, and devops branches or pull requests. After a capability's spec exists, frontend work may use a versioned contract or mock while its corresponding implementation evolves.

Candidate capabilities are intentionally movable. Split, merge, or reorder them when discovery, dependencies, or source material justify it.

## Source Precedence

Use these sources in order when defining or changing a capability:

1. [PRDs](prd/product-overview.md)
2. [Context boundaries and ownership](architecture/context-map.md) and architecture decisions
3. [Ubiquitous language](domain/ubiquitous-language.md)
4. [DBML and data dictionaries](data-models/conceptual/)

## Delivery Scope

Each milestone may include the backend, API, business logic, database work, frontend, historical demonstration data, user access, and basic user training needed for its business outcome.

## Milestone 1: Initial Operational Control

**Construction weeks 1–3**

Warehouse and a pilot productive section become usable with initial access.

| Candidate Capability | Spec Focus | Dependency Hints |
| --- | --- | --- |
| User/password access | Access entry and initial authorization | Access policy and approved operational scopes |
| Raw-bale reception and stock balances | Warehouse raw-material custody and derived balances | Canonical yarn counts and Warehouse ownership |
| Release to Operation | Warehouse material handoff | Raw-bale reception and authorization |
| Pilot productive-section recording | One Yarn Spinning section's production record | Production identity as external context and access scope |
| Historical demonstration data | Representative demonstration flow | Candidate capabilities available for demonstration |

**Business value:** the supervisor records production and the Warehouse lead controls stock.

## Milestone 2: Complete Operational Recording and Traceability

**Construction weeks 4–6**

The Operational Unit expands to its full production scope and Warehouse adds the remaining priority flows.

| Candidate Capability | Spec Focus | Dependency Hints |
| --- | --- | --- |
| Yarn Spinning recording | The five Yarn Spinning sections | Pilot recording and shared yarn-count references |
| Process quality and waste | Section process quality and production waste | Yarn Spinning recording and ownership boundaries |
| Lot Processing traceability | The six Lot Processing stages and their history | Skein availability and Warehouse-defined production identity |
| Finished-product receipt | Warehouse receipt after Quality Send | Lot Processing handoff and Warehouse ownership |
| Production supplies | Warehouse supplies custody and movements | Warehouse stock behavior and authorization |
| Differentiated access | Configurable technical roles, actions, and approved scopes | Access Control policy; do not map organizational titles directly to permissions |

**Business value:** complete Operations recording and lot traceability.

## Milestone 3: Management Visibility and Controlled Administration

**Construction weeks 7–10**

Management and Administration receive consolidated visibility, while access and corrections become fully governed.

| Candidate Capability | Spec Focus | Dependency Hints |
| --- | --- | --- |
| Production Head dashboard | Production visibility for management | Consolidated operational and Warehouse facts |
| Administration daily consolidated report | Daily reporting for Administration | Production and Warehouse information ownership |
| Inventory valuation | Inventory valuation for Administration | Warehouse stock information |
| Audited record corrections | Controlled correction history | Owning context's record semantics and Access Control policy |
| Configurable users and permissions | User lifecycle, technical roles, and scope assignments | Access Control ownership and approved-scope confirmation |

**Business value:** unified visibility and replacement of the current workflow.

## Later or Out of Scope

The following are not part of this delivery schedule:

- Formal user acceptance
- Production deployment
- Definitive historical migration
- Complete user documentation
- Costing
- Commercialization integration
- Advanced business intelligence

## Navigation Boundaries

- The roadmap does not make a milestone a completion gate.
- The roadmap does not impose fixed implementation sequencing beyond the dependency hints above.
- The roadmap does not replace architecture or redefine bounded-context ownership.
- Each spec determines its own scope from the authoritative sources; this roadmap does not prescribe implementation details.
- This schedule provides delivery priority. Product requirements, ownership and architecture decisions, ubiquitous language, and database documentation remain the sources for business meaning and design.
