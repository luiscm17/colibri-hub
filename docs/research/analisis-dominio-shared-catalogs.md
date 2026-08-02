---
document_type: research
status: active
implementation: not-started
scope: catalogs
authority: evidence
owner: architecture
last_reviewed: 2026-07-27
---

# Análisis: Shared Catalogs — Punto de Partida

> **Propósito:** Analizar el PRD y la arquitectura para identificar qué entidades son globales (Shared Catalogs) y deben implementarse PRIMERO antes que cualquier contexto específico.

---

## 1. Análisis del PRD

### 1.1 Catálogos Compartidos ([PRD Maestro §3](../prd/product-overview.md#3-business-areas))

Del `docs/prd/product-overview.md` [§3 Business Areas](../prd/product-overview.md#3-business-areas):

| Catálogo | Usado por |
|---|---|
| **Empleados** | Operación, Almacén, Jefe Producción |
| **Máquinas** | Operación (por sección y grupo) |
| **Títulos de hilado** | Operación, Lotes |
| **Secciones** | Operación (Preparación, Continuas, Bobinados, Retorcido, Madejeras) |
| **Turnos** | Operación, Almacén |
| **Tipos de MP** | Almacén |
| **Ubicaciones físicas** | Almacén |
| **Unidades de medida** | Todos (kg, madejas, conos, bolsas, piezas) |
| **Proveedores** | Almacén |
| **Lotes** | Operación, Almacén, Administración |

**Observación:** TODOS estos catálogos son compartidos entre contextos.

---

## 2. Análisis de la Arquitectura

### 2.1 Context Map ([Context Map §1](../architecture/context-map.md#1-bounded-contexts))

```
┌──────────────────────────────────────────────────────────────┐
│                     YARN EPR SYSTEM                           │
│                                                               │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐   │
│  │  AUTH    │    │  WAREHOUSE   │    │   OPERATION        │   │
│  │          │◄──►│              │◄──►│                   │   │
│  └──────────┘    └──────────────┘    └───────────────────┘   │
│                                                               │
│              ┌─────────────────────────────┐                  │
│              │     SHARED CATALOGS          │                  │
│              │  Employees, Machines,        │                  │
│              │  YarnCounts, Sections        │                  │
│              └─────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Shared Catalogs ([backend.md §6.5](../../backend/docs/architecture/overview.md#65-catalogs))

Del `backend/docs/architecture/overview.md` [§6.5 `catalogs`](../../backend/docs/architecture/overview.md#65-catalogs):

| Catalog | Contains | Used by |
|---------|----------|---------|
| **User** | Personal identification (name, email), organizational role (not RBAC role), active status | Auth, Warehouse, Operation |
| **Machine** | Machine identity, associated section and group, machine type (PSJ, FIN, etc.) | Operation (Yarn Spinning) |
| **MachineGroup** | Group identity and its section | Operation (waste) |
| **Section** | Section identity and name (Preparación, Continuas, etc.) | Operation |
| **Shift** | Shift identity and code (e.g., A, B, C) | Warehouse, Operation |
| **YarnCount** | Yarn count identity and designation (e.g., 2/18, 2/32) | Warehouse, Operation |
| **MovementType** | Movement type identity, subdomain, direction (in/out), whether it requires authorization | Warehouse |

**Nota:** `User` está en Shared Catalogs PERO también es parte del contexto Auth (tiene password, roles). Es un caso especial.

---

## 3. Identificación de Entidades Globales vs Locales

### 3.1 Entidades en Shared Catalogs (globales)

Estas entidades NO pertenecen a ningún contexto específico — son **master data**:

| Entidad | Propósito | Responsable de gestión |
|---|---|---|
| `YarnTitle` | Catálogo de títulos de hilado (2/18, 2/32, etc.) | Administración (seed data) |
| `Section` | Secciones productivas (Preparación, Continuas, etc.) | Administración (seed data) |
| `Shift` | Turnos (mañana, tarde, noche / A, B, C) | Administración (seed data) |
| `Machine` | Máquinas físicas de la planta | Jefe de Producción (gestión) |
| `MachineGroup` | Grupos de máquinas (para desperdicio) | Jefe de Producción (gestión) |
| `Employee` | Empleados de la planta (identidad personal) | RRHH / Administración |
| `MovementType` | Tipos de movimiento de almacén | Administración (seed data) |

**Proveedores y Clientes** NO aparecen en backend.md — hay que decidir si van en Shared o en Warehouse.

### 3.2 Entidades Específicas de Contexto

| Entidad | Contexto | Propósito |
|---|---|---|
| `Movement` | Warehouse | Registro de entrada/salida de inventario |
| `Lot (identity)` | Warehouse | Código de lote + metadatos (creado por Warehouse) |
| `ProductionDischarge` | Operation | Descarga de producción de una máquina |
| `StageRecord` | Operation | Paso del lote por una etapa |
| `User` (con auth) | Auth | Usuario con password y roles RBAC |

---

## 4. Análisis de Dependencias

### 4.1 Warehouse Context Depende De:

```
Warehouse
  ├── YarnTitle (shared)          → para registrar título en Reception
  ├── Shift (shared)              → para registrar turno en Movement
  ├── Employee (shared)           → para registrar "authorized_by", "responsible"
  ├── MovementType (shared)       → para clasificar tipo de Movement
  └── Supplier (¿shared o local?) → para registrar proveedor en Reception
```

**Conclusión:** NO podés implementar Warehouse sin antes tener Shared Catalogs.

### 4.2 Operation Context Depende De:

```
Operation
  ├── YarnTitle (shared)          → para registrar título en ProductionDischarge
  ├── Section (shared)            → para clasificar sección productiva
  ├── Shift (shared)              → para registrar turno en ProductionDischarge
  ├── Machine (shared)            → para identificar máquina productiva
  ├── MachineGroup (shared)       → para agrupar desperdicio
  ├── Employee (shared)           → para registrar supervisores, operarios
  └── Lot (identity) (warehouse)  → para leer código de lote (read-only)
```

**Conclusión:** NO podés implementar Operation sin antes tener Shared Catalogs Y Warehouse (identity del lote).

---

## 5. Orden Correcto de Implementación

Según el análisis de dependencias:

```
1. SHARED CATALOGS (base de todo)
   ├── YarnTitle
   ├── Section
   ├── Shift
   ├── Machine
   ├── MachineGroup
   ├── Employee (sin auth)
   └── MovementType

2. AUTH (usuarios con roles)
   └── User (con password, roles, scopes)

3. WAREHOUSE (identidad del lote)
   ├── Movement
   ├── Lot (identity)
   └── Supplier (si es local)

4. OPERATION (producción)
   ├── ProductionDischarge
   └── StageRecord
```

---

## 6. Decisiones Pendientes

### 6.1 ¿Supplier y Client van en Shared o en Warehouse?

**Argumentos para Shared:**
- Podrían usarse en futuros contextos (ej: Comercialización)
- Son master data (se gestionan centralmente)

**Argumentos para Warehouse:**
- PRD solo los menciona en Warehouse
- Operation NO los usa

**Recomendación:** Empezar en Warehouse (local). Si otro contexto los necesita, mover a Shared.

### 6.2 ¿Employee en Shared incluye roles RBAC?

**NO.** Según backend.md:

> **User** | Personal identification (name, email), **organizational role (not RBAC role)**, active status

- `Employee` en Shared = identidad personal + rol organizacional (ej: "Supervisor", "Jefe de Almacén")
- `User` en Auth = mismo empleado + password + roles RBAC + scopes

**Relación:** `User.employee_id` → `Employee.id`

### 6.3 ¿YarnTitle es Value Object o Entity?

**Opción 1: Value Object**
```python
@dataclass(frozen=True)
class YarnTitle:
    value: str  # "2/18"
```

**Opción 2: Entity**
```python
@dataclass
class YarnTitle:
    id: YarnTitleId
    designation: str    # "2/18"
    description: str    # "Título 2/18 (Stoll)"
    is_active: bool
```

**Recomendación:** **Entity** (catálogo con gestión, seed data, puede desactivarse).

---

## 7. Estructura de Shared Catalogs

```
backend/shared/
├── domain/
│   ├── entities/
│   │   ├── employee.py
│   │   ├── machine.py
│   │   ├── machine_group.py
│   │   ├── section.py
│   │   ├── shift.py
│   │   ├── yarn_title.py
│   │   └── movement_type.py
│   ├── value_objects/
│   │   ├── employee_id.py
│   │   ├── machine_id.py
│   │   └── ...
│   └── exceptions/
│       └── catalog_exceptions.py
└── kernel/
    ├── entity.py          # Base class
    ├── value_object.py    # Base class
    ├── port.py            # Interface marker
    └── use_case.py        # Base class
```

---

## 8. Plan de Acción Corregido

### Fase 0: Shared Catalogs (1 semana)

**Objetivo:** Implementar las entidades globales que todos los contextos necesitan.

**Día 1-2: Kernel + Value Objects**
- [ ] `Entity` base class
- [ ] `ValueObject` base class
- [ ] `Port` interface marker
- [ ] IDs (EmployeeId, MachineId, SectionId, etc.)

**Día 3-4: Entidades de Catálogo**
- [ ] `YarnTitle` (designation, description, is_active)
- [ ] `Section` (name, code, is_active)
- [ ] `Shift` (code, name, start_time, end_time)
- [ ] `Employee` (name, email, organizational_role, is_active)
- [ ] `MovementType` (code, name, subdomain, direction, requires_authorization)

**Día 5: Machine Entities**
- [ ] `MachineGroup` (name, section)
- [ ] `Machine` (code, name, section, group, machine_type)

**Resultado:** `backend/shared/domain/` completo y testeado.

---

### Fase 1: Warehouse Context (después de Shared)

**Objetivo:** Implementar Movement + Lot (identity) que dependen de Shared Catalogs.

---

## 9. Pregunta para Vos

Antes de seguir, necesito que decidas:

1. **¿Supplier y Client van en Shared o en Warehouse?**
2. **¿YarnTitle es Value Object o Entity?** (yo recomiendo Entity)
3. **¿Employee tiene un ID único o usamos email como identidad?**

¿Empezamos con Shared Catalogs o querés ajustar algo del análisis?
