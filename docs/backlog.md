---
document_type: backlog
status: active
scope: global
authority: explanatory
owner: product
last_reviewed: 2025-06-21
---

# Product Backlog

Items migrated from Core Documentation during the temporal-content cleanup.
These are acknowledged enhancement ideas — not commitments, not scheduled work.

## Warehouse — Bale Management

| # | Item | Impact | Source |
|---|------|--------|--------|
| 1 | Delivery actors: record who delivers and who receives | Audit trail completeness | [bale-management.md §9.2](./prd/warehouse/bale-management.md#92-delivery-exclusions) |
| 2 | Controlled reversal (Delivered → In Warehouse) with authorization and audit requirements | State machine design and correction policy | [bale-management.md §8.3](./prd/warehouse/bale-management.md#83-reversibility) |
| 3 | Post-registration correction: how to correct errors in already-registered batches (typos, wrong weights) | Edit policy, audit requirements, and correction window rules | [bale-management.md §8.3](./prd/warehouse/bale-management.md#83-reversibility) |
| 4 | Multi-bale delivery atomicity: atomic (all-or-nothing) vs. individual delivery | Multi-bale delivery command design | [bale-management.md §9.2](./prd/warehouse/bale-management.md#92-delivery-exclusions) |
| 5 | Transport fields: truck number, license plate, or driver on batch header | Reception contract | [bale-management.md §7.4](./prd/warehouse/bale-management.md#74-transport-fields) |
| 6 | Provider catalog: managed supplier catalog vs. free text | Data quality and validation | [bale-management.md §5.1](./prd/warehouse/bale-management.md#51-raw-material-batch-attributes) |
| 7 | Material type catalog: managed catalog vs. free text with normalization | Data quality and validation | [bale-management.md §5.2](./prd/warehouse/bale-management.md#52-bale-attributes) |

## Warehouse — Production Identity

| # | Item | Impact | Source |
|---|------|--------|--------|
| 1 | Lot code format: define format rules for the production identifier (length, allowed characters, prefix conventions) | Validation rules | [finished-product.md §5.3](./prd/warehouse/finished-product.md#53-identity-and-requirement-rules) |
| 2 | Catalog references: determine whether client, color, or title should reference managed catalogs | Data quality and validation | [finished-product.md §5.2](./prd/warehouse/finished-product.md#52-requirement-data) |
| 3 | Link to bales: allow explicit linking of specific bales to a production identity | Delivery flow and traceability | [finished-product.md §5.3](./prd/warehouse/finished-product.md#53-identity-and-requirement-rules) |

## Warehouse — Finished Product

| # | Item | Impact | Source |
|---|------|--------|--------|
| 1 | Availability catalog detail: define transition rules between availability states | State machine design | [finished-product.md §7.3](./prd/warehouse/finished-product.md#73-availability-catalog) |
| 2 | Return reclassification: determine whether returned PT requires a new classification review or can revert to its prior classification | Return flow and availability logic | [finished-product.md §9](./prd/warehouse/finished-product.md#9-pt-returns) |
| 3 | Partial dispatch: determine whether partial dispatch of a lot is supported or dispatch is always the full lot | Dispatch granularity | [finished-product.md §8](./prd/warehouse/finished-product.md#8-pt-dispatch) |

## Warehouse — Production Supplies

| # | Item | Impact | Source |
|---|------|--------|--------|
| 1 | Supply catalog: determine whether supply items reference a managed catalog or remain free text | Data quality and reporting | [production-supplies.md §4](./prd/warehouse/production-supplies.md#4-supply-categories) |
| 2 | Stock levels and alerts: determine whether the system maintains running stock levels per item and triggers alerts | Inventory visibility | [production-supplies.md §8](./prd/warehouse/production-supplies.md#8-supplies-dashboard-and-query-capabilities) |
| 3 | Batch/lot tracking for supplies: determine whether certain supplies (dyes, chemicals) track supplier batch numbers for quality traceability | Traceability depth | [production-supplies.md §6](./prd/warehouse/production-supplies.md#6-supply-movement-data) |

## Product Overview

| # | Item | Impact | Source |
|---|------|--------|--------|
| 1 | Supplies detail (Dyeing + Packaging): defined but not yet covered | Warehouse module must cover all 4 subdomains | [product-overview.md §3](./prd/product-overview.md#3-business-areas) |
| 2 | Commercialization integration: define boundary and output format for finished product handoff | Inter-context boundary definition | [product-overview.md §7](./prd/product-overview.md#7-architecture-and-context-boundaries) |
| 3 | Production Manager bottleneck risk: dashboard UX must be immediate, not demanding | UX design and interaction load | [product-overview.md §3](./prd/product-overview.md#3-business-areas) |
| 4 | Adoption risk: UX must prioritize simplicity for users migrating from Excel and paper | UX design and onboarding | [product-overview.md §4](./prd/product-overview.md#4-actors) |
| 5 | Historical data migration: data in Excel, papers, various spreadsheets requires separate plan | Data migration planning | [product-overview.md §2](./prd/product-overview.md#2-scope) |


## Operation — Yarn Spinning

| # | Item | Impact | Source |
|---|------|--------|--------|
| 1 | Granularidad exacta de datos por máquina en Bobinados: confirmar si el registro body/km/cortes se captura por descarga, por máquina/turno o por otro corte operativo | Record granularity design for Winding quality | [yarn-spinning.md §3](./prd/operation/yarn-spinning.md#3-production-records) |
| 2 | Frecuencia exacta de muestreo aleatorio: definir la frecuencia mínima de pruebas aleatorias en Continua y Retorcido (ej. N pruebas por semana, o por cada N kg producidos) | Quality sampling frequency policy | [yarn-spinning.md §5](./prd/operation/yarn-spinning.md#5-process-quality) |
