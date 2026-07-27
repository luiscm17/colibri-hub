# Conceptual Data Models

> **⚠️ These are conceptual dictionaries only — not the implemented schema.**
>
> For the authoritative schema derived from current migrations, see [`backend/docs/database/`](../../../backend/docs/database/).

## Current State

The DBML relational diagram files were retired from the active tree (Git history preserves them). The conceptual dictionaries below describe planned data structures for contexts not yet implemented. They are **referential only** and may diverge from what is eventually built.

New DBML files aligned with the current PRDs will be created in a future phase.

## Dictionaries

| Context | Dictionary | Implementation Status |
| --- | --- | --- |
| Access Control | [access-dictionary.md](access-dictionary.md) | Not started |
| Batch Processing (Lot Processing) | [batch-processing-dictionary.md](batch-processing-dictionary.md) | Not started |
| Shared Catalogs | [catalogs-dictionary.md](catalogs-dictionary.md) | Not started |
| Yarn Production | [yarn-production-dictionary.md](yarn-production-dictionary.md) | Not started |

## Warehouse

The Warehouse context has an implemented schema. Its documentation lives at [`backend/docs/database/warehouse-schema.md`](../../../backend/docs/database/warehouse-schema.md) and is derived from the applied Supabase migration — not from the former conceptual DBML.
