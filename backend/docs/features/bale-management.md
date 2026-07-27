---
document_type: technical-spec
status: active
implementation: partial
scope: warehouse/bales
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Technical Specification — Backend Bale Management

> **Normative PRD:** [Bale Management](../../../docs/prd/warehouse/bale-management.md)

**Product:** Colibri Hub  
**Context:** Warehouse  
**Type:** Technical Specification — Backend  
**Status:** Partially implemented  
**Technical baseline:** Repository `luiscm17/colibri-hub`, branch `main`, commit `447ee79`  
**Complementary spec:** Frontend bale management technical specification  
**Date:** 26 de julio de 2026

---

## 1. Resumen ejecutivo

> This document is a **technical specification** describing how the backend implements the bale management capability. Business rules and acceptance criteria are defined in the [normative PRD](../../../docs/prd/warehouse/bale-management.md); this specification details the implementation approach, API contracts, and architecture.

El backend de Warehouse ya permite registrar una partida de materia prima y todos sus fardos mediante una operación transaccional. La capacidad está implementada con FastAPI, Pydantic, SQLAlchemy, PostgreSQL y migraciones Supabase, siguiendo una arquitectura hexagonal orientada al dominio `warehouse.bales`.

Esta especificación técnica define la evolución necesaria para completar el flujo de gestión de fardos requerido por el frontend:

1. Ajustar el registro masivo existente para trabajar con una fecha empresarial y una respuesta resumida.
2. Consultar indicadores agregados del inventario mediante filtros.
3. Consultar un fardo mediante la identidad empresarial compuesta por `shipment_number` y `bale_number`.
4. Cambiar de manera irreversible el estado de un fardo de `in_warehouse` a `delivered`.

El alcance mantiene el modelo de negocio actual: los fardos son unidades discretas, se entregan completos, `delivered` representa entregado/utilizado por Producción y no existen devoluciones ni estados adicionales.

## 2. Situación actual del backend

> **Implementation status**: This section describes both the **current implementation** and the **target state**. Section 2.1 documents what is already built; section 2.2 lists the gaps that remain to reach the target state defined in the normative PRD.

### 2.1 Capacidades disponibles

El repositorio contiene actualmente:

- Endpoint `POST /api/v1/warehouse/bales`.
- Registro atómico de una cabecera `RawMaterialBatch` y uno o más `Bale`.
- Identificación global de la partida mediante `shipment_number`.
- Identificación empresarial del fardo mediante `shipment_number + bale_number`.
- Normalización a mayúsculas de `shipment_number`, `bale_number` y `material_type`.
- Estados `in_warehouse` y `delivered`.
- Regla de dominio `Bale.deliver()` para la transición irreversible a `delivered`.
- Cálculo de peso neto en el dominio como peso bruto menos tara.
- Puertos de repositorio, identidad y transacción.
- Adaptadores SQLAlchemy y composición de dependencias en FastAPI.
- Tablas `raw_material_batches` y `raw_material_bales`.
- Restricciones nombradas de integridad, índice por partida, RLS habilitado y privilegios revocados.
- Contrato común de errores con `code`, `message` y `fields`.
- Pruebas unitarias con `unittest` y pruebas de integración protegidas para PostgreSQL.

### 2.2 Brechas respecto al producto objetivo

| Área | Estado actual | Estado objetivo |
|---|---|---|
| Fecha de recepción | Fecha y hora con zona (`datetime` / `timestamptz`) | Fecha empresarial (`date` / `DATE`) |
| Cantidad de fardos por partida | Uno o más, sin máximo explícito | Entre 1 y 100 |
| Respuesta del registro | Incluye todos los fardos registrados | Incluye solo resumen y `bale_count` |
| Consulta agregada | No disponible | Resumen filtrable calculado en PostgreSQL |
| Consulta individual | No disponible | Búsqueda por partida y número de fardo |
| Actualización de estado | Regla de dominio disponible, sin caso de uso ni endpoint | `PATCH` irreversible a `delivered` |
| Lectura de repositorios | Solo inserción | Proyecciones de consulta y carga de fardo para transición |
| Integración navegador | Sin política CORS configurada | Orígenes permitidos mediante configuración |

## 3. Objetivos

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> Objectives below reflect implementation targets derived from the PRD.

### 3.1 Objetivos funcionales

- Registrar en una sola transacción una partida de entre 1 y 100 fardos.
- Tratar `received_at` como fecha de negocio sin inventar una hora.
- Entregar al frontend una respuesta de registro breve y estable.
- Calcular en backend cantidades y pesos agregados sobre datos persistidos.
- Localizar inequívocamente un fardo con `shipment_number + bale_number`.
- Exponer los datos completos necesarios para la pantalla de detalle.
- Permitir únicamente la transición `in_warehouse → delivered`.
- Mantener contratos de errores utilizables por popups generales y errores de campo o celda.

### 3.2 Objetivos técnicos

- Extender el límite de capacidad existente `warehouse.bales`.
- Mantener la dirección de dependencias de la arquitectura hexagonal.
- Reutilizar el comportamiento de dominio ya implementado para la entrega.
- Separar comandos de escritura de consultas de lectura sin incorporar una plataforma CQRS.
- Conservar precisión decimal en entrada, persistencia, cálculos y respuestas.
- Proteger la atomicidad del registro y la exclusividad de la transición de estado.
- Documentar todos los contratos mediante OpenAPI y pruebas automatizadas.

## 4. Alcance

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> Scope boundaries below describe the technical implementation scope.

### 4.1 Incluido

- Ajustes al endpoint de registro existente.
- Migración de `received_at` a tipo fecha.
- Endpoint de resumen agregado.
- Endpoint de detalle individual.
- Endpoint de actualización parcial del estado.
- Nuevos casos de uso, puertos, adaptadores, modelos HTTP y composición.
- Extensión del contrato de errores.
- Índices necesarios para las consultas aprobadas.
- Configuración CORS para la aplicación web.
- Pruebas de dominio, aplicación, persistencia, HTTP, OpenAPI e integración PostgreSQL.
- Actualización de documentación técnica y de negocio afectada.

### 4.2 Fuera de alcance

- Autenticación, RBAC y políticas de autorización por usuario.
- Integración del backend con Supabase Auth.
- Nuevos estados de fardo.
- Entregas parciales.
- Devoluciones a almacén.
- Historial o auditoría de movimientos.
- Fecha, responsable, destino o referencia de entrega.
- Listado general o paginado de fardos.
- Edición de pesos, material, Dtex, proveedor, partida o número de fardo.
- Eliminación de partidas o fardos.
- Métricas del contexto Producción distintas del estado `delivered`.
- Totales enviados por el frontend durante el registro.

## 5. Reglas de negocio

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> The rules below are reproduced for implementation reference. The [normative PRD](../../../docs/prd/warehouse/bale-management.md) is authoritative.

| ID | Regla |
|---|---|
| BR-01 | Una partida contiene entre 1 y 100 fardos. |
| BR-02 | `shipment_number` es único globalmente. |
| BR-03 | `bale_number` es único dentro de una partida y puede repetirse en partidas distintas. |
| BR-04 | La identidad empresarial de un fardo es `shipment_number + bale_number`. |
| BR-05 | Los identificadores empresariales y el tipo de material se normalizan según las reglas existentes del dominio. |
| BR-06 | `received_at` representa únicamente la fecha empresarial de recepción. |
| BR-07 | Todo fardo nuevo se registra con estado `in_warehouse`. |
| BR-08 | Los únicos estados permitidos son `in_warehouse` y `delivered`. |
| BR-09 | La única transición admitida es `in_warehouse → delivered`. |
| BR-10 | Un fardo `delivered` no puede volver a `in_warehouse` ni entregarse nuevamente. |
| BR-11 | La entrega afecta siempre a un fardo completo. |
| BR-12 | Para este alcance, `delivered` significa entregado y utilizado por Producción. |
| BR-13 | El peso neto es `gross_weight_kg - container_weight_kg` y nunca se recibe como dato persistible del cliente. |
| BR-14 | Dtex y pesos se manejan como decimales finitos; el peso bruto debe ser mayor que la tara. |
| BR-15 | El registro de la partida y todos sus fardos es atómico. |
| BR-16 | Los filtros de una consulta se combinan mediante conjunción: un fardo debe cumplir todos los filtros proporcionados. |

## 6. Diseño funcional de la API

### 6.1 Inventario de operaciones

| Capacidad | Método | Ruta | Resultado principal |
|---|---|---|---|
| Registrar partida | `POST` | `/api/v1/warehouse/bales` | Resumen de la partida creada |
| Consultar resumen | `GET` | `/api/v1/warehouse/bales/summary` | Cantidades y pesos agregados |
| Consultar fardo | `GET` | `/api/v1/warehouse/bales/detail` | Detalle de un fardo |
| Cambiar estado | `PATCH` | `/api/v1/warehouse/bales/{bale_id}/status` | Confirmación del estado actualizado |

`summary` y `detail` son recursos de consulta diferentes. El primero devuelve agregados; el segundo devuelve un único fardo. Ninguno reemplaza al otro ni devuelve un listado exhaustivo.

## 7. Registro masivo de una partida

### 7.1 Endpoint

`POST /api/v1/warehouse/bales`

### 7.2 Request

| Campo | Tipo de contrato | Requerido | Regla |
|---|---|---:|---|
| `shipment_number` | String | Sí | No vacío, máximo 10 caracteres tras normalización, único globalmente |
| `received_at` | Fecha ISO `YYYY-MM-DD` | Sí | Fecha empresarial válida |
| `provider_name` | String | Sí | No vacío después de eliminar espacios exteriores |
| `bales` | Colección | Sí | Entre 1 y 100 elementos |
| `bales.n.bale_number` | String | Sí | Máximo 10 caracteres; único dentro de la partida |
| `bales.n.material_type` | String | Sí | Máximo 20 caracteres; normalizado por dominio |
| `bales.n.dtex` | String decimal | Sí | Finito y mayor que cero |
| `bales.n.gross_weight_kg` | String decimal | Sí | Finito y mayor que cero |
| `bales.n.container_weight_kg` | String decimal | Sí | Finito, mayor que cero y menor que el peso bruto |

No se aceptan campos adicionales. Los decimales continúan enviándose como strings JSON para conservar precisión.

### 7.3 Response exitoso

**Estado:** `201 Created`

| Campo | Tipo |
|---|---|
| `raw_material_batch_id` | UUID |
| `shipment_number` | String normalizado |
| `received_at` | Fecha ISO |
| `provider_name` | String |
| `bale_count` | Entero |

La respuesta no incluye el arreglo `bales`, peso neto ni identificadores temporales del frontend.

### 7.4 Comportamiento requerido

- Validar toda la entrada antes de persistir.
- Generar identidades técnicas en backend.
- Insertar primero la partida y después sus fardos dentro de una única transacción.
- Revertir la operación completa ante cualquier error.
- Mantener la traducción estable del conflicto de `shipment_number`.
- Producir rutas indexadas para errores asociados a un fardo cuando pueda identificarse el elemento, por ejemplo `bales.17.gross_weight_kg`.

## 8. Resumen agregado del inventario

### 8.1 Endpoint

`GET /api/v1/warehouse/bales/summary`

### 8.2 Filtros

Todos los filtros son opcionales.

| Query parameter | Tipo | Semántica |
|---|---|---|
| `received_from` | Fecha ISO | Incluye recepciones desde esta fecha |
| `received_to` | Fecha ISO | Incluye recepciones hasta esta fecha |
| `shipment_number` | String | Coincidencia exacta tras normalización |
| `status` | Enum | `in_warehouse` o `delivered` |
| `provider_name` | String | Coincidencia exacta sin distinguir mayúsculas, ignorando espacios exteriores |
| `material_type` | String | Coincidencia exacta tras normalización |
| `dtex` | String decimal | Coincidencia decimal exacta |

Los límites de fecha son inclusivos. Si se proporcionan ambos, `received_from` no puede ser posterior a `received_to`.

### 8.3 Response exitoso

**Estado:** `200 OK`

| Campo | Tipo | Definición |
|---|---|---|
| `total_bale_count` | Entero | Fardos que cumplen los filtros |
| `in_warehouse_bale_count` | Entero | Fardos filtrados actualmente en almacén |
| `delivered_bale_count` | Entero | Fardos filtrados entregados/utilizados |
| `net_weight_total_kg` | String decimal | Peso neto total filtrado |
| `net_weight_in_warehouse_kg` | String decimal | Peso neto filtrado en almacén |
| `net_weight_delivered_kg` | String decimal | Peso neto filtrado entregado/utilizado |

Si no existen coincidencias, las cantidades deben ser `0` y los pesos deben serializarse como cero decimal; no se responde `404`.

Cuando se aplica un filtro de estado, el total representa únicamente ese subconjunto y el contador del estado contrario es cero. Los pesos deben calcularse en PostgreSQL sobre datos persistidos; el backend no debe cargar todos los fardos para agregarlos en memoria.

## 9. Consulta individual de un fardo

### 9.1 Endpoint

`GET /api/v1/warehouse/bales/detail`

### 9.2 Parámetros requeridos

| Query parameter | Tipo | Regla |
|---|---|---|
| `shipment_number` | String | Identificador de partida normalizado |
| `bale_number` | String | Identificador del fardo normalizado |

La consulta utiliza ambos valores. No se admite buscar únicamente por `bale_number`, porque este puede repetirse en distintas partidas.

### 9.3 Response exitoso

**Estado:** `200 OK`

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `shipment_number` | String |
| `bale_number` | String |
| `received_at` | Fecha ISO |
| `provider_name` | String |
| `material_type` | String |
| `dtex` | String decimal |
| `gross_weight_kg` | String decimal |
| `container_weight_kg` | String decimal |
| `net_weight_kg` | String decimal calculado |
| `status` | `in_warehouse` o `delivered` |

### 9.4 No encontrado

Si la combinación no existe, el backend responde `404 Not Found` con código `bale_not_found`. No debe revelar si existía la partida pero no el fardo, porque para el consumidor ambos valores forman una sola identidad de búsqueda.

## 10. Actualización del estado

### 10.1 Endpoint

`PATCH /api/v1/warehouse/bales/{bale_id}/status`

El UUID se obtiene previamente mediante el endpoint de detalle. Se usa como identidad técnica inequívoca para la escritura.

### 10.2 Request

| Campo | Tipo | Valor admitido |
|---|---|---|
| `status` | Enum | Únicamente `delivered` |

No se aceptan campos adicionales. El endpoint no funciona como editor genérico de estados.

### 10.3 Response exitoso

**Estado:** `200 OK`

| Campo | Tipo |
|---|---|
| `id` | UUID |
| `shipment_number` | String |
| `bale_number` | String |
| `status` | `delivered` |

### 10.4 Comportamiento requerido

- Cargar la entidad `Bale` por su UUID.
- Ejecutar la transición mediante la regla existente del dominio.
- Persistir exclusivamente el estado modificado.
- Confirmar la operación en una transacción.
- Responder `404` si el UUID no existe.
- Responder `409` con código `bale_already_delivered` si el estado ya es `delivered`.
- Rechazar cualquier intento de establecer `in_warehouse` u otro valor.
- Impedir que dos solicitudes concurrentes confirmen la entrega del mismo fardo. Solo una puede resultar exitosa; la otra debe recibir `409`.

## 11. Contrato de errores

Todas las operaciones mantienen el envelope actual:

| Campo | Uso |
|---|---|
| `error.code` | Código estable y procesable por el cliente |
| `error.message` | Resumen legible de la causa |
| `error.fields` | Errores asociados a rutas concretas; colección vacía cuando no aplica |

### 11.1 Matriz mínima

| Estado | Código | Caso |
|---:|---|---|
| 404 | `bale_not_found` | No existe el fardo solicitado |
| 409 | `duplicate_shipment_number` | La partida ya fue registrada |
| 409 | `bale_already_delivered` | El fardo ya no está disponible en almacén |
| 422 | `request_validation_error` | Tipo, campo requerido, valor o filtro inválido |
| 422 | `duplicate_bale_number` | Número repetido dentro de la partida |
| 422 | `domain_validation_error` | Regla de dominio incumplida |
| 500 | `internal_server_error` | Fallo no previsto sin detalles internos |

### 11.2 Rutas de campo

- Los errores Pydantic deben conservar rutas concretas como `received_at`, `status` o `bales.17.dtex`.
- Los errores generales de una partida pueden señalar `shipment_number`.
- Cuando el backend conozca el índice del fardo inválido, debe evitar rutas genéricas como `bales[].campo`.
- Los mensajes internos de base de datos, trazas, SQL y secretos nunca se incluyen en el response.

## 12. Arquitectura de aplicación

### 12.1 Principios

- La capacidad continúa bajo `warehouse.bales`.
- Los modelos HTTP no ingresan al dominio ni a los puertos.
- SQLAlchemy permanece restringido a adaptadores de persistencia e infraestructura.
- Las escrituras usan entidades y reglas de dominio.
- Las consultas devuelven proyecciones de lectura específicas para cada caso de uso.
- No se incorpora event sourcing, bus de comandos ni una base de datos de lectura separada.

### 12.2 Casos de uso requeridos

| Tipo | Responsabilidad |
|---|---|
| Comando | Registrar una partida completa |
| Consulta | Obtener resumen agregado con filtros |
| Consulta | Obtener detalle por identidad empresarial |
| Comando | Entregar un fardo a Producción |

El caso de entrega debe reutilizar `Bale.deliver()`. No debe modificar directamente el string de estado en el router o en el repositorio.

### 12.3 Puertos y adaptadores

El diseño debe incorporar:

- Un puerto de lectura para resumen agregado.
- Un puerto de lectura para detalle por `shipment_number + bale_number`.
- Capacidad del repositorio de fardos para cargar una entidad por UUID.
- Capacidad para persistir el estado actualizado con control de concurrencia.
- Adaptadores SQLAlchemy que implementen las consultas y modificaciones.
- Proveedores de dependencias diferenciados por caso de uso, evitando que un único proveedor quede acoplado solo al registro.

Las consultas pueden leer directamente proyecciones construidas mediante joins y agregados. No necesitan reconstruir `RawMaterialBatch` ni todos los agregados `Bale` cuando no se ejecuta comportamiento de dominio.

## 13. Persistencia y migraciones

### 13.1 Fecha empresarial

- La columna `raw_material_batches.received_at` debe pasar de `timestamp with time zone` a `DATE`.
- El record SQLAlchemy debe utilizar un tipo de fecha.
- El dominio debe reemplazar la semántica `ReceptionDateTime` por un valor de fecha empresarial.
- Comandos, resultados, mappers, requests, responses y pruebas deben usar el mismo tipo.
- La migración debe definir explícitamente cómo preservar la fecha empresarial de cualquier dato preexistente y validar el resultado antes de eliminar la semántica temporal.
- La fecha de auditoría técnica, si se requiere en el futuro, será otro campo como `created_at`; no forma parte de este alcance.

### 13.2 Índices

Además de la unicidad e índice actuales, deben evaluarse y verificarse índices para:

- Fecha de recepción de la partida.
- Estado del fardo.
- Tipo de material.
- Consultas combinadas por partida y número de fardo, ya cubiertas parcialmente por las restricciones actuales.

La selección final debe justificarse con los planes de consulta reales de `summary` y `detail`. No se crearán índices para filtros que no formen parte del contrato aprobado.

### 13.3 Integridad

- Se conservan las restricciones nombradas de clave primaria, clave foránea, unicidad y estado.
- La migración nueva debe mantener RLS habilitado y la política actual de privilegios.
- No se agregan políticas de acceso mientras autenticación y autorización permanezcan fuera de alcance.
- Los pesos y Dtex permanecen en columnas `NUMERIC`.

## 14. Concurrencia y transacciones

- El registro masivo conserva una sola transacción para partida y fardos.
- El cambio de estado utiliza una transacción independiente.
- La entrega debe aplicar bloqueo de fila o actualización condicional equivalente para asegurar que el estado esperado sea `in_warehouse`.
- Un conflicto concurrente se traduce al mismo contrato `bale_already_delivered`.
- Las consultas no deben efectuar commits ni modificar entidades.
- Toda excepción durante una escritura debe provocar rollback.

## 15. Seguridad e integración

### 15.1 CORS

La aplicación debe permitir llamadas desde el frontend mediante una lista configurable de orígenes:

- Los orígenes se obtienen de configuración de entorno tipada.
- Desarrollo local admite únicamente los orígenes declarados para Vite.
- Producción no utiliza wildcard.
- No se exponen credenciales ni `DATABASE_URL` al navegador.

### 15.2 Seguridad de datos

- Se conserva la validación estricta y la prohibición de campos extra.
- Se mantienen respuestas genéricas para errores inesperados.
- Los logs pueden contener contexto técnico, pero no secretos ni payloads completos sensibles.
- RLS y privilegios existentes no deben debilitarse para facilitar el desarrollo.

## 16. Requisitos no funcionales

| ID | Requisito |
|---|---|
| NFR-01 | Las operaciones deben conservar exactitud decimal de extremo a extremo. |
| NFR-02 | El resumen debe resolverse mediante agregación SQL, sin materializar todos los fardos en memoria. |
| NFR-03 | El POST debe admitir 100 fardos dentro de los límites operativos normales del servicio. |
| NFR-04 | La API debe mantener contratos deterministas y documentados en OpenAPI. |
| NFR-05 | Ningún error `500` debe exponer excepciones, SQL, rutas internas o secretos. |
| NFR-06 | Las escrituras deben ser atómicas y seguras ante concurrencia. |
| NFR-07 | Las consultas deben aprovechar índices compatibles con sus filtros y joins. |
| NFR-08 | Los cambios no deben introducir dependencias de framework en dominio o aplicación. |
| NFR-09 | La configuración debe fallar tempranamente cuando un valor obligatorio sea inválido. |
| NFR-10 | La solución debe conservar Python 3.13, `uv`, `unittest`, FastAPI, SQLAlchemy, Psycopg y migraciones Supabase ya adoptados. |

## 17. Estrategia de pruebas

### 17.1 Dominio

- Fecha empresarial válida e inválida.
- Transición exitosa a `delivered`.
- Rechazo de una segunda entrega.
- Conservación de reglas de identificadores, Dtex y peso.

### 17.2 Aplicación

- Registro de 1 y 100 fardos.
- Rechazo de 0 y más de 100 fardos.
- Resultado resumido sin colección de fardos.
- Construcción correcta de filtros.
- Detalle encontrado y no encontrado.
- Entrega exitosa, fardo inexistente y fardo ya entregado.
- Rollback y traducción de conflictos.

### 17.3 Persistencia unitaria

- Mapeo de fecha.
- Proyección de detalle con join.
- Agregados y ceros cuando no existen coincidencias.
- Combinación de filtros.
- Carga y actualización del fardo.

### 17.4 API y OpenAPI

- Métodos, rutas, parámetros, status codes y modelos.
- Fecha ISO sin componente de hora.
- Decimales serializados como strings.
- Response del POST sin `bales`.
- Errores indexados por campo.
- Rechazo de campos extra y estados no permitidos.
- CORS para origen permitido y rechazo de origen no autorizado.

### 17.5 Integración PostgreSQL

- Migración de `received_at` a `DATE`.
- Round-trip de fecha y decimales.
- Registro atómico de 100 fardos.
- Resumen correcto con cada filtro y combinaciones representativas.
- Consulta por identidad compuesta.
- Planes de consulta e índices esperados.
- Transición concurrente: una solicitud exitosa y una en conflicto.
- Persistencia del estado después del commit.
- Rollback ante fallos.

Las pruebas SQLite pueden continuar como soporte unitario, pero no sustituyen las verificaciones de tipos, restricciones, concurrencia, diagnósticos ni agregaciones reales en PostgreSQL.

## 18. Criterios de aceptación

> For authoritative business rules, see the [normative PRD](../../../docs/prd/warehouse/bale-management.md).
> The acceptance criteria below are implementation-level verification points derived from the PRD.

| ID | Criterio |
|---|---|
| AC-01 | El POST acepta `received_at` como `YYYY-MM-DD` y rechaza valores con hora. |
| AC-02 | La columna persistida de recepción es `DATE`. |
| AC-03 | El POST acepta entre 1 y 100 fardos y rechaza colecciones fuera de ese rango. |
| AC-04 | El response `201` contiene únicamente los cinco campos resumidos aprobados. |
| AC-05 | Un `shipment_number` duplicado produce `409 duplicate_shipment_number`. |
| AC-06 | Los errores de fardo identificables incluyen una ruta indexada compatible con la grilla. |
| AC-07 | El endpoint de resumen aplica todos los filtros opcionales de forma conjuntiva. |
| AC-08 | El resumen devuelve cantidades y pesos correctos calculados por PostgreSQL. |
| AC-09 | Un resumen sin coincidencias devuelve ceros y estado `200`. |
| AC-10 | El detalle requiere `shipment_number` y `bale_number`. |
| AC-11 | El detalle devuelve el UUID, cabecera, atributos, peso neto y estado del fardo. |
| AC-12 | Una identidad empresarial inexistente produce `404 bale_not_found`. |
| AC-13 | El PATCH admite exclusivamente el valor `delivered`. |
| AC-14 | El PATCH ejecuta la transición mediante el dominio y persiste el cambio. |
| AC-15 | Un fardo ya entregado produce `409 bale_already_delivered`. |
| AC-16 | Dos entregas concurrentes no pueden confirmarse ambas. |
| AC-17 | Todas las rutas y respuestas están representadas correctamente en OpenAPI. |
| AC-18 | El frontend puede consumir la API desde un origen CORS expresamente configurado. |
| AC-19 | Las suites unitarias e integración PostgreSQL aprobadas finalizan sin fallos. |
| AC-20 | La documentación de Warehouse, arquitectura, persistencia y contratos queda alineada con la implementación. |

## 19. Secuencia recomendada de implementación

1. Alinear fecha empresarial, límite de 100 fardos y response resumido del registro.
2. Incorporar la migración de fecha y los índices iniciales.
3. Implementar la consulta individual y su proyección de lectura.
4. Implementar el cambio irreversible de estado con control de concurrencia.
5. Implementar el resumen agregado y sus filtros.
6. Ampliar composición, contratos HTTP, errores y OpenAPI.
7. Configurar CORS.
8. Completar pruebas PostgreSQL y validar la integración con el frontend.

Cada bloque debe conservar el endpoint de registro funcional y mantener alineados dominio, aplicación, adaptadores, migraciones, OpenAPI y pruebas.

## 20. Riesgos y decisiones pendientes de implementación

| Riesgo | Tratamiento |
|---|---|
| Conversión de timestamps existentes a fecha | Definir y probar una regla explícita de preservación de fecha antes de ejecutar la migración |
| Doble entrega concurrente | Bloqueo de fila o actualización condicional con estado esperado |
| Sumatorias nulas | Normalizar agregados sin resultados a cero decimal |
| Filtros que degraden rendimiento | Verificar planes reales y añadir únicamente índices justificados |
| Errores de dominio sin índice de fardo | Conservar el índice durante la construcción/validación para producir una ruta útil |
| Divergencia entre ORM y migración | Mantener pruebas de contrato de esquema en PostgreSQL |
| CORS permisivo | Usar lista explícita por entorno y prohibir wildcard en producción |

## 21. Definición de terminado

La capacidad se considera terminada cuando:

- Los cuatro endpoints cumplen los contratos de esta especificación técnica.
- El POST utiliza fecha simple, limita la carga y devuelve un resumen.
- Dashboard, consulta individual y actualización de estado pueden integrarse sin datos simulados.
- La transición irreversible es correcta incluso bajo concurrencia.
- Migraciones, records, mappers y dominio usan tipos consistentes.
- Los errores permiten al frontend diferenciar fallos globales y de campo.
- OpenAPI refleja el comportamiento real.
- Las pruebas unitarias y PostgreSQL cubren los criterios de aceptación.
- La configuración CORS permite la integración autorizada con el frontend.
- La documentación del repositorio no conserva descripciones incompatibles con la implementación.

