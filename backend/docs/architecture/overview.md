---
document_type: architecture
status: active
implementation: partial
scope: backend
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Backend Architecture Overview

Backend architecture reference for Colibri Hub. This document unifies the high-level
backend design view and the detailed technical design baseline into a single
coherent reference.

For system-wide context and boundary decisions, see:

- [System Overview](../../../docs/architecture/system-overview.md)
- [Context Map](../../../docs/architecture/context-map.md)
- [Technology Baseline](../../../docs/architecture/technology-baseline.md)

For persistence principles and database design:

- [Persistence Design Principles](../database/design-principles.md)
- [Warehouse Schema](../database/warehouse-schema.md)

---

## 1. Architectural Principles

1. **Boundaries follow the domain map.** Backend modules align with Warehouse,
   Yarn Spinning, Lot Processing, Access Control, and Shared Reference Data.
2. **Capability-first organization.** Each module owns its business capability
   end-to-end: domain, application, ports, and adapters.
3. **Hexagonal isolation.** Domain logic has no framework dependencies; external
   concerns reach the domain only through ports.
4. **No cross-context writes.** Modules collaborate through explicit read ports,
   integration contracts, or published views — never by writing into another
   module's internal model.
5. **Correction is first-class.** Business records support controlled edits with
   full audit trail; the backend never assumes strict append-only behavior.
6. **Single lot identity.** Warehouse defines the production identity; all
   downstream contexts reference it without creating duplicates.

---

## 2. Capability-First Module Structure

Each backend context follows a consistent internal organization:

```text
<module>/
├── domain/          # Aggregates, value objects, domain services, invariants
├── application/     # Use cases, commands, queries, orchestration
├── ports/           # Repository, policy, integration, and external contracts
└── adapters/        # Persistence, HTTP, messaging, auth integrations
```

### Module Mapping

| Business Context       | Code Module        | Primary Responsibility                                                         |
| ---------------------- | ------------------ | ------------------------------------------------------------------------------ |
| Warehouse              | `warehouse`        | Custody, stock movements, production identity, finished-product reception       |
| Yarn Spinning          | `yarn-production`  | Continuous production records before lot assembly                               |
| Lot Processing         | `batch-processing` | Inventory assembly, sequential stage history, Quality Send to Warehouse        |
| Access Control         | `access`           | RBAC, scopes, permission assignments, authorization decisions                  |
| Shared Reference Data  | `catalogs`         | Canonical yarn counts and stable identifiers                                   |

Each module owns its domain concepts, application use cases, repository
contracts, integration contracts, correction rules, and audit responsibilities.

---

## 3. Hexagonal Layers

### 3.1 Domain Layer

Contains aggregates, value objects, domain services, and invariants. Pure
business logic with no infrastructure dependencies.

Key design rules:

- Aggregate boundaries reflect business ownership, not persistence shape
- Value objects are immutable and self-validating
- Domain services encapsulate logic that spans multiple aggregates within a
  single context
- Invariants are enforced at the domain boundary, not at the adapter level

### 3.2 Application Layer

Contains use cases (commands and queries) that orchestrate domain operations.
Defines the transactional boundary and coordinates domain objects.

Key design rules:

- One use case per business action (register batch, deliver bale, etc.)
- Application services depend on port interfaces, never on concrete adapters
- Transaction boundaries are declared at this layer
- Application errors translate domain failures into actionable responses

### 3.3 Ports Layer

Defines contracts that the domain and application layers require from the
outside world. Ports are interfaces — they express what is needed without
dictating how.

Common port types:

- **Repository ports** — persistence contracts for aggregates
- **Policy ports** — authorization and business-rule evaluation
- **Integration ports** — cross-context read/write contracts
- **Identity ports** — ID generation contracts
- **Transaction ports** — unit-of-work and conflict contracts
- **Audit ports** — trail-writing contracts

### 3.4 Adapters Layer

Implements port contracts with concrete infrastructure: ORM mappings, HTTP
handlers, message consumers, external API clients.

Key design rules:

- Adapters depend on ports, never the reverse
- Multiple adapters may satisfy the same port (e.g., test doubles for tests,
  PostgreSQL for production)
- Adapter-specific exceptions are translated into domain/application errors at
  the boundary

---

## 4. Composition

### 4.1 Application Bootstrap

The composition root wires adapters to ports and assembles the runnable
application. In the current codebase, `bootstrap.http_application.create_app`
performs this role:

- Creates the persistence engine and session factory
- Instantiates adapters (repositories, identity generators)
- Wires use cases with their adapter-backed ports
- Registers HTTP routes and exception handlers
- Returns the configured ASGI application

### 4.2 Cross-Context Collaboration

Contexts interact exclusively through their declared ports:

| From             | To               | Mechanism                                           |
| ---------------- | ---------------- | --------------------------------------------------- |
| Access Control   | All business     | Authorization decision port                         |
| Shared Ref Data  | All business     | Catalog query/validation port                       |
| Warehouse        | Yarn Spinning    | Production identity read port                       |
| Warehouse        | Lot Processing   | Production identity + specifications read port      |
| Yarn Spinning    | Lot Processing   | Skein availability read port                        |
| Lot Processing   | Warehouse        | Processed-lot delivery contract                     |

### 4.3 Dependency Direction

Supporting contexts (Access Control, Shared Reference Data) point inward toward
business contexts. Peer business contexts interact only through explicit
integration contracts.

```text
Access Control ──────► Warehouse ◄────── Shared Reference Data
        │                  │ │                      │
        │                  │ └─────► Lot Processing ◄┘
        │                  │              ▲
        │                  └──► Yarn Spinning
        │                            │
        └────────────────────────────┘
```

---

## 5. Current Implementation State

> This section documents what exists today in code and migrations.

### 5.1 Implemented: `warehouse.bales`

The Warehouse context has one implemented capability: **raw-material batch and
bale registration**.

**Domain layer** (`warehouse.bales.domain`):

- `RawMaterialBatch` — aggregate grouping one or more bales under a shipment number
- `RawMaterialBale` — independently identified entity within a batch, owning
  custody state (`IN_WAREHOUSE`, `DELIVERED`)
- Value objects for bale number, shipment number, and batch attributes
- Domain invariants: shipment number uniqueness, bale number uniqueness within
  batch, valid state transitions

**Application layer** (`warehouse.bales.application`):

- `RegisterRawMaterialBatchUseCase` — registers a complete batch with its bales
  in one transaction
- Application-level error types for conflict detection (duplicate shipment,
  duplicate bale number)
- Result type carrying the created `raw_material_batch_id`

**Ports layer** (`warehouse.bales.ports`):

- `RawMaterialBatchRepository` — persistence contract
- `IdentityPort` — ID generation contract
- `TransactionPort` — unit-of-work contract
- `TransactionConflictPort` — uniqueness-constraint conflict detection

**Adapters layer** (`warehouse.bales.adapters`):

- SQLAlchemy ORM adapter implementing the repository port
- PostgreSQL-backed persistence via Supabase migrations
- Test doubles for unit testing (stubs and fakes via `backend/tests/support/doubles.py`)
- Named constraints: `uq_raw_material_batches_shipment_number`,
  `uq_raw_material_bales_raw_material_batch_bale_number`,
  `ck_raw_material_bales_status`

**HTTP composition** (`bootstrap.http_application`):

- `POST /api/v1/warehouse/bales` — registers a batch and its bales
- Exception handlers translating application conflicts to HTTP 409

**Persistence** (Supabase migration):

- Tables: `raw_material_batches`, `raw_material_bales`
- RLS enabled; privileges revoked from `anon`, `authenticated`, `service_role`
- No policies or runtime authorization flow defined yet

### 5.2 Not Yet Implemented

The following capabilities are designed but have no implementation in the
codebase:

| Module             | Planned Capabilities                                                                  |
| ------------------ | ------------------------------------------------------------------------------------- |
| `warehouse`        | Production identity, bale delivery, material emission, PT reception/classification    |
| `yarn-production`  | Production discharge, progress, quality, waste records, skein availability            |
| `batch-processing` | Inventory assembly, stage progression, stage records, Quality Send                    |
| `access`           | RBAC, scope management, permission assignments, authorization decisions               |
| `catalogs`         | Yarn-count catalog, validation, query ports                                           |

---

## 6. Per-Module Design Reference

### 6.1 `warehouse`

**Record families:** Raw-material batch, Bale (custody/lifecycle), Production
identity, Material emission, Finished-product reception, PT
classification/disposition, PT exit/return, Supply movements.

**Key invariants:**

- Raw material is received as bales, not as a production lot
- `RawMaterialBatch` groups bales and shared shipment evidence — it is not a lot
- Reception is an application action; the collective POST registers the complete batch
- Bale delivery rejects repeats and transitions custody state
- Production identity is defined after reception, as a separate business act
- Quality state, availability/disposition, and physical presentation are
  independent dimensions
- Warehouse does not rewrite Lot Processing history

**Ports:** Repository, production identity export, stock balance, authorization
policy, audit trail, catalog validation, lot-processing delivery intake.

### 6.2 `yarn-production`

**Record families:** Production discharge, Progress, Process quality, Spinning
waste, Skein output availability.

**Key invariants:**

- No lot aggregate — continuity is by section, machine, shift, date, yarn count
- Skein output is availability for downstream assembly, not the start of a lot
- Net weights and derived values are domain-computed, not arbitrary user input
- Waste and quality belong to spinning even with configurable recorder

**Ports:** Production record persistence, progress, quality/waste, authorization
policy, skein availability publication, upstream identity reference, audit trail.

### 6.3 `batch-processing`

**Record families:** Lot stage records, Stage notes/inconveniences, Stage waste,
Quality Send evidence.

**Key invariants:**

- Inventory is the first operational record under the Warehouse-defined lot
- Stage records use dedicated models per intervention (not receipt/delivery pairs)
- Multiple records per stage/date/shift are legitimate — no false uniqueness
- Quality stage records condition; Warehouse decides disposition separately
- Stage corrections preserve sequence meaning and historical responsibility

**Ports:** Stage sequence policy, skein intake, production identity read,
authorization policy, Quality Send contract, audit trail, catalog validation.

### 6.4 `access`

**Record families:** Roles/capabilities, Permission assignments, Scopes,
Exceptions/overrides, Permission change audit.

**Key invariants:**

- Policy context only — does not own business workflow meaning
- Organizational roles and system permissions are related but not equivalent
- Permission changes are auditable domain events
- Override behavior is explicit and reviewable

**Ports:** Authorization decision, permission assignment persistence, scope
persistence, permission audit, user identity.

### 6.5 `catalogs`

**Record families:** Yarn counts.

**Key invariants:**

- Owns canonical values and stable IDs, not transactional meaning
- Catalog corrections have broad downstream impact and must be traceable
- Reference changes do not silently redefine historical business records

**Ports:** Yarn-count query, validation, persistence.

---

## 7. Correction and Audit Model

All business contexts adopt a consistent correction baseline:

1. Critical records are never deleted silently
2. Within the operational correction window: edits follow scoped RBAC/policy
3. Outside the window: only SysAdmin may edit
4. Audit trail preserves: who, when, previous values, new values, reason,
   authorization context

Each context owns its correction rules, its editable time-window policy, and its
audit persistence contract. The system avoids both a blanket append-only
assumption and burying correction semantics in infrastructure.

---

## 8. DB-Design Constraints

Persistence and database design must preserve:

1. **Persistence follows ownership.** Each record family belongs to its owning
   context.
2. **Explicit lot identity.** Warehouse owns `production_identity_id`; Lot
   Processing references it directly.
3. **Correction is first-class in persistence.** Editable truth with auditable
   history.
4. **Cross-context references stay explicit.** Shared identifiers preserve
   context boundaries.
5. **Read models do not redefine ownership.** Reporting views never flatten
   write-model ownership.

---

## 9. Related Documents

- [System Overview](../../../docs/architecture/system-overview.md)
- [Context Map](../../../docs/architecture/context-map.md)
- [Technology Baseline](../../../docs/architecture/technology-baseline.md)
- [Persistence Design Principles](../database/design-principles.md)
- [Warehouse Schema](../database/warehouse-schema.md)
- [Bale Management PRD](../../../docs/prd/warehouse/bale-management.md)
