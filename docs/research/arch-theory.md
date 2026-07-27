---
document_type: research
status: active
implementation: not-applicable
scope: global/architecture
authority: evidence
owner: architecture
last_reviewed: 2026-07-27
---

# Colibri Hub — Arquitectura

> Documento de diseño arquitectónico del sistema Colibri Hub.
> Define las capas, patrones y decisiones que gobiernan la estructura del código.
>
> **Estado:** Borrador inicial — sujeto a revisión.
> **Contexto:** Proyecto pre-código. No hay implementación aún.
> **Stack objetivo:** Ver `docs/dev-guide/` para el stack concreto.

---

## 1. Estilo Arquitectónico

**Hexagonal (Ports & Adapters) con Casos de Uso explícitos.**

Elegido porque:

- **Pureza del dominio:** las reglas de negocio se prueban sin HTTP, DB, ni IO.
- **Intercambiabilidad:** infraestructura (host, auth, DB) puede cambiar sin tocar el dominio.
- **Mantenibilidad 5+ años:** la separación evita que el código se vuelva un monolito de dependencias.
- **Auditabilidad:** los casos de uso son el punto de control explícito para autorización y registros.

El nombre "hexagonal" no implica 6 puertos — implica que el **núcleo (dominio + aplicación) no sabe nada del mundo exterior**. Todo lo externo llega a través de puertos (interfaces) que la infraestructura implementa.

---

## 2. Capas

```
┌────────────────────────────────────────────┐
│              INTERFACES                     │
│  (Routers / Controllers / Handlers)        │
│  → Traducen requests del mundo exterior    │
│  → Delegan en Application Layer            │
│  → NO tienen lógica de negocio             │
├────────────────────────────────────────────┤
│              APPLICATION                    │
│  (Use Cases / Application Services)        │
│  → Orquestan: validate → auth → domain     │
│  → Cada caso de uso es una función/clase   │
│  → Depende de puertos (interfaces)         │
│  → NO depende de infraestructura           │
├────────────────────────────────────────────┤
│              DOMAIN                         │
│  (Entities / Value Objects / Domain Svcs)  │
│  → Reglas de negocio puras                 │
│  → Cero dependencias externas              │
│  → Testeable sin IO                        │
├────────────────────────────────────────────┤
│           INFRASTRUCTURE                    │
│  (Adapters / Repositories / Clients)       │
│  → Implementa los puertos de Application   │
│  → DB, API externas, sistema de archivos   │
│  → Solo cambia cuando cambia la tecnologia │
└────────────────────────────────────────────┘
```

### 2.1 Domain

Contiene las **entidades**, **objetos de valor**, y **servicios de dominio** que modelan el negocio textil.

**Qué va aquí:**

- Entidades: `Movement`, `Lot`, `ProductionDischarge`, `StageRecord`, `RoleDefinition`, `Assignment`
- Value Objects: `YarnCount`, `LotCode`, `Shift`, `Weight`, `ScopePath`
- Servicios de dominio: `check_access()` — función pura que resuelve si un usuario tiene permiso
- Reglas de negocio: "un StageRecord no se modifica una vez cerrado", "el peso neto se calcula, no se ingresa"

**Qué NO va aquí:**

- Llamadas a la base de datos
- Validación de autenticación (tokens, sesiones)
- HTTP, colas, sistema de archivos
- Frameworks u ORMs

### 2.2 Application

Cada **caso de uso** es una operación atómica del sistema. Es el orquestador que:

1. Recibe un comando/request (ya validado por Interfaces)
2. Verifica autorización vía `AuthorizationPort`
3. Ejecuta lógica de dominio pura
4. Persiste vía puertos de infraestructura
5. Devuelve un resultado

**Ejemplo — `CreateMovementUseCase`:**

```
1. Validar comando (formato, campos requeridos)
2. AuthorizationPort.check(user, "movement", "create") → si no, 403
3. domain.Movement.create(command) → entidad pura
4. MovementRepositoryPort.save(movement) → persiste
5. Devolver MovementResponse
```

**Puertos (interfaces que define Application, implementa Infrastructure):**

| Puerto | Responsabilidad |
|--------|---------------|
| `AuthorizationPort` | Verifica si un usuario puede ejecutar una acción sobre un recurso |
| `MovementRepositoryPort` | Persiste y recupera Movements |
| `LotRepositoryPort` | Persiste y recupera Lots |
| `UnitOfWorkPort` | Transacciones atómicas entre repositorios |

### 2.3 Infrastructure

Implementa los puertos definidos en Application. **Es la única capa que sabe de tecnologías concretas.**

- Implementaciones de repositorios (SQL, cache, archivos)
- Adapters de auth (JWT decoder, RBAC cache)
- Clientes HTTP para APIs externas
- Configuración de conexiones, pools, migrations

La infraestructura **implementa interfaces**, no las define. Si cambia la base de datos, solo cambian los adapters — Domain y Application no se tocan.

### 2.4 Interfaces

La capa más externa. Traduce requests del mundo exterior a llamadas a Application.

- **Controllers/Routers**: traducen HTTP → comando → respuesta HTTP
- **CLI commands**: para tareas administrativas
- **Event listeners**: para integración con colas/mensajería

**Regla:** Interfaces NO contiene lógica de negocio. Solo parsing, validación de formato (no de reglas), y delegación.

---

## 3. Authorization Flow

El diseño de autorización combina dos patrones:

### 3.1 Verificación ("antes de crear, pregunta si puede")

Cada caso de uso que crea o modifica datos llama a `AuthorizationPort.check()` al inicio:

```
UseCase.execute(command):
    auth_port.check(usuario, recurso, accion)  → si FALSE, denegar
    domain.logica_de_negocio()
    repo_port.guardar()
```

El `check()` es síncrono y sin efectos secundarios. Su implementación:

1. Obtiene el role del usuario (del token JWT)
2. Resuelve asignaciones (role + scope)
3. Verifica matriz de permisos
4. Aplica excepciones (deny siempre gana)
5. Retorna bool

### 3.2 Restricciones de contexto (instancia)

Después del `check()` genérico, el servicio puede validar restricciones específicas:

- El operador solo registra descargas de su máquina asignada
- El supervisor solo ve datos de su turno
- Calidad puede inspeccionar cualquier máquina

Esto NO es autorización genérica — es **lógica de negocio** que vive en Application o Domain según el caso.

### 3.3 Resumen

| Capa | Responsabilidad |
|------|----------------|
| **Domain** | `check_access(user, resource_type, action) → bool` — algoritmo puro |
| **Application** | Llama a `AuthorizationPort.check()` antes de cada operación |
| **Infrastructure** | Cache de asignaciones, decoder de JWT, implementación del port |
| **Interfaces** | Traduce 403 HTTP, extrae token del header |

---

## 4. Append-only y Audit Trail

### 4.1 Registros de negocio (append-only por dominio)

Tres dominios modelan sus registros como **inmutables por definición de negocio**:

| Contexto | Registros inmutables | Corrección |
|----------|---------------------|------------|
| **Warehouse** | Movements (entry/exit) | Nuevo Movement con `referenceMovement` |
| **Yarn Spinning** | ProductionDischarge, Advance, QualityControl, WasteRecord | Nuevo registro con trazabilidad |
| **Lot Processing** | StageRecord (cerrado), Observations | Nueva Observation |

Estos registros **NO son un log de auditoría** — son la fuente de verdad. El stock se calcula de movements. La producción se suma de discharges. No hay estado mutable separado que auditar.

### 4.2 Qué NO necesita audit trail separado

- **Authorization checks**: no generan registros. El registro creado después del check es el trail.
- **Lecturas**: no se auditan.
- **Operaciones denegadas**: log de infraestructura (no persistente), no dominio.

### 4.3 Qué SÍ necesita audit trail (pendiente)

| Cambio | Por qué |
|--------|---------|
| Asignaciones RBAC | Estado mutable que requiere trazabilidad |
| Cambios en catálogos compartidos | Quién agregó/modificó un título o máquina |
| Cierre/apertura de períodos | Control contable |

Estos se resolverán con Domain Events o `AuditLog` genérico en una iteración futura.

---

## 5. Comunicación entre Contextos

El sistema tiene dos bounded contexts principales que comparten la entidad **Lot**:

```
┌──────────────────────────────────────────────────┐
│                   WAREHOUSE                       │
│  Propietario de la identidad del Lot              │
│  - Crea el código NN-GGGG-NNN                    │
│  - Movements de entrada/salida                    │
│  - StockBalance (calculado)                       │
├──────────────────────────────────────────────────┤
│                   OPERATION                       │
│  Consume el código del Lot (read-only)            │
│  - StageRecords (6 etapas secuenciales)           │
│  - Observations                                   │
│  - QualityClassification                          │
└──────────────────────────────────────────────────┘
```

**Reglas de comunicación:**

- Cada contexto es dueño de sus datos
- Warehouse emite el Lot a Operation; Operation no modifica la identidad
- La comunicación entre contextos es vía el código de lote compartido (`NN-GGGG-NNN`)
- Cada contexto persiste en su propio esquema/tablas
- NO hay llamadas directas entre contextos en tiempo real — la consistencia es eventual

---

## 6. Decisiones Arquitectónicas Registradas

| ID | Decisión | Alternativas | Por qué |
|----|----------|-------------|---------|
| ADR-001 | Hexagonal con Casos de Uso explícitos | Capas simple, CQRS, Modular | Pureza del dominio, intercambiabilidad, testabilidad |
| ADR-002 | Monorepo con raíz compartida | Multi-repo | Un equipo, un proyecto; contexto compartido |
| ADR-003 | Append-only para registros de negocio | Estado mutable + auditoría | Es requisito de negocio, no decisión técnica |
| ADR-004 | Auth check como port de infraestructura | Middleware global, decoradores | Cada caso de uso decide cuándo y cómo verificar |
| ADR-005 | RBAC: seed + code (sin UI de permisos) | UI de gestión de permisos | Simplicidad en etapa inicial |
| ADR-006 | Contextos aislados, consistencia eventual | Llamadas síncronas entre contextos | Cada contexto evoluciona independientemente |

---

## 7. Estructura de Código Esperada (Monorepo)

```
└── src/
    ├── context/
    │   ├── warehouse/
    │   │   ├── domain/
    │   │   ├── application/
    │   │   ├── infrastructure/
    │   │   └── interfaces/
    │   ├── operation/
    │   │   ├── yarn-spinning/
    │   │   └── lot-processing/
    │   └── auth/
    │       ├── domain/
    │       ├── application/
    │       ├── infrastructure/
    │       └── interfaces/
    └── shared/
        ├── domain/      (value objects compartidos)
        └── kernel/      (abstracciones base: Entity, ValueObject, Port)
```

Cada contexto sigue la misma estructura hexagonal. `shared/kernel` contiene las abstraccionesbase que todos los contextos usan.

---

## 8. Pendientes para Próximas Iteraciones

- [ ] Definir mecanismo de Domain Events para cambios de estado mutable
- [ ] Definir política de correcciones cross-domain (Operation → Warehouse)
- [ ] Definir manejo de correcciones en períodos contables cerrados
- [ ] Diseño detallado de API (contratos por contexto)
- [ ] Política de caché para autorización (invalidez por cambio de asignación)
