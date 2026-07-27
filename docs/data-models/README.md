# Data Models

Conceptual data models for the Colibri Hub system.

## Conceptual Dictionaries

> **⚠️ These represent planned or exploratory structures. They do NOT represent the implemented database schema.** For the authoritative schema, see [backend/docs/database/](../../backend/docs/database/).

For detailed information about each context's conceptual model, see the [conceptual models directory](conceptual/).

| Context | Dictionary |
| --- | --- |
| Access Control | [access-dictionary.md](conceptual/access-dictionary.md) |
| Batch Processing (Lot Processing) | [batch-processing-dictionary.md](conceptual/batch-processing-dictionary.md) |
| Shared Catalogs | [catalogs-dictionary.md](conceptual/catalogs-dictionary.md) |
| Yarn Production | [yarn-production-dictionary.md](conceptual/yarn-production-dictionary.md) |

## Implemented Schema

The Warehouse context has an implemented schema documented at [`backend/docs/database/warehouse-schema.md`](../../backend/docs/database/warehouse-schema.md), derived from applied Supabase migrations.

## Future

New DBML relational diagrams aligned with current PRDs will be created as contexts are designed for implementation.
