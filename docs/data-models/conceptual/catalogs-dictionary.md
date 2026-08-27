---
document_type: conceptual-model
status: active
implementation: not-started
scope: catalogs/shared-reference-data
authority: conceptual
owner: architecture
last_reviewed: 2026-07-27
---

# Catalogs DB Dictionary

This dictionary is a concise review aid for the current Catalogs DBML. Catalogs is intentionally minimal: it defines shared operational identities only when they are already justified by multiple records or contexts.

## Review focus

- This is not a generic catalog, vocabulary, or metadata framework.
- `yarn_counts` is included because Yarn Production records repeatedly select a yarn count identity.
- Yarn count characteristics belong to the yarn count identity, not to every operational record.
- Operational records should reference `yarn_count_id` by default and avoid duplicating title/material/dtex snapshots unless a future historical-evidence case requires it.

## Tables

### `yarn_counts`

Represents a shared yarn count/title identity and its stable business characteristics.

| Field | Why it exists | Optional / challenge later |
| --- | --- | --- |
| `yarn_count_id` | Technical identifier referenced by operational records. | No. |
| `notation_spinning` | Yarn Spinning designation shown in the Hilatura UI/context, such as `1/4`. | No; exact formatting rules may be defined later. |
| `material_type` | Material characteristic of the yarn count identity. | No; keep as simple text until fixed material choices are proven necessary. |
| `dtex` | Technical linear-density characteristic when known or needed. | Yes. |
| `notation_lot` | Lot Processing designation for the same identity, such as `2/4`. | Yes; absent when Lot Processing has no separate notation. |
| `is_active` | Allows disabling selection for new records without deleting history. | No. |
| `created_at`, `updated_at` | System capture and last update timestamps. | Created no; updated yes. |

## Out of scope for this pass

- Generic catalog item tables.
- Catalog types, vocabulary engines, or dynamic attribute schemas.
- Separate material-type catalogs until the business proves they are shared identities.
