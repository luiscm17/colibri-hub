---
document_type: domain
status: active
implementation: partial
scope: global
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# Ubiquitous Language — Naming Contract

This document defines the **canonical English naming contract** for architecture, code, APIs, database design, and cross-team technical discussions.

It is intentionally **small and stable**. It does **not** try to translate every business term in the system. It only covers terms that are easy to mistranslate, easy to overload, or likely to cause bad code names.

---

## Scope

Use this document when naming:

- bounded contexts and modules
- entities, value objects, enums, and state fields
- API contracts and DTOs
- database tables and columns
- frontend feature areas and technical artifacts

If a term is not listed here, keep the nearest existing architecture/PRD wording unless a later naming decision explicitly replaces it.

This document is a **naming contract only**. It does **not** define:

- bounded-context ownership
- lifecycle timing
- persistence strategy
- internal identifier strategy
- workflow state rules

For full business rules, attribute definitions, validation constraints, and acceptance criteria, refer to the normative PRD for the relevant capability (e.g., [Bale Management PRD](../prd/warehouse/bale-management.md)).

---

## Canonical terms

| Spanish term | Business meaning | Canonical English term for docs | Canonical code term | Avoid / notes |
| --- | --- | --- | --- | --- |
| `fardo` | Raw-material unit received from suppliers before any production lot exists | **bale** | `bale` | Avoid `bundle` or `lot`. A `fardo` is not a production lot. |
| `partida de materia prima` | Supplier shipment grouping one or more bales and their shared evidence/characteristics | **raw-material batch** | `RawMaterialBatch` | Identified by `ShipmentNumber`. Never use it for a production lot/batch. |
| `número de envío` | Business-visible identifier of a raw-material batch | **shipment number** | `ShipmentNumber` | Transport and persistence expose `shipment_number`. Globally unique across all batches. |
| `número de fardo` | Bale identifier within a batch | **bale number** | `bale_number` | Unique within its parent batch only; the same bale number is valid in different batches. |
| `recepción de fardos` | Application action that registers one complete raw-material batch and one or more bales | **receiving action** | `ReceiveBales` or `RegisterRawMaterialBatch` | Reception is a business act, not a domain aggregate. Do not model `Reception` or `BaleReception` as an entity. |
| `entrega de fardos a Producción` | Custody transfer of one or more independently loaded bales from Warehouse to Production | **delivery to Production** | `DeliverBales` | Delivery means the bale has been delivered to and used by Production. Binary irreversible fact. |
| `en Almacén` | Bale remains under Warehouse custody | **in Warehouse** | `IN_WAREHOUSE` | Bale lifecycle state. Persistence/API: `in_warehouse`. |
| `entregado` | Bale has been physically transferred to Production. The system assumes immediate use upon delivery — delivery is the terminal fact. The system does not model or verify subsequent processing stages. | **delivered** | `DELIVERED` | Bale lifecycle state. Persistence/API: `delivered`. Delivery is the terminal recorded fact; no post-delivery states exist. |
| `fecha de recepción` | Calendar date when the physical reception occurred | **reception date** | `received_at` | A business date (no time component). Not the system creation timestamp. |
| `tipo de material` | Raw-material classification for a bale | **material type** | `material_type` | Normalized to uppercase before persistence. |
| `dtex` | Linear density of the raw material | **dtex** | `dtex` | Decimal, finite, greater than zero. |
| `peso bruto` | Gross weight of a bale in kilograms | **gross weight** | `gross_weight_kg` | Decimal, finite, greater than zero. User-provided at reception. |
| `peso de envase` | Tare/container weight of a bale in kilograms | **container weight** | `container_weight_kg` | Decimal, finite, greater than zero, must be less than gross weight. |
| `peso neto` | Net weight of a bale (gross minus tare) | **net weight** | `net_weight_kg` | Always derived (`gross_weight_kg - container_weight_kg`). Never persisted or accepted as input. |
| `título` | Textile count/thickness designation of the yarn, such as `2/18` or `2/32` | **yarn count** | `yarnCount` | Avoid bare `title`; it is overloaded in software and weak in English. Keep `title` only when quoting legacy business wording. |
| `lote` | Physical batch tracked through Lot Processing and later Warehouse continuity | **lot** | `lot` | Use only for the physical batch, not for upstream raw-material reception. |
| `identidad de producción` | Business identity used across contexts before and during production flow | **production identity** | `productionIdentity` | Keep distinct from `lot`. |
| `código de lote` | Visible shared identifier used by business users to track a lot | **lot code** | `lotCode` | Visible business code only. Technical identifier rules belong in persistence docs. |
| `madeja` | Skein output from Madejeras and input to lot assembly | **skein** | `skein` | Avoid leaving `madeja` in new code unless integrating with external/local terminology that must stay Spanish. |
| `devanado` | Conversion of skeins into cones for the industrial format | **winding** | `winding` | Avoid translating both `devanado` and `ovillado` as `winding`; they are different stages/variants. |
| `ovillado` | Conversion of skeins into yarn balls for direct-sale format | **ball winding** | `balling` | Avoid generic `winding`. Use a distinct term because it produces balls, not cones. |
| `embolsado` | Bagging/packing stage after winding or balling | **bagging** | `bagging` | Avoid `packaging` for the stage name unless talking about the broader packaging domain. |
| `avance` | Section-level summary record of inputs, outputs, and flow in Yarn Spinning | **progress record** | `progress` | Avoid the false friend `advance` in code. Use `progress` for the record family. |
| `descarga` | One machine-level production output event within a shift | **production discharge** | `discharge` | Avoid `download`, `unload`, or `shipment`. In this domain it is a production event. |
| `desperdicio` | Material loss or discard recorded by context/stage | **waste** | `waste` | Use qualifiers when needed: `realWaste`, `accumulatedWaste`, `theoreticalWaste`. |
| `observado` | Product or lot with documented issues that require review or conditional handling | **flagged** | `flagged` | Avoid literal `observed`; in code, qualify if needed (`flaggedLot`, `flaggedProduct`). |
| `defectuoso` | Product classified as significantly defective in Warehouse handling | **defective** | `defective` | Keep separate from `waste`; in code, qualify if needed (`defectiveLot`, `defectiveProduct`). |
| `disponibilidad` | Warehouse readiness for use, distribution, or release | **availability state** | `availabilityState` | Do not use this as a synonym for stock quantity. In code, prefer qualified names such as `lotAvailabilityState`, `productAvailabilityState`, or `warehouseAvailabilityState` when ambiguity is possible. |
| `presentación` | Physical form in which PT is stored or handled, such as bagged/bulk or cone/ball form | **physical presentation** | `physicalPresentation` | Prefer `physicalPresentation` in code and schemas; avoid generic `presentation`. |
| `Inventario` (rol / etapa en Operación) | Operational role and first stage in Lot Processing where the physical lot is assembled | **Inventory stage / Inventory operator** | `inventoryStage`, `inventoryOperator` | Never use bare `inventory` to mean Warehouse stock in the same model. |
| `inventario` / `existencias` (Almacén) | Warehouse stock, balances, and custody quantities | **stock** | `stock` | Prefer `stock` for Warehouse quantities. Reserve `inventory` for the Operation role/stage or clearly qualified technical names. |
| `envío de calidad` | Domain event: Quality completes inspection and sends the lot toward Warehouse. Mandatory, unilateral, irrevocable once the 6 stages are complete. The lot ALWAYS goes to Warehouse regardless of quality classification. | **Quality Send** | `qualitySend` | Avoid "approval", "Quality approval", "Warehouse delivery". Quality Send is documentation and handoff, not a gate. |
| `en espera de validación de Almacén` | Intermediate lot state between Quality Send and Warehouse reception. The lot has been sent but Warehouse has not yet registered physical receipt. | **awaiting Warehouse receipt** | `awaitingWarehouseReceipt` | Avoid "pending validation", "en espera de validación". |

---

## Canonical section and stage names

Use these names for **operation section/stage identifiers** so process names stay stable across docs, code, APIs, and tables.

| Spanish name in business docs | Scope | Canonical English name for docs | Canonical code term | Avoid / notes |
| --- | --- | --- | --- | --- |
| `Preparación` | Yarn Spinning section | **Preparation** | `preparation` | Keep the Spanish business label visible in PRDs when useful, but do not shorten to `prep` in shared models. |
| `Continuas` | Yarn Spinning section | **Ring Spinning** | `ringSpinning` | Avoid literal `continuous` / `continuing`; the business section maps to ring spinning. |
| `Bobinados` | Yarn Spinning section | **Bobbin Winding** | `bobbinWinding` | Avoid bare `winding`; that would collide with `Devanado`. Keep `Bobinados` visible in docs when referring to the plant section name. |
| `Retorcido` | Yarn Spinning section | **Twisting** | `twisting` | Avoid `twisted` as a stage name. |
| `Madejeras` | Yarn Spinning section | **Madejeras (`Skeining`)** | `skeining` | Keep **Madejeras** visible in docs because it is the plant section name. Use `skeining` in code. |
| `Inventario` | Lot Processing stage | **Inventory stage** | `inventoryStage` | Do not reuse this for Warehouse stock. If a very local enum already sits inside Lot Processing, `inventory` is acceptable only when no stock collision exists. |
| `Tintorería` | Lot Processing stage | **Dyeing** | `dyeing` | Avoid `tinting`; it is the wrong production term here. |
| `Secado` | Lot Processing stage | **Drying** | `drying` | Keep it distinct from generic completion or cooldown states. |
| `Devanado` | Lot Processing stage / variant | **Winding** | `winding` | This is the canonical `winding` term in Lot Processing. Do not reuse `winding` for `Bobinados`. |
| `Ovillado` | Lot Processing stage / variant | **Ball Winding** | `balling` | Keep separate from `Devanado`; they produce different physical presentations. |
| `Embolsado` | Lot Processing stage | **Bagging** | `bagging` | Avoid `packaging` as the stage name unless discussing the broader packaging domain. |
| `Calidad` (función de proceso) | Cross-section or in-process quality control activity | **Process Quality** | `processQuality` | Use for quality records inside Yarn Production / in-process control. |
| `Calidad` (etapa final de lote) | Final stage where the lot is inspected before handoff to Warehouse | **Quality stage** | `lotQuality` | Use for the final Lot Processing stage and its outcome. |

---

## Intentional distinctions

### Yarn count vs title

- In business conversations, people may still say **título**.
- In technical English artifacts, prefer **yarn count**.
- In code, prefer `yarnCount`.

### Inventory vs stock

- In **Lot Processing**, `inventoryStage` and `inventoryOperator` are valid.
- In **Warehouse**, balances and custody should prefer **stock** terminology.

This is a hard rule to avoid one of the worst naming collisions in the current docs.

### Raw-material batch vs production lot

- `RawMaterialBatch` groups supplier-shipment bales before production and is identified by `ShipmentNumber`.
- `Bale` has independent technical identity and owns the `in_warehouse` → `delivered` lifecycle; its business-visible identity is `shipment_number` + `bale_number`.
- A production `lot` belongs to the later production flow. It is never a synonym for `RawMaterialBatch`.
- Receiving is an application action, not a `Reception` aggregate.

### Delivery meaning

- `delivered` = delivered to and used by Production. Binary irreversible fact.
- It does **not** assert consumption, processing, or assignment to a production identity.
- What Production does with the bale after delivery is outside Warehouse scope.

### Bale lifecycle states

- `in_warehouse` / `delivered` are the only canonical states.
- The transition is `in_warehouse → delivered` (one-way).
- No reversal mechanism exists. Controlled reversal requires a separate capability following the correction policy.
- Layer conventions: persistence/API use lowercase (`in_warehouse`, `delivered`); domain code uses uppercase enum constants (`IN_WAREHOUSE`, `DELIVERED`).

### Availability state vs stock

- **availabilityState** = Warehouse operational readiness for release or distribution.
- **stock** = Warehouse quantities and balances.

Do not use `availability` as a synonym for `stock`.

### Process quality vs lot quality

- **processQuality** = quality control during the process, usually by section or machine.
- **lotQuality** = final quality evaluation of the lot before handoff to Warehouse.

They are not interchangeable and should not share one generic code term.

### Stage names vs action names

When a process term can mean both a **stage/section** and an **action**, keep
the naming roles separate:

- use the **noun form** for the stage or section name
- use the **verb form** for the command/use case name
- use a **result/state form** only when a resulting condition must be modeled explicitly

Examples:

- `bagging` = stage, `bagLot` = action, `bagged` = result/state when needed
- `winding` = stage, `windLot` = action
- `dyeing` = stage, `dyeLot` = action
- `drying` = stage, `dryLot` = action

This prevents one term from carrying section, command, and status meanings at the same time.

---

## How to use this contract

### Architecture

- Use the **canonical English term for docs** in architecture narratives.
- When a distinction is boundary-critical, prefer the fuller phrase even if code stays shorter.

### Backend

- Use the **canonical code term** for entities, fields, enums, ports, repositories, and module-internal names.
- If a field lives in a broad/shared schema or the term is too generic on its own, qualify it with its domain meaning instead of inventing a synonym.

### Frontend

- Use the same code terms for feature modules, API clients, and state models.
- UI copy may follow business wording, but internal model names should still follow this contract.

### Database

- Prefer stable noun-based names from the **canonical code term** column.
- Do not encode Spanish synonyms and English synonyms for the same concept in different tables or columns.
- When a canonical term is too broad on its own, qualify it by domain meaning instead of using a vague short form.

---

## Non-goals

- This is not a full business glossary.
- This does not replace the PRDs.
- This does not redefine bounded-context ownership.
- This does not define technical IDs, database references, or persistence rules.
- This does not define validation constraints, attribute types, or acceptance criteria — those live in the normative PRDs.

It only stabilizes naming so later design and implementation stop drifting.

---

## References

- [Bale Management PRD](../prd/warehouse/bale-management.md) — normative source for bale-related business rules, attributes, and acceptance criteria
- [Warehouse Domain Map](warehouse.md) — domain model and boundaries for the Warehouse context
