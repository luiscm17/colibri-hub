# Yarn EPR — Persistence Decisions

> Canonical persistence decisions for backend data design.

---

## 1. Correction and audit decisions

| Decision | Rule |
|---|---|
| Business truth | The current business record may be corrected under policy rather than replaced by append-only duplicate records. |
| Audit persistence | Every correction preserves actor, system time, reason, authorization basis when relevant, and before/after values. |
| Ownership | Each bounded context owns the correction history of its own records. |
| Storage shape | Audit follows a shared pattern, but remains persisted in separate context-owned audit tables. |

---

## 2. Identifier decisions

| Scope | Identifier | Rule |
|---|---|---|
| Warehouse | `productionIdentityId` | Internal technical ID of the Warehouse-owned production identity. |
| Warehouse raw material | `ShipmentNumber` / `shipment_number` | Business-visible identity of a `RawMaterialBatch`; globally unique. |
| Warehouse bale | Technical Bale ID plus `shipment_number` + `bale_number` | Technical identity is independent; the composite is business-visible and bale number is unique within its batch. |
| Cross-context business navigation | `lotCode` | Visible business code shared across contexts for operator recognition and traceability. |
| Lot Processing | `productionIdentityId` | Reference to the Warehouse-defined single lot identity used by every stage record. |
| Cross-context links | `productionIdentityId` and `lotCode` | The technical ID links records to the same lot; the visible code supports operator recognition and traceability. |

### Stable rule

- The Warehouse-owned `productionIdentityId` is the single technical lot identity across Warehouse and Lot Processing records.
- Visible business codes remain separate from technical IDs.
- `lotCode` does not replace `productionIdentityId`.
- If a column stores a technical identifier, name it with `_id`.
- If a column stores a visible business identifier, name it with `_code` or another explicit visible-number/code term.

---

## 3. Snapshot and reference decisions

| Area | Decision |
|---|---|
| Production identity | Snapshot business-defining descriptors such as yarn count, color requirement, destination/client, and request notes when they are part of the meaning of the identity. |
| Raw-material batch and Bale custody | `raw_material_batches` maps one header to `RawMaterialBatch`; `raw_material_bales` maps each detail to an independently identified `Bale` through `raw_material_batch_id`. Shipment number is globally unique through `uq_raw_material_batches_shipment_number`; bale number is unique within a batch through `uq_raw_material_bales_raw_material_batch_bale_number`. Bales do not link to production identities or finished-product lots. The current lifecycle is `IN_WAREHOUSE -> DELIVERED`; `ck_raw_material_bales_status` permits only the corresponding persisted values and repeat delivery is rejected. Delivery actors and timestamps are not current evidence; adding either requires a future explicit decision. |
| Lot stage records | Keep inherited references explicit and snapshot the values that the stage actually received, verified, or produced. Later-stage registration requires prior-stage completion as a use-case/domain invariant; it is not represented by cross-table database constraints across the specialized stage tables. |
| PT handoff and reception | Preserve the one permitted Quality Send marker and exact send timestamp separately from Warehouse's later acceptance. A pending handoff is that singular marker with no Warehouse receipt for the same `productionIdentityId`; it needs no timestamp tie-breaker. Warehouse verifies the existing route-sheet facts and records acceptance, presentation, and differences; it does not duplicate quality state, lot weight, bag count, or unit count. |
| Shared catalogs | Keep only references when the catalog remains authoritative and the historical wording is not itself business evidence. |

### Stable rule

- Snapshot values that preserve historical meaning, evidence, or operator-readable context.
- Keep only references where canonical lookup data remains authoritative and current synchronization matters more than historical wording.
- Catalog changes must not silently rewrite past business facts.

---

## 4. Physical duration decision

Physical entry/exit timestamp pairs are not persisted for Lot Processing interventions. The current model records business date, shift, responsible actors, and system timestamps. A physical-duration model is deferred until the business defines the start and end events, capture responsibility, and intended operational use.

---

## Related documents

- [Backend Architecture](../backend.md)
- [Backend Technical Design Baseline](./backend-technical-design.md)
- [Persistence Design Principles](./persistence-design-principles.md)
