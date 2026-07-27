---
document_type: prd
status: active
implementation: not-started
scope: operation/lot-processing
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# PRD: Lot Processing — Proceso por Lotes

> **Parte de:** Unidad Operación — Colibri Hub
> **Dependencias:** `docs/prd/operation.md` (PRD de Operación), `docs/prd/warehouse.md` (PRD de Almacén)
> **Documentos relacionados:** `docs/prd/operation/yarn-spinning.md`
> **Siguiente:** `docs/domain/operation/lot-processing.md` (Modelo de Dominio)

---

## 1. Propósito y Alcance

### 1.1 Propósito

Definir el proceso de transformación de las madejas provenientes de Hilatura / `Yarn Spinning` en Producto Terminado (PT) listo para verificación física, a través de un flujo secuencial de 6 etapas con trazabilidad individual por lote.

### 1.2 Ciclo de vida del lote en el sistema

El lote recorre tres dominios durante su vida en el sistema. Este PRD cubre el tramo de Operación:

```
ALMACÉN                        OPERACIÓN (Lot Processing)               ALMACÉN
   │                                │                                       │
   ├── Asigna código único de lote │                                       │
   ├── Define: título, color,      │                                       │
   │   cliente, especificaciones   │                                       │
   └── Emite a Operación ─────────►│                                       │
                                    │                                       │
                                    ├── Inventario (arma lote físico)       │
                                    ├── Tintorería (aplica color)           │
                                    ├── Secado                              │
                                    ├── Devanado / Ovillado                 │
                                    ├── Embolsado                           │
                                    └── Calidad (evalúa y observa)          │
                                         │                                  │
                                         └── Entrega a Almacén ────────────►│
                                       (con documentación de calidad)       │
                                                                             ├── Verificación física
                                                                             └── Clasificación y disposición
```

Almacén define la única identidad del lote mediante `production_identity_id` y su código visible `lot_code`; ambos se mantienen durante todo este proceso. Operación no genera otra identidad ni códigos nuevos. Inventario registra el armado del conjunto de madejas que será procesado bajo esa identidad. El sistema es la fuente de toda esta información; cualquier respaldo físico (planilla, etiqueta) es solo una representación impresa de los datos del sistema.

### 1.3 Límites del sistema

| Límite         | Detalle                                                                                                                                                                                                                                                                                                                                                        |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Entrada**    | La identidad de producción definida por Almacén (`production_identity_id`, `lot_code`, título, color, cliente o destino y especificaciones del pedido) y las madejas producidas en Madejeras. Inventario recibe esa información digitalmente y registra el armado físico bajo la misma identidad, según el título y peso especificados. |
| **Salida**     | Lote procesado, inspeccionado por Calidad con su documentación completa, entregado a Almacén para verificación física y disposición.                                                                                                                                                                                                                           |
| **No incluye** | La asignación del código de lote, el enriquecimiento con datos del pedido ni la emisión de MP (documentado en `docs/prd/warehouse.md`). La verificación física final del PT, su clasificación en Almacén ni su almacenamiento/distribución (documentado en `docs/prd/warehouse.md`). La producción de hilado en las 5 secciones de Hilatura (`Yarn Spinning`) (documentado en `docs/prd/operation/yarn-spinning.md`). |

### 1.4 Dependencias

- **Hilatura (`Yarn Spinning`):** Madejeras produce las madejas crudas que Inventario utiliza para armar los lotes físicos. Sin producción en Madejeras no hay lotes.
- **Almacén:** Define `production_identity_id`, `lot_code` y las especificaciones del pedido (título, color, cliente o destino) en el sistema. Esa información guía el armado físico y el proceso productivo.
- **Roles de Operación:** Inventario, Personal de Tintorería, Embolsado y Calidad son los actores que registran datos en el sistema a lo largo del proceso.

---

## 2. Las 6 Etapas del Proceso

Cada lote atraviesa las siguientes etapas en orden secuencial estricto. No se puede registrar una etapa si la anterior no está completada.

The process usually lasts approximately one to two days, and a lot may physically cross multiple shifts. Each intervention records only the work actually performed at that moment. A lot may have multiple legitimate records in the same stage, business date, or shift, including records by different users or at different times. Business date, shift, actors, and system timestamps describe process history; they do not define uniqueness. The use-case/domain layer rejects a later-stage intervention until the prior stage is complete; this cross-table invariant is not a DBML constraint. Controlled edits remain subject to the existing audit policy.

### 2.1 Inventario — Armado del lote

El lote ingresa formalmente al proceso cuando Inventario arma físicamente el conjunto de madejas bajo la identidad única que Almacén definió previamente (`production_identity_id` y `lot_code`, título, color, cliente o destino y especificaciones del pedido). Inventario consulta esa información, busca en las madejas crudas disponibles (producidas por Madejeras) y registra el armado físico según el **título** y **peso** especificados. El color es competencia de Almacén y Tintorería, no de Inventario.

| Aspecto                     | Descripción                                                                                                                                                                                                                         |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quién**                   | Inventario                                                                                                                                                                                                                          |
| **Cuándo**                  | Cuando existe la identidad definida por Almacén y hay madejas del título requerido disponibles |
| **Qué se registra**         | — `production_identity_id` y `lot_code` (definidos por Almacén)<br>— Fecha y turno de armado<br>— Responsable que armó el lote<br>— Supervisor a cargo<br>— Título del hilado<br>— Cantidad de madejas que componen el lote<br>— Peso total del lote |
| **Inconvenientes posibles** | — Madejas insuficientes del título requerido<br>— Peso fuera del rango especificado<br>— Datos de emisión incompletos                                                                                                               |
| **Resultado**               | El lote armado pasa a Tintorería                                                                                                                                                                                                    |

### 2.2 Tintorería — Aplicación de color

Las madejas del lote ingresan a las tinas para ser teñidas según el color especificado por Almacén en el sistema.

| Aspecto                     | Descripción                                                                                                                                                                                                                                                              |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Quién**                   | Personal de Tintorería                                                                                                                                                                                                                                                   |
| **Cuándo**                  | Cuando las madejas ingresan a las tinas                                                                                                                                                                                                                                  |
| **Qué se registra**         | — Fecha y turno de ingreso<br>— Responsable que recibe el lote<br>— Supervisor a cargo<br>— Cantidad de madejas recibidas<br>— Peso neto del lote al ingresar<br>— Número de tina utilizada<br>— Temperatura del proceso<br>— Observaciones categorizadas si corresponde |
| **Inconvenientes posibles** | — Reteñir (color no conforme, requiere un segundo baño)<br>— Temperatura fuera de rango<br>— Tina incorrecta o contaminada<br>— Material (tipo de fibra) no coincide con el proceso                                                                                      |
| **Resultado**               | El lote teñido pasa a Secado                                                                                                                                                                                                                                             |

### 2.3 Secado — Eliminación de humedad

Las madejas teñidas pasan al proceso de secado para eliminar la humedad residual.

| Aspecto                     | Descripción                                                                                                                                                     |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quién**                   | Personal de Tintorería                                                                                                                                          |
| **Cuándo**                  | Cuando las madejas salen del proceso de tintorería                                                                                                              |
| **Qué se registra**         | — Fecha y turno de ingreso<br>— Responsable que recibe el lote<br>— Supervisor a cargo<br>— Cantidad de madejas ingresadas<br>— Peso total del lote al ingresar |
| **Inconvenientes posibles** | — Lote no viene de Tintorería (control de secuencia)<br>— Peso inconsistentemente alto (exceso de humedad)                                                      |
| **Resultado**               | El lote seco pasa a Devanado u Ovillado                                                                                                                         |

### 2.4 Devanado / Ovillado — Conversión a formato final

Las madejas secas se convierten al formato final según el destino del producto. Son dos variantes del mismo tipo de proceso:

| Variante     | Destino                          | Producto        |
| ------------ | -------------------------------- | --------------- |
| **Devanado** | Cliente industrial               | Conos de hilado |
| **Ovillado** | Venta directa / Comercialización | Ovillos         |

| Aspecto                     | Descripción                                                                                                                                                                                                       |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quién**                   | Responsable operativo asignado a Devanado/Ovillado según la política vigente. Hoy puede coincidir con el mismo responsable que atiende Embolsado.                                                               |
| **Cuándo**                  | Cuando las madejas secas están listas para procesar                                                                                                                                                               |
| **Qué se registra**         | — Fecha y turno de proceso<br>— Responsable que recibe el lote<br>— Supervisor a cargo<br>— Cantidad de madejas procesadas<br>— Cantidad de conos u ovillos producidos<br>— Desperdicio generado en la conversión, con registro en el historial del lote |
| **Inconvenientes posibles** | — Conos dañados<br>— Título incorrecto<br>— Equipo no calibrado para el título<br>— Desperdicio excesivo                                                                                                          |
| **Resultado**               | El lote en conos u ovillos pasa a Embolsado                                                                                                                                                                       |

### 2.5 Embolsado — Empaque del producto final

Los conos u ovillos se empacan en bolsas con sus etiquetas y fichas correspondientes.

| Aspecto                     | Descripción                                                                                                                                                                                    |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quién**                   | Embolsado                                                                                                                                                                                      |
| **Cuándo**                  | Cuando los conos u ovillos están listos para empacar                                                                                                                                           |
| **Qué se registra**         | — Fecha y turno de empaque<br>— Responsable que recibe el lote<br>— Supervisor a cargo<br>— Cantidad de bolsas utilizadas<br>— Cantidad de conos u ovillos por bolsa<br>— Desperdicio generado en Embolsado, con registro en el historial del lote |
| **Inconvenientes posibles** | — Bolsas dañadas<br>— Etiqueta o ficha incorrecta<br>— Conos dañados detectados al empacar<br>— Cantidad de conos no coincide con lo registrado en Devanado                                    |
| **Resultado**               | El lote empacado pasa a Control de Calidad                                                                                                                                                     |

### 2.6 Calidad — Inspección final y clasificación

Calidad inspecciona el lote completo, verifica parámetros, documenta defectos y deja registrado el **estado de calidad** en el que el lote será entregado a Almacén, incluyendo nomenclaturas especiales si corresponde. Si el lote no cumple parámetros mínimos, queda **observado** y dentro de Operación se deben agotar las instancias viables de solución antes de reportar sus condiciones de entrega a Almacén. El lote sale de Operación hacia Almacén con su historial completo de calidad.

| Aspecto             | Descripción                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quién**           | Control de Calidad                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Cuándo**          | Antes de entregar el lote a Almacén                                                                                                                                                                                                                                                                                                                                                                                  |
| **Qué se registra** | — Fecha y turno de inspección<br>— Responsable que inspecciona<br>— Supervisor a cargo<br>— Defectos visuales detectados (doble tono, manchado, varilla, madejas picadas, colas, flames, baja/alta torsión, mezcla)<br>— Defectos internos detectados (purgado, parafinado, ficha, doble cabo, malos amarres, cantidad de amarres, contaminación, etc)<br>— Nomenclatura especial si corresponde<br>— Estado de calidad del lote al momento de entrega<br>— Condiciones de entrega si corresponde |
| **Resultado**       | El lote sale de Operación hacia Almacén con su documentación completa de calidad y el estado en que se entrega                                                                                                                                                                                                                                                                                                                                     |

---

## 3. Inconvenientes y Documentación

### 3.1 Observaciones categorizadas

Cada etapa puede reportar inconvenientes mediante un conjunto predefinido de categorías. Esto permite filtrar, reportar y analizar problemas sin recurrir a texto libre ambiguo.

La categoría se selecciona de un listado específico para cada etapa. Si no aplica ninguna, simplemente no se selecciona.

| Etapa                 | Categorías de inconveniente                                                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Inventario**        | Madejas insuficientes del título requerido / Peso fuera de rango / Datos de emisión incompletos                                                                                       |
| **Tintorería**        | Reteñir (color no conforme) / Temperatura fuera de rango / Tina contaminada / Material incorrecto                                                                                     |
| **Secado**            | Peso fuera de rango / Humedad excesiva                                                                                                                                                |
| **Devanado/Ovillado** | Conos dañados / Título incorrecto / Equipo no calibrado / Desperdicio excesivo                                                                                                        |
| **Embolsado**         | Bolsas dañadas / Etiqueta incorrecta / Conteo no coincide                                                                                                                             |
| **Calidad**           | Doble tono / Manchado / Varilla / Madejas picadas / Colas / Flames / Baja torsión / Alta torsión / Mezcla / Purgado / Parafinado / Ficha / Doble cabo / Malos amarres / Contaminación |

Además de la categoría, se puede incluir un campo opcional de **detalles** en texto libre para contexto adicional (ej: "la tina T-03 presentó residuos del lote anterior").

### 3.2 Registro de historial

Cada intervención conserva fecha de negocio, turno, responsables aplicables y timestamps del sistema. No se persisten pares de timestamps físicos de entrada/salida en el modelo actual. La duración física por etapa queda diferida hasta que el negocio defina qué evento inicia y termina esa medición, cómo se capturará y qué decisiones la usarán.

Esto permite mantener trazabilidad de responsabilidad y de registro, incluso cuando el lote cruza múltiples turnos, sin inferir una duración física que el negocio aún no definió.

El lote avanza cuando **físicamente** cambia de etapa. No existen estados intermedios formales fuera de estas etapas; si el lote está en Tintorería esperando una decisión sobre un reteñir, sigue estando en Tintorería hasta que sale a Secado. Las demoras, observaciones o decisiones pendientes se registran como parte de la etapa actual.

---

## 4. Ciclo de Vida y Estados del Lote

### 4.1 Diagrama de estados

```mermaid
stateDiagram-v2
    [*] --> En_Almacen: Definición de código único
    En_Almacen --> En_Inventario: Armado del lote
    En_Inventario --> En_Tintoreria
    En_Tintoreria --> En_Secado
    En_Secado --> En_Devanado
    En_Devanado --> En_Embolsado
    En_Embolsado --> En_Calidad
    En_Calidad --> En_Espera_Validacion_Almacen: Quality Send
    En_Espera_Validacion_Almacen --> En_Almacen_PT: Recepción de Almacén
    En_Almacen_PT --> [*]
```

### 4.2 Estados

| Estado            | Significado                                                                                     |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| **En_Almacen**    | Lote registrado por Almacén, con código asignado. Pendiente de emisión a Operación. |
| **En_Inventario** | Lote armado por Inventario, primer registro en el sistema de Operación.                         |
| **En_Tintoreria** | Lote en proceso de teñido.                                                                      |
| **En_Secado**     | Lote en proceso de secado.                                                                      |
| **En_Devanado**   | Lote en proceso de devanado u ovillado.                                                         |
| **En_Embolsado**  | Lote en proceso de empaque.                                                                     |
| **En_Calidad**    | Lote en inspección final.                                                                       |
| **En_Espera_Validacion_Almacen** | Quality realizó el único envío permitido; el mismo lote espera la validación y recepción de Almacén. Las notas breves de coordinación no son aceptación ni generan otro envío. |
| **En_Almacen_PT** | Almacén registró la recepción del mismo lote después de la validación física. |

### 4.3 Reglas de transición

1. **Secuencial obligatorio:** No se puede registrar una etapa si el lote no completó la anterior. Para registrar en Devanado, el estado actual debe ser `En_Secado`.
2. **Sin retroceso:** Una vez que el lote avanza a la siguiente etapa, no se retrocede. El lote siempre sigue adelante en el flujo.
3. **Edición controlada con auditoría:** Los datos de una etapa pueden corregirse si hubo error de carga, pero toda edición debe dejar trazabilidad completa de quién editó, cuándo, qué cambió y por qué.
4. **Ventana operativa de corrección:** La edición puede permitirse durante una ventana definida posterior al turno o al cierre de la etapa (por ejemplo 24 o 48 horas, según la política vigente).
5. **Edición restringida fuera de ventana:** Una vez vencida la ventana operativa, solo el rol **SysAdmin** puede editar registros de etapas, manteniendo la misma trazabilidad obligatoria.
6. **Quality Send único:** Todo lote que completa las 6 etapas puede realizar un único Quality Send hacia Almacén con su documentación completa, incluyendo defectos y condiciones de entrega si existieran. El envío deja al lote en espera de validación de Almacén; no se repite ni ocurre concurrentemente para la misma identidad.
7. **Recepción de Almacén:** La aceptación se evidencia solo cuando Almacén registra la recepción para la misma identidad del lote. Las notas breves durante la espera no son aceptación ni otro envío.

### 4.4 Clasificación de Calidad

Calidad documenta el estado de calidad del lote al momento de la entrega. Esa información permite que Almacén verifique lo recibido y luego defina, por separado, su disponibilidad operativa, su disposición y su presentación física según corresponda. El lote siempre se entrega a Almacén, aun cuando llegue con observaciones o condiciones especiales.

| Clasificación         | Significado                                                                                     | Ejemplo de uso                                                                |
| --------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Estándar**          | PT sin defectos o con defectos menores dentro de tolerancia                                     | Lote que cumple especificaciones                                              |
| **Con nomenclatura**  | PT con características especiales que modifican su clasificación o valor                        | Lote con una designación especial definida por calidad según la política vigente |
| **Observado**         | PT con defectos o condiciones documentadas que obligan a tomar decisiones dentro de Operación o a informar condiciones de entrega a Almacén | Doble tono, manchado, conos dañados, defectos que requieren definir salida    |

---

## 5. Reglas de Negocio

### 5.1 Trazabilidad multi-turno

El proceso completo del lote puede durar entre 1 y 2 días, cruzando múltiples turnos. Cada registro de etapa captura:

- La fecha de negocio y el turno de la intervención
- El responsable que recibe, entrega o ejecuta, según corresponda a la etapa
- El supervisor a cargo
- Los timestamps de registro y corrección del sistema

Esto permite responder quién hizo qué y en qué turno. La duración física de cada etapa no se calcula ni se infiere hasta que exista una definición de negocio aprobada.

### 5.2 Peso por etapa

El peso del lote se mide al inicio de cada etapa para calcular la merma acumulada. La diferencia entre etapas consecutivas revela pérdidas de material durante el proceso.

### 5.3 Corrección de registros

Los registros de cada etapa (fechas, responsables, datos técnicos) pueden corregirse si hubo error de carga, pero toda corrección debe dejar auditoría completa: usuario editor, fecha/hora, valores anteriores, valores nuevos y motivo del cambio. La edición operativa puede permitirse dentro de una ventana definida; fuera de esa ventana, solo **SysAdmin** puede editar.

### 5.4 Validación antes de avanzar

Antes de registrar una etapa, el sistema verifica:

- Que el lote existe y tiene un código válido
- Que la etapa anterior está completada
- Que los datos obligatorios están presentes (turno, supervisor, responsable, peso/cantidad)

### 5.5 Cierre del ciclo del lote en Operación

El tramo de Operación concluye cuando Calidad completa su inspección y realiza el único Quality Send. El mismo lote queda en espera de validación de Almacén hasta que Almacén registra su recepción. A partir de esa aceptación, Almacén verifica lo recibido, clasifica el estado del PT y decide su disposición. Esa decisión ya corresponde al dominio de Almacén, no al de Operación.

---

## 6. Visibilidad por Rol

La siguiente visibilidad describe la operación actual esperada. La política exacta de permisos puede cambiar según RBAC. Cada rol ve la información necesaria para su trabajo, más la etapa inmediatamente anterior para validar consistencia. Calidad ve el historial del lote y sus características de calidad; Supervisor puede ver la información de ambos procesos para consolidación operativa.

| Rol                          | Ve sus datos          | Ve (lectura)                                     |
| ---------------------------- | --------------------- | ------------------------------------------------ |
| **Inventario**               | Inventario (armado y seguimiento)   | Información de Almacén: código, título, cliente  |
| **Personal de Tintorería**   | Tintorería, Secado    | Inventario: madejas, peso total                  |
| **Responsable operativo de Devanado/Ovillado** | Devanado/Ovillado     | Secado: madejas, peso total                      |
| **Embolsado**                | Embolsado             | Devanado/Ovillado: conos, desperdicio            |
| **Calidad**                  | Calidad               | Historial del lote y sus características registradas |
| **Supervisor**               | Todas (solo lectura)  | Todas (solo lectura). No registra como regla general; supervisa y consolida.    |
| **Jefe de Producción**       | Dashboard consolidado | Todas las etapas de todos los lotes activos      |
| **Almacén**                  | Sus movimientos       | Datos productivos del lote (solo lectura)        |

---

## 7. Glosario

| Término                       | Definición                                                                                                                                |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Lote**                      | Conjunto físico de madejas que comparten título, color y destino, armado en este proceso e identificado por el código definido por Almacén                                       |
| **Código de lote**            | Identificador único asignado por Almacén al definir el pedido. Su formato podrá rediseñarse más adelante                                                                               |
| **Especificaciones del lote** | Información definida por Almacén en el sistema: código de lote, título, color, cliente y datos del pedido                           |
| **Armado de lote**            | Proceso por el cual Inventario selecciona madejas crudas producidas en Madejeras para formar un lote según el título y peso especificados |
| **Clasificación de calidad**  | Categoría asignada por Calidad al PT (estándar, con nomenclatura u observado) que documenta su estado de calidad al momento de la entrega                   |
| **Nomenclatura**              | Designación especial asignada por Calidad al PT que modifica su clasificación según la política vigente                                       |
| **Merma**                     | Diferencia de peso entre etapas consecutivas que revela pérdida de material                                                               |
| **Devanado**                  | Conversión de madejas en conos (formato para cliente industrial)                                                                          |
| **Ovillado**                  | Conversión de madejas en ovillos (formato para venta directa)                                                                             |
