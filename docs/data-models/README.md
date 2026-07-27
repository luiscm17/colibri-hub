# Data Models

Conceptual and reference data models for the Colibri Hub system.

## Conceptual Models

> **⚠️ These models represent exploratory or planned structures. They do NOT represent the implemented database schema.** For the authoritative schema, see [backend/docs/database/](../../backend/docs/database/).

For detailed information about each model, see the [conceptual models directory](conceptual/).

| Context | Model | Dictionary |
| --- | --- | --- |
| Access Control | [access.dbml](../db/access.dbml) | [access-dictionary.md](conceptual/access-dictionary.md) |
| Batch Processing (Lot Processing) | [batch-processing.dbml](../db/batch-processing.dbml) | [batch-processing-dictionary.md](conceptual/batch-processing-dictionary.md) |
| Shared Catalogs | [catalogs.dbml](../db/catalogs.dbml) | [catalogs-dictionary.md](conceptual/catalogs-dictionary.md) |
| Warehouse | [warehouse.dbml](../db/warehouse.dbml) | — |
| Yarn Production | [yarn-production.dbml](../db/yarn-production.dbml) | [yarn-production-dictionary.md](conceptual/yarn-production-dictionary.md) |

> **Note:** The warehouse dictionary has been promoted to authoritative schema documentation at [`backend/docs/database/warehouse-schema.md`](../../backend/docs/database/warehouse-schema.md) since its content reflects the implemented migrations.
