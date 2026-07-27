---
document_type: research
status: active
implementation: partial
scope: warehouse/raw-material
authority: evidence
owner: backend
last_reviewed: 2026-07-27
---

# Guía de Implementación: Dominio Warehouse / Raw Material

> **Propósito:** Documento de trabajo para el diseño e implementación del dominio Raw Material (Warehouse context).
> 
> **Enfoque:** Solo capa de dominio — entidades, value objects, reglas de negocio.
> 
> **No es documentación oficial** — es una guía práctica de trabajo.
>
> **Referencias:**
> - Arquitectura: `docs/architecture/system-overview.md` + `backend/docs/architecture/overview.md`
> - PRD: `docs/prd/warehouse.md` + `docs/prd/warehouse/`

---

## 1. Contexto del Proyecto

### Arquitectura Establecida

Según `backend/docs/architecture/overview.md`, el sistema sigue **Hexagonal Architecture por contexto**:

```
warehouse/
├── domain/           # ← ESTA FASE
├── application/      # (fase futura)
├── infrastructure/   # (fase futura)
└── interfaces/       # (fase futura)
```

**Esta guía cubre SOLO `warehouse/domain/`.**

### Naturaleza del Sistema (Crítico)

- **NO es tiempo real** — registro batch por turno
- **NO es concurrente** — un turno registra una sola vez al final de su jornada
- **NO es streaming** — los datos se capturan en papel durante el turno y se digitalizan al cierre
- **Es append-only** — los registros son inmutables, las correcciones son nuevos registros

Ver `docs/research/analisis-malinterpretacion-concurrencia.md` para detalles.

---

## 2. Alcance de Esta Fase: Dominio de Raw Material

### Objetivo

Diseñar e implementar las **entidades, value objects y reglas de negocio** del subdominio Raw Material:

1. Recepción de fardos de MP
2. Asignación automática del código único `NN-GGGG-NNN` (lot identity)
3. Enriquecimiento con datos del pedido
4. Emisión a Operación

### Bounded Context: Warehouse

Según `backend/docs/architecture/overview.md`, el contexto Warehouse tiene tres subdominios:

1. **Raw Material (MP)** — esta fase
2. Finished Product (PT) — fase futura
3. Supplies — fase futura

### Entidades del Contexto (según arquitectura)

| Entidad | Descripción |
|---------|-------------|
| **Movement** | Registro inmutable de entrada/salida de inventario |
| **StockBalance** | NO almacenado — calculado desde Movements |
| **Lot (identity)** | Código de lote + metadatos (creado por Warehouse, leído por Operation) |
| **Supplier** | Proveedor de MP |
| **Client** | Cliente destino del PT |

**Esta fase implementa:** `Movement` (para MP), `Lot (identity)`, `Supplier`.

### Fuera de Alcance (Esta Fase)

- Application layer (use cases)
- Infrastructure layer (repositories, DB)
- Interfaces layer (API endpoints)
- Auth / RBAC
- Finished Product
- Supplies
- Frontend

---

## 3. Diseño del Dominio

### 3.1 Decisión Arquitectónica: Movement vs Aggregate

Según `backend/docs/architecture/overview.md`, la entidad central del contexto Warehouse es **`Movement`** (registro inmutable de entrada/salida), no un aggregate "Lote".

**Implicación para Raw Material:**

- **NO modelamos un "RawMaterialLot" aggregate** con métodos `enrich()` y `emit()`
- **SÍ modelamos cada operación como un Movement independiente:**
  - `Movement` tipo "MP Reception" → crea la identidad del lote
  - `Movement` tipo "MP Enrichment" → agrega metadatos
  - `Movement` tipo "MP Emission to Production" → registra salida

**Ventaja:** Modelo uniforme para todos los subdominios (MP, PT, Supplies).

**Desventaja:** La lógica de negocio (ej: "no emitir sin enriquecer") vive en los use cases, no en el dominio.

**¿Querés seguir este modelo o preferís un aggregate `RawMaterialLot`?**

Por ahora documento ambas opciones:

---

### 3.2 Opción A: Movement-Centric (Arquitectura Actual)

#### Entidades

**`Movement`** (entidad central)

Registro inmutable de un movimiento de inventario. Atributos según PRD:

```python
@dataclass
class Movement:
    # Identity
    id: MovementId
    movement_number: str          # Correlativo por tipo/año
    
    # Temporal
    date: datetime
    shift: Shift                  # Turno (A, B, C)
    
    # Classification
    subdomain: Subdomain          # MP, PT, Supplies
    movement_type: MovementType   # Reception, Emission, etc.
    direction: Direction          # IN, OUT
    
    # Item data
    lot_code: Optional[LotCode]   # Solo para MP/PT
    quantity: Decimal
    unit: Unit                    # kg, L, pieces
    
    # Authorization trail
    authorized_by: Optional[str]  # Role que autorizó (si aplica)
    responsible: str              # Persona que ejecutó
    
    # Traceability
    corrects: Optional[MovementId]  # Si corrige un movimiento previo
    
    # Business rules (métodos de dominio)
    def is_correction(self) -> bool:
        return self.corrects is not None
    
    def requires_authorization(self) -> bool:
        # Según MovementType
        ...
```

**`Lot` (identity)**

La identidad del lote (código + metadatos). Creada en el primer Movement de recepción.

```python
@dataclass
class Lot:
    lot_code: LotCode
    
    # Reception metadata
    supplier: Supplier
    reception_date: datetime
    gross_weight_kg: Decimal
    title: YarnTitle
    fiber_color: str
    truck_number: str
    
    # Enrichment metadata (nullable hasta enriquecimiento)
    client: Optional[str]
    requested_color: Optional[str]
    requested_title: Optional[YarnTitle]
    type_n_ch: Optional[str]
    observations: Optional[str]
    
    def is_enriched(self) -> bool:
        return self.client is not None
```

#### Value Objects

**`LotCode`**

```python
@dataclass(frozen=True)
class LotCode:
    truck_number: str      # NN (2 dígitos)
    year: str              # GGGG (4 dígitos)
    sequence: str          # NNN (3 dígitos)
    
    def __str__(self) -> str:
        return f"{self.truck_number}-{self.year}-{self.sequence}"
    
    @classmethod
    def generate(cls, truck_number: str, year: int, sequence: int) -> "LotCode":
        # Validación + formato
        if not (0 <= int(truck_number) <= 99):
            raise InvalidLotCode("Truck number must be 00-99")
        if not (1000 <= year <= 9999):
            raise InvalidLotCode("Year must be 4 digits")
        if not (1 <= sequence <= 999):
            raise InvalidLotCode("Sequence must be 001-999")
        
        return cls(
            truck_number=str(truck_number).zfill(2),
            year=str(year),
            sequence=str(sequence).zfill(3)
        )
    
    @classmethod
    def from_string(cls, code: str) -> "LotCode":
        # Parse "NN-GGGG-NNN"
        parts = code.split("-")
        if len(parts) != 3:
            raise InvalidLotCode(f"Invalid format: {code}")
        return cls(parts[0], parts[1], parts[2])
```

**`YarnTitle`**

```python
@dataclass(frozen=True)
class YarnTitle:
    value: str  # "2/18", "2/32", "4/9", etc.
    
    def __post_init__(self):
        # Validar formato (número/número)
        if "/" not in self.value:
            raise InvalidYarnTitle(f"Invalid format: {self.value}")
        parts = self.value.split("/")
        if len(parts) != 2:
            raise InvalidYarnTitle(f"Invalid format: {self.value}")
        try:
            int(parts[0])
            int(parts[1])
        except ValueError:
            raise InvalidYarnTitle(f"Invalid numbers: {self.value}")
```

**Otros value objects:**

- `Supplier` (nombre, identificación fiscal)
- `MovementType` (código, nombre, requiere autorización)
- `Subdomain` (enum: MP, PT, Supplies)
- `Direction` (enum: IN, OUT)
- `Unit` (enum: kg, L, pieces, meters)
- `Shift` (código: A, B, C)

#### Domain Events

```python
@dataclass(frozen=True)
class RawMaterialReceived:
    movement_id: MovementId
    lot_code: str
    supplier: str
    gross_weight_kg: Decimal
    received_at: datetime

@dataclass(frozen=True)
class LotEnriched:
    lot_code: str
    client: str
    requested_color: str
    enriched_at: datetime

@dataclass(frozen=True)
class LotEmittedToProduction:
    movement_id: MovementId
    lot_code: str
    quantity_kg: Decimal
    destination: str
    emitted_at: datetime
```

#### Domain Exceptions

```python
class InvalidLotCode(ValueError): ...
class InvalidYarnTitle(ValueError): ...
class LotCodeAlreadyExists(Exception): ...
class LotNotEnriched(Exception): ...
class InsufficientQuantity(Exception): ...
class MovementAlreadyCorrected(Exception): ...
```

---

### 3.3 Opción B: Aggregate-Centric (Alternativa)

Si preferís un modelo más tradicional DDD con aggregates:

**`RawMaterialLot` (aggregate root)**

```python
@dataclass
class RawMaterialLot:
    lot_code: LotCode
    
    # Reception
    reception_date: datetime
    supplier: Supplier
    invoice_number: str
    gross_weight_kg: Decimal
    title: YarnTitle
    fiber_color: str
    truck_number: str
    received_by: str
    
    # Enrichment (nullable)
    enrichment: Optional[Enrichment]
    
    # Emissions (list de value objects)
    emissions: List[Emission]
    
    # Computed properties
    @property
    def status(self) -> LotStatus:
        if not self.enrichment:
            return LotStatus.RECEIVED
        total_emitted = sum(e.quantity_kg for e in self.emissions)
        if total_emitted == 0:
            return LotStatus.ENRICHED
        elif total_emitted < self.gross_weight_kg:
            return LotStatus.PARTIALLY_EMITTED
        else:
            return LotStatus.FULLY_EMITTED
    
    @property
    def remaining_quantity_kg(self) -> Decimal:
        total_emitted = sum(e.quantity_kg for e in self.emissions)
        return self.gross_weight_kg - total_emitted
    
    # Business methods
    def enrich(
        self,
        client: str,
        requested_color: str,
        title: YarnTitle,
        type_n_ch: str,
        observations: Optional[str],
        enriched_by: str
    ) -> None:
        if self.enrichment is not None:
            raise LotAlreadyEnriched(f"Lot {self.lot_code} already enriched")
        
        self.enrichment = Enrichment(
            client=client,
            requested_color=requested_color,
            title=title,
            type_n_ch=type_n_ch,
            observations=observations,
            enriched_at=datetime.now(),
            enriched_by=enriched_by
        )
    
    def emit(
        self,
        quantity_kg: Decimal,
        supervisor: str,
        destination: str,
        authorized_by: str
    ) -> None:
        if not self.enrichment:
            raise LotNotEnriched(f"Lot {self.lot_code} must be enriched before emission")
        
        if quantity_kg > self.remaining_quantity_kg:
            raise InsufficientQuantity(
                f"Cannot emit {quantity_kg} kg, only {self.remaining_quantity_kg} kg remaining"
            )
        
        emission = Emission(
            emission_date=datetime.now(),
            supervisor=supervisor,
            quantity_kg=quantity_kg,
            destination=destination,
            authorized_by=authorized_by
        )
        self.emissions.append(emission)
```

**Value objects** (iguales que Opción A)

---

### 3.4 Comparación de Opciones

| Aspecto | Opción A (Movement-Centric) | Opción B (Aggregate-Centric) |
|---|---|---|
| **Alineación con arquitectura** | ✅ Sigue `backend.md` | ⚠️ Desvío del diseño |
| **Uniformidad** | ✅ Mismo modelo para MP/PT/Supplies | ❌ Aggregates distintos por subdominio |
| **Lógica de negocio** | ❌ En use cases (más dispersa) | ✅ En aggregate (más cohesiva) |
| **Inmutabilidad** | ✅ Movements son naturalmente append-only | ⚠️ Aggregate muta (pero registra Movements) |
| **Complejidad** | ⚠️ Lógica de validación en application layer | ✅ Validaciones en el dominio |

**Recomendación:** Empezar con **Opción A** (Movement-Centric) porque:
1. Ya está en la arquitectura (`backend.md`)
2. Es más simple para el primer subdominio
3. Se puede refactorizar a aggregates después si hace falta

**PERO:** Si te sentís más cómodo con aggregates, Opción B es perfectamente válida para un spike.

---

## 4. Estructura del Dominio (Warehouse Context)

Según la arquitectura, el dominio de Warehouse queda así:

```
backend/warehouse/domain/
├── __init__.py
├── entities/
│   ├── __init__.py
│   ├── movement.py          # Movement entity
│   └── lot.py               # Lot (identity) entity
├── value_objects/
│   ├── __init__.py
│   ├── lot_code.py          # LotCode value object
│   ├── yarn_title.py        # YarnTitle value object
│   ├── supplier.py          # Supplier value object
│   ├── movement_type.py     # MovementType value object
│   ├── subdomain.py         # Subdomain enum
│   ├── direction.py         # Direction enum
│   └── unit.py              # Unit enum
├── events/
│   ├── __init__.py
│   └── raw_material_events.py  # Domain events
└── exceptions/
    ├── __init__.py
    └── warehouse_exceptions.py  # Domain exceptions
```

**Notas:**
- `Shift`, `Employee`, `YarnCount` viven en `shared/domain/` (catálogos compartidos)
- Por ahora NO implementamos `Client` (es para PT)
- Por ahora NO implementamos repositorios (ports) — eso es application layer

---

## 5. Reglas de Negocio del Dominio

### 5.1 Movement (Raw Material)

**Invariantes:**
1. Todo Movement tiene `date`, `shift`, `subdomain`, `movement_type`, `direction`
2. Movements de MP DEBEN tener `lot_code`
3. Movements con `direction=OUT` que sean tipo "Emission to Production" requieren `authorized_by`
4. Un Movement que corrige (`corrects != null`) debe tener `direction` opuesta al original
5. `quantity` debe ser > 0
6. `movement_number` es único por tipo/año

**Métodos de dominio:**
```python
def is_correction(self) -> bool
def requires_authorization(self) -> bool
def is_mp_reception(self) -> bool
def is_mp_emission(self) -> bool
```

### 5.2 Lot (Identity)

**Invariantes:**
1. `lot_code` es único en todo el sistema
2. Una vez creado, el código NO cambia
3. `reception_date`, `supplier`, `gross_weight_kg` son obligatorios
4. `enrichment` es opcional hasta que se enriquece
5. Una vez enriquecido, NO se puede "desenriquecer"

**Métodos de dominio:**
```python
def is_enriched(self) -> bool
```

**Nota:** Las validaciones de "no emitir sin enriquecer" y "no exceder cantidad" van en los **use cases**, NO en el dominio (porque requieren consultar Movements previos).

### 5.3 LotCode

**Invariantes:**
1. Formato `NN-GGGG-NNN`
2. `NN` = 00-99
3. `GGGG` = año de 4 dígitos
4. `NNN` = secuencia 001-999

**Métodos:**
```python
@classmethod
def generate(cls, truck_number: str, year: int, sequence: int) -> "LotCode"

@classmethod
def from_string(cls, code: str) -> "LotCode"

def __str__(self) -> str
```

### 5.4 YarnTitle

**Invariantes:**
1. Formato `N/N` o `N/NN` (ej: 2/18, 4/9)
2. Ambas partes deben ser números enteros positivos

---

## 6. Plan de Implementación (Solo Dominio)

### Semana 1: Value Objects + Entities

**Día 1-2: Value Objects básicos**
- [ ] `LotCode` con validación y generación
- [ ] `YarnTitle` con validación de formato
- [ ] `Supplier` (nombre, tax_id)
- [ ] `Subdomain` (enum: MP, PT, SUPPLIES)
- [ ] `Direction` (enum: IN, OUT)
- [ ] `Unit` (enum: KG, L, PIECES, METERS)
- [ ] Tests unitarios de value objects

**Día 3-4: Entidades**
- [ ] `Lot` (identity) con métodos `is_enriched()`
- [ ] `Movement` con métodos `is_correction()`, `requires_authorization()`
- [ ] `MovementType` (código, nombre, requiere_autorizacion)
- [ ] Tests unitarios de entidades

**Día 5: Events + Exceptions**
- [ ] `RawMaterialReceived` event
- [ ] `LotEnriched` event
- [ ] `LotEmittedToProduction` event
- [ ] `InvalidLotCode`, `LotCodeAlreadyExists`, etc. exceptions
- [ ] Tests de events (básicos)

### Documentación Producida

Al final de esta semana deberías tener:

1. **Código del dominio** (`backend/warehouse/domain/`)
2. **Tests unitarios** (`backend/tests/unit/warehouse/domain/`)
3. **Documento de dominio** (`docs/domain/warehouse.md`) con:
   - Entidades y sus responsabilidades
   - Value objects y sus invariantes
   - Reglas de negocio
   - Eventos de dominio

---

## 7. Decisiones Pendientes

| Decisión | Opciones | Recomendación |
|---|---|---|
| **Modelo Movement vs Aggregate** | A (Movement-centric) o B (Aggregate-centric) | Opción A (alineado con arquitectura) |
| **Generación de secuencia** | 1. Auto-increment DB<br>2. Redis counter<br>3. Lógica en use case | Use case (fase application) |
| **Validación de "no emitir sin enriquecer"** | 1. En dominio (Lot)<br>2. En use case | Use case (requiere consultar Movements) |
| **Catálogo MovementType** | 1. Enum<br>2. Entity | Entity (es seed data) |

---

## 8. Criterios de Éxito (Solo Dominio)

- [ ] Todos los value objects tienen validación
- [ ] `LotCode.generate()` produce códigos válidos
- [ ] `Movement` y `Lot` tienen sus invariantes documentadas
- [ ] Cobertura de tests del dominio > 90%
- [ ] `docs/domain/warehouse.md` está actualizado con el diseño real
- [ ] El código sigue `docs/dev-guide/naming-conventions.md`

---

## 9. Siguientes Fases (NO en esta guía)

Después de completar el dominio:

1. **Application Layer:** Use cases que orquestan el dominio
2. **Infrastructure Layer:** Repositories (SQLAlchemy)
3. **Interfaces Layer:** FastAPI routes
4. **Auth:** RBAC + permisos

---

## 10. Referencias

- **PRD Almacén:** `docs/prd/warehouse.md`
- **PRD Capacidades Almacén:** `docs/prd/warehouse/` (bale-management, production-identity, finished-product, production-supplies)
- **Arquitectura:** `docs/architecture/system-overview.md` + `backend/docs/architecture/overview.md`
- **Naming Conventions:** `docs/dev-guide/naming-conventions.md`
- **Análisis de Concurrencia:** `docs/research/analisis-malinterpretacion-concurrencia.md`
