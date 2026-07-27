# Data Models

Conceptual and reference data models for the Colibri Hub system.

## Conceptual Models

> **⚠️ These models represent exploratory or planned structures. They do NOT represent the implemented database schema.** For the authoritative schema, see [backend/docs/database/](../../backend/docs/database/).

For detailed information about each model, see the [conceptual models directory](conceptual/).

| Context | Dictionary |
| --- | --- |
| Access Control | [access-dictionary.md](conceptual/access-dictionary.md) |
| Batch Processing (Lot Processing) | [batch-processing-dictionary.md](conceptual/batch-processing-dictionary.md) |
| Shared Catalogs | [catalogs-dictionary.md](conceptual/catalogs-dictionary.md) |
| Warehouse | — (promoted to [warehouse-schema.md](../../backend/docs/database/warehouse-schema.md)) |
| Yarn Production | [yarn-production-dictionary.md](conceptual/yarn-production-dictionary.md) |

> **Note:** DBML source files were retired from the active tree. Git history preserves them. The dictionaries above describe the conceptual structure for each context.

> **Note:** The warehouse dictionary has been promoted to authoritative schema documentation at [`backend/docs/database/warehouse-schema.md`](../../backend/docs/database/warehouse-schema.md) since its content reflects the implemented migrations.
