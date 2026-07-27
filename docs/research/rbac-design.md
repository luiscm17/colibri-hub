---
document_type: research
status: active
implementation: not-applicable
scope: access-control
authority: evidence
owner: architecture
last_reviewed: 2026-07-27
---

# RBAC Design — Colibri Hub

> **Research document**
> Propuesta de diseño para el sistema de autorización basado en RBAC con scopes
> jerárquicos, inspirado en el modelo de Azure RBAC.
>
> **Contexto:** Colibri Hub es un sistema de gestión de producción textil con
> múltiples direcciones (Producción, Administración, eventualmente
> Comercialización), cada una con estructura jerárquica propia.

---

## 1. Conceptos básicos

### 1.1 Autenticación vs Autorización

| Concepto | Pregunta que responde | En Colibri Hub |
|----------|----------------------|-------------|
| **Autenticación** | ¿Quién sos? | Supabase Auth (email + password, JWT) |
| **Autorización** | ¿Qué podés hacer? | El sistema que diseñamos acá — RBAC |

La autenticación verifica identidad. La autorización verifica permisos sobre
recursos específicos. Son capas separadas: un usuario puede estar autenticado
pero no tener permiso para una operación concreta.

### 1.2 RBAC (Role-Based Access Control)

RBAC es un modelo de control de acceso donde los permisos no se asignan
directamente a usuarios, sino a **roles**, y los usuarios **heredan** los
permisos a través de los roles que tienen asignados.

```
Usuarios ──tienen──> Roles ──tienen──> Permisos
```

Ventaja principal: si 10 auxiliares de almacén necesitan los mismos permisos,
no se asignan 10 veces — se asigna un rol y los 10 usuarios se vinculan a él.

### 1.3 Modelo Clásico vs Modelo con Scopes

El RBAC clásico asigna roles a usuarios, y cada rol tiene una lista plana de
permisos. Es simple pero frágil:

```
Usuario: Auxiliar Almacén
  └── Rol: auxiliar_almacen
        ├── warehouse.reception.create
        ├── warehouse.reception.read
        └── warehouse.emission.request
```

**Problema:** el nombre del dominio (`warehouse`) está incrustado en el permiso.
Si la estructura organizacional cambia, los permisos se rompen.

La variante con **scopes** (Azure RBAC) separa el qué del dónde:

```
Usuario: Auxiliar Almacén
  ├── Rol: staff
  │     └── create, read, request (acciones genéricas)
  └── Scope: warehouse.*
        └── ámbito donde aplican esas acciones
```

---

## 2. El problema que resolvemos

### 2.1 Estructura organizacional del PRD

El sistema cubre la **Dirección de Producción**, que se divide en dos unidades:

```
Dirección de Producción
├── Jefe de Producción (autoriza, supervisa, consolida)
│   ├── Unidad Almacén
│   │   ├── Jefe de Unidad Almacén (supervisa almacén)
│   │   └── Auxiliares Operativos (ejecutan movimientos)
│   └── Unidad Operación
│       └── Supervisores (1 por turno)
│           ├── Control de Calidad (pruebas, registra producción)
│           ├── Inventario (registra producción, desperdicio, lotes)
│           ├── Personal de Tintorería
│           └── Embolsado
└── Reporte diario a Administración
```

### 2.2 Lo que no funciona

Si diseñamos los permisos atados a los cargos actuales:

```python
# ❌ Así NO
role_permissions = {
    "auxiliar_almacen": ["warehouse.reception.create", ...],
    "supervisor": ["operation.production.read", "operation.supplies.approve", ...],
}
```

| Escenario | Por qué se rompe |
|-----------|-----------------|
| Crean "Dirección de Comercialización" | No existe `commercial.x` en el código — hay que agregarlo |
| Fusionan Almacén y Operación | Los permisos `warehouse.*` y `operation.*` ya no tienen sentido separados |
| Renombran "Supervisor" a "Coordinador de Turno" | El nombre del cargo está en el código como clave del dict |
| Secretaria = JP sin autorizar | Habría que duplicar el rol JP y sacarle approve — dos lugares que mantener |
| Crean "Jefe de Planta" sobre JP y Jefe Almacén | No hay un nivel superior a director en el modelo |

### 2.3 La lección de Azure RBAC

Azure tiene roles definidos como **listas planas de acciones** sobre tipos de
recurso. Un rol no sabe qué es una VM o una base de datos — solo sabe que
permite `virtualMachines/start` o `storageAccounts/listKeys`. Los dominios
(Compute, Storage, Network) existen como metadata, no como parte del permiso.

Además, Azure permite asignar el **mismo rol** en **scopes diferentes**:

```
Rol: Contributor
  ├── Asignado en scope: Subscription A   →   puede contribuir en toda la subscripción
  └── Asignado en scope: Resource Group B →   puede contribuir solo en ese grupo
```

Esto es exactamente lo que necesitamos: un mismo rol genérico (`staff`, `lead`,
`manager`, `director`) que se asigna con scopes diferentes según el dominio.

---

## 3. Modelo propuesto

### 3.1 Arquitectura conceptual

```
USERS                 ROLE DEFINITIONS          SCOPES
┌─────────┐           ┌────────────────┐        ┌──────────────────┐
│ user_id │──has──>  │ role_def_id    │──en──> │ scope_id         │
│ name    │           │ code (staff)   │        │ code (warehouse) │
│ ...     │           │ actions:       │        │ parent_id        │
└─────────┘           │   create       │        └──────────────────┘
                      │   read         │               │
                      │   approve      │          (jerárquicos)
                      └────────────────┘               │
                              │                   nested sets
                              │                   
                      ┌───────┴────────┐
                      │  EXCEPCIONES   │
                      │  + allow       │
                      │  - deny        │
                      └────────────────┘
```

### 3.2 Componentes

#### Role Definitions (niveles jerárquicos genéricos)

Son los **perfiles de capacidad** — definen qué tipo de acciones puede realizar
una persona. No están vinculados a ningún dominio específico.

| Código | Display name | Acciones base | Uso en cualquier dominio |
|--------|-------------|---------------|--------------------------|
| `executive` | Ejecutivo | `read` | Gerencia, solo lectura de reportes |
| `director` | Director | `read, approve, consolidate, manage` | Jefe de Producción, autoriza entre unidades |
| `manager` | Gerente | `read, create, approve` | Jefe de Unidad, gestiona y autoriza en su ámbito |
| `lead` | Líder | `read, create, approve_limited` | Supervisor, supervisa ejecución |
| `staff` | Staff | `create, read_own` | Auxiliares y personal operativo |
| `sysadmin` | SysAdmin | `manage` | Solo sistema, ningún dominio de negocio |

#### Resource Types (registrados por cada módulo)

Cada módulo del sistema registra los tipos de recurso sobre los que se pueden
realizar acciones. El motor de permisos no sabe qué son — solo evalúa patrones.

```sql
emission           → 'Emisión de MP a Operación'
pt_reception       → 'Recepción de Producto Terminado'
supplies_movement  → 'Movimiento de Insumos'
production_record  → 'Registro de producción por máquina'
quality_test       → 'Control de calidad'
waste_record       → 'Registro de desperdicio'
valuation          → 'Valuación de inventario'
costing            → 'Costeo'
monthly_close      → 'Cierre mensual'
daily_report       → 'Reporte diario consolidado'
user_management    → 'Gestión de usuarios'
catalog            → 'Gestión de catálogos'
```

#### Matriz de permisos (rol × recurso × acción)

Define qué acciones puede realizar cada nivel sobre cada recurso.

```
                    staff  lead   manager  director  executive  sysadmin
emission.create     allow  allow   deny     deny      deny      deny
emission.request    allow  allow   deny     deny      deny      deny
emission.read       allow  allow   allow    allow     deny      deny
emission.approve    deny   deny    deny     allow     deny      deny

production_record   allow  allow   allow    allow     deny      deny
quality_test        allow  allow   allow    allow     deny      deny
waste_record        allow  allow   allow    allow     deny      deny

daily_report.read   deny   allow   allow    allow     allow     deny
daily_report.consol deny   deny    deny     allow     deny      deny

user_management     deny   deny    deny     allow     deny      allow
catalog.manage      deny   deny    allow    allow     deny      allow
```

#### Scopes (jerarquía organizacional)

Definen el **ámbito** donde aplica un permiso. Son jerárquicos: un scope padre
hereda a sus hijos.

```
production.*
  ├── warehouse.*
  │   ├── warehouse.mp
  │   ├── warehouse.pt
  │   └── warehouse.supplies
  └── operation.*
      ├── operation.production
      ├── operation.quality
      ├── operation.waste
      └── operation.lots
reports.admin
system
```

La jerarquía se implementa con **nested sets** (`lft`, `rgt`) para consultas
eficientes de sub-árbol.

### 3.3 Asignaciones y excepciones

Una asignación vincula un usuario con un rol y un scope:

```sql
Usuario: Auxiliar Pérez
  Rol: staff
  Scope: warehouse.*
  Excepciones: (ninguna)
```

Las excepciones permiten agregar o quitar permisos específicos sin crear
definiciones de rol nuevas:

```sql
Usuario: María (Secretaria)
  Rol: director
  Scope: production.*
  Excepciones:
    - deny: (emission, approve)
    - deny: (pt_sale, approve)

Usuario: Carlos (Calidad)
  Rol: staff
  Scope: operation.quality
  Excepciones:
    + allow: (production_record, create)
```

### 3.4 Algoritmo de resolución

```python
def check_access(user, required_resource: str, required_action: str) -> bool:
    """
    Evalúa si un usuario tiene un permiso específico.
    Las excepciones deny siempre ganan sobre allow.
    """
    for assignment in user.assignments:
        # 1. Verificar excepciones primero (deny explícito)
        for exc in assignment.exceptions:
            if matches(exc.resource_type, required_resource) \
               and matches(exc.action, required_action):
                if exc.effect == 'deny':
                    return False
                # allow explícito como excepción
                return True

        # 2. Verificar scope: el scope de la asignación ¿cubre este recurso?
        if not scope_covers(assignment.scope, required_resource):
            continue

        # 3. Verificar permiso base de la definición del rol
        for perm in assignment.role.role_resource_permissions:
            if perm.resource_type.code == required_resource \
               and perm.action == required_action:
                return perm.effect == 'allow'

    return False


def scope_covers(assignment_scope, resource_type) -> bool:
    """¿El scope de la asignación cubre el recurso consultado?"""
    # Ej: assignment_scope = 'warehouse.*'
    #     resource_type.domain = 'warehouse.mp'
    #     → True (warehouse.* cubre warehouse.mp)
    return resource_type.domain.startswith(assignment_scope.replace('*', ''))


def matches(pattern, value) -> bool:
    """Match con soporte de wildcard: 'approve' == 'approve', '*' == todo."""
    return pattern == '*' or pattern == value
```

---

## 4. Mapeo completo al PRD actual

### Asignaciones

| Persona | Rol | Scope | Excepciones |
|---------|-----|-------|-------------|
| Auxiliar Almacén (×N) | `staff` | `warehouse.*` | — |
| Jefe Almacén | `manager` | `warehouse.*` | — |
| Jefe Producción | `director` | `production.*` | — |
| Secretaria | `director` | `production.*` | `deny: (emission, approve)`, `deny: (pt_sale, approve)` |
| Supervisor (×3) | `lead` | `operation.*` | — |
| Calidad (×N) | `staff` | `operation.quality` | `allow: (production_record, create)` |
| Inventario (×N) | `staff` | `operation.production` | `allow: (waste_record, create)` |
| Tintorería (×N) | `staff` | `operation.lots` | — |
| Embolsado (×N) | `staff` | `operation.lots` | — |
| Gerencia | `executive` | `reports.admin` | — |
| SysAdmin | `sysadmin` | `system` | — |

### Mapa visual

```
                        STAFF         LEAD        MANAGER      DIRECTOR    EXECUTIVE
                    ┌──────────────────────────────────────────────────────────────┐
warehouse.mp       │ create,read  │ read        │ create,read │ read       │       │
                   │ → Auxiliar   │             │ → Jefe Alm  │ → JP       │       │
warehouse.pt       │ create,read  │ read        │ create,read │ read       │       │
                   │ → Auxiliar   │             │ → Jefe Alm  │ → JP       │       │
warehouse.supplies │ create,read  │ approve(lim)│ create,read │ read       │       │
                   │ → Auxiliar   │ → Supervisor│ → Jefe Alm  │ → JP       │       │
────────────────────┼──────────────┼─────────────┼─────────────┼────────────┼──────│
operation.prod.    │ create(lim)  │ create,read │ read        │ read       │       │
                   │ → Calidad,   │ → Supervisor│             │ → JP       │       │
                   │   Inventario │             │             │            │       │
operation.quality  │ create,read  │ read        │ read        │ read       │       │
                   │ → Calidad    │ → Supervisor│             │ → JP       │       │
operation.waste    │ create       │ read        │ read        │ read       │       │
                   │ → Inventario │ → Supervisor│             │ → JP       │       │
────────────────────┼──────────────┼─────────────┼─────────────┼────────────┼──────│
reports.daily      │              │ read        │ read        │ consolidate│ read  │
                   │              │ → Supervisor│             │ → JP/Sec   │→ Gcia │
reports.admin      │              │             │             │ read       │ read  │
                   │              │             │             │ → JP/Sec   │→ Gcia │
────────────────────┼──────────────┼─────────────┼─────────────┼────────────┼──────│
system.users       │              │             │             │ manage     │       │
                   │              │             │             │ → JP/Sec   │       │
catalogs           │ read         │ read        │ manage      │ manage     │       │
                   │ → todos op   │ → Superv    │ → Jefe Alm  │ → JP       │       │
                    └──────────────┴─────────────┴─────────────┴────────────┴──────┘
```

---

## 5. Esquema de base de datos

```sql
-- ============================================================
-- 1. Definiciones de rol (niveles jerárquicos genéricos)
-- ============================================================
CREATE TABLE role_definitions (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(50) UNIQUE NOT NULL CHECK (code IN (
                'staff', 'lead', 'manager', 'director', 'executive', 'sysadmin'
              )),
    display_name VARCHAR(200) NOT NULL,
    rank     INT NOT NULL,           -- 1 staff → 6 executive, solo para UI
    description TEXT
);

-- ============================================================
-- 2. Scopes organizacionales (jerarquía con nested sets)
-- ============================================================
CREATE TABLE scopes (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    parent_id INT REFERENCES scopes(id),
    lft      INT NOT NULL,           -- nested set: inicio del sub-árbol
    rgt      INT NOT NULL            -- nested set: fin del sub-árbol
);

-- ============================================================
-- 3. Tipos de recurso (registrados por cada módulo)
-- ============================================================
CREATE TABLE resource_types (
    id       SERIAL PRIMARY KEY,
    code     VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 4. Permisos base: nivel × recurso × acción
-- ============================================================
CREATE TABLE role_resource_permissions (
    role_def_id     INT NOT NULL REFERENCES role_definitions(id),
    resource_type_id INT NOT NULL REFERENCES resource_types(id),
    action          VARCHAR(50) NOT NULL,
    effect          VARCHAR(10) NOT NULL DEFAULT 'allow'
                    CHECK (effect IN ('allow', 'deny')),
    PRIMARY KEY (role_def_id, resource_type_id, action)
);

-- ============================================================
-- 5. Asignaciones: usuario + rol + scope
-- ============================================================
CREATE TABLE user_role_assignments (
    id          SERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id),
    role_def_id INT NOT NULL REFERENCES role_definitions(id),
    scope_id    INT NOT NULL REFERENCES scopes(id),
    UNIQUE (user_id, role_def_id, scope_id)
);

-- ============================================================
-- 6. Excepciones por asignación (override granular)
-- ============================================================
CREATE TABLE assignment_exceptions (
    assignment_id    INT NOT NULL REFERENCES user_role_assignments(id)
                     ON DELETE CASCADE,
    resource_type_id INT NOT NULL REFERENCES resource_types(id),
    action           VARCHAR(50) NOT NULL,
    effect           VARCHAR(10) NOT NULL CHECK (effect IN ('allow', 'deny')),
    UNIQUE (assignment_id, resource_type_id, action)
);
```

---

## 6. Ejemplos de resolución

### Caso 1: Auxiliar registra recepción de MP

```
check_access(
    user=Auxiliar, 
    resource="emission", 
    action="request"
)
```

1. `staff` tiene `allow: (emission, request)` ✓
2. Scope del auxiliar es `warehouse.*` y `emission` pertenece a `warehouse.mp` ✓
3. No hay excepciones → **True**

### Caso 2: Secretaria intenta aprobar emisión

```
check_access(
    user=Secretaria, 
    resource="emission", 
    action="approve"
)
```

1. `director` tiene `allow: (emission, approve)` ✓ base
2. Scope `production.*` cubre `warehouse.mp` ✓
3. Excepción: `deny: (emission, approve)` → **False**

### Caso 3: Supervisor lee reporte diario

```
check_access(
    user=Supervisor, 
    resource="daily_report", 
    action="read"
)
```

1. `lead` tiene `allow: (daily_report, read)` ✓
2. Scope `operation.*` ... `daily_report` no pertenece a `operation`. 
   Pertenece a `reports.admin`.
3. Scope NO cubre → no encuentra permiso → sigue al siguiente assignment
4. No hay más assignments → **False**

**Esto detecta un error de diseño.** El supervisor debería tener un segundo
assignment o su scope debería incluir reports. La resolución correcta:

```sql
-- Solución: segundo assignment que cubra reports
INSERT INTO user_role_assignments VALUES
    (sup_uid, 'lead', (SELECT id FROM scopes WHERE code='reports.daily'));
```

---

## 7. Escenarios de cambio

| Escenario | Qué se hace | ¿Código afectado? |
|-----------|------------|-------------------|
| **Nueva dirección: Comercialización** | `INSERT scope (commercial.*)`, `INSERT resource_types (contract, invoice)`, se asignan usuarios a staff/lead/manager/director | Solo datos |
| **Renombran "Auxiliar" a "Técnico"** | Se cambia en la UI, el role_def `staff` no se toca | Solo UI |
| **Secretaria ahora autoriza** | Se borra la excepción `deny` | Solo datos |
| **Crean "Jefe de Turno"** | Usan rol `lead` + scope `operation.*` | Solo datos |
| **Fusionan Almacén y Operación** | Se reasignan scopes hijos bajo nuevo scope padre | Solo datos |
| **Nuevo recurso: "Control de calidad de lote"** | `INSERT resource_type`, se definen permisos base en matriz | Solo datos |
| **Un usuario necesita permiso excepcional** | Se agrega excepción `allow` en su assignment | Solo datos |
| **Desactivan un rol completo** | `UPDATE role_definitions SET is_active = false` | Solo datos |

---

## 8. Lo que NO cubre este modelo (y está bien)

### Restricciones por instancia (contexto)

El RBAC responde: *"¿puede este usuario, en teoría, aprobar emisiones?"*

Pero no responde: *"¿puede aprobar ESTA emisión específica que ocurrió en otro turno?"*

Eso es responsabilidad de la **capa de servicio**, no del engine de permisos:

```python
# En el servicio, después de check_access():
def approve_emission(user, emission_id):
    emission = emission_repo.get(emission_id)
    if emission.shift != user.assigned_shift:
        raise HTTPException(403, "No autorizado para emisiones de otro turno")
    # ...
```

### Separación clara de responsabilidades

```
Capa de router / middleware:     check_access(user, resource, action) → 401/403
Capa de servicio:                validación de contexto de negocio → 403
Capa de repositorio:             filtrar datos por alcance del usuario → solo sus datos
```

Las tres capas son necesarias. El RBAC es la primera barrera, no la única.

---

## 9. Conclusión

Este modelo ofrece:

- **Genericidad:** los role definitions (`staff`, `lead`, `manager`, `director`)
  funcionan para cualquier dominio futuro sin cambios estructurales.
- **Flexibilidad:** scopes jerárquicos y excepciones por asignación cubren
  cualquier reestructuración organizacional.
- **Mantenibilidad:** ningún cambio organizacional requiere modificar código
  del engine de permisos — solo datos en DB.
- **Traza:** la matriz `role_resource_permissions` documenta explícitamente
  qué puede hacer cada nivel, sin ambigüedad.
- **Separación de concerns:** el RBAC sabe de recursos y acciones, no de
  dominios ni instancias. El contexto de negocio vive en los servicios.

La implementación de este diseño corresponde al Sprint 1 del proyecto,
junto con el scaffolding de auth y catálogos compartidos.
