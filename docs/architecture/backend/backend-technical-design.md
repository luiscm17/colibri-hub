# Yarn EPR — Backend Technical Design Baseline

> First detailed backend technical design artifact for Yarn EPR.
> This document sits below the overview layer in
> [Architecture](../ARCHITECTURE.md),
> [Context Boundaries and Ownership](../context-boundaries-and-ownership.md),
> [Stack Baseline](../stack.md), and
> [Backend Architecture](../backend.md).

---

## 1. Purpose and scope

This document defines the **first stable technical-design layer for the backend**.

Its job is to make the backend structure explicit enough to support later work on:

- domain modeling
- application-service design
- API design
- persistence strategy
- database design

without jumping too early into SQL, tables, or low-level implementation.

This document focuses on:

- backend module boundaries
- per-context record/aggregate families
- use-case groupings
- ports and contracts between contexts
- correction and audit implications
- dependency direction and technical constraints

---

## 2. Position in the architecture set

This document belongs to the detailed backend-design layer within the current architecture set.

| Layer | Document | Role |
|---|---|---|
| Stable overview | [Architecture](../ARCHITECTURE.md) | System-wide context map, lifecycle, and architectural principles |
| Stable overview | [Context Boundaries and Ownership](../context-boundaries-and-ownership.md) | Business ownership rules and boundary decisions |
| Stable overview | [Stack Baseline](../stack.md) | Technology baseline and architectural style |
| Stable overview | [Backend Architecture](../backend.md) | High-level backend-oriented architecture view |
| Detailed backend design | [Backend Technical Design](./backend-technical-design.md) | Technical backend module design baseline |
| Detailed backend design | [Persistence Design Principles](./persistence-design-principles.md) | Conceptual persistence ownership, identity, correction, and time-model rules |
| Context-level schema design | Applied Supabase migrations and [Warehouse DB Dictionary](../../db/warehouse-dictionary.md) | Migration-authoritative physical schema and explanatory Markdown mapping; DBML remains design detail |

---

## 3. Backend module mapping

The backend should keep descriptive architecture names in documentation while using concise code-facing module names in implementation.

| Architecture context | Code-facing module | Primary responsibility |
|---|---|---|
| Warehouse | `warehouse` | Custody, stock movements, production identity setup, finished-product reception, and warehouse lifecycle |
| Yarn Spinning | `yarn-production` | Continuous production records before Inventory assembles a lot |
| Lot Processing | `batch-processing` | Inventory assembly facts, sequential stage history, Quality Send back to Warehouse |
| Access Control | `access` | RBAC, scopes, permission assignments, exceptions, and authorization decisions |
| Shared Reference Data | `catalogs` | Canonical yarn counts and their identifiers |

### Technical boundary rule

Each module should own its own:

- domain concepts
- application use cases
- repository contracts
- integration contracts
- correction rules
- audit responsibilities for its own records

No module should write directly into another module's internal record model.

---

## 4. Cross-context backend design rules

### 4.1 Boundary-preserving collaboration

Cross-context collaboration should happen through explicit contracts such as:

- read ports
- command/integration ports
- published read models
- authorization decision ports
- catalog validation/query ports

### 4.2 Single lot identity

The backend must preserve this ownership split:

- **Warehouse** defines the single lot identity
- **Lot Processing** appends stage records directly to that identity
- **Yarn Spinning** never pretends to own a lot aggregate

### 4.3 Correction and audit baseline

All business contexts must support controlled corrections with audit trail.

At minimum, each context design must account for:

- editable operational records inside a policy window
- elevated correction authority outside the normal window
- audit capture for who changed what, when, why, and under which authorization scope

### 4.4 Support contexts remain support contexts

- `access` governs authorization, not business meaning
- `catalogs` provides canonical yarn counts, not workflow ownership

---

## 5. Per-context technical design baseline

## 5.1 `warehouse`

### Record / aggregate families

- Raw-material batch (`RawMaterialBatch`) identified by `ShipmentNumber`
- Independently identified `Bale` aggregates owning their custody lifecycle
- Receiving application action that registers one complete batch plus one or more bales in one transaction
- Production identity definition
- Material emission to production
- Finished-product reception from Operation
- PT availability / disposition / classification
- PT exit and return records
- Supply movement records

### Use-case groups

- Register one complete raw-material batch and its one-or-more bales
- Define production identity from available raw material
- Deliver one or more independently loaded whole bales to Production; each transition records `delivered_at` and rejects repeat delivery
- Accept a finished product lot after Warehouse physical verification
- Classify finished product for warehouse disposition
- Execute sale, transfer, return, and stock-affecting warehouse actions
- Query stock, movement history, and custody traceability

### Ports / contracts

- production identity read/export contract for downstream contexts
- stock balance and movement persistence ports
- warehouse authorization policy port
- Quality send and finished-product acceptance contracts with `batch-processing`
- audit trail writer port
- catalog query/validation ports

### Correction and audit implications

- raw-material reception, whole-bale delivery, identity definition, PT acceptance, and PT classification are separate auditable business acts
- receiving is not a `Reception` aggregate, and normalized header/detail persistence does not impose an aggregate shape
- `IN_PRODUCTION` expresses resulting custody/location, not consumption or processing; responsible delivery actors are not mandatory evidence in the current model
- Warehouse corrections must not rewrite Lot Processing stage history
- Lot Processing-owned quality state must not be duplicated in Warehouse; Warehouse availability/disposition and physical presentation remain separately auditable dimensions

### Key dependencies

- Depends on `access` for action + scope authorization
- Depends on `access` for canonical user references and `catalogs` for yarn counts
- Consumes delivery context from `batch-processing`
- Exposes production identity and material availability to `yarn-production` and `batch-processing`

## 5.2 `yarn-production`

### Record / aggregate families

- Production discharge records
- Progress records
- Process quality records
- Spinning waste records
- Skein output availability views/contracts

### Use-case groups

- Register production by machine / shift / yarn count / discharge
- Register section progress where applicable
- Register process-quality controls
- Register spinning waste by section or machine group
- Publish skein availability for downstream Inventory assembly
- Query operational production summaries by section, shift, machine, and yarn count

### Ports / contracts

- production record persistence ports
- progress persistence ports
- quality and waste persistence ports
- production authorization policy port
- skein availability publication/read port
- upstream production identity reference read port
- audit trail writer port
- catalog query/validation ports

### Correction and audit implications

- correction rules must preserve the difference between business date, shift, and system timestamp
- calculated values such as net weights should remain explainable and auditable
- corrections must not fabricate a lot history that does not exist in this context

### Key dependencies

- Depends on `access` for register/validate/approve/correct permissions
- Depends on `access` for canonical user references and `catalogs` for yarn counts
- Consumes production identity and material context from `warehouse`
- Exposes skein availability and readiness to `batch-processing`

## 5.3 `batch-processing`

### Record / aggregate families

- Lot stage records
- Stage note / inconvenience records
- Stage waste records
- Quality send evidence for Warehouse receipt

### Use-case groups

- Record Inventory assembly facts from the upstream lot identity and skein availability
- Advance the lot through its ordered stage history
- Register stage-local verified data, generated data, stage notes/exceptions, and waste
- Capture final quality state and send the validated lot to Warehouse
- Query lot history, derived process position, delays, and cross-stage traceability

### Ports / contracts

- lot stage sequence policy port
- skein availability intake port
- warehouse production identity read port
- lot-processing authorization policy port
- Quality send contract toward `warehouse`; Warehouse acceptance stays Warehouse-owned
- audit trail writer port
- catalog query/validation ports

### Correction and audit implications

- the Inventory stage is the first operational record for the Warehouse-defined lot
- stage records must preserve the dedicated record model per intervention rather than split into artificial receipt/delivery pairs; a lot may have multiple legitimate records in the same stage, business date, or shift
- each correction must preserve stage sequence meaning and historical responsibility
- The Quality stage records Quality Send while the lot awaits Warehouse receipt; the pending condition ends when Warehouse records its receipt for the same `production_identity_id`, and Warehouse does not mutate Lot Processing history

### Key dependencies

- Depends on `access` for stage-level permissions and elevated corrections
- Depends on `access` for canonical user references and `catalogs` for yarn counts
- Consumes production identity from `warehouse`
- Consumes skein availability from `yarn-production`
- Exposes processed-lot delivery back to `warehouse`

## 5.4 `access`

### Record / aggregate families

- System role/capability definitions
- Permission assignments
- Scope definitions
- Exceptions or overrides
- Permission change audit records

### Use-case groups

- Define capabilities and protected actions
- Assign permissions by scope
- Manage overrides and exceptions
- Evaluate authorization decisions for business actions
- Audit permission changes and effective access history

### Ports / contracts

- authorization decision port
- permission assignment persistence ports
- scope persistence ports
- permission audit ports
- canonical user identity read port

### Correction and audit implications

- permission changes are themselves auditable domain events
- override behavior must remain explicit and reviewable
- correction of access assignments must not erase prior effective authorization history

### Key dependencies

- Owns canonical users and technical RBAC roles
- Consumes protected action and scope definitions from business modules
- Exposes authorization decisions to every business context

## 5.5 `catalogs`

### Record / aggregate families

- Yarn counts

### Use-case groups

- Maintain canonical yarn counts
- Validate yarn-count references used by business contexts
- Publish query access to reusable yarn-count data

### Ports / contracts

- yarn-count query port
- yarn-count validation port
- yarn-count persistence port

### Correction and audit implications

- catalog corrections can have broad downstream impact and must remain traceable
- reference changes must not silently redefine historical business records without an explicit policy

### Key dependencies

- Depends on business governance for yarn-count curation rules
- Exposes canonical yarn-count values and stable IDs to `warehouse`, `yarn-production`, and `batch-processing`

---

## 6. Dependency summary

| Module | Depends on | Provides to |
|---|---|---|
| `warehouse` | `access`, `catalogs`, delivery data from `batch-processing` | production identity and warehouse lifecycle data |
| `yarn-production` | `access`, `catalogs`, production context from `warehouse` | skein availability and spinning records |
| `batch-processing` | `access`, `catalogs`, identity from `warehouse`, skein availability from `yarn-production` | processed-lot delivery and lot traceability |
| `access` | shared identity references, protected action definitions | authorization decisions and policy enforcement |
| `catalogs` | yarn-count governance inputs | canonical yarn-count references and validations |

---

## 7. What this document intentionally does not define yet

This document does **not** define:

- SQL schema
- table structure
- foreign keys
- exact ORM models
- endpoint URLs or payload shapes
- message/event infrastructure choices
- final package layout inside a concrete codebase
- detailed read-model projections or reporting schemas

Those decisions should come later, after domain and persistence design are derived from these module boundaries.

---

## 8. DB-design constraints derived from this document

Any later persistence or database design must preserve these constraints:

1. **Persistence follows ownership.** Each record family belongs to the context that owns its business meaning.
2. **One lot identity remains explicit.** Warehouse owns `production_identity_id`; Lot Processing records reference it directly without a duplicate aggregate.
3. **Correction and audit are first-class.** Persistence must support editable business truth with auditable history.
4. **Cross-context references stay explicit.** Shared identifiers and integration references must preserve context ownership.
5. **Read models do not redefine ownership.** Cross-context traceability and reporting views must not flatten the owning write models.
