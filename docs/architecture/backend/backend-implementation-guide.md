# Yarn EPR — Backend Implementation Guide

> **SUPERSEDED / HISTORICAL:** This guide predates the current backend,
> migration, and approved `RawMaterialBatch`/`Bale` model. Do not use its
> Alembic, async SQLAlchemy, in-memory CRUD, generic CRUD, single-Bale POST,
> package-tree, or phased implementation instructions for current work.
>
> Current Warehouse implementation work must follow, in authority order:
> [Warehouse PRD](../../prd/warehouse.md),
> [Warehouse functional records](../../prd/warehouse/warehouse-records.md),
> [Architecture](../ARCHITECTURE.md),
> [Backend Architecture](../backend.md), and
> [`backend/docs/task.md`](../../../backend/docs/task.md).
> The current public registration operation remains collective
> `POST /api/v1/warehouse/bales`; Supabase migrations, not Alembic or DBML,
> define the implemented schema. The historical body below is retained only as
> provenance and is non-normative.

> **Hoja de ruta operativa** para implementar el backend por fases.
> No contiene código para copiar y pegar. Contiene decisiones, estructura, contratos
> y el orden exacto de cada paso.
>
> Fuentes: [Architecture](../ARCHITECTURE.md), [Backend Architecture](../backend.md),
> [Backend Technical Design](./backend-technical-design.md), DBML en `docs/db/`,
> [Ubiquitous Language](../../domain/ubiquitous-language.md).

---

## Cómo usar esta guía

Cada fase produce código **funcional y testeable**. La regla es:

1. Leé la fase completa primero.
2. Codeá los archivos siguiendo las especificaciones.
3. Verificá que corre (test manual, curl, lo que prefieras).
4. Recién ahí pasá a la siguiente fase.

No hay código listo para copiar. Hay **qué crear**, **qué campos tiene**,
**qué reglas aplicar** y **qué evitar**.

---

## Part 0: Estado inicial y limpieza

### Árbol actual

```
backend/
├── auth/domain/                     # Funcional, buen DDD
│   ├── assignment.py                # Importa UserId que no existe
│   ├── check_access.py              # Pure function, correcta
│   ├── events.py                    # Importa UserId que no existe
│   ├── exception.py
│   ├── resource_type.py
│   ├── role_definition.py
│   ├── scope.py
│   ├── value_objects.py
│   └── __init__.py                  # Exports prolijos
├── shared/domain/
│   ├── user/                        # VACÍO — pero auth lo necesita
│   ├── machine/                     # VACÍO
│   ├── section/                     # VACÍO
│   └── yarn_count/
│       ├── yarn_count.py            # CLASE INCORRECTA — no alineada con DBML
│       └── value_object.py          # STUB
├── warehouse/                       # VACÍO
├── operation/                       # VACÍO (archivo dice yarn-production + batch-processing)
└── shared/base/                     # VACÍO
```

### Decisiones pre-Fase 1

| Decisión                                                          | Opción              | Recomendación                                                                                                      |
| ----------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Renombrar `auth/` → `access/`                                     | Sí / No / Después   | **Después.** Primero functionality, después names. No detener el avance por rename.                                |
| Renombrar `shared/` → `catalogs/`                                 | Sí / No / Después   | **Ídem.** Codeamos los domain objects donde están, renombramos al final.                                           |
| Renombrar `operation/` → `yarn-production/` + `batch-processing/` | Inmediato / Después | **Después**, cuando empecemos a codear esos contextos.                                                             |
| `shared/base/`                                                    | Sirve para algo?    | Base de value objects compartidos (ej. `Entity`, `ValueObject` marcadores). Opcional. Agregar solo si se necesita. |

---

## Part 1: Fase 1a — Foundation domain layer (catalogs + access fix)

### Objetivo

Que el dominio de `access` funcione sin imports rotos, y que `catalogs` tenga los
value objects y entidades compartidas que el resto del sistema necesita.

### Lo que NO hay que hacer en esta fase

- No crear endpoints
- No crear repositorios
- No crear aplicación FastAPI
- No crear tablas ni SQL
- No agregar validaciones complejas ni reglas de negocio

Solo domain objects simples con dataclasses.

---

### 1a.1 — `catalogs/domain/` — Shared value objects

#### `catalogs/domain/__init__.py`

Exportar TODO el dominio público de catalogs: `UserId`, `YarnCount`, `Machine`, `Section`, `Shift`.

#### `catalogs/domain/user.py` — UserId (CRÍTICO, auth lo necesita)

```text
UserId
├── frozen dataclass
├── value: uuid4 (default)
├── __post_init__: validar que no esté vacío
└── str: representation corta
```

Dónde se usa: `access/domain/assignment.py` y `access/domain/events.py` ya lo
importan. Una vez que existe, el import deja de romper.

#### `catalogs/domain/yarn_count.py` — Refactorizar YarnCount

La clase `Yarn` actual NO sirve. Reemplazarla por `YarnCount` alineada al DBML:

```text
YarnCount
├── frozen dataclass
├── yarn_count_id: UUID (uuid4)
├── yarn_count_code: str     # único, visible: "2/18", "2/32"
├── material_type: str       # tipo de materia prima
├── dtex: Decimal | None     # densidad lineal técnica
├── business_label: str | None  # etiqueta alternativa
├── is_active: bool          # por defecto True
└── __post_init__: yarn_count_code no vacío
```

Referencia DBML: `docs/db/catalogs.dbml` → tabla `yarn_counts`.

#### `catalogs/domain/machine.py` — Machine reference

Value object / referencia mínima:

```text
Machine
├── dataclass (no frozen aún)
├── machine_id: UUID
├── section: str              # yarn_spinning_section (preparation, ring_spinning, etc.)
├── machine_code: str         # único visible: "FIN-A"
├── machine_name: str | None
└── is_active: bool
```

Referencia DBML: `docs/db/yarn-production.dbml` → tabla `yarn_production_machines`.
Por ahora sin enum — `section` es str.

#### `catalogs/domain/section.py` — Section value object

```text
Section
├── frozen dataclass
├── section_id: UUID
├── section_code: str         # "preparation", "ring_spinning", etc.
├── display_name: str         # "Preparación", "Continuas", etc.
└── context: str              # "yarn-production" | "batch-processing"
```

#### `catalogs/domain/shift.py` — Shift value object

```text
Shift
├── frozen dataclass
├── shift_code: str           # "A", "B", "C"
└── display_name: str
```

---

### 1a.2 — Fix `access/domain/` imports

#### Qué arreglar

1. `assignment.py` — línea 6: `from catalogs.domain.user import UserId`
   (o `from shared.domain.user import UserId` si no renombramos aún)
2. `events.py` — línea 6: lo mismo
3. Verificar que todo el resto de `access/domain/` corre sin errores de import

La estructura de `access/domain/` ya está bien — entities, value objects,
domain service (`check_access`), eventos. No hay que redesignar nada.

#### Dependencia circulr que NO existe

`access` importa `catalogs.domain.user.UserId`.
`catalogs` NO importa nada de `access`.
Esto es correcto — `catalogs` es la base de todas las referencias compartidas.

---

### 1a.3 — Verificación

```bash
# Desde la raíz del proyecto
uv run --locked python -c "
from catalogs.domain.user import UserId
from catalogs.domain.yarn_count import YarnCount
from access.domain import Assignment, check_access

print('Fase 1a OK — domain objects funcionan')
print('UserId:', UserId())
print('YarnCount:', YarnCount(yarn_count_code='2/18', material_type='algodon'))
"
```

Si corre sin errores, la fase 1a está lista.

---

## Part 2: Fase 1b — In-memory CRUD para catalogs + access

### Objetivo

Tener endpoints HTTP básicos para:

- ABM de yarn counts
- ABM de usuarios
- ABM de roles
- Authorization check (un endpoint que diga "puede? sí/no")

Sin DB, sin validaciones complejas, sin autenticación real.

### Lo que NO hay que hacer en esta fase

- No crear PostgreSQL adapters
- No agregar auth middleware real
- No crear validaciones complejas
- No manejar errores de forma sofisticada

Solo repo en memoria + endpoint FastAPI básico que devuelva JSON.

---

### 1b.1 — Esqueleto FastAPI mínimo

#### `backend/main.py` — Punto de entrada único

Necesita:

- Crear la app FastAPI
- Incluir routers de cada contexto
- Config básica (título, descripción)
- Un health check endpoint: `GET /health` → `{"status": "ok"}`

#### `backend/core/config.py` (o similar)

Por ahora mínimo:

```text
class Settings:
    ├── app_name: str = "Yarn EPR"
    ├── debug: bool = True
    └── (más adelante: db_url, secret_key, etc.)
```

---

### 1b.2 — Repositorio en memoria

#### Contrato (interfaz) del repositorio

Para cada entidad, definí la interfaz que usará el endpoint.
La implementación en memoria es un dict indexado por UUID.

```text
class YarnCountRepository(ABC):
    def save(self, yarn_count: YarnCount) -> None
    def find_by_id(self, yarn_count_id: UUID) -> YarnCount | None
    def find_all(self) -> list[YarnCount]
    def delete(self, yarn_count_id: UUID) -> None
```

**Implementación: `InMemoryYarnCountRepository`**

- Atributo `_store: dict[UUID, YarnCount]`
- `save` hace upsert (inserta o reemplaza)
- `find_all` devuelve copia de los valores
- `delete` borra del dict si existe

Hacé lo mismo para:

- `UserRepository` (Id, display_name, is_active)
- `RoleRepository` (código, display_name, rank, permissions)

---

### 1b.3 — Endpoints CRUD

#### `GET /health` → `{"status": "ok", "contexts": [...]}`

#### `GET  /catalogs/yarn-counts` → listar todos

#### `GET  /catalogs/yarn-counts/{id}` → obtener uno

#### `POST /catalogs/yarn-counts` → crear (body: yarn_count_code, material_type, ...)

#### `PATCH /catalogs/yarn-counts/{id}` → actualizar (partial update)

#### `DELETE /catalogs/yarn-counts/{id}` → borrado lógico (is_active = False)

#### `GET  /access/users` → listar usuarios

#### `POST /access/users` → crear (body: user_code, display_name, role_id)

#### `GET  /access/roles` → listar roles

#### `POST /access/roles` → crear (body: role_code, display_name, rank)

#### `POST /access/check` → {assignments, resource_code, resource_domain, action} → {allowed: bool}

---

### 1b.4 — Inyección de dependencias manual

No necesitás DI framework. Un módulo `backend/core/dependencies.py` puede tener:

```python
# Singleton de repositorios en memoria
_yarn_count_repo: YarnCountRepository | None = None

def get_yarn_count_repo() -> YarnCountRepository:
    global _yarn_count_repo
    if _yarn_count_repo is None:
        _yarn_count_repo = InMemoryYarnCountRepository()
    return _yarn_count_repo
```

FastAPI usa `Depends()` para inyectar. Cuando más adelante haya repos reales,
solo cambiás la implementación — el contrato no cambia.

---

### 1b.5 — Verificación

```bash
uv run --locked uvicorn backend.main:app --reload

# Health check
curl http://localhost:8000/health

# Crear yarn count
curl -X POST http://localhost:8000/catalogs/yarn-counts \
  -H "Content-Type: application/json" \
  -d '{"yarn_count_code": "2/18", "material_type": "algodon"}'

# Listar
curl http://localhost:8000/catalogs/yarn-counts

# Check access
curl -X POST http://localhost:8000/access/check \
  -H "Content-Type: application/json" \
  -d '{"assignments": [], "resource_code": "emission", "resource_domain": "warehouse", "required_action": "create"}'
```

Todo debe responder JSON. No hay DB, no hay auth. Solo dominio + repo en memoria.

---

## Part 3: Fase 2 — Warehouse domain + CRUD básico

### Objetivo

Dominio de Warehouse: recepción de fardos y definición de identidad de producción.
Endpoints CRUD para ambas.

### Lo que NO hay que hacer en esta fase

- No implementar emisiones a producción (fase posterior)
- No implementar recepción de PT
- No implementar entregas, transferencias, devoluciones
- No implementar lógica de stock

Solo Bale + ProductionIdentity.

---

### 3a — Warehouse domain

#### `warehouse/domain/bale.py` — Bale entity

```text
Bale
├── dataclass
├── bale_id: UUID
├── bale_number: str           # única, visible
├── raw_material_type: str
├── yarn_count_label: str | None  # snapshot al recibir
├── color_or_fiber: str | None
├── receipt_number: str | None
├── business_received_at: datetime
├── supplier_name: str | None
├── received_weight_kg: Decimal
├── delivered: bool = False     # TODO: fase de emisiones cambia esto
├── received_by_user_id: UserId
├── condition_notes: str | None
└── created_at: datetime
```

No incluir aún: `delivered_at`, `delivered_by_user_id`, etc. — eso viene con emisiones.

#### `warehouse/domain/production_identity.py` — ProductionIdentity entity

```text
ProductionIdentity
├── dataclass
├── production_identity_id: UUID
├── lot_code: str                # única, visible
├── yarn_count_id: UUID          # referencia a catalogs
├── required_color: str | None
├── destination_name: str | None
├── production_variant: str | None
├── request_notes: str | None
├── business_defined_at: datetime
├── defined_by_user_id: UserId
├── authorized_by_user_id: UserId | None
└── created_at: datetime
```

Referencia DBML: `docs/db/warehouse.dbml` → tablas `raw_material` y `production_identities`.
Notar que en DBML la tabla `raw_material` tiene más campos (delivered, etc.) que
irán apareciendo en fases posteriores.

#### `warehouse/domain/__init__.py`

Exportar `Bale`, `ProductionIdentity`.

---

### 3b — Warehouse repos + endpoints

Repositorios en memoria:

- `BaleRepository`: save, find_by_id, find_all, delete (lógico)
- `ProductionIdentityRepository`: save, find_by_id, find_all, delete (lógico)

Endpoints:

```
GET    /warehouse/bales
GET    /warehouse/bales/{id}
POST   /warehouse/bales                 # Recibir fardo
PATCH  /warehouse/bales/{id}            # Corregir datos del fardo

GET    /warehouse/production-identities
GET    /warehouse/production-identities/{id}
POST   /warehouse/production-identities  # Definir identidad
PATCH  /warehouse/production-identities/{id}
```

---

## Part 4: Fase 3 — Yarn Production domain + CRUD básico

### Objetivo

Dominio de hilandería: descargas, progreso, calidad de proceso, desperdicio, madejas.
Sin lotes, sin timeline de lotes — solo registros continuos.

### Lo que NO hay que hacer en esta fase

- No hay entidad "lote" ni "stage"
- No hay relación con batch-processing todavía
- No implementar reglas de reconciliación (descarga vs progreso)

Solo CRUD básico de cada familia de registros.

---

### 4a — Yarn Production domain

Referencia DBML: `docs/db/yarn-production.dbml`.

Entidades (una por tabla DBML, con los campos principales):

- `ProductionDischarge` — descarga por máquina/turno/título
- `SkeinRecord` — registro de madejeras
- `ProgressRecord` — avance de sección
- `ProcessQualityRecord` — calidad de proceso
- `WasteRecord` — desperdicio

Cada entidad sigue el mismo patrón: dataclass, UUID id, campos del DBML,
sin lógica de negocio compleja aún.

#### `production_discharge.py` ejemplo (campos principales)

```text
ProductionDischarge
├── production_discharge_id: UUID
├── section: str                    # yarn_spinning_section
├── machine_id: UUID
├── business_date: date
├── shift_code: str
├── supervisor_user_id: UserId
├── yarn_count_id: UUID
├── gross_weight_kg: Decimal
├── spindle_tare_kg: Decimal
├── operative_spindle_count: int
├── cart_weight_kg: Decimal
├── net_weight_kg: Decimal           # calculado? Por ahora campo directo
├── registered_by_user_id: UserId
└── notes: str | None
```

No implementar cálculos aún — `net_weight_kg` es un campo que se setea, no se calcula.
Eso viene en fase de lógica de negocio.

---

### 4b — Endpoints

CRUD básico para cada entidad:

```
GET    /yarn-production/discharges
POST   /yarn-production/discharges
GET    /yarn-production/discharges/{id}
PATCH  /yarn-production/discharges/{id}

GET    /yarn-production/skein-records
POST   /yarn-production/skein-records
...

GET    /yarn-production/progress-records
...
```

Mismo patrón: repo en memoria, endpoint thin, sin lógica de negocio.

---

## Part 5: Fase 4 — Batch Processing domain + CRUD básico

### Objetivo

Dominio de procesamiento de lotes: cada etapa tiene su registro especializado.
Warehouse define la identidad, Batch Processing registra el historial operativo.

Referencia DBML: `docs/db/batch-processing.dbml`.

---

### 5a — Entidades de etapa

Una entidad por etapa (misma estructura):

- `InventoryStageRecord` — ensamblado del lote físico
- `DyeingStageRecord` — tintorería
- `DryingStageRecord` — secado
- `WindingStageRecord` — devanado (cono)
- `BallingStageRecord` — ovillado (bola) — NOTA: DBML usa winding_stage_records con conversion_variant
- `BaggingStageRecord` — embolsado
- `LotQualityRecord` — calidad final + Quality Send

Cada una lleva `production_identity_id` como referencia a la identidad de Warehouse,
NO como FK a una entidad de Batch Processing.

#### Ejemplo: `inventory_stage_record.py`

```text
InventoryStageRecord
├── inventory_stage_record_id: UUID
├── production_identity_id: UUID     # identidad de Warehouse
├── business_date: date
├── shift_code: str
├── assembled_by_user_id: UserId
├── supervisor_user_id: UserId
├── skein_count: int
├── total_weight_kg: Decimal
├── assembly_issue_category: str | None
├── notes: str | None
└── created_at: datetime
```

---

### 5b — Endpoints

CRUD básico por etapa. El más importante temprano es `inventory-stage` porque
es donde el lote "nace" operativamente.

```
GET    /batch-processing/inventory-stage
POST   /batch-processing/inventory-stage
GET    /batch-processing/inventory-stage/{id}
PATCH  /batch-processing/inventory-stage/{id}
```

Luego similar para dyeing, drying, winding, bagging, lot-quality.

---

## Part 6: Fase 5 — Validaciones, enums, reglas de negocio

### Objetivo

Agregar las capas que se omitieron intencionalmente en las fases 1-4.

### Qué incluye

#### Enums tipados

Reemplazar strings por enums donde el DBML los define:

| DBML enum                        | Dónde                                                        |
| -------------------------------- | ------------------------------------------------------------ |
| `yarn_spinning_section`          | `yarn-production` — preparation, ring_spinning, etc.         |
| `process_quality_method`         | `yarn-production` — samples, machine_counters, random_check  |
| `waste_record_type`              | `yarn-production` — real, accumulated                        |
| `conversion_variant`             | `batch-processing` — winding, balling                        |
| `lot_quality_state`              | `batch-processing` — standard, special_nomenclature, flagged |
| `product_availability_state`     | `warehouse` — available, flagged, etc.                       |
| `finished_product_delivery_type` | `warehouse` — direct_sale, commercialization_transfer        |

#### Validaciones de dominio

- `Bale`: received_weight_kg > 0
- `ProductionDischarge`: net_weight_kg >= 0, operative_spindle_count > 0
- `InventoryStageRecord`: skein_count > 0, total_weight_kg > 0
- `YarnCount`: yarn_count_code no vacío, material_type no vacío
- Fechas: business_date no puede ser futura (o sí? decisión de negocio)

#### Reglas de negocio (ejemplos)

- `ProductionDischarge.net_weight_kg = gross_weight_kg - spindle_tare_kg - cart_weight_kg`
  → implementar como computed property o validation en el dominio
- `SkeinRecord.estimated_weight_kg = skein_count * unit_skein_weight_kg`
- `Bale`: no se puede marcar `delivered=True` sin `delivered_at` y `delivered_by_user_id`

---

## Part 7: Fase 6 — PostgreSQL adapters (opcional para ahora)

### Objetivo

Reemplazar repos en memoria por implementaciones reales con SQLAlchemy async + PostgreSQL.

No está en el alcance inmediato. Se menciona aquí para tener el plano completo.

### Lo que implica

- Agregar `sqlalchemy[asyncio]` y `asyncpg` a `pyproject.toml`
- Crear modelos SQLAlchemy en `adapters/persistence/models.py` por contexto
- Implementar repos reales que implementan las mismas interfaces
- Migration tool (Alembic)
- Connection management, session factory
- Seed data (roles base, sysadmin, yarn counts iniciales)

---

## Part 8: Fase 7 — Endpoints completos y aplicación

### Objetivo

Reemplazar los CRUD básicos por endpoints con:

- Validación de entrada (Pydantic models en vez de dicts)
- Manejo de errores consistente
- Dependency injection con los reales repos
- Logging
- Authorization real (llamando a `check_access`)
- Tests

---

## Apéndice A: Patrón de archivo por fase

Cada archivo nuevo sigue esta convención:

```text
backend/<context>/
├── domain/
│   ├── __init__.py          # Re-export de TODO el dominio público
│   ├── <entity>.py          # Una entidad por archivo
│   └── <value_object>.py    # Value object cuando es compartido
├── application/             # (fase 5+)
├── ports/                   # (fase 5+)
└── adapters/                # (fase 6+)
```

### Reglas de `__init__.py`

Cada `__init__.py` de dominio exporta SOLO lo que es público para otros contextos.
Nada de importar cosas de infraestructura en el dominio.

---

## Apéndice B: Dependencias entre fases

```
Fase 1a (catalogs domain + access fix)
    │
    ▼
Fase 1b (in-memory CRUD)
    │
    ▼
Fase 2  (warehouse domain + CRUD)
    │
    ▼
Fase 3  (yarn-production domain + CRUD)    ── puede parallelizarse con Fase 2
    │
    ▼
Fase 4  (batch-processing domain + CRUD)   ── requiere Fase 2 (production_identity_id)
    │
    ▼
Fase 5  (validations, enums, business logic)
    │
    ▼
Fase 6  (PostgreSQL adapters)
    │
    ▼
Fase 7  (endpoints completos + auth real)
```

Fases 2 y 3 pueden hacerse en paralelo si trabajás en distintas branches.
Fase 4 necesita Fase 2 (la identidad de Warehouse es referencia).

---

## Apéndice C: Checklist rápido Fase 1a

- [ ] `catalogs/domain/user.py` — UserId
- [ ] `catalogs/domain/yarn_count.py` — YarnCount entity (refactor)
- [ ] `catalogs/domain/machine.py` — Machine entity
- [ ] `catalogs/domain/section.py` — Section value object
- [ ] `catalogs/domain/shift.py` — Shift value object
- [ ] `catalogs/domain/__init__.py` — exports
- [ ] `access/domain/assignment.py` — arreglar import a `catalogs.domain.user`
- [ ] `access/domain/events.py` — arreglar import
- [ ] Verificar que `uv run --locked python -c "from access.domain import Assignment, check_access; from catalogs.domain.yarn_count import YarnCount; print('OK')"` corre
