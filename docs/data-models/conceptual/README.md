# Conceptual Data Models

> **⚠️ These models represent exploratory or planned structures. They do NOT represent the implemented database schema.**
>
> For the authoritative schema documentation derived from current migrations, see [`backend/docs/database/`](../../../backend/docs/database/).

These DBML files document conceptual designs for each bounded context in the Colibri Hub system. They serve as communication and planning aids for the team, capturing intended data structures before or alongside implementation. The implemented schema is defined exclusively by Supabase migrations under `supabase/migrations/`.

## Models

| Context | Model | Dictionary |
| --- | --- | --- |
| Access Control | [access.dbml](../../db/access.dbml) | [access-dictionary.md](access-dictionary.md) |
| Batch Processing (Lot Processing) | [batch-processing.dbml](../../db/batch-processing.dbml) | [batch-processing-dictionary.md](batch-processing-dictionary.md) |
| Shared Catalogs | [catalogs.dbml](../../db/catalogs.dbml) | [catalogs-dictionary.md](catalogs-dictionary.md) |
| Warehouse | [warehouse.dbml](../../db/warehouse.dbml) | — |
| Yarn Production | [yarn-production.dbml](../../db/yarn-production.dbml) | [yarn-production-dictionary.md](yarn-production-dictionary.md) |

> **Note:** The warehouse dictionary has been promoted to authoritative schema documentation at [`backend/docs/database/warehouse-schema.md`](../../../backend/docs/database/warehouse-schema.md) since its content reflects the implemented migrations.
