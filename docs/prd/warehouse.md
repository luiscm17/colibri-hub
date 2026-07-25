# PRD: Unidad Almacén

> **Parte de:** Dirección de Producción — Yarn EPR
> **Dependencias:** `docs/prd.md` (PRD maestro)
> **Siguiente:** `docs/domain/warehouse.md` (Modelo de Dominio)

---

## 1. Propósito y alcance

### 1.1 Propósito

Definir los subdominios, reglas de negocio y requerimientos de la **Unidad Almacén**, responsable de gestionar las existencias de fardos de materia prima, producto terminado e insumos de producción, así como el registro de todos los movimientos de entrada y salida. Este PRD establece la perspectiva de Almacén sobre la identidad de producción, el movimiento de existencias y la continuidad del historial del lote.

### 1.2 Alcance

Cubre los siguientes subdominios operativos:

- **Materia Prima (MP / fardos):** recepción de fardos, registro de camiones entrantes, control de existencias de MP y emisión a Operación.
- **Producto Terminado (PT):** recepción desde Operación, almacenamiento (bolsa / suelto), salidas por venta directa a cliente o transferencia a Comercialización, devoluciones, y control de existencias con la fórmula `(Saldo Anterior + Entradas) − Salidas = Saldos`.
- **Insumos de Producción:** todo insumo que consume producción: colorantes, químicos, bolsas, etiquetas, fichas de devanado, talonarios, repuestos, lubricantes, conos, tubos, etc. Se organiza por categorías según el tipo de insumo.

Además, Almacén participa en la **definición de identidad de producción** que
acompaña al flujo posterior del lote, pero esa definición no debe confundirse
con la recepción física inicial de fardos.

### 1.3 Límite con otros dominios

El sistema tendrá un **historial único por lote**, pero cada dominio escribe y
consulta solo su propia información. Almacén inicia la identidad y luego
continúa el historial cuando recibe Producto Terminado desde Operación:

| Dominio | Escribe | No ve |
|---|---|---|
| **Almacén** | Recepción de fardos, definición de identidad para producción, emisión a Operación, recepción de PT, salidas, devoluciones | Las 6 etapas productivas, calidad, desperdicio real |
| **Operación** | 6 etapas del lote, calidad, nomenclaturas, desperdicio real | Movimientos internos de existencias de Almacén, clientes, saldos |

### 1.4 Fuera de alcance

- Las 6 etapas productivas del lote y su máquina de estados (compete a `docs/prd/operation.md`)
- Control de calidad de proceso y nomenclaturas especiales del PT (competencia de Operación)
- Desperdicio real y acumulado (competencia de Operación y Jefe de Producción)
- Facturación, contabilidad y libros fiscales
- Modelo de datos detallado y diseño de API (se documenta en `docs/domain/`)

### 1.5 Audiencia

Jefe de Producción, Jefe de Unidad Almacén, arquitectos, desarrolladores, QA.

---

## 2. Contexto organizacional

### 2.1 Ubicación en la estructura

La Unidad Almacén depende de la **Dirección de Producción**. Su responsable es el **Jefe de Unidad Almacén**, que reporta al Jefe de Producción.

```
Dirección de Producción
├── Jefe de Producción (incl. Secretaria)
│   ├── Unidad Almacén
│   │   └── Jefe Unidad Almacén
│   │       └── Auxiliares Operativos
│   └── Unidad Operación
│       └── Supervisores (1 por turno)
```

### 2.2 Roles

| Rol | Responsabilidades en el sistema |
|---|---|
| **Jefe de Unidad Almacén** | Supervisa recepción de MP, emisiones a Operación, verificación de PT y control de existencias. Reporta al Jefe de Producción. |
| **Auxiliar Operativo** | Ejecuta movimientos físicos como recepción, verificación, embolsado y despacho. |

> **Nota sobre permisos:** estas responsabilidades describen la operación actual
> de Almacén, pero la asignación de quién registra, valida, autoriza o corrige
> movimientos puede cambiar por política organizacional. La autorización del
> sistema se define de forma transversal en `docs/prd/access-control.md`.

### 2.3 Relación con otros roles

- **Jefe de Producción:** planifica la producción (ver [sección 5 de operation.md](../prd/operation.md#5-planificación-de-la-producción)), autoriza emisiones de MP, recibe reportes de stock y alertas del Jefe de Almacén.
- **Supervisores (Operación):** reciben las solicitudes de material desde las secciones productivas y las elevan al Jefe de Almacén. Coordinan la recepción de MP/insumos y la entrega de PT desde las secciones productivas a Almacén.
- **Comercialización:** recibe PT transferido para venta por unidad o cantidades pequenas. Es un destino de salida, no un usuario del sistema.
- **Cliente directo:** destino de salida cuando el lote completo se vende al por mayor. No es usuario del sistema.

### 2.4 Principios operativos

1. **Recepción de MP como fardos.** Almacén recibe materia prima desde proveedor en forma de fardos. Esa recepción no debe confundirse con el lote físico que nace más adelante en Operación.
2. **Identidad de producción como acto separado.** Almacén define la única identidad del lote mediante `production_identity_id` y el código visible `lot_code`, junto con título, color, cliente o destino y demás requerimientos. Este acto es separado de la recepción física de fardos, que no se vinculan a la identidad de producción.
3. **Trazabilidad obligatoria.** Todo lote de producción debe conservar un historial auditable de su recorrido, incluyendo definición inicial, emisión a Operación, recepción de PT, salidas, devoluciones y ajustes documentados. El historial no se elimina y su continuidad pasa entre Almacén y Operación bajo la misma identidad.
4. **Consistencia de saldos.** El stock reflejado en el sistema debe coincidir con las existencias físicas. Cualquier discrepancia requiere ajuste documentado.
5. **Cada dominio escribe su historial.** Almacén registra sus movimientos y no interfiere con los datos de Operación. La historia del lote es única, pero se compone con aportes de ambos dominios.
6. **Dos canales de salida de PT.** El PT puede salir por venta directa a cliente o por transferencia a Comercialización. Warehouse owns availability or operational disposition and physical presentation; Lot Processing retains ownership of quality.
7. **Permisos configurables.** La asignación de capacidades de registro, validación, autorización, corrección y consulta no se fija rígidamente por cargo. El sistema debe permitir reasignarlas sin rediseñar los procesos de Almacén.

**Estados operativos iniciales del PT en Almacén:**

- **Disponible**: puede distribuirse normalmente.
- **Observado**: tiene observaciones o defectos reportados que requieren decisión antes de su salida.
- **Disponible con condición**: puede distribuirse, pero bajo condiciones explícitas documentadas.
- **Defectuoso**: estado terminal gestionado por Almacén para PT con defectos significativos. No es desperdicio y no vuelve normalmente a estados disponibles.
- **Entregado / Despachado**: ya salió de Almacén.

---

## 3. Subdominios

La Unidad Almacén opera sobre tres subdominios. El detalle funcional de sus
registros, actos de negocio y flujos documentales está desarrollado en:

> Ver [`docs/prd/warehouse/warehouse-records.md`](warehouse/warehouse-records.md)

| # | Subdominio | Propósito | Unidad |
|---|---|---|---|
| 3.1 | **Materia Prima (MP / fardos)** | Recepción de fardos, registro de camiones entrantes, control de stock de MP y emisión a Operación | kg |
| 3.2 | **Producto Terminado (PT)** | Recepción desde Operación, almacenamiento (bolsa / suelto), salida por venta directa o transferencia a Comercialización | kg |
| 3.3 | **Insumos de Producción** | Todo insumo de producción: colorantes, químicos, empaque, repuestos, lubricantes, etc. Organizado por categorías. | según categoría (kg, piezas, L) |

---

## 4. Reglas de negocio

### 4.1 Historial de movimientos

Todo movimiento en Almacen debe conservar **trazabilidad completa**. Si existe
un error de carga, la corrección debe dejar auditoría completa del cambio,
incluyendo usuario editor, fecha/hora, valores anteriores, valores nuevos y
motivo de corrección.

La edición puede permitirse durante una ventana operativa definida por la
política vigente. Fuera de esa ventana, solo **SysAdmin** puede editar.

### 4.2 Tipos de movimiento

Cada subdominio define sus propios tipos de movimiento. No son intercambiables entre subdominios.

La unidad de medida del movimiento depende del subdominio: Materia Prima y Producto Terminado usan **kilogramos (kg)**; Insumos de Producción usa la unidad que corresponda a cada categoria (kg, L, piezas, etc.).

| Subdominio | Tipo de movimiento | Direccion | Autoriza |
|---|---|---|---|
| Materia Prima | Recepción de fardos | Entrada | — |
| Materia Prima | Emisión a Producción | Salida | Jefe de Producción |
| Producto Terminado | Recepción desde Producción | Entrada | — |
| Producto Terminado | Venta directa | Salida | Jefe de Producción |
| Producto Terminado | Transferencia a Comercialización | Salida | Jefe de Producción |
| Producto Terminado | Devolución | Entrada | — |
| Insumos de Producción | Recepción desde proveedor | Entrada | — |
| Insumos de Producción | Consumo de Producción | Salida | Supervisor de turno |
| Insumos de Producción | Devolución a proveedor | Salida | — |

Toda solicitud sigue el orden jerarquico. Para los movimientos que requieren autorizacion, la solicitud llega a Almacen con el visto bueno del rol correspondiente segun la politica vigente de permisos:

- **Jefe de Produccion** autoriza emisiones de MP y salidas de PT.
- **Supervisor de turno** autoriza consumos de Insumos de Producción.

Estas asignaciones representan la operacion actual esperada. El sistema debe
permitir que la empresa reasigne estas autorizaciones a otros roles habilitados
sin cambiar la estructura funcional del proceso.

**Nota conceptual:** la recepción física de fardos, la definición de identidad
para producción y la recepción posterior de Producto Terminado son actos de
negocio distintos. No deben modelarse como un único evento.

Casos particulares:

- **Producto Terminado / Devolución**: puede ser total o parcial. El lote devuelto se reincorpora a existencias y puede tener una salida posterior. El movimiento referencia a la venta original.
- **Producto Terminado / Transferencia a Comercialización**: la cantidad se registra en kilogramos. El precio unitario lo define Comercialización.
- **Producto Terminado / Venta directa**: la cantidad se registra en kilogramos.
- **Datos verificados**: Almacen registra la recepción de PT a partir de la información entregada por Operación y de su propia verificación física. Si un lote llega con datos inconsistentes, se documenta la incidencia antes de aceptarlo o clasificarlo para disponibilidad.

### 4.3 Cierre de existencias

El sistema debe facilitar el calculo de saldos para el cierre de existencias, que se realiza:

- **Mensualmente** (control de gestion)
- **Anualmente** (cierre fiscal)
- **Extraordinariamente** (cuando la planta detiene produccion y se puede hacer conteo fisico)

En cada cierre, el sistema calcula los saldos con la formula `(Saldo Anterior + Entradas) − Salidas = Saldos` y los presenta para su verificacion. Los movimientos del periodo cerrado pasan a solo lectura.

---

## 5. Requerimientos funcionales

### 5.1 Materia Prima

| ID | Requerimiento |
|---|---|
| WH-RM-01 | El sistema debe permitir registrar una partida de materia prima (`RawMaterialBatch`) completa, identificada por un `shipment_number` obligatorio y globalmente único, con uno o más fardos. Cada fardo tiene identidad técnica independiente y un `bale_number` obligatorio, único dentro de la partida aunque pueda repetirse en partidas diferentes; su identidad visible para el negocio es `shipment_number` + `bale_number`. También se registran proveedor, peso bruto, título, color/fibra y número de camión; la factura o documento del proveedor es un respaldo comercial opcional y separado. El alta actual ocurre en una única solicitud y transacción. Agregar después fardos omitidos no forma parte del flujo actual; una futura corrección de carga deberá ser explícita y auditada. |
| WH-RM-02 | El sistema debe permitir definir una identidad de producción independiente mediante `production_identity_id` y un `lot_code` único visible. |
| WH-RM-03 | El sistema debe registrar en esa identidad los datos del pedido: cliente o destino, color solicitado, título, tipo N/CH y observaciones. Este enriquecimiento es el insumo para la planificación de producción que realiza el Jefe de Producción (ver [sección 5 de operation.md](../prd/operation.md#5-planificación-de-la-producción)). |
| WH-RM-04 | El sistema debe permitir registrar una única entrega completa de un fardo a Producción. La entrega es el hecho de negocio y su resultado es que el fardo pasa de `IN_WAREHOUSE` a `DELIVERED`, sin afirmar consumo ni procesamiento. Los fardos completos se entregan únicamente a Producción, por lo que no se requiere ni se persiste un destino. Una segunda entrega debe rechazarse. La reversión solo puede ocurrir mediante corrección controlada y auditada. La entrega no vincula el fardo a una identidad de producción o código de lote. No se exigen una fecha de entrega ni los responsables que entregan o reciben; solo podrán incorporarse mediante un requerimiento futuro explícito. |
| WH-RM-05 | El sistema debe mantener el historial de fardos recibidos y entregados a Operación, independiente de las definiciones de producción. |

### 5.2 Producto Terminado

| ID | Requerimiento |
|---|---|
| WH-PT-01 | The system must allow Warehouse to accept PT from Operation with the lot identifier, description, received physical presentation, and origin supervisor. Warehouse physically verifies the route-sheet facts already recorded by Inventory and Bagging without re-entering a weight, bag count, or unit count. |
| WH-PT-02 | El sistema debe permitir documentar inconsistencias entre lo entregado por Operación y la verificación física realizada por Almacén antes de aceptar o clasificar el PT para disponibilidad. |
| WH-PT-03 | El sistema debe permitir registrar la salida de PT por venta directa a cliente con: cliente, cantidad (kg), fecha y numero de factura. Requiere autorizacion del Jefe de Produccion. |
| WH-PT-04 | El sistema debe permitir registrar la transferencia de PT a Comercializacion con: cantidad (kg), fecha. Requiere autorizacion del Jefe de Produccion. |
| WH-PT-05 | El sistema debe permitir registrar devoluciones de PT (totales o parciales) referenciando a la venta original. El lote devuelto se reincorpora a existencias. |
| WH-PT-06 | El sistema debe permitir registrar el cambio de presentación física de un lote (por ejemplo bolsa/suelto) dejando registro en el historial. |
| WH-PT-07 | El sistema debe mostrar el historial completo de movimientos de cada lote de PT, desde su recepcion hasta su salida final. |
| WH-PT-08 | The system must allow Warehouse to manage PT operational availability separately from the Lot Processing-owned quality state and the physical presentation, without persisting a separate quality-state snapshot. |

### 5.3 Insumos de Producción

| ID | Requerimiento |
|---|---|
| WH-SU-01 | El sistema debe permitir definir categorias de insumos de forma flexible (Dyehouse, Packaging, Maintenance, Lubricants, Cones & Tubes, Others), sin limite fijo. |
| WH-SU-02 | El sistema debe permitir registrar la recepcion de insumos con: categoria, proveedor, cantidad y unidad de medida (kg, L, piezas, metros, etc.). |
| WH-SU-03 | El sistema debe permitir registrar el consumo de insumos por parte de Produccion con: categoria, cantidad, area de destino y supervisor que autoriza. |
| WH-SU-04 | El sistema debe permitir registrar devoluciones de insumos a proveedor. |
| WH-SU-05 | Cada ítem de Insumos de Producción debe tener su propia unidad de medida, definida por categoría. |

### 5.4 Transversales

| ID | Requerimiento |
|---|---|
| WH-TR-01 | El sistema debe generar un numero de movimiento unico y correlativo por tipo de movimiento y gestion. |
| WH-TR-02 | El sistema debe registrar fecha y hora en cada movimiento. La fecha/hora refleja **cuándo ocurrió físicamente el movimiento** (ej: emisión a las 10:00 AM), no cuándo se registró en el sistema. El registro digital puede ocurrir después (ej: al cierre del turno). Ver [sección 2.4 del PRD maestro](../prd.md#24-modelo-de-captura-de-datos). |
| WH-TR-03 | El sistema debe impedir la edicion, eliminacion o sobreescritura de movimientos ya registrados. |
| WH-TR-04 | El sistema debe permitir registrar movimientos correctivos que referencien al movimiento original. |
| WH-TR-05 | El sistema debe verificar que el usuario que autoriza un movimiento tenga el rol correspondiente (Jefe de Produccion o Supervisor de turno). |
| WH-TR-06 | El sistema debe calcular los saldos de existencias en cualquier momento usando la formula `(Saldo Anterior + Entradas) − Salidas = Saldos`. |
| WH-TR-07 | El sistema debe facilitar el cierre mensual, anual y extraordinario de existencias, poniendo los movimientos del periodo cerrado en solo lectura. |
| WH-TR-08 | El sistema debe permitir consultar el historial completo de movimientos de cualquier lote o item. |
| WH-TR-09 | El sistema debe permitir a Almacen leer los datos productivos del lote (codigo, descripcion) desde el historial de Operacion, sin poder modificarlos. |
| WH-TR-10 | El sistema debe permitir que los permisos de registro, validacion, autorizacion y correccion en Almacen se configuren sin alterar el flujo funcional definido en este PRD. |

---

## 6. Glosario

| Termino | Definicion |
|---|---|
| **Almacen** | Unidad organizacional responsable de gestionar las existencias de materia prima, producto terminado e insumos de produccion. Depende de la Direccion de Produccion. |
| **Fardo** | Unidad física de materia prima recibida desde proveedor. La recepción inicial de MP ocurre en fardos, no en lotes de proceso. |
| **Partida de materia prima** | Agrupación `RawMaterialBatch` identificada visiblemente por `shipment_number`, que reúne uno o más fardos y su evidencia o características compartidas. No es un lote de producción. |
| **Número de envío** | `shipment_number`; identificador visible y globalmente único de una partida de materia prima. |
| **Identidad del fardo** | Cada fardo posee identidad técnica independiente; para el negocio se reconoce por `shipment_number` + `bale_number`. |
| **Lote** | Unidad de producción cuya única identidad es definida por Almacén y cuyo armado físico ocurre más adelante en Operación. |
| **Codigo de lote** | `lot_code` visible definido por Almacén para la única `production_identity_id` que acompaña la producción y el historial del lote. |
| **Movimiento** | Registro auditable de una entrada o salida de existencias en Almacen. Puede corregirse mediante edición controlada con trazabilidad completa. Cada movimiento pertenece a un tipo especifico (reception, emission, sale, etc.). |
| **Existencias** | Cantidad de un producto disponible en Almacen en un momento dado. Se calcula con la formula `(Saldo Anterior + Entradas) − Salidas`. |
| **Estado operativo del PT** | Situación del Producto Terminado dentro de Almacén para efectos de disponibilidad y distribución: disponible, observado, disponible con condición, defectuoso o entregado/despachado. |
| **Presentación física** | Forma en que Almacén mantiene o recibe el PT, por ejemplo bolsa/suelto o modalidad industrial/ovillado cuando corresponda. |
| **Recepcion** | Acción de negocio o caso de uso que registra una entrada a Almacén. Para MP registra una partida completa con uno o más fardos; no define un agregado de dominio `Reception`. |
| **Emision** | Entrega de un fardo completo desde Almacén hacia Producción. El hecho deja al fardo en `DELIVERED`, sin afirmar consumo o procesamiento. |
| **Salida** | Movimiento de salida de PT hacia cliente directo (venta) o Comercializacion. |
| **Devolucion** | Movimiento de entrada de PT o Insumos de Producción que retorna a Almacen despues de haber salido. Puede ser total o parcial. |
| **Consumo** | Movimiento de salida de Insumos de Producción desde Almacen hacia Produccion para su uso en el proceso productivo. |
| **Operacion** | Unidad organizacional responsable del proceso productivo (Hilatura / `Yarn Spinning` + Proceso por Lotes / `Lot Processing`, documentado en `docs/prd/operation.md`). Recibe MP e insumos de Almacen y devuelve PT verificado. |
| **Comercializacion** | Area que recibe PT desde Almacen para su venta por unidades. No es usuario del sistema de Almacen; es un destino de salida. |
| **Supervisor de turno** | Rol en Operacion que autoriza solicitudes de material y coordina la entrega de PT a Almacen. |
| **Jefe de Produccion** | Rol que autoriza emisiones de MP y salidas de PT. Reporta a la Direccion de Produccion. |
| **Cierre de existencias** | Proceso de calculo de saldos al cierre de un periodo (mensual, anual o extraordinario). Los movimientos del periodo cerrado pasan a solo lectura. |
