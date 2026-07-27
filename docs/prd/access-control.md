---
document_type: prd
status: active
implementation: not-started
scope: access-control
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# SISTEMA DE GESTIÓN DE PRODUCCIÓN TEXTIL — Control de Acceso

> **Cross-cutting PRD — Roles, permisos y autorización**
>
> Define los requisitos de negocio y producto para el control de acceso del
> sistema, de forma transversal a todas las direcciones, unidades, procesos y
> áreas.
>
> Este documento complementa los PRD de dominio. No redefine sus procesos: define
> cómo se gobierna quién puede ver, registrar, validar, aprobar, consolidar o
> administrar información dentro del sistema.

---

## 1. Propósito

Establecer un modelo de control de acceso que permita que el sistema evolucione
con la organización, sin quedar atado rígidamente a la estructura actual de
cargos, áreas o unidades.

El sistema debe soportar cambios organizacionales como:

- creación de nuevos roles
- retiro de roles existentes
- división o fusión de responsabilidades
- reassignment of access between approved areas, units, or Operational Unit sections
- excepciones puntuales para usuarios específicos

sin exigir rediseño funcional de los procesos de negocio ya definidos en los PRD
de dominio.

---

## 2. Alcance

Este PRD aplica a todo el sistema.

Incluye:

- Dirección de Producción
- Unidad Almacén
- Unidad Operación
- Administración
- futuras direcciones o áreas que se incorporen al sistema

No define autenticación ni infraestructura técnica. Su foco es la
**autorización**: qué puede hacer cada usuario dentro del sistema y en qué
ámbito puede hacerlo.

---

## 3. Problema que resuelve

La organización puede cambiar con el tiempo. Un mismo proceso puede mantenerse
estable mientras cambian:

- los cargos que participan
- quién registra los datos
- quién valida
- quién aprueba
- quién consolida información

Si el sistema ata los permisos directamente a la estructura organizacional del
momento, cada cambio interno obliga a rediseñar formularios, reglas o flujos.

El sistema debe separar:

1. **la responsabilidad operativa del negocio**
2. **la autorización para actuar dentro del sistema**

Ambas se relacionan, pero no son equivalentes.

---

## 4. Conceptos base

### 4.1 Actores organizacionales

Son los cargos, funciones o personas que existen en la organización real.

Ejemplos:

- Jefe de Producción
- Secretaría de Producción
- Supervisor
- Control de Calidad
- Inventario
- Jefe Unidad Almacén
- Administración

Estos actores describen la estructura y las responsabilidades del negocio.

### 4.2 Roles del sistema

Son perfiles de capacidad dentro de la aplicación. Definen qué tipo de acciones
puede realizar un usuario, independientemente del nombre exacto de su cargo.

Un actor organizacional puede mapearse a uno o más roles del sistema, y ese
mapeo puede cambiar con el tiempo.

### 4.3 Permisos

For the initial release, permissions use this fixed action vocabulary:

- `read`
- `write`
- `edit`
- `edit_outside_window`
- `manage_access`

`write` covers recording a new business fact and owner-scope handoffs. `edit`
is an audited correction of an already recorded fact within the operational
window; it is not a generic update. `edit_outside_window` and `manage_access`
are exclusive to System Administrator. No Quality Send or Warehouse Accept
action is created: both remain domain events authorized by `write` in the
respective owner scope.

### 4.4 Ámbitos o scopes

These permissions depend on both action and scope. The initial scope model is
deliberately limited to Operational Unit sections and to units or areas
elsewhere. It has no scope hierarchy, wildcard matching, process, lot-stage,
or shift scopes. This lets a user act in one approved target without widening
access elsewhere.

For the initial release, each user has exactly one current technical role and
may hold multiple concurrent scope assignments. Technical role names and codes
describe capability profiles, never organizational job titles. System
Administrator alone creates, deactivates, and reactivates users; manages roles
and scope assignments; grants or revokes exceptions; and performs
`edit_outside_window`. `manage_access` and `edit_outside_window` may be allowed
only by the System Administrator role and may never be individually granted.
Lifecycle and access-administration changes must verify that their actor is an
active System Administrator. Authorization defaults to deny.

The mandatory, unique active technical role `sys_admin` is the System
Administrator role. Initial deployment must create it, its five fixed action
allowances, and the initial active bootstrap user atomically in one controlled
database seed or migration transaction. That bootstrap alone may omit a
pre-existing System Administrator actor for the bootstrap user, role-action,
and audit records. All later lifecycle and access administration requires an
active `sys_admin` actor and normal audit evidence.

After bootstrap, the database transaction must atomically reject any
deactivation, reassignment, revocation, or other change that would leave no
active user whose current role is the active `sys_admin` role.

An active `sys_admin` has automatic global operational authorization for every
current and future section, unit, and area. It needs no domain scope assignment
and no individual exception may constrain any of its actions. This is a narrow,
explicit System Administrator bypass, not a wildcard scope hierarchy or generic
permission engine. Ordinary roles retain default-deny action-plus-active-scope
assignment evaluation and time-bounded grant/restrict exceptions.

---

## 5. Requisitos del sistema

### 5.1 Permisos configurables

The system must permit configuration of who may perform fixed actions in an
approved scope without altering the business workflow defined in domain PRDs.

### 5.2 Independencia del organigrama actual

El modelo de permisos no debe depender rígidamente de los nombres actuales de
los cargos ni asumir que la organización permanecerá igual en el tiempo.

### 5.3 Evolución organizacional

El sistema debe soportar sin rediseño funcional:

- creación de nuevos roles
- eliminación de roles
- cambio de responsabilidades
- reasignación de permisos entre roles
- incorporación de nuevas direcciones, áreas o unidades

### 5.4 Permisos por ámbito

The first release assigns access only to an Operational Unit section or to a
unit or area in other contexts. Scope targets remain external business-context
references; Access does not invent organizational nodes or own workflow data.
Access maintains only a small approved-scope registry: a target is pending
until validated with its owning context and confirmed, and only a confirmed
active target may authorize. Rejected, pending, and inactive targets are
retained for history but are denied. This validation has no cross-context FK.

### 5.5 Authorization of domain acts

Domain acts may have different business owners, but their first-release
authorization uses only the fixed action vocabulary and approved scope model.
The Access context does not derive separate `validate`, `approve`,
`consolidate`, `send`, or `accept` permissions from operational labels.

For a simple operational action, authorization is assigned by action and scope;
it must not create separate permissions for implicit sub-steps. Quality Send
and Warehouse acceptance are domain events authorized by `write` in their
respective owner scopes, rather than separate inspect, review, approve, send,
or accept permissions. Operational `*_user_id` fields remain audit facts and
are not permission sources.

### 5.6 Excepciones controladas

The system must permit direct individual exceptions that grant or restrict one
action in one scope without redefining the global role. Each exception requires
an explicit validity start and end date, reason, grant/revoke actor, and
grant/revoke time. An exception may not grant `manage_access` or
`edit_outside_window`. This is not a generic policy engine.

### 5.7 Trazabilidad de permisos

Todo cambio relevante en asignaciones de acceso debe ser auditable. Debe poder
conocerse:

- qué permiso tenía un usuario
- en qué ámbito aplicaba
- desde cuándo aplicó
- qué cambio se realizó

### 5.8 Coherencia con los PRD de dominio

Los PRD de dominio describen procesos, actores y operación esperada. Este PRD
define cómo el sistema traduce eso en permisos configurables sin congelar la
estructura organizacional en el software.

---

## 6. Reglas de negocio transversales

1. **Los procesos no deben rediseñarse por cambios de permisos.**
   Si cambia el rol que registra una sección o etapa, el flujo del proceso debe
   mantenerse estable.

2. **Los cargos organizacionales no equivalen automáticamente a permisos.**
   Un mismo cargo puede tener distintas capacidades según el área, el turno o la
   decisión vigente de la empresa.

3. **Los permisos pueden cambiar sin cambiar el dominio.**
   Una reasignación de registro, validación o aprobación es una decisión de
   política de acceso, no una redefinición del proceso productivo.

4. **Las excepciones deben ser explícitas y trazables.**
   Los permisos especiales para usuarios puntuales deben quedar identificados y
   auditables.

5. **Read and intervention are distinct capabilities.**
   `read` does not imply `write`, `edit`, `edit_outside_window`, or
   `manage_access`.

6. **El sistema debe tolerar crecimiento organizacional.**
   La aparición de nuevas direcciones, áreas, unidades o funciones no debe
    invalidar el modelo de acceso existente.

7. **La reactivación requiere una nueva autorización explícita.**
   La desactivación y la reactivación preservan el historial, pero invalidan
   para autorización efectiva las asignaciones y excepciones de la generación
   anterior. Se deben reasignar o reotorgar explícitamente.

---

## 7. Ejemplos de uso esperados

### 7.1 Reasignación dentro de una sección

Hoy, en una sección determinada, el registro puede estar a cargo de
**Inventario**. Mañana la empresa puede decidir que ese registro pase a
**Control de Calidad**.

El sistema debe permitir ese cambio sin:

- rediseñar el proceso
- reescribir el PRD del proceso
- perder trazabilidad histórica

### 7.2 Distintos permisos para el mismo cargo

Dos usuarios con el mismo cargo organizacional pueden tener permisos distintos
si trabajan en ámbitos diferentes o si existe una excepción aprobada.

### 7.3 Nuevas áreas futuras

Si el sistema incorpora una nueva dirección o área, el modelo de control de
acceso debe poder extenderse a ese nuevo ámbito sin romper lo ya definido para
Producción, Almacén u Operación.

---

## 8. Relación con los PRD de dominio

### PRD maestro (`docs/prd/product-overview.md`)

Define el marco organizacional, las unidades, los actores y las reglas
transversales del sistema.

### PRD de Operación (`docs/prd/operation.md`)

Describe la operación productiva, los turnos, los roles operativos y la
asignación actual o esperada de responsabilidades dentro del proceso.

### PRD de Almacén (`docs/prd/warehouse.md`)

Describe la operación documental y física de Almacén, sus movimientos y sus
actores.

### Este PRD transversal

Define cómo esas responsabilidades se convierten en permisos configurables,
auditables y reasignables dentro del sistema.

---

## 9. No objetivos

Este documento no define:

- el proveedor o mecanismo de autenticación
- tablas de base de datos
- endpoints o contratos técnicos
- estructura de tokens o sesiones
- detalles de implementación interna

Tampoco reemplaza los PRD de dominio. Su función es servir como contrato de
producto para la autorización transversal.

---

## 10. Decisiones abiertas

1. Qué nivel de administración de permisos existirá en la primera versión:
   - solo configuración controlada por desarrollo/soporte
   - o interfaz administrativa para gestión de permisos

2. Individual exception grants and revocations are performed only by System
   Administrator.

3. The initial scope inventory must identify the existing Operational Unit
    sections and the existing unit/area targets in other contexts. It must not
    invent organizational nodes. Access confirmation must validate each target
    with its owning context; pending, rejected, and inactive targets cannot
    authorize.

---

## 11. Glosario

| Término | Definición |
|---|---|
| **Control de acceso** | Conjunto de reglas que determina qué puede hacer un usuario dentro del sistema. |
| **Autorización** | Decisión sobre si un usuario puede ejecutar una acción en un ámbito determinado. |
| **Rol del sistema** | Perfil de capacidades usado para asignar permisos dentro de la aplicación. |
| **Actor organizacional** | Cargo, función o persona definida por la estructura real de la empresa. |
| **Permiso** | Capacidad concreta para actuar sobre información o procesos del sistema. |
| **Scope / ámbito** | Approved authorization target: an Operational Unit section, or a unit or area in another context. |
| **Excepción** | Permiso especial o restricción particular aplicada a un usuario o caso específico. |
| **Trazabilidad de permisos** | Capacidad de reconstruir históricamente qué permisos existían, cuándo y para quién. |
