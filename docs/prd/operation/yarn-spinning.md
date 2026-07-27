---
document_type: prd
status: active
implementation: not-started
scope: operation/yarn-spinning
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Hilatura (`Yarn Spinning`)

> **Domain PRD — Hilatura (`Yarn Spinning`)**
>
> Proceso continuo de hilatura que transforma la Materia Prima en hilado
> de un título específico a través de 5 secciones productivas.
>
> Pertenece a la Unidad Operación. Para el contexto general, actores y
> reglas transversales, ver [Operation Overview](./overview.md).
>
> **Siguiente:** `docs/domain/operation/yarn-spinning.md` (Modelo de Dominio)

---

## 1. Propósito y Alcance

### 1.1 Propósito

Documentar el proceso de **Hilatura (`Yarn Spinning`)**,
un flujo continuo y secuencial que transforma los fardos de MP recibidos de
Almacén en hilado de un título específico, listo para su salida en madejas
desde Madejeras y posterior uso en el Proceso por Lotes (`Lot Processing`). En
este proceso aún no existe el lote como entidad física ni se opera con código
de lote.

### 1.2 Alcance

Cubre las 5 secciones productivas, sus registros de producción, avance,
calidad de proceso y desperdicio:

| Sección                   | Producción | Avance             | Calidad            | Desperdicio |
| ------------------------- | ---------- | ------------------ | ------------------ | ----------- |
| Preparación               | ✓          | ✓ (entrada/salida) | ✓ (muestras)       | ✓           |
| Continuas (Ring Spinning) | ✓          | ✓ (entrada/salida) | ✓ (muestras)       | ✓           |
| Bobinados (Winding)       | ✓          | —                  | ✓ (body/km/cortes) | ✓           |
| Retorcido (Twisting)      | ✓          | ✓ (entrada/salida) | ✓ (aleatoria)      | ✓           |
| Madejeras (Skeining)      | ✓          | —                  | ✓ (aleatoria)      | ✓           |

**No incluye:**

- El proceso por lotes posterior (Proceso por Lotes / `Lot Processing`, documentado en `lot-processing.md`)
- Calidad de lote (evaluación final antes de entrega a Almacén, en `lot-processing.md`)
- Gestión de insumos o MP (responsabilidad de Almacén)

### 1.3 Dependencias

| Proceso                     | Relación                                                                 |
| --------------------------- | ------------------------------------------------------------------------ |
| **Almacén (entrada)**       | Entrega la MP y la información necesaria para su procesamiento                     |
| **Proceso por Lotes (`Lot Processing`) (salida)** | Recibe las madejas producidas para el armado posterior de lotes |

---

## 2. Las 5 Secciones

### 2.1 Flujo del Proceso

```
MP (fardos)
  │
  ▼
PREPARACIÓN
  │  Máquinas: PSJ (Preparación A/B) + FIN (Finisores A/B)
  │  Registro: FIN producen, PSJ solo avance
  ▼
CONTINUAS (Ring Spinning)
  │  Máquinas: marcos de hilatura
  │  Registro: peso neto, No. husos
  ▼
BOBINADOS (Winding)
  │  Máquinas: bobinadoras
  │  Registro: peso neto, No. husos (sin avance)
  ▼
RETORCIDO (Twisting)
  │  Máquinas: retorcedoras
  │  Registro: peso neto, No. husos (gestiona Inventario)
  ▼
MADEJERAS (Skeining)
  │  Producción: madejas (no husos)
  │  Punto de salida hacia el proceso siguiente
  ▼
  PROCESO POR LOTES (`Lot Processing`)
```

### 2.2 Cuadro por Sección

| #   | Sección                       | Tipo de máquinas     | Unidad de producción   | Tiene avance | Quién registra prod. | Quién registra avance |
| --- | ----------------------------- | -------------------- | ---------------------- | ------------ | -------------------- | --------------------- |
| 1   | **Preparación**               | PSJ (A/B), FIN (A/B) | kg (neto), No. mechas  | Sí           | Calidad              | Calidad               |
| 2   | **Continuas** | Marcos de hilatura | kg (neto), No. husos   | Sí           | Calidad              | Calidad               |
| 3   | **Bobinados** | Bobinadoras        | kg (neto), No. husos   | No           | Calidad              | —                     |
| 4   | **Retorcido** | Retorcedoras       | kg (neto), No. husos   | Sí           | Inventario           | Inventario            |
| 5   | **Madejeras** | Madejeras          | No. madejas, peso neto | No           | Inventario           | —                     |

> **Nota:** La asignación actual de registro en Bobinados recae en Calidad,
> aunque puede reasignarse por política de permisos.

---

## 3. Registro de Producción

### 3.1 Naturaleza del Registro

El registro de producción es **granular, por descarga**. Una misma máquina
puede tener múltiples descargas en un mismo turno (del mismo o distinto título),
o puede no tener ninguna.

**Granularidad:** 1 descarga × 1 máquina × 1 turno × 1 fecha × 1 título.

**Momento del registro:** Aunque las descargas ocurren físicamente a lo largo
del turno (ej: 8:00 AM, 10:30 AM, 1:00 PM), el registro digital de **todas**
se realiza al finalizar el turno (ej: 2:00 PM) en una sola sesión de captura.
El sistema captura el timestamp real de cada descarga, pero no es un sistema
en tiempo real. Ver [sección 2.4 del PRD maestro](../product-overview.md#5-data-capture-model).

### 3.2 El Número de Husos

Cada máquina tiene entre 20 y 200 husos (según la sección y tipo de máquina).
No es práctico pesar cada huso individualmente. Por eso el **número de husos
operativos** es un dato fundamental. El cálculo del peso varía según el tipo
de registro:

| Tipo de registro | Cálculo de peso |
|---|---|
| **Avance (entrada/salida/acumulado)** | Se pesa 1 huso como muestra (bruto − tara de ese huso), se asume que todos los husos tienen el mismo peso, y se multiplica por el número total de husos. |
| **Descarga (producción granular)** | Se pesa el carro/tacho/turril completo (peso bruto total). El neto se calcula como: **bruto_total − (tara_huso × num_husos) − peso_carro**. |

> En las descargas, el peso neto no es simplemente bruto − tara de un
> contenedor, porque cada descarga contiene el producto de múltiples husos
> y se transporta en un carro que tiene su propio peso.

### 3.3 Datos Registrados por Descarga

#### Preparación, Continuas, Bobinados, Retorcido

Para cada descarga se registra:

- **Máquina** que produjo
- **Turno** y **fecha**
- **Supervisor de turno**
- **Título** producido (ej. 2/18, 2/32). Puede ser distinto del título
  inicial del turno si hubo cambio.
- **Peso bruto total** de la descarga (carro o contenedor completo)
- **Tara por huso** (para el cálculo ajustado)
- **Número de husos** operativos en la máquina
- **Peso del carro / contenedor** usado para transportar la descarga
- **Registro actual:** Calidad en Preparación, Continuas y Bobinados; Inventario en Retorcido

#### Madejeras

Para cada descarga se registra:

- **Máquina** que produjo
- **Turno** y **fecha**
- **Supervisor de  turno**
- **Título**
- **Número de madejas** producidas
- **Peso unitario estimado** por monio (1 monio = 10 madejas ~ 5kg, en ocasiones la madeja debe pesar 600g y no 500g de acuerdo a requirimeinto del titulo)
- **Registro actual:** Inventario

> [!NOTE] Madejeras
> La producción es operario-dependiente, no ciclo-máquina.
> La métrica principal es el número de madejas producidas. No usa husos ni tara.
> El peso total se estima como: madejas × peso unitario. En Hilatura, Madejeras
> todavía no arma lotes: solo produce madejas con determinado peso para el
> proceso siguiente.

### 3.4 Reglas de Producción

1. **Peso neto siempre calculado:** El sistema calcula el neto aplicando la
   fórmula correspondiente (con husos y carro para descarga; con muestreo
   proporcional para avance). No se ingresa peso neto directo.
2. **Solo FIN producen en Preparación:** Las máquinas FIN-A y FIN-B son las
   únicas que registran producción en Preparación. Las PSJ solo registran avance.
3. **Madejeras no usa husos ni tara:** Madejeras registra madejas producidas
   (valor numérico) y peso unitario estimado. No aplica el cálculo con husos.
4. **Múltiples descargas por turno:** Una máquina puede tener varias descargas
   en un mismo turno, o ninguna. Cada descarga es un registro independiente.
5. **Cambio de título durante el turno:** Una máquina puede cambiar de título
   dentro del mismo turno, o trabajar con títulos diferentes simultáneamente
   en distintos husos. Cada descarga lleva el título que le corresponde.
6. **Sin lote en Hilatura:** En este proceso no existe todavía el lote como
   entidad física ni se registra código de lote. La salida de Hilatura son
   madejas y registros de producción por sección/máquina/turno/título.
7. **Edición controlada con auditoría:** Los registros operativos pueden
   corregirse cuando exista un error de carga, pero toda edición debe dejar
   trazabilidad completa del cambio, incluyendo usuario, fecha, valores
   anteriores, valores nuevos y motivo de corrección.
8. **Ventana de corrección operativa:** La edición puede permitirse durante una
   ventana definida posterior al turno (por ejemplo 24 o 48 horas, según la
   política vigente).
9. **Edición restringida fuera de ventana:** Una vez vencida la ventana de
   corrección operativa, solo el rol **SysAdmin** puede editar el registro,
   manteniendo la misma trazabilidad obligatoria.

---

## 4. Avance

### 4.1 Naturaleza del Registro

El registro de avance es un **reporte/resumen** por máquina, turno y título.
A diferencia de la producción (granular por descarga), el avance consolida
en un solo registro:

- Lo que **entró** a la máquina/sección como materia prima
- Lo que **se produjo** (sumatoria de descargas del turno)
- Lo que **sale** como producto hacia la siguiente sección

Es decir, el avance es una **sumatoria del detalle de producción** más los
datos de entrada y salida del proceso.

**Cálculo del peso en avance:** A diferencia de las descargas (que se pesan
por carro completo), en el avance el peso de entrada y salida se calcula
**por muestreo de huso**: se pesa 1 huso, se resta su tara, y se multiplica
por el número total de husos de la máquina. Se asume que todos los husos
tienen el mismo peso.

### 4.2 Secciones con Avance

Solo 3 secciones registran avance:

| Sección | Quién registra | Datos registrados |
|---|---|---|
| **Preparación** | Calidad | Peso de entrada, peso total descargado (suma de descargas), peso de salida |
| **Continuas** | Calidad | Peso de entrada, peso neto en máquina, peso total descargado, No. husos, horas trabajadas, peso de salida |
| **Retorcido** | Inventario | Peso de entrada, peso neto en máquina, peso total descargado, No. husos, horas trabajadas, peso de salida |

**Bobinados y Madejeras no registran avance.**

### 4.3 Granularidad

Cada registro de avance representa: **1 máquina × 1 turno × 1 fecha × 1 título**.

### 4.4 Propósito del Avance

El avance permite:

- **Validación cruzada:** El peso total descargado (del avance) debe coincidir
  con la suma de las descargas individuales de producción.
- **Cálculo de merma:** Diferencia entre peso de entrada y peso de salida revela
  pérdidas en la sección.
- **Productividad:** kg/hora por máquina y sección.
- **Estado del proceso:** Saber cuánto material está procesando cada sección.

---

## 5. Calidad de Proceso

### 5.1 Responsable

**Calidad** es responsable del control de calidad de proceso en TODAS las
secciones de Hilatura (`Yarn Spinning`), sin excepción. La frecuencia y el método varían
según la sección.

### 5.2 Métodos por Sección

| Sección         | Método                     | Descripción                                                                                       |
| --------------- | -------------------------- | ------------------------------------------------------------------------------------------------- |
| **Preparación** | Muestras                   | Se toman muestras de Preparación A y B para evaluar consistencia                                  |
| **Continuas**   | Muestras (12/máquina/tipo) | 12 muestras por máquina y tipo de hilado. Evalúa CV%, tenacidad, elongación                       |
| **Bobinados**   | Body/km/cortes             | No se toman muestras. Se registran datos de la máquina: body, kilómetros, cortes por bobina       |
| **Retorcido**   | Aleatoria                  | Pruebas aleatorias. Frecuencia menor que en Preparación y Continuas                               |
| **Madejeras**   | Aleatoria                  | Pruebas aleatorias. Madejeras no tiene calidad de proceso sistemática (se evalúa a nivel de lote) |

### 5.3 Datos Registrados

Por cada control de calidad se captura:

- **Sección, máquina y turno** evaluados
- **Tipo de muestra:** según el título evaluado (HB, N, CH, etc.)
- **Resultados de las pruebas:** varían según el método:
  - *Muestras:* valores individuales de cada muestra, CV%, tenacidad
  - *Body/km/cortes:* datos registrados por la máquina
  - *Aleatorio:* resultados de las pruebas realizadas
- **Quién registra** (Calidad)

### 5.4 Reglas de Calidad

1. **Todas las secciones son evaluadas:** No hay excepciones. Calidad prueba
   todas las máquinas en todas las secciones.
2. **Frecuencia variable:** Preparación y Continuas tienen muestreo sistemático.
   Retorcido y Madejeras tienen muestreo aleatorio. Bobinados usa registro de
   máquina en lugar de muestras.
3. **Nomenclaturas especiales:** Como resultado de la calidad de proceso y de
   lote, Calidad puede asignar nomenclaturas al PT según la política vigente.
   Esto aplica al producto completo que luego se entregará al proceso
   siguiente, no a la máquina individual.
4. **Registro separado:** La calidad de proceso en Hilatura (`Yarn Spinning`) es distinta e
   independiente de la calidad de lote (evaluación final en Proceso por Lotes / `Lot Processing`).

---

## 6. Desperdicio

### 6.1 Responsable

**Inventario** registra el desperdicio real de TODAS las secciones y máquinas
de la planta, incluyendo Hilatura (`Yarn Spinning`).

### 6.2 Datos Registrados

Por cada registro de desperdicio se captura:

- **Sección** y **grupo de máquinas** (se pesan juntas)
- **Turno** y **fecha**
- **Peso** del desperdicio
- **Tipo:** real o acumulado
- **Quién registra** (Inventario)

### 6.3 Reglas de Desperdicio

1. **Desperdicio por grupo de máquinas:** Las máquinas se pesan juntas
   físicamente. No se pesa máquina por máquina.
2. **Desperdicio real vs acumulado:** El desperdicio real lo registra
   Inventario. El desperdicio acumulado lo gestiona Producción. La suma
   de ambos se denomina "desperdicio teórico".
3. **Madejeras — desperdicio excepcional:** Las madejas fuera de
   especificación no se registran como desperdicio convencional. Retornan
   a una etapa anterior del proceso para reproceso.
4. **Edición controlada del desperdicio:** Si existe un error de carga, el
   registro puede corregirse con trazabilidad completa de quién editó, cuándo,
   qué cambió y por qué.
5. **Restricción temporal:** La corrección del desperdicio sigue la misma
   ventana operativa definida para los registros de producción. Fuera de esa
   ventana, solo **SysAdmin** puede editar.

---

## 7. Actores y Responsabilidades

| Actor                      | Rol en Hilatura (`Yarn Spinning`)                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Supervisor**             | Supervisa la producción de su turno. Responsable de la planta y del personal. Verifica coherencia de datos.            |
| **Control de Calidad**     | Realiza pruebas de calidad en TODAS las secciones y máquinas. Registra actualmente producción y avance de Preparación, Continuas y Bobinados. |
| **Inventario**             | Registra producción y avance de Retorcido y Madejeras. Registra desperdicio real de todas las secciones.               |
| **Embolsado**              | No interviene directamente en Hilatura (`Yarn Spinning`). Su participación comienza en Proceso por Lotes (`Lot Processing`).                              |
| **Personal de Tintorería** | No interviene en Hilatura (`Yarn Spinning`).                                                                                        |

---

## 8. Requerimientos Funcionales

### 8.1 Producción

| ID       | Requerimiento                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| YS-PR-01 | El sistema debe permitir registrar producción por máquina, turno, fecha y título para cada sección.                                   |
| YS-PR-02 | El sistema debe calcular el peso neto automáticamente (gross - tare).                                                                 |
| YS-PR-03 | El sistema debe validar que solo las máquinas FIN (A/B) registren producción en Preparación.                                          |
| YS-PR-04 | El sistema debe permitir el registro de Madejeras con madejas y peso unitario, no peso bruto/tara.                       |
| YS-PR-05 | El sistema debe soportar una asignación configurable de quién registra por sección. La operación actual registra Calidad para Preparación, Continuas y Bobinados; e Inventario para Retorcido y Madejeras. |
| YS-PR-06 | El sistema debe permitir al Supervisor consultar la producción de su turno en todas las secciones.                                    |

### 8.2 Avance

| ID       | Requerimiento                                                                                                                          |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| YS-AV-01 | El sistema debe permitir registrar avance (entrada/salida) por máquina, turno, fecha y título para Preparación, Continuas y Retorcido. |
| YS-AV-02 | El sistema debe calcular la diferencia entrada - salida para detectar merma en cada sección.                                           |
| YS-AV-03 | Bobinados y Madejeras no deben tener formulario de avance.                                                                             |

### 8.3 Calidad de Proceso

| ID       | Requerimiento                                                                                                                                         |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| YS-QL-01 | El sistema debe permitir registrar controles de calidad por máquina, turno y sección.                                                                 |
| YS-QL-02 | El sistema debe soportar los 3 métodos de calidad: muestras (Preparación, Continuas), body/km/cortes (Bobinados), y aleatorio (Retorcido, Madejeras). |
| YS-QL-03 | El sistema debe permitir registrar nomenclaturas especiales del PT a nivel de lote (no por máquina).                                                  |
| YS-QL-04 | Calidad debe poder consultar el historial de calidad de cualquier máquina y sección.                                                                  |

### 8.4 Desperdicio

| ID       | Requerimiento                                                                                                                                      |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| YS-WS-01 | El sistema debe permitir registrar desperdicio por grupo de máquinas, no por máquina individual.                                                   |
| YS-WS-02 | El sistema debe distinguir entre desperdicio real (registrado por Inventario) y teorico (real + acumulado).                             |
| YS-WS-03 | El sistema debe manejar el caso especial de Madejeras: madejas fuera de especificación no se registran como desperdicio, se marcan para reproceso. |

### 8.5 Transversales

| ID       | Requerimiento                                                                                                              |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| YS-TR-01 | El sistema debe permitir la edición controlada de registros de producción, avance, calidad y desperdicio cuando exista error de carga, preservando auditoría completa del cambio.                             |
| YS-TR-02 | El sistema debe registrar para cada corrección: usuario editor, fecha/hora, valores anteriores, valores nuevos y motivo del cambio.                                         |
| YS-TR-03 | El sistema debe validar que el usuario tenga el permiso correspondiente según la política de acceso vigente para cada tipo de registro. |
| YS-TR-04 | El sistema debe permitir la edición por roles operativos solo dentro de una ventana definida posterior al turno (por ejemplo 24 o 48 horas).               |
| YS-TR-05 | Una vez vencida la ventana operativa de corrección, solo el rol **SysAdmin** puede editar registros de Hilatura.               |
| YS-TR-06 | El Supervisor debe poder visualizar un consolidado de producción, avance, calidad y desperdicio de su turno.               |

---

## 9. Métricas y Reportes

A partir de los datos registrados (producción, avance, calidad y desperdicio),
el sistema debe calcular las siguientes métricas para el dashboard de cada
sección y el consolidado del Supervisor.

### 9.1 Métricas de Producción

| Métrica | Unidad | Propósito |
|---|---|---|
| **Total descargado** | kg | Suma de todas las descargas del período (turno/día/semana) por máquina, título y sección |
| **Número de descargas** | — | Cantidad de descargas realizadas en el período. Ayuda a detectar frecuencia de descarga |
| **Promedio por descarga** | kg | Total descargado / número de descargas. Control de consistencia |

### 9.2 Métricas de Avance

| Métrica | Unidad | Propósito |
|---|---|---|
| **Productividad** | kg/h | Peso total descargado / horas trabajadas. Por máquina y sección |
| **Merma** | kg | Peso de entrada − peso de salida. Pérdida de material en la sección |
| **Merma relativa** | % | (entrada − salida) / entrada × 100 |
| **Horas efectivas** | h | Horas registradas por máquina en el turno |

### 9.3 Métricas de Calidad

| Métrica | Propósito |
|---|---|
| **CV% promedio** | Consistencia del hilado en las pruebas de muestras |
| **Muestras fuera de tolerancia** | Porcentaje de muestras que no pasan los límites establecidos |
| **Body promedio** | Nivel de imperfecciones en Bobinados |
| **Cortes por bobina** | Frecuencia de cortes en Bobinados |

### 9.4 Métricas de Desperdicio

| Métrica | Unidad | Propósito |
|---|---|---|
| **Desperdicio real** | kg | Suma del desperdicio registrado por Inventario en el período |
| **Tasa de desperdicio** | % | Desperdicio real / total producido × 100. Por sección y grupo de máquinas |

### 9.5 Métricas Transversales

| Métrica | Propósito |
|---|---|
| **Producción vs planificación** | Compara lo producido con la base planificada (ver [sección 5 de operation.md](./overview.md#35-production-planning)). Alerta si hay desviación significativa, especialmente en títulos 2/18 y 2/32 |
| **Utilización de husos** | Husos operativos / husos totales de la máquina. Porcentaje de capacidad utilizada |
| **Consolidado por turno** | Producción, calidad y desperdicio agregado por Supervisor para su reporte diario |

> **Nota:** Las fórmulas detalladas, filtros temporales (cruce con turno anterior),
> y lógica de cálculo específica se documentarán en la especificación de métricas
> o en el diseño del dominio, no en este PRD.

---

## 10. Decisiones Diferidas

| Decisión                                               | Estado                                                                                                                                                                            |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Granularidad exacta de datos por máquina en Bobinados** | Pendiente. Confirmar si el registro body/km/cortes se captura por descarga, por máquina/turno o por otro corte operativo. |
| **Frecuencia exacta de muestreo aleatorio**            | Pendiente. Definir la frecuencia mínima de pruebas aleatorias en Retorcido y Madejeras (ej. N pruebas por semana, o por cada N kg producidos).                                    |

---

## 11. Glosario

| Término                   | Definición                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Finisor**         | Máquinas Finisores en Preparación. Las únicas que registran producción en esa sección.                                          |
| **Pasaje**                   | Máquinas de Preparación A/B. Solo registran avance (entrada/salida), no producción.                                             |
| **Título**                | Designación del grosor del hilado (ej. 2/18, 2/32, 4/9). Se produce durante Hilatura (`Yarn Spinning`).                                      |
| **Huso**                  | Unidad de producción en las máquinas de hilatura (Continuas, Bobinados, Retorcido).                                             |
| **Madeja**                | Unidad de producción en Madejeras. El hilado se presenta en madejas (ovillos sueltos), no en conos.                             |
| **Body**                  | Medida de calidad en Bobinados. Registro de imperfecciones por unidad de longitud.                                              |
| **CV%**                   | Coeficiente de variación — medida de consistencia del hilado en las pruebas de calidad.                                         |
| **Nomenclatura especial** | Sufijo o marca de calidad que luego podrá asociarse al PT en el proceso posterior. Es asignado por Calidad. |
| **Desperdicio real**      | Desperdicio registrado por Inventario durante el proceso, por grupo de máquinas.                                                |
| **Desperdicio teórico**   | Suma del desperdicio real + acumulado.                                                                              |
