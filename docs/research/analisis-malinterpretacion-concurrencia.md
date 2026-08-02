---
document_type: research
status: active
implementation: not-applicable
scope: global/concurrency
authority: evidence
owner: architecture
last_reviewed: 2026-07-27
---

# Análisis de Malinterpretación — Concurrencia y Tiempo Real

> **Propósito:** Identificar qué fragmentos del PRD podrían haber llevado a interpretar
> erróneamente el sistema como concurrente, streaming o en tiempo real, cuando en realidad
> es un sistema de **registro batch por turno secuencial**.
>
> **Conclusión anticipada:** La confusión NO proviene de una redacción ambigua del PRD,
> sino de **asumir que "multi-turno" significa concurrencia**, cuando en realidad significa
> **trazabilidad a través de múltiples turnos secuenciales**.

---

## 1. Fragmentos que Podrían Malinterpretarse

### 1.1 PRD Maestro — [§6 Transversal Rules](../prd/product-overview.md#6-transversal-rules)

#### Fragmento original:

> **5. La operación es continua por turnos.** 3 turnos, cada uno con un Supervisor
> a cargo. La producción no se detiene. El sistema debe soportar el traspaso
> de información entre turnos sin pérdida ni duplicación.

#### ¿Por qué podría confundir?

- **"La producción no se detiene"** — podría interpretarse como que el sistema debe
  procesar datos en tiempo real mientras la planta opera, cuando en realidad significa
  que la planta física opera 24/7 pero el **registro se hace al final del turno**.

- **"Soportar el traspaso de información entre turnos"** — podría entenderse como
  sincronización concurrente entre turnos activos, cuando en realidad significa
  **registrar quién hizo qué y en qué turno**, porque un lote puede cruzar múltiples
  turnos antes de completarse.

#### ¿Qué dice realmente?

- Los turnos son **secuenciales** (mañana → tarde → noche), NO concurrentes.
- El sistema debe **registrar el timeline** del lote para saber en qué turno estuvo en cada etapa.
- El "traspaso" es **documental**, no operativo en tiempo real.

---

### 1.2 PRD Operación — [§2 Actors](../prd/operation/overview.md#2-actors)

#### Fragmento original:

> **Nota:** A diferencia de lo definido en el PRD maestro, donde se indica
> que "los operarios no usan el sistema", en Operación existen roles operativos
> (Calidad, Inventario, Personal de Tintorería, Embolsado) que **sí registran datos en el sistema** según su ámbito.

#### ¿Por qué podría confundir?

- **"Registran datos en el sistema"** — podría interpretarse como que están escribiendo
  en el sistema **durante el proceso**, cuando en realidad el registro se hace **al completar
  cada etapa o al final del turno**.

#### ¿Qué dice realmente?

- Los roles operativos registran los datos **de su turno** una vez que tienen los datos consolidados.
- No es streaming ni en tiempo real. Es **registro batch post-facto**.

---

### 1.3 Yarn Spinning — [§3.1 Record Nature](../prd/operation/yarn-spinning.md#31-record-nature)

#### Fragmento original:

> El registro de producción es **granular, por descarga**. Una misma máquina
> puede tener múltiples descargas en un mismo turno (del mismo o distinto título),
> o puede no tener ninguna. Cada descarga se registra individualmente.

#### ¿Por qué podría confundir?

- **"Cada descarga se registra individualmente"** — podría interpretarse como que se
  registra cada descarga **en el momento que ocurre**, cuando en realidad se registran
  todas las descargas del turno **al final del turno** o cuando el encargado tenga tiempo.

#### ¿Qué dice realmente?

- La granularidad es **por descarga** (no por turno agregado), pero el **momento del registro**
  es al final del turno o cuando el encargado lo documente, no necesariamente al instante de la descarga.
- El sistema necesita soportar **múltiples registros por turno**, pero no implica streaming.

---

### 1.4 Lot Processing — [§1.3 Lifecycle across contexts](../prd/operation/lot-processing.md#13-lifecycle-across-contexts)

#### Fragmento original:

> El tiempo total del proceso es de aproximadamente 1 a 2 días, pudiendo cruzar
> múltiples turnos. Cada registro incluye el turno y responsable correspondiente
> para mantener trazabilidad multi-turno.

#### ¿Por qué podría confundir?

- **"Cruzar múltiples turnos"** — podría interpretarse como que múltiples supervisores
  están trabajando **simultáneamente** sobre el mismo lote, cuando en realidad significa
  que el lote **avanza secuencialmente** por turnos diferentes (ej: entra a Tintorería en
  turno mañana, sale en turno tarde).

- **"Trazabilidad multi-turno"** — podría sonar como "sincronización entre turnos concurrentes",
  cuando simplemente significa **registrar quién recibió y quién entregó el lote en cada etapa**.

#### ¿Qué dice realmente?

- Los turnos son **secuenciales**, no concurrentes.
- Un lote puede estar en Tintorería desde el turno de mañana hasta el turno de tarde,
  pero cada turno registra su parte del proceso **al final de su turno**, no en tiempo real.

---

### 1.5 Lot Processing — [§4.1 Categorized observations](../prd/operation/lot-processing.md#41-categorized-observations)

#### Fragmento original:

> Cada etapa puede reportar inconvenientes mediante un conjunto predefinido de categorías.
> Esto permite filtrar, reportar y analizar problemas sin recurrir a texto libre ambiguo.

#### ¿Por qué podría confundir?

- **"Reportar inconvenientes"** — podría interpretarse como que el sistema debe notificar
  en tiempo real cuando ocurre un problema, cuando en realidad el inconveniente se
  **documenta al registrar la etapa**, no necesariamente cuando ocurrió físicamente.

#### ¿Qué dice realmente?

- Los inconvenientes se documentan **al momento de registrar la etapa en el sistema**,
  que puede ser al final del turno o cuando el encargado completa el registro.
- No hay alertas en tiempo real ni streaming de inconvenientes.

---

### 1.6 Yarn Spinning — [§4.1 Record Nature](../prd/operation/yarn-spinning.md#41-record-nature)

#### Fragmento original:

> El registro de avance es un **reporte/resumen** por máquina, turno y título.
> A diferencia de la producción (granular por descarga), el avance consolida
> en un solo registro:
>
> - Lo que **entró** a la máquina/sección como materia prima
> - Lo que **se produjo** (sumatoria de descargas del turno)
> - Lo que **sale** como producto hacia la siguiente sección

#### ¿Por qué podría confundir?

- **"Lo que sale como producto"** — podría interpretarse como que el sistema debe calcular
  el saldo en tiempo real mientras la máquina produce, cuando en realidad es un **reporte
  consolidado al final del turno**.

#### ¿Qué dice realmente?

- El avance es un **resumen consolidado** que se registra **al final del turno** o cuando
  el encargado (Calidad o Inventario) tiene todos los datos.
- No es un cálculo en tiempo real. Es un registro batch.

---

## 2. Características del PRD que SÍ Dejan Clara la Naturaleza Batch

### 2.1 Lot Processing — [§4.2 History recording](../prd/operation/lot-processing.md#42-history-recording)

> Cada etapa captura el momento en que el lote **entra** y el momento en que **sale**,
> junto con quién lo recibió y quién lo entregó.

**Interpretación correcta:**

- El sistema registra **eventos discretos** (entrada y salida de cada etapa).
- No hay estados intermedios ni actualización continua.
- Es un **registro de eventos batch**, no streaming.

### 2.2 Yarn Spinning — [§7 Actors and Responsibilities](../prd/operation/yarn-spinning.md#7-actors-and-responsibilities)

> **Supervisor**: Supervisa la producción de su turno. Responsable de la planta y del personal.
> Verifica coherencia de datos.

**Interpretación correcta:**

- El Supervisor **verifica coherencia** al final del turno, cuando los datos ya están registrados.
- No está monitoreando en tiempo real mientras ocurre la producción.

### 2.3 PRD Maestro — [§4 Actors](../prd/product-overview.md#4-actors)

> **Supervisor**: Está a cargo de la operación en su turno. Registra producción por sección,
> control de calidad, lotes y desperdicio **directamente en el sistema**.

**Interpretación correcta:**

- **"Directamente en el sistema"** significa que no usa planillas intermedias en Excel,
  **NO que lo hace en tiempo real mientras opera**.
- El registro se hace **al completar el turno** o cuando el Supervisor tiene los datos consolidados.

---

## 3. ¿Por Qué Surgió la Confusión?

### 3.1 Términos que suenan "concurrentes" pero no lo son

| Término del PRD | Interpretación errónea | Significado real |
|---|---|---|
| **"La producción no se detiene"** | Sistema debe procesar en tiempo real 24/7 | Planta opera 24/7, pero registro es batch por turno |
| **"Soportar el traspaso de información entre turnos"** | Sincronización concurrente entre turnos activos | Registrar quién hizo qué y en qué turno (trazabilidad) |
| **"Cruzar múltiples turnos"** | Múltiples supervisores editando el mismo lote simultáneamente | El lote avanza secuencialmente por turnos diferentes |
| **"Trazabilidad multi-turno"** | Sincronización de estados en tiempo real | Timeline de eventos discretos (entrada/salida de cada etapa) |
| **"Cada descarga se registra individualmente"** | Streaming de descargas en tiempo real | Registro granular al final del turno |

### 3.2 Ausencia de palabras clave "batch" o "al final del turno"

El PRD no dice explícitamente **"el registro se hace al final del turno"** en todos los puntos donde
describe el registro de datos. Esto deja abierta la interpretación de que el registro ocurre
**mientras la producción está en curso**.

Sin embargo, el PRD sí lo dice en algunos lugares clave:

- `operation.md` [§2 Actors](../prd/operation/overview.md#2-actors): **"Registra producción por sección"** (implica consolidación post-turno).
- `lot-processing.md` [§4.2 History recording](../prd/operation/lot-processing.md#42-history-recording): **"Captura el momento en que el lote entra y el momento en que sale"**
  (eventos discretos, no streaming).

### 3.3 Analogía con sistemas de manufactura en tiempo real

Muchos sistemas de manufactura modernos (MES, SCADA) procesan datos en tiempo real desde
sensores y PLCs. Si el lector tiene experiencia con esos sistemas, es natural asumir que
este sistema también es en tiempo real.

**Pero este no es un sistema de ese tipo.** Es un sistema de **registro documental batch**
que reemplaza planillas de Excel y papel.

---

## 4. Recomendaciones para Evitar Futuras Confusiones

### 4.1 Agregar una sección "Modelo de Registro" al PRD Maestro

Propongo agregar una sección explícita en `docs/prd/product-overview.md` que aclare el modelo de registro:

```markdown
### 2.4 Modelo de Registro

El sistema es un **sistema de registro batch por turno secuencial**, NO un sistema en tiempo real.

| Aspecto | Descripción |
|---|---|
| **Cuándo se registran los datos** | Al final del turno o cuando el encargado tiene los datos consolidados |
| **Granularidad del registro** | Por descarga (Yarn Spinning) o por etapa (Lot Processing) |
| **Turnos** | Secuenciales (mañana → tarde → noche), NO concurrentes |
| **Trazabilidad multi-turno** | Registrar quién hizo qué y en qué turno, NO sincronización en tiempo real |
| **"La producción no se detiene"** | La planta opera 24/7, pero el registro es batch post-turno |
```

### 4.2 Enfatizar "batch" en las secciones de Yarn Spinning y Lot Processing

Agregar al inicio de `yarn-spinning.md` [§3.1 Record Nature](../prd/operation/yarn-spinning.md#31-record-nature):

> **Modelo de registro:** El registro de producción es **batch por turno**. Cada descarga
> se registra individualmente, pero el registro se hace **al final del turno** o cuando
> el encargado (Calidad o Inventario) tiene los datos consolidados. **No es streaming ni en tiempo real.**

Agregar al inicio de `lot-processing.md` [§4.2 History recording](../prd/operation/lot-processing.md#42-history-recording):

> **Modelo de registro:** El registro de cada etapa es **batch al completar la etapa**.
> Los datos se capturan cuando el lote **sale físicamente** de la etapa hacia la siguiente,
> no durante el proceso. Los turnos son **secuenciales**, no concurrentes.

### 4.3 Glosario unificado

Agregar al glosario del PRD Maestro:

| Término | Definición |
|---|---|
| **Registro batch** | Los datos se registran en el sistema al final del turno o al completar la etapa, NO en tiempo real durante el proceso |
| **Multi-turno** | El lote puede cruzar múltiples turnos antes de completarse. Los turnos son **secuenciales** (mañana → tarde → noche), NO concurrentes |
| **Trazabilidad multi-turno** | Registrar quién recibió y quién entregó el lote en cada turno y etapa, permitiendo reconstruir el timeline completo del lote |

---

## 5. Conclusión

La confusión sobre concurrencia y tiempo real **NO proviene de una redacción ambigua o defectuosa del PRD**.

El PRD es técnicamente correcto y completo. La confusión surge de:

1. **Asumir que "multi-turno" implica concurrencia**, cuando en realidad significa trazabilidad
   secuencial a través de turnos.

2. **Interpretar "la producción no se detiene" como "el sistema debe operar en tiempo real"**,
   cuando en realidad significa que la planta física opera 24/7 pero el registro es batch.

3. **Falta de experiencia con sistemas de registro documental batch** — si el lector viene de
   sistemas MES/SCADA en tiempo real, es natural asumir que este sistema también lo es.

**Solución:**

- Agregar una sección explícita "Modelo de Registro" al PRD Maestro.
- Enfatizar "batch por turno" en las secciones de registro de Yarn Spinning y Lot Processing.
- Agregar al glosario las definiciones de "Registro batch", "Multi-turno" y "Trazabilidad multi-turno".

Con estos ajustes, el PRD será **imposible de malinterpretar** en este aspecto.
