# Registros Funcionales — Unidad Almacén

> **Encadenado desde:** `docs/prd/warehouse.md`
> **Relacionados:** `docs/prd/access-control.md`, `docs/prd/operation/lot-processing-records.md`

---

## 1. Propósito

Este documento describe los **registros funcionales** y los **flujos
documentales** de la **Unidad Almacén**.

Su función es servir como puente entre:

- el PRD del negocio
- el diseño posterior del dominio
- el futuro modelado de datos
- el diseño de formularios, validaciones y pantallas

No define tablas, columnas técnicas ni estructura de base de datos. Define qué
necesita registrar el negocio, con qué granularidad y con qué significado.

---

## 2. Regla transversal de uso

Los registros descritos aquí reflejan la operación actual esperada de Almacén.

- El **registrador actual** indica quién suele cargar hoy ese dato.
- Esa asignación **no es rígida**: puede cambiar por política de acceso según
  `docs/prd/access-control.md`.
- Almacén y Operación mantienen un **historial único del lote**, pero cada
  dominio escribe solo la parte que le corresponde.

Cuando corresponda, cada registro debe distinguir explícitamente entre:

- **dato de negocio**: información que representa el hecho operativo o comercial
- **fecha de negocio**: fecha operativa ingresada por el usuario responsable
- **timestamp de registro**: fecha y hora capturadas automáticamente por el sistema

Estas piezas no representan lo mismo y no deben confundirse.

Además, este documento separa cuatro actos de negocio que no deben modelarse
como un único evento:

1. **recepción física de fardos**
2. **definición de identidad para producción**
3. **movimientos de stock**
4. **continuidad del historial del lote entre Almacén y Operación**

---

## 3. Vista rápida del flujo funcional

```text
Proveedor
  → Recepción física de fardos
  → Definición de identidad para producción
  → Emisión a Operación
  → Operación continúa el historial del lote
  → Recepción de PT desde Operación
  → Clasificación / disponibilidad para distribución
  → Salida de PT o devolución de PT

Proveedor de insumos
  → Recepción de insumos
  → Consumo por Producción / devolución a proveedor
```

---

## 4. Familias de registros en Almacén

Dentro de Almacén existen ocho familias funcionales principales:

1. **Registro de recepción de materia prima en fardos**
2. **Registro de definición de identidad para producción**
3. **Registro de emisión a Operación**
4. **Registro de recepción de producto terminado desde Operación**
5. **Registro de disponibilidad, disposición o clasificación operativa de PT**
6. **Registro de salida de PT**
7. **Registro de devolución de PT**
8. **Registro de insumos de producción**

Estas familias no equivalen todavía a entidades técnicas ni a tablas. Son
agrupaciones funcionales para cerrar el significado del dato antes del diseño.

---

## 5. Registros funcionales por flujo

## 5.1 Materia Prima — Recepción física de fardos

- **Qué representa:** ingreso físico de materia prima desde proveedor.
- **Granularidad:** 1 partida de materia prima (`RawMaterialBatch`) × uno o más fardos recibidos.

### Regla de frontera

- Aquí **no nace todavía el lote de producción**.
- Almacén recibe **fardos**, no lotes productivos.
- Esta recepción crea existencia de MP bajo custodia de Almacén.

### Datos de cabecera

- `shipment_number`: identificador visible de la partida de materia prima; es
  obligatorio y globalmente único
- proveedor
- documento de respaldo del proveedor, como dato comercial opcional y separado
- origen o procedencia
- número de camión cuando aplique
- fecha de negocio de recepción
- responsable que recibe
- observaciones o incidencias de descarga

### Datos por ítem o fardo

- `bale_number`: obligatorio y único dentro de la partida de materia prima; puede
  repetirse en partidas diferentes
- tipo de materia prima
- título o referencia técnica conocida al momento de recibir
- color, fibra o variante si aplica
- cantidad o peso recibido
- unidad principal de control: kg
- estado u observación del fardo si existe diferencia física

Cada fardo tiene identidad técnica y ciclo de vida independientes. Su identidad
visible para el negocio queda determinada por `shipment_number` + `bale_number`.
El registro actual recibe la partida completa y todos sus fardos en una única
solicitud y transacción. Una futura corrección de errores tipográficos debe ser
explícita y auditada; este flujo no promete CRUD genérico ni permite agregar en
silencio fardos omitidos.

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- personal de Almacén

### Nota de permisos

- configurable por política de acceso

---

## 5.2 Identidad de producción — Definición posterior a la recepción

- **Qué representa:** acto posterior en el que se define la identidad de una
  unidad de producción planificada y la continuidad de su historial operativo.
- **Granularidad:** 1 definición de identidad × 1 unidad de producción a planificar.

### Regla de frontera

- Este acto es **separado** de la recepción física de fardos.
- No selecciona, asigna ni vincula fardos recibidos con la identidad de
  producción; la entrega de fardos sigue siendo un acto independiente.
- La identidad definida aquí será la base de continuidad del historial con
  Operación.

### Datos de negocio principales

- identificador de producción o lote
- título objetivo
- color requerido
- cliente o destino
- tipo, variante o clasificación aplicable
- requerimientos u observaciones del pedido
- fecha de negocio de definición
- responsable que define o autoriza

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- normalmente Almacén con definición/autorización asociada al Jefe de Producción

### Nota de permisos

- configurable por política de acceso

### Continuidad del historial

- desde este punto existe una identidad única que Operación debe continuar
- Operación no debería crear una identidad paralela para el mismo flujo

---

## 5.3 Materia Prima — Emisión a Operación

- **Qué representa:** salida de MP desde Almacén hacia Operación para su uso en
  producción.
- **Granularidad:** 1 emisión × 1 destino operativo o agrupación autorizada.

### Regla de frontera

- la emisión mueve stock de MP
- no redefine la identidad del lote
- documenta la entrega completa del fardo únicamente a Producción, sin vincularlo a una identidad de producción o código de lote; no requiere ni registra un destino
- la entrega es el hecho de negocio; su resultado es `IN_PRODUCTION`, condición de custodia/ubicación que no significa consumo ni procesamiento
- un fardo pasa una sola vez de `IN_WAREHOUSE` a `IN_PRODUCTION`; la entrega exige `delivered_at` y una entrega repetida se rechaza
- los responsables que entregan o reciben no son evidencia obligatoria actual; pueden definirse después mediante un requerimiento explícito
- una reversión solo puede ocurrir como corrección controlada y auditada

### Datos de negocio principales

- número de emisión
- fecha de negocio de emisión
- fardo entregado completo
- peso del fardo entregado en kg
- `delivered_at`, fecha y hora del hecho de entrega
- autorización operativa correspondiente
- observaciones o incidencias

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- personal de Almacén

### Autorizador actual

- Jefe de Producción

### Nota de permisos

- registrador y autorizador configurables por política de acceso; esto no vuelve obligatoria la captura de actores de entrega en el modelo actual

---

## 5.4 Producto Terminado — Recepción desde Operación

- **Qué representa:** retorno del historial del lote a Almacén cuando Operación
  entrega producto terminado.
- **Granularidad:** 1 recepción de aceptación de PT × 1 identidad de lote; no se admite una segunda recepción para la misma identidad.

### Regla de frontera

- Almacén no recrea el historial productivo.
- Almacén recibe el lote bajo la **misma identidad** que ya fue usada por
  Operación.
- La única recepción para esa misma identidad es la evidencia de aceptación del
  único Quality Send. Hasta registrarla, el lote permanece en espera de validación
  de Almacén; una nota breve de coordinación no constituye aceptación ni otro envío.
- La recepción puede apoyarse en datos heredados de Operación y en verificación
  física propia de Almacén.

### Datos heredados o de referencia

- identificador de lote o producción
- título
- color
- cliente o destino
- estado documentado por Operación, which remains owned by Lot Processing
- información relevante de calidad o condición de entrega
- route-sheet facts already recorded by Inventario and Embolsado

### Datos que Almacén verifica localmente

- presentación física recibida
- physical consistency of the route-sheet facts already recorded by Inventario and Embolsado
- incidencias visibles al momento de la recepción

Almacén no vuelve a cargar peso, cantidad de bolsas ni cantidad de unidades: esos son hechos ya registrados por Operación en la route sheet. La recepción de Almacén registra aceptación, presentación física y diferencias observadas.

### Datos generados por la recepción

- número de recepción
- fecha de negocio de recepción
- responsable que recibe
- supervisor o responsable de origen
- observaciones o diferencias detectadas

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- personal de Almacén

### Nota de permisos

- configurable por política de acceso

---

## 5.5 Producto Terminado — Disponibilidad o clasificación operativa para distribución

- **Qué representa:** decisión operativa de cómo queda disponible el PT dentro de
   Almacén para su salida posterior.
- **Granularidad:** 1 clasificación o cambio de disponibilidad × 1 lote o fracción controlada.

### Regla de frontera

- esta clasificación ocurre después de la recepción de PT
- no reemplaza el registro de calidad de Operación
- define cómo Almacén tratará el PT para almacenamiento, reserva o distribución
- debe separar explícitamente calidad informada, disponibilidad operativa y presentación física

### Datos de negocio principales

- identidad de lote
- fecha de negocio de clasificación
- Lot Processing-owned quality state, read only as context and not persisted by Warehouse
- condición de disponibilidad o disposición operativa definida por Almacén
- presentación física o modalidad de almacenamiento
- destino operativo previsto cuando ya se conozca
- observaciones de Almacén
- motivo de cambio si la clasificación se corrige posteriormente

### Catálogo inicial de disponibilidad operativa

- **Disponible**
- **Observado**
- **Disponible con condición**
- **Defectuoso**
- **Entregado / Despachado**

### Dimensiones funcionales que no deben mezclarse

- Lot Processing-owned quality state: estándar / con nomenclatura / observado
- disponibilidad o disposición en Almacén: disponible / observado / disponible con condición / defectuoso / entregado-despachado
- presentación física: bolsa / suelto u otra presentación relevante
- modalidad o destino operativo: industrial / ovillado u otra clasificación comercial u operativa relevante

### Regla de simplificación actual

- **Defectuoso** se considera un estado terminal dentro de Almacén.
- No se trata como desperdicio.
- No vuelve normalmente a estados disponibles.

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- personal de Almacén

### Nota de permisos

- configurable por política de acceso

---

## 5.6 Producto Terminado — Salidas

- **Qué representa:** salida de PT fuera de la custodia de Almacén.
- **Granularidad:** 1 salida × 1 destino o documento de salida.

### Tipos funcionales principales

1. **venta directa a cliente**
2. **transferencia a Comercialización**

### Datos de negocio principales

- número de salida
- tipo de salida
- fecha de negocio de salida
- lote o lotes afectados
- cantidad salida en kg
- destino
- documento comercial o referencia cuando aplique
- responsable que entrega
- autorización operativa correspondiente
- observaciones

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- personal de Almacén

### Autorizador actual

- Jefe de Producción

### Nota de permisos

- registrador y autorizador configurables por política de acceso

---

## 5.7 Producto Terminado — Devoluciones

- **Qué representa:** retorno total o parcial de PT que ya había salido.
- **Granularidad:** 1 devolución × 1 salida original o fracción de ella.

### Regla de frontera

- la devolución reingresa existencia a Almacén
- debe mantener la referencia al historial previo de salida
- no crea una identidad nueva para el producto devuelto

### Datos de negocio principales

- número de devolución
- fecha de negocio de devolución
- referencia a la salida original
- lote o lotes devueltos
- cantidad devuelta en kg
- motivo o condición de la devolución
- responsable que recibe la devolución
- observaciones sobre estado físico o reclamo asociado

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- personal de Almacén

### Nota de permisos

- configurable por política de acceso

---

## 5.8 Insumos de Producción

- **Qué representa:** entradas y salidas de insumos consumidos por Producción.
- **Granularidad:** 1 movimiento de insumo × 1 tipo de operación × 1 ítem.

### Regla de frontera

- los insumos no comparten necesariamente el historial único del lote de PT
- sí requieren trazabilidad propia de stock y de consumo
- la unidad de medida depende del ítem y no debe forzarse a kg si no corresponde

### Tipos funcionales principales

1. **recepción desde proveedor**
2. **salida por consumo de Producción**
3. **devolución a proveedor**

### Datos de negocio principales

- número de movimiento
- tipo de movimiento
- fecha de negocio
- categoría del insumo
- ítem o referencia
- proveedor o destino
- cantidad
- unidad de medida del ítem
- responsable que entrega o recibe
- autorizador cuando aplique
- observaciones

### Datos técnicos automáticos

- timestamp de registro en el sistema

### Registrador actual

- personal de Almacén

### Autorizador actual

- para consumo de Producción, normalmente supervisor o responsable definido por la política vigente

### Nota de permisos

- configurable por política de acceso

---

## 6. Reglas transversales de los registros

1. **Recepción física primero:** la materia prima entra al sistema como fardos,
   no como lote de producción.
2. **Identidad posterior:** la identidad del lote o producción se define después,
   cuando se decide qué MP será destinada a producción.
3. **Historial único del lote:** la identidad de producción debe sostener un
   solo historial transversal entre Almacén y Operación.
4. **Escritura separada por dominio:** Almacén y Operación escriben partes
   distintas de ese historial y no deben sobrescribir las responsabilidades del
   otro dominio.
5. **Dato de negocio vs sistema:** cuando aplique, debe distinguirse la fecha de
   negocio ingresada por el usuario del timestamp automático del sistema.
6. **Corrección con auditoría:** si existe error de carga, el registro puede
   corregirse, pero con auditoría completa.
7. **Ventana operativa:** los roles operativos pueden corregir dentro de la
   ventana definida por la política vigente.
8. **Restricción posterior:** fuera de esa ventana, solo SysAdmin puede editar.
9. **Movimientos de stock separados:** recepción, definición de identidad,
   emisión, recepción de PT, clasificación, salida y devolución son actos
   funcionales distintos.
10. **Permisos configurables:** el registrador actual y el autorizador actual no
    equivalen a permisos fijos.

---

## 7. Cómo usar este documento más adelante

Este documento debe alimentar, en ese orden:

1. **modelo de dominio**
   - qué conceptos son entidades, eventos, agregados o value objects
   - dónde termina la responsabilidad de Almacén y dónde continúa la de Operación
2. **modelado de datos**
   - qué registros funcionales deben persistirse
   - qué referencias deben conservar continuidad histórica
   - qué relaciones existen entre identidad de producción, PT e insumos, manteniendo los fardos independientes
3. **formularios y UI**
   - qué pantallas necesita cada acto de negocio
   - qué datos son obligatorios
   - qué datos hereda Almacén desde Operación
   - qué datos verifica localmente
   - qué captura el usuario y qué genera automáticamente el sistema
4. **reglas de validación**
   - consistencia de stock
   - continuidad del historial
   - autorizaciones según política vigente
   - consistencia entre recepción física, identidad definida y movimientos posteriores

No debe usarse directamente como diseño de tablas. Su función es cerrar el
significado funcional del dato antes del diseño técnico.

---

## 8. Ambigüedades todavía abiertas

1. Debe definirse con más detalle el catálogo inicial de estados de
   disponibilidad o clasificación operativa de PT.
2. Debe decidirse si las devoluciones de PT reingresan siempre a la misma
   clasificación operativa previa o pasan primero por una nueva revisión de
   disponibilidad.
