# Reporte corregido de arquitectura y plan de refactor del backend

> Este reporte deriva del PRD y la arquitectura vigentes. No los reemplaza ni
> puede autorizar reglas de negocio que esos documentos no hayan aprobado.

## Veredicto ejecutivo

El backend debe adoptar una organización **primero por capacidad** antes de agregar endpoints o bounded contexts. La capacidad inicial será `warehouse.bales`, con su propio dominio, aplicación, puertos y adaptadores.

Este refactor es estructural. Debe preservar el contrato HTTP, el comportamiento transaccional y el esquema existente. No autoriza rediseños de base de datos ni cambios funcionales encubiertos.

Las decisiones centrales quedan cerradas:

- `Bale` es un agregado raíz con identidad y ciclo de vida independientes.
- `RawMaterialBatch` es la agrupación de dominio inmutable identificada por `ShipmentNumber`.
- La recepción es una acción de aplicación que registra un `RawMaterialBatch` y uno o más `Bale` de forma atómica; no es una entidad ni un agregado.
- El namespace transversal `raw_material` debe desaparecer en favor del módulo vertical `warehouse.bales`.
- El endpoint público sigue siendo exactamente `POST /api/v1/warehouse/bales`, con su comportamiento colectivo actual.
- La siguiente capacidad funcional será la entrega de varios fardos a Producción, cargando cada `Bale` de forma independiente.
- `delivered_at` es la única evidencia obligatoria actual de entrega; los responsables que entregan o reciben quedan diferidos.

## Alcance y restricciones

### Incluido

- Corregir los artefactos SDD antes de reanudar implementación.
- Resolver de forma segura el residuo del PR1 interrumpido.
- Introducir composición jerárquica de routers.
- Mover el slice completo a `warehouse.bales`.
- Alinear nombres estructurales estables y límites hexagonales.
- Preservar y verificar el comportamiento actual.
- Preparar el siguiente caso de uso de entrega sin implementarlo dentro del refactor P0.

### Fuera de alcance

- Nuevos endpoints durante P0.
- Nuevos estados del ciclo de vida distintos de los dos confirmados.
- Cambios de tablas, restricciones, RLS, privilegios o historial de migraciones.
- CRUD genérico para corregir datos compartidos de una partida.
- Factories, eventos de dominio, CQRS o servicios adicionales sin una necesidad demostrada.
- Renombres menores o especulativos que no sean necesarios para establecer la estructura.

## Hechos de dominio autoritativos

### `RawMaterialBatch`

`RawMaterialBatch` representa la partida o agrupación de materia prima recibida bajo un mismo `ShipmentNumber`.

Propiedades confirmadas:

- Es una entidad de dominio identificada por `ShipmentNumber`.
- Agrupa uno o más `Bale`.
- Posee la evidencia compartida de recepción/partida: número de envío, fecha de recepción y evidencia de proveedor.
- Sus datos compartidos son inmutables en los flujos normales.
- Una eventual corrección de typo debe ser un caso de uso explícito, autorizado y auditable; no una actualización CRUD genérica.
- No es un lote o batch de producción.

El término `provider` o `supplier` no se renombra en este refactor sin validación del lenguaje ubicuo. El contrato público existente se conserva.

### `Bale`

`Bale` es un agregado raíz independientemente direccionable y propietario de su ciclo de vida.

Consecuencias:

- Cada fardo se carga y persiste por su propia identidad.
- La identidad técnica es independiente; la identidad visible para el negocio es `shipment_number + bale_number`.
- El estado de un fardo puede cambiar sin cargar todos los fardos de su `RawMaterialBatch`.
- La pertenencia a una partida se representa por referencia a la identidad de `RawMaterialBatch`, no mediante un grafo completo obligatorio.
- Las reglas de transición pertenecen a `Bale`, no al caso de uso ni al ORM.

### Recepción

`Reception` y `BaleReception` no son entidades ni agregados del dominio.

La recepción es la acción de aplicación que, en una única solicitud y transacción:

1. valida el comando colectivo;
2. crea y registra un `RawMaterialBatch`;
3. crea y registra uno o más agregados `Bale` asociados;
4. confirma el conjunto de forma atómica;
5. devuelve el resultado colectivo existente.

La atomicidad entre estos agregados es una necesidad del caso de uso de alta inicial. No convierte el encabezado de persistencia en un agregado llamado `Reception`.

## Ciclo de vida de `Bale`

El modelo actual tiene exactamente dos estados:

```python
class BaleStatus(Enum):
    IN_WAREHOUSE = "in_warehouse"
    IN_PRODUCTION = "in_production"
```

La única transición actual es:

```text
IN_WAREHOUSE -> IN_PRODUCTION
```

La transición debe:

- registrar `delivered_at` como la fecha y hora en que el fardo fue entregado;
- rechazar una nueva entrega de un fardo ya entregado;
- rechazar la transición si falta el timestamp;
- mantener la decisión dentro del agregado `Bale`.
- no exigir responsable que entrega ni responsable receptor en el alcance actual.

No se deben usar `STAGED`, `PROCESSED` ni `DELIVERED` como estados finales. El estado modelado expresa que el fardo está bajo ubicación/custodia de Producción.
La entrega es el hecho que causa la transición; `IN_PRODUCTION` no significa que el fardo haya sido consumido o procesado.

Tampoco se debe introducir `is_in_warehouse` como reemplazo automático y más verboso de `is_available`. Ambos helpers se eliminan o difieren hasta que exista una política real que justifique una consulta nombrada. El método de transición debe imponer directamente la elegibilidad.

El verbo exacto del método de dominio se validará con el lenguaje ubicuo. No se impone `issue_to_production()` solo por ser más explícito; un verbo conciso es válido dentro de `warehouse.bales.domain.bale.Bale` si expresa inequívocamente la operación.

## Decisión estructural

### Organización por capacidad

La dirección canónica es:

```text
backend/src/warehouse/
└── bales/
    ├── domain/
    ├── application/
    ├── ports/
    └── adapters/
        ├── http/
        └── persistence/
```

Regla de dependencias:

```text
adapters -> application -> domain
                 |
                 -> ports
```

El núcleo define las abstracciones que necesita. Los adaptadores implementan esas abstracciones y contienen los detalles de FastAPI, SQLAlchemy y PostgreSQL.

`raw_material` se elimina como namespace Python transversal. No debe quedar como propietario de implementaciones canónicas.

### Bounded contexts

Los aliases de contextos aprobados son `warehouse`, `yarn-production`,
`batch-processing`, `access` y `catalogs`. Solo en ejemplos de paquetes Python,
los guiones se representan como guiones bajos:

```text
warehouse
yarn_production
batch_processing
access
catalogs
```

No se deben recomendar ni introducir los aliases supersedidos `spinning`, `lot_processing`, `access_control` o `reference_data`.

No se crean ahora paquetes vacíos para contextos futuros. Esta lista establece la convención cuando cada contexto sea implementado.

### Composición jerárquica de routers

La propiedad del path debe componerse jerárquicamente:

```text
/api/v1 -> /warehouse -> /bales
```

Cada nivel posee únicamente su prefijo. El ensamblaje debe conservar exactamente:

```http
POST /api/v1/warehouse/bales
```

También debe conservar el comportamiento actual respecto de slash final. No se acepta un redirect nuevo, una ruta duplicada ni una variante adicional como resultado del refactor.

### Superficies de paquete

Los archivos `__init__.py` deben ser mínimos y deliberados.

- Reexportar solo una API pública estable y necesaria.
- Preferir imports desde el módulo propietario.
- No convertir cada capa en una fachada global.
- Evitar aliases permanentes que oculten el origen canónico.

Ejemplo preferido:

```python
from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
```

## Modelo de aplicación y naming

### Convención estable

Los casos de uso siguen esta convención:

- clase: verbo + objeto;
- entrada: mismo nombre + `Command`;
- salida: mismo nombre + `Result`;
- operación uniforme: `execute()`.

Ejemplos coherentes:

```python
warehouse.bales.domain.raw_material_batch.RawMaterialBatch
warehouse.bales.domain.bale.Bale
warehouse.bales.application.receive_bales.ReceiveBales
ReceiveBalesCommand
ReceiveBalesResult
DeliverBales
DeliverBalesCommand
```

`ReceiveBales` es el nombre provisional coherente para el alta colectiva. Debe validarse con el lenguaje de negocio antes de estabilizarlo, pero el reporte y los artefactos SDD no deben volver a usar `RegisterReception` como nombre canónico después de eliminar Reception del modelo de dominio.

Los modelos HTTP mantienen nombres de campos compatibles con el contrato existente. Los nombres de transporte no tienen que copiar exactamente los nombres internos del dominio.

### Puertos y adaptadores

Los repositorios se definen por agregado, no por tabla.

Puertos posibles según comportamiento requerido:

```python
RawMaterialBatchRepository
BaleRepository
Transaction
```

`RawMaterialBatchRepository` y `BaleRepository` solo deben existir si cada agregado necesita comportamiento de persistencia expresado por el caso de uso. El alta colectiva puede coordinar ambos dentro de una transacción sin crear puertos duplicados que reflejen mecánicamente las tablas de encabezado y detalle.

Los adaptadores concretos hacen visible la tecnología una sola vez por FQN. Por ejemplo:

```python
warehouse.bales.adapters.persistence.raw_material_batch_repository.SqlAlchemyRawMaterialBatchRepository
warehouse.bales.adapters.persistence.bale_repository.SqlAlchemyBaleRepository
```

Se debe evitar repetir tecnología en paquete, módulo y clase simultáneamente, por ejemplo `sqlalchemy/sqlalchemy_bale_repository/SqlAlchemyBaleRepository`.

Los nombres definitivos de módulos concretos pueden simplificarse mientras la FQN siga siendo inequívoca.

### Transacción y sesión

Se usa `Transaction`, no `UnitOfWork`, mientras la abstracción solo controle límites transaccionales y no sea propietaria de repositorios.

La composición debe preservar:

- una sesión por request;
- la misma sesión compartida por repositorios y transacción;
- inserción del encabezado normalizado antes de sus detalles;
- commit atómico;
- rollback ante fallo;
- traducción de las dos restricciones de unicidad nombradas a conflictos de aplicación;
- propagación de errores de integridad desconocidos.

No se debe crear una sesión independiente por repositorio ni ocultar repositorios dentro de `Transaction`.

## Persistencia y migraciones

El esquema normalizado de encabezado/detalle se conserva durante este refactor.

La distinción es obligatoria:

- El modelo de dominio expresa identidad, comportamiento e invariantes.
- Los records ORM expresan tablas y relaciones de persistencia.
- Un record o tabla existente no obliga a crear un agregado de dominio con el mismo nombre.

Por tanto, el encabezado persistido puede mapear a `RawMaterialBatch` aunque la tabla histórica conserve su nombre actual. Este refactor no justifica una migración destructiva ni una reescritura del historial.

Se mantienen sin cambios:

- migraciones existentes;
- nombres de tablas y columnas;
- restricciones y sus nombres;
- unicidad global de shipment number;
- unicidad de bale number dentro de la recepción/partida persistida;
- RLS;
- revocaciones y privilegios.

El reset local de Supabase es una verificación del esquema existente, no un paso para regenerar o reemplazar migraciones.

## Contrato HTTP preservado

P0 no cambia el comportamiento observable de:

```http
POST /api/v1/warehouse/bales
```

Debe conservarse:

- el mismo path y método;
- la misma política de slash;
- el input de múltiples fardos;
- el output colectivo actual;
- validaciones y códigos HTTP existentes;
- conflictos conocidos por shipment number y bale number;
- atomicidad del alta;
- propagación de fallos de integridad no reconocidos.

Cualquier mejora del contrato requiere una propuesta separada.

## Estado del PR1 interrumpido

El PR1 parcial debe tratarse como **residuo no verificado de un incidente**, no como implementación completada.

Evidencia conocida:

- la ejecución fue interrumpida;
- no existe apply-progress persistido;
- no existe receipt de revisión reutilizable;
- no hay tareas completadas que puedan asumirse válidas;
- parte del árbol nuevo envuelve implementaciones antiguas, con dirección de propiedad nuevo -> viejo;
- faltan pruebas bajo la nueva capacidad.

La parte recuperable debe auditarse después de corregir propuesta, spec, diseño y tareas. Se debe reparar o revertir de forma explícita; no continuar silenciosamente sobre el árbol parcial ni asumir que sus aliases representan la arquitectura final.

Los FQN antiguos solo pueden sobrevivir temporalmente como aliases acotados hacia implementaciones canónicas nuevas:

```text
old FQN -> new canonical FQN
```

Nunca al revés. Cada alias temporal necesita alcance, consumidor concreto y criterio de eliminación. Si no existe compatibilidad externa o persistida que lo requiera, se elimina en el mismo refactor.

## Matriz de prioridades

| Prioridad | Objetivo | Resultado esperado |
|---|---|---|
| P0 | Establecer la plantilla arquitectónica antes de más endpoints o contextos | Slice actual movido y verificado sin cambios de comportamiento |
| P1 | Implementar entrega colectiva a Producción | Transición y timestamp de cada `Bale` probados sobre agregados cargados individualmente |
| P2 | Mejoras opcionales con evidencia futura | Complejidad agregada solo cuando exista una necesidad concreta |
| Rechazado/supersedido | Evitar decisiones incorrectas o prematuras | Artefactos e implementación libres de esos enfoques |

## P0: refactor estructural obligatorio

La secuencia es deliberada y no debe alterarse silenciosamente:

1. Congelar en este reporte y en los artefactos SDD las decisiones corregidas de dominio, arquitectura, naming y compatibilidad.
2. Corregir proposal, spec, design y tasks antes de reanudar implementación.
3. Auditar y reparar o revertir de forma segura el PR1 parcial interrumpido; queda prohibida su continuación silenciosa.
4. Introducir composición jerárquica de routers `/api/v1` -> `/warehouse` -> `/bales` preservando path y slash.
5. Mover el slice completo a `warehouse.bales` con propiedad en la dirección nueva; los FQN antiguos solo pueden ser aliases temporales acotados hacia implementaciones canónicas nuevas.
6. Ajustar imports y pruebas sin cambiar comportamiento.
7. Reducir las fachadas `__init__.py` a superficies mínimas deliberadas.
8. Aplicar únicamente renombres estructurales estables, incluidos `RawMaterialBatch`, `ReceiveBales`, `Command`, `Result` y `Transaction` cuando corresponda.
9. Separar puertos y adaptadores preservando sesión compartida, atomicidad, orden de inserción, traducción de restricciones nombradas y propagación de integridad desconocida.
10. Verificar backend completo, descubrimiento de paquetes, import ASGI/OpenAPI, suite unitaria, reset/estado de migraciones Supabase e integración PostgreSQL.

P0 termina solo cuando todos los gates de aceptación están satisfechos. No se abre un endpoint nuevo en paralelo para “probar” la estructura.

## P1: entrega de fardos a Producción

P1 implementará el siguiente caso de uso sobre los límites ya decididos:

```python
DeliverBales
DeliverBalesCommand
```

El comando de aplicación debe aceptar múltiples identidades de `Bale`. La cifra
aproximada de 18 fardos por día es una observación operativa no normativa, no un
máximo ni una regla de validación. Debe:

1. cargar cada `Bale` de forma independiente mediante `BaleRepository`;
2. invocar en cada agregado la transición `IN_WAREHOUSE -> IN_PRODUCTION`;
3. proporcionar y registrar `delivered_at`;
4. rechazar reentregas;
5. rechazar timestamp ausente;
6. persistir cada agregado modificado según el límite transaccional que se apruebe para el comando;
7. no cargar el `RawMaterialBatch` completo ni todos sus fardos.

P1 se usa para implementar y verificar el comportamiento del ciclo de vida, no para reabrir por defecto los límites de agregado. Estos límites solo pueden revisarse si aparece evidencia de dominio contradictoria y documentada.
La atomicidad de una futura entrega de múltiples fardos permanece abierta: el
comando puede agrupar varios fardos, pero cada transición de `Bale` es
independiente y este reporte no impone todavía éxito o rollback colectivo.

## P2: diferido

Los siguientes temas quedan fuera de P0 y P1 salvo evidencia nueva:

- factories;
- eventos de dominio;
- servicios de dominio o aplicación adicionales;
- correcciones generalizadas de datos compartidos;
- estados adicionales;
- limpieza de estilo de mappers;
- renombres menores de value objects;
- puertos de entrada explícitos;
- CQRS prematuro.

“Diferido” no significa aprobado. Cada elemento requiere un problema concreto y su propia decisión.

## Rechazado o supersedido

| Enfoque | Motivo |
|---|---|
| `BaleReception` o `Reception` como entidad/agregado | La recepción es una acción de aplicación; la agrupación de dominio es `RawMaterialBatch` y el ciclo de vida independiente pertenece a `Bale`. |
| `RegisterReception` como caso de uso canónico | Mantiene un sustantivo de dominio eliminado. Se usa provisionalmente `ReceiveBales`. |
| Renombrar automáticamente `is_available` a `is_in_warehouse` | Solo reemplaza ambigüedad por verbosidad; el helper se difiere hasta existir una política real. |
| Mandatar `issue_to_production()` solo por verbosidad | El verbo debe ser conciso, contextual y validado con lenguaje ubicuo. |
| `DELIVERED`, `PROCESSED` o `STAGED` como estado final | No expresan la condición confirmada de ubicación/custodia `IN_PRODUCTION`. |
| `UnitOfWork` antes de poseer repositorios | La abstracción actual solo controla transacciones y debe llamarse `Transaction`. |
| Valores especulativos del enum `Material` | No hay evidencia de negocio suficiente para inventar o renombrar clasificaciones. |
| Framework repetido en cada nivel de una FQN | Añade ruido sin mejorar identidad; la tecnología aparece una vez en el adaptador. |
| Reescritura destructiva del historial de migraciones | Un refactor de paquetes no modifica el esquema ni invalida migraciones aplicadas. |
| Repositorio por tabla | Los repositorios representan agregados y comportamiento de persistencia, no records ORM. |
| Implementación canónica antigua envuelta por paquetes nuevos | Invierte la propiedad deseada y prolonga `raw_material`; la dirección válida es antiguo -> nuevo y solo si existe necesidad temporal. |

## Gates de aceptación de P0

### Dominio y aplicación

- [ ] `Bale` es el agregado raíz y propietario de su ciclo de vida.
- [ ] `RawMaterialBatch` representa la agrupación inmutable identificada por `ShipmentNumber`.
- [ ] No existe `Reception` ni `BaleReception` como entidad o agregado canónico.
- [ ] El alta colectiva se expresa con `ReceiveBales`, `ReceiveBalesCommand`, `ReceiveBalesResult` y `execute()`.
- [ ] No se agregan estados, helpers ni reglas no confirmadas.

### Estructura y dependencias

- [ ] El slice completo pertenece a `warehouse.bales.{domain,application,ports,adapters}`.
- [ ] `raw_material` deja de ser namespace propietario.
- [ ] Todo alias temporal apunta del FQN antiguo al nuevo y tiene criterio de eliminación.
- [ ] Los `__init__.py` exponen únicamente superficies deliberadas.
- [ ] El núcleo no importa FastAPI, SQLAlchemy ni PostgreSQL.
- [ ] Los repositorios corresponden a agregados, no a tablas.
- [ ] Se usa `Transaction`, no `UnitOfWork`.

### HTTP y composición

- [ ] La jerarquía de routers es `/api/v1` -> `/warehouse` -> `/bales`.
- [ ] Existe exactamente `POST /api/v1/warehouse/bales` con la política de slash previa.
- [ ] Request, response, errores y códigos HTTP preservan el comportamiento anterior.
- [ ] El esquema OpenAPI no contiene rutas duplicadas o accidentales.

### Persistencia

- [ ] Repositorios y transacción comparten la misma sesión request-scoped.
- [ ] El alta registra encabezado y detalles en una sola transacción.
- [ ] Las dos restricciones nombradas conservan su traducción a conflictos de aplicación.
- [ ] Los errores de integridad desconocidos se propagan.
- [ ] No cambian migraciones, tablas, restricciones, RLS ni privilegios.

### Verificación

- [ ] El paquete editable descubre `warehouse`, `infra` y `bootstrap` correctamente.
- [ ] El import de la aplicación ASGI funciona con configuración válida.
- [ ] La ruta y OpenAPI ensamblados son correctos.
- [ ] La suite unitaria completa pasa.
- [ ] El reset local aplica el historial existente sin seed.
- [ ] El estado local de migraciones es consistente.
- [ ] La suite de integración PostgreSQL pasa contra el Supabase local migrado.
- [ ] No se reutiliza ningún receipt previo al incidente.

## Comandos de verificación posteriores

Estos comandos documentan la verificación exigida. No deben ejecutarse durante la edición de este reporte.

### Suite unitaria del backend

```bash
uv run --locked python -m unittest discover -s backend/tests -v
```

### Módulo o test enfocado

```bash
uv run --locked python -m unittest backend.tests.test_warehouse.domain.test_raw_material_bale -v
```

Se puede agregar la clase o el método punteado al comando del módulo.

### Supabase local

```bash
supabase start
supabase db reset --local --no-seed
supabase migration list --local
```

`--no-seed` es obligatorio porque `supabase/config.toml` referencia `supabase/seed.sql` y ese archivo no existe.

### Integración PostgreSQL

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres \
  uv run --locked python -m unittest discover -s backend/integration_tests -v
```

La suite de integración acepta únicamente una URL `postgresql+psycopg` sobre loopback, puerto `54322`, base `postgres`.

### ASGI y OpenAPI

La verificación debe usar `backend/main.py`, cuyo símbolo público es `app`. Como `DATABASE_URL` es obligatorio al importar, se debe proporcionar una configuración válida. La creación del engine no conecta hasta que una request utiliza una sesión.

Se debe confirmar explícitamente:

- import correcto de `app`;
- única operación `POST /api/v1/warehouse/bales`;
- ausencia de variante accidental con slash;
- composición jerárquica reflejada en OpenAPI.

## Criterio de salida

El refactor P0 queda listo para revisión solo cuando:

1. los artefactos SDD reflejen estas decisiones sin contradicciones;
2. el residuo del PR1 interrumpido haya sido resuelto de forma explícita;
3. `warehouse.bales` sea propietario de la implementación canónica completa;
4. el contrato HTTP y la persistencia permanezcan invariantes;
5. todos los gates de verificación tengan evidencia nueva.

Hasta entonces, no se debe iniciar P1 ni otro bounded context. La finalidad de P0 no es reducir caracteres: es fijar una dirección de propiedad que permita crecer sin repetir el mismo dominio en cada capa ni confundir tablas con agregados.
