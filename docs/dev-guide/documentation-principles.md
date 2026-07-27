# Documentation Principles

## Core Rule: Business Vocabulary Only

All **Core Documentation** uses exclusively the business vocabulary defined in the "Canonical English term for docs" column of the [Ubiquitous Language](../domain/ubiquitous-language.md) document.

Code-level names — class names, snake_case field names, enum values, type annotations, and layer conventions — belong **only** in Implementation Specs and in the Ubiquitous Language document itself (which serves as the sole bridge between business and code vocabulary).

---

## Document Classification

### Core Documentation (business vocabulary only)

| Path | Content |
| --- | --- |
| `docs/prd/**/*.md` | Product Requirements Documents — business rules, acceptance criteria, flows |
| `docs/architecture/*.md` (excluding `decisions/`) | Architecture narratives — context map, system overview, technology baseline |
| `docs/domain/*.md` (excluding `ubiquitous-language.md`) | Domain maps — bounded context models, concept definitions, boundaries |

### Implementation Specs (code names permitted)

| Path | Content |
| --- | --- |
| `backend/docs/**` | Backend technical specifications, schema docs, API contracts |
| `frontend/docs/**` | Frontend technical specifications, component docs |
| `.kiro/specs/**` | Feature implementation specs tied to a specific change |

### Exempt from this rule

| Path | Reason |
| --- | --- |
| `docs/architecture/decisions/*.md` | ADRs document code-level decisions by nature |
| `docs/domain/ubiquitous-language.md` | The naming bridge — it must contain both business and code terms |

---

## What This Means in Practice

### In Core Documentation, use:

- "raw-material batch" — not `RawMaterialBatch`
- "shipment number" — not `shipment_number`
- "In Warehouse" / "Delivered" — not `IN_WAREHOUSE` / `DELIVERED` or `in_warehouse` / `delivered`
- "gross weight" — not `gross_weight_kg`
- "production identity" — not `production_identity_id`
- "lot code" — not `lot_code` or `lotCode`
- "text, up to 10 characters" — not `String(10)` or `varchar(10)`
- "numeric (decimal precision)" — not `Decimal` or `NUMERIC`

### In Core Documentation, do NOT include:

- Layer conventions ("persistence uses lowercase; domain uses uppercase constants")
- Type annotations in attribute tables (`String(10)`, `Decimal`, `UUID`)
- Class or aggregate names as parenthetical clarifications (`(`RawMaterialBatch`)`)
- Method or command names (`deliver()`, `ReceiveBales`)
- Database column names or API field names in backtick formatting

### Before / After Example

**Before (code-coupled PRD attribute table):**

| Attribute | Type | Required | Description |
| --- | --- | --- | --- |
| `shipment_number` | String(10) | Yes | Globally unique batch identifier |
| `gross_weight_kg` | Decimal | Yes | Gross weight in kilograms |

**After (business-vocabulary PRD attribute table):**

| Attribute | Format | Required | Description |
| --- | --- | --- | --- |
| Shipment number | text, up to 10 characters | Yes | Globally unique batch identifier |
| Gross weight | numeric (decimal precision), in kilograms | Yes | Gross weight of the bale |

---

## How to Find the Correct Business Term

1. Look up the code term in the [Ubiquitous Language](../domain/ubiquitous-language.md) "Canonical code term" column.
2. Use the corresponding value from the "Canonical English term for docs" column.
3. If the term is not listed, use a space-separated English phrase derived from the identifier (e.g., `physical_presentation` → "physical presentation") and consider adding it to the ubiquitous language for future stability.

---

## Why This Matters

- **Longevity**: Core Documentation should remain valid even if the codebase is refactored, renamed, or rewritten in a different language.
- **Readability**: A product owner or new team member should be able to read a PRD without needing to understand code naming conventions.
- **Single source of truth**: The ubiquitous language is the ONE place where business terms map to code terms. Duplicating that mapping inside PRDs creates drift.
- **Separation of concerns**: Business rules define WHAT the system must do. Technical specs define HOW. Mixing them creates documents that are too coupled to be useful as either.
