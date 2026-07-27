# Conceptual Data Models

> **⚠️ These models represent exploratory or planned structures. They do NOT represent the implemented database schema.**
>
> For the authoritative schema documentation derived from current migrations, see [`backend/docs/database/`](../../../backend/docs/database/).

These DBML files document conceptual designs for each bounded context in the Colibri Hub system. They serve as communication and planning aids for the team, capturing intended data structures before or alongside implementation. The implemented schema is defined exclusively by Supabase migrations under `supabase/migrations/`.

## Models

| Context | Dictionary |
| --- | --- |
| Access Control | [access-dictionary.md](access-dictionary.md) |
| Batch Processing (Lot Processing) | [batch-processing-dictionary.md](batch-processing-dictionary.md) |
| Shared Catalogs | [catalogs-dictionary.md](catalogs-dictionary.md) |
| Warehouse | — (promoted to [warehouse-schema.md](../../../backend/docs/database/warehouse-schema.md)) |
| Yarn Production | [yarn-production-dictionary.md](yarn-production-dictionary.md) |

> **Note:** DBML source files were retired from the active tree. Git history preserves them. The dictionaries above describe the conceptual structure for each context.

> **Note:** The warehouse dictionary has been promoted to authoritative schema documentation at [`backend/docs/database/warehouse-schema.md`](../../../backend/docs/database/warehouse-schema.md) since its content reflects the implemented migrations.
