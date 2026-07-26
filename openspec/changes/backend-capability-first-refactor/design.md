# Design: Backend Capability-First Refactor v2

> **Historical P0 design.** The cutover described here is complete. Its
> compatibility-era physical, API, and adapter names were later superseded by
> `../align-warehouse-persistence-naming/` and remain only as phase evidence.

## Technical Approach

Move—not wrap—the registration slice into `warehouse.bales`, preserving the external API, schema, one request-scoped `Session`, header-before-detail order, atomic rollback/commit, named-constraint translation, unknown-integrity propagation, and every P0 exclusion. Completed PR1–PR4 decisions remain unchanged. Original PR5 is replaced by exactly two successive-to-main work units: independently runnable PR5A, then independently runnable PR5B; PR6 only removes compatibility seams and performs final verification.

## Architecture Decisions

| Choice | Rejected | Rationale |
|---|---|---|
| `RawMaterialBatchId` is technical identity; immutable globally unique `ShipmentNumber` is visible identity | Shipment number as entity ID | Preserves the established domain decision. |
| Batch tuple-copies `BaleId`s; each Bale stores `BaleId`, `RawMaterialBatchId`, and `BaleNumber`, not ShipmentNumber | Mutable collections or duplicated visible identity | Preserves aggregate invariants and visible identity `ShipmentNumber + BaleNumber`. |
| Two repositories share one `Session` and concrete transaction | Repository-per-table transaction ownership | Keeps application ports technology-neutral and the use case atomic. |
| PR5A owns driven adapters; PR5B owns driver adapter and composition cutover | One 960-line PR5 | Each slice has one behavior, runnable end state, tests, and rollback. |

## Ownership and FQN Contracts

Technology appears once per canonical FQN: in the concrete class, not repeated in package/module names.

| Slice | Canonical owner / old→new compatibility |
|---|---|
| PR5A | Create `warehouse.bales.adapters.identity.identity_generator.UuidIdentityGenerator` and `warehouse.bales.adapters.persistence.transaction.SqlAlchemyTransaction`. Replace old implementations with aliases: `warehouse.adapters.identity.uuid_identity_generator.UuidIdentityGenerator` → canonical identity class; `warehouse.adapters.persistence.warehouse_transaction.WarehouseTransaction` → canonical transaction class. Canonical code imports `warehouse.bales.ports.{identity_generator,transaction,transaction_errors}` only. |
| PR5B | Create canonical modules under `warehouse.bales.adapters.http`: `router`, `bale_reception_{mapping,request,response}`, `error_{handlers,mapping,response}`. Every `warehouse.adapters.http.raw_material.*` module becomes an old→new alias. `warehouse.adapters.http.router` remains the `/warehouse` owner but imports the canonical Bales leaf. Modify `bootstrap.warehouse_bale_dependency`, `bootstrap.http_error_handlers`, and, only as required for canonical composition, `bootstrap.http_application`; all runtime imports point new. |

During this P0 phase, historical `reception_id` remained transport/persistence vocabulary. There was no canonical `BaleReceptionId`; all earlier domain/application/port/persistence aliases remained until PR6. The later alignment change supersedes this compatibility decision.

## Data Flow and Intermediate States

```text
PR4 → PR5A → PR5B → PR6
        📍      depends on 5A
old HTTP/DI ──aliases──→ canonical identity/transaction (5A runnable)
canonical HTTP/DI ─────→ canonical application + adapters (5B runnable)
```

At the PR5A boundary, HTTP/DI remained operational through bounded old-FQN aliases, using canonical identity/transaction behavior. PR5B cut HTTP/DI to canonical FQNs while aliases kept old import consumers runnable. Routing remained `POST ""` → `/bales` → `/warehouse` → `/api/v1`; one session reached both repositories and the then-current `SqlAlchemyTransaction`.

## Verification Matrix

| Slice | Required focused evidence |
|---|---|
| PR5A | Canonical/legacy class identity; UUID generation; transaction protocol; commit and rollback-on-body/commit failure; exact two constraint names translated; unknown integrity preserved; same session accepted by repositories and transaction. No ASGI cutover required. |
| PR5B | Canonical/legacy HTTP identity; exact request/collective response including `reception_id`; decimal/datetime validation; 201/409/422/500 envelopes; one route and OpenAPI operation; slash 307; canonical bootstrap imports; one request creates and shares one session across repositories/transaction. |
| PR6 | Alias/tree removal, static canonical-import/package audit, full unit suite, ASGI/OpenAPI, Supabase reset/migration list, and loopback PostgreSQL integration. |

## Workload, Rollback, and Chain

The reverted complete PR5 prototype measured **960 changed lines**. Ownership-based forecasts are **PR5A 280** and **PR5B 680** authored additions+deletions; each implementation must report its actual count. PR5A needs `size:exception` only if actual exceeds 400; PR5B is forecast above 400 and may use the maintainer-approved bounded exception. No blanket 960-line exception exists.

Sequence: `PR1 → PR2 → PR3 → PR4 → PR5A → PR5B → PR6`. PR5A rollback removes only canonical identity/transaction, their aliases, and tests, restoring PR4. PR5B rollback removes only canonical HTTP, alias conversions, bootstrap cutover, and tests, restoring runnable PR5A. PR6 rollback restores cleanup seams only.

## Threat Matrix

| Boundary | Applicability / response / RED test |
|---|---|
| HTTP routing | Applicable: exactly one POST, existing slash redirect, unchanged OpenAPI; fail on duplicate/prefix/transport drift; route, slash, OpenAPI, and contract tests in PR5B. |
| Documentation-like paths | N/A: no executable classification. |
| Git repository selection | N/A: no VCS automation. |
| Commit state | N/A: no commit automation. |
| Push state | N/A: no push automation. |
| PR commands | N/A: no PR-command integration. |

## Migration / Scope / Open Questions

No migration required. Schema, migrations, RLS/privileges, delivery/lifecycle, corrections, actors, multi-Bale delivery semantics, and API redesign remain excluded. No blocking questions.
