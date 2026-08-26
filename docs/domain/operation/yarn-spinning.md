---
document_type: domain
status: active
scope: operation/yarn-spinning
authority: normative
owner: architecture
last_reviewed: 2026-07-27
---

# Domain Model: Yarn Spinning

> **Part of:** Operation Unit — Colibri Hub
> **Source:** `docs/prd/operation/yarn-spinning.md`
> **Related:** `docs/domain/operation/lot-processing.md` (downstream), `docs/domain/warehouse.md` (upstream)

---

## 1. Bounded Context

Yarn Spinning is a subdomain within **Operation**. Transforma fardos de MP en
hilado de un título específico a través de 5 secciones en flujo continuo.

La MP sale de Warehouse y la recibe Inventario en Hilandería. El producto
final (madejas) sale de Hilandería hacia Lot Processing.

```mermaid
flowchart LR
    W["MP desde Warehouse"] --> P["Preparación"]
    P --> C["Continuas"]
    C --> B["Bobinados"]
    B --> R["Retorcido"]
    R --> M["Madejeras"]
    M --> LP["LOT PROCESSING"]

    subgraph YS["YARN SPINNING"]
        direction LR
        P
        C
        B
        R
        M
    end
```

Los registros por sección son Producción (descarga), Avance (control de
proceso), Calidad de proceso y Desperdicio. Ver [Sección 2](#2-lo-que-se-registra)
y [Sección 3](#3-qué-se-registra-en-cada-sección).

---

## 2. Lo que se registra

### 2.1 Production Discharge (Descarga de Producción)

Es el registro de cada descarga que hace una máquina. Aplica a las secciones
que trabajan con **husos**: Preparación (solo FIN), Continuas, Bobinados y
Retorcido.

**Qué se registra por cada descarga:**

| Dato | Descripción |
|---|---|
| Máquina | Qué máquina produjo la descarga |
| Turno | A, B o C |
| Fecha | Fecha de producción |
| Título | Título del hilado (ej. 2/18, 2/32, 2/13, 2/24, 4/9, etc.) |
| Tipo | Variedad del título: HB, N, CH, etc. |
| Supervisor | Supervisor del turno |
| Encargado | Quién registra (Calidad o Inventario según la sección) |
| Peso Bruto | Peso del carro/tacho completo con el producto (kg) |
| No. Husos | Cantidad de husos operativos que produjeron esta descarga |
| Tara por Huso | Peso del cañete/bobina por huso (gramos) |
| Peso Carro | Peso del carro/tacho vacío (kg) |
| Peso Neto | Calculado: Bruto − (TaraHuso × Husos / 1000) − PesoCarro |
| Observaciones | Texto libre |

**Reglas:**
- Una máquina puede tener varias descargas en un turno (del mismo o distinto título)
- Puede no tener ninguna descarga en un turno
- El peso neto lo calcula el sistema, no se ingresa manualmente

### 2.2 Skeining Production (Producción de Madejeras)

Es el registro de producción de Madejeras. No usa husos, usa **madejas**.

**Qué se registra por cada descarga:**

| Dato | Descripción |
|---|---|
| Máquina | Máquina que produjo las madejas |
| Turno | A, B o C |
| Fecha | Fecha de producción |
| Título | Título del hilado |
| Tipo | Variedad del título (HB, N, etc.) |
| Supervisor | Supervisor del turno |
| Encargado | Quién registra (Inventario) |
| No. Madejas | Cantidad de madejas producidas |
| Peso Unitario | Peso estimado por madeja (gramos). Generalmente ~500g, pero varía según el título (ej. 600g) |
| Peso Neto | Calculado: No. Madejas × PesoUnitario / 1000 |
| Operario | Nombre del operador (texto libre, no es una referencia a empleado) |
| Observaciones | Texto libre |

**Reglas:**
- No usa husos, tara por huso, ni peso carro
- El operario es informativo — la producción es operario-dependiente, no ciclo-máquina

### 2.3 Advance Tracking (Registro de Avance)

Es un resumen por máquina al finalizar el turno. Consolida el trabajo del
turno: el material que entró (heredado del turno anterior), el material
existente en la máquina (calculado por muestreo de un huso), el material
que sale, y la descarga neta acumulada del turno.

**Aplica a:** Preparación (solo PSJ), Continuas, Retorcido.
**No aplica a:** Bobinados, Madejeras.

**Qué se registra por cada avance:**

| Dato | Descripción |
|---|---|
| Máquina | Máquina que se está controlando |
| Turno | A, B o C |
| Fecha | Fecha |
| Título | Título del hilado |
| Tipo | Variedad del título |
| Supervisor | Supervisor del turno |
| Encargado | Quién registra |
| Peso Muestra Bruto | Peso bruto de una canilla/huso de muestra al inicio del turno (gramos) |
| Peso Muestra Tara | Tara de esa canilla/huso de muestra (gramos) |
| No. Husos | Total de husos operativos de la máquina |
| Peso de Entrada | Material que entró a la sección (lo que dejó el turno anterior como salida, kg) |
| Peso de Salida | Material existente en la máquina calculado por balance de materia (kg) |
| Peso Descargado | Suma de pesos netos de todas las descargas de producción del turno (kg) |
| Horas Trabajadas | Horas que operó la máquina |

**Relación con Production Discharge:**
- `Peso Descargado` es la suma de los `Peso Neto` de todas las descargas de producción de esa máquina/turno
- Si no hay descargas en el turno, el `Peso Descargado` es cero
- El `Peso de Entrada` de un turno es el `Peso de Salida` registrado por el turno anterior para esa máquina

**Propósito:**
- Validar que la suma de descargas sea coherente con el control de proceso
- Calcular merma: Entrada vs Salida
- Medir productividad: kg/hora por máquina

### 2.4 Quality Control (Control de Calidad de Proceso)

Calidad evalúa todas las secciones. El método varía según la sección.

**Qué se registra en cada control:**

| Dato | Descripción |
|---|---|
| Sección | Sección evaluada |
| Máquina | Máquina evaluada |
| Turno | Turno |
| Fecha | Fecha |
| Título | Título evaluado |
| Tipo | HB, N, CH, etc. |
| Inspector | Empleado de Calidad |
| Método | Sample, MachineRegister o Random |

**Según el método, se registran datos distintos:**

*Método Sample (Preparación, Continuas)*
- Número de muestras tomadas (generalmente 12 por máquina/tipo)
- Valores individuales de cada muestra
- CV%, tenacidad, elongación (calculados)

*Método MachineRegister (Bobinados)*
- Body (imperfecciones por unidad de longitud)
- Kilómetros procesados
- Cortes por cono

*Método Random (Retorcido, Madejeras)*
- Resultados variables según la prueba

**Nota:** Las nomenclaturas especiales (-AT, -FT, -VARR, -D, etc.) se asignan
al lote en Lot Processing, no a la máquina en Yarn Spinning.

### 2.5 Waste Record (Registro de Desperdicio)

Inventario registra el desperdicio de todas las secciones. Se pesa por
**grupo de máquinas**, no por máquina individual.

**Qué se registra en cada control de desperdicio:**

| Dato | Descripción |
|---|---|
| Sección | Sección donde se generó |
| Grupo de Máquinas | Grupo de máquinas que se pesaron juntas |
| Turno | Turno |
| Fecha | Fecha |
| Peso | Peso del desperdicio (kg) |
| Tipo | Real (registrado por Inventario) o Acumulado (gestionado por Producción) |
| Quién registra | Empleado de Inventario |

**Reglas:**
- El desperdicio teórico es Real + Acumulado (no se almacena, se calcula)
- Madejeras: las madejas fuera de especificación NO se registran como desperdicio — vuelven a una etapa anterior para reproceso

---

## 3. Qué se registra en cada sección

| Sección | Production Discharge | Skeining Production | Advance Tracking | Quality Control | Waste Record |
|---|---|---|---|---|---|
| **Preparación** | FIN (Calidad) | — | PSJ (Calidad) | Calidad | Inventario |
| **Continuas** | Calidad | — | Calidad | Calidad | Inventario |
| **Bobinados** | TBD | — | — | Calidad | Inventario |
| **Retorcido** | Inventario | — | Inventario | Calidad | Inventario |
| **Madejeras** | — | Inventario | — | Calidad | Inventario |

---

## 4. Shared Catalogs

Son datos maestros compartidos con otros contextos de Operation:

| Catálogo | Descripción |
|---|---|
| **Employee** | Empleados de la planta. Cada uno tiene un rol (Supervisor, Calidad, Inventario) |
| **Shift** | Turnos fijos: A (mañana), B (tarde), C (noche) |
| **YarnCount** | Títulos de hilado (2/18, 2/32, 4/9, 2/13, 2/24, 2/40, 3/11, Fantasía, Otro, etc.) |
| **Section** | Las 5 secciones de hilandería: Preparación, Continuas, Bobinados, Retorcido, Madejeras |
| **Machine** | Máquinas de cada sección con su código (CONT-0A, FIN-A, RET-1B, etc.) y tipo (PSJ, FIN) |
| **MachineGroup** | Agrupación de máquinas para pesaje de desperdicio |

---

## 5. Business Rules

1. **Solo FIN producen en Preparación.** PSJ solo registra avance.
2. **Bobinados no tiene responsable fijo de registro.** El Supervisor asigna según el turno (TBD).
3. **Producción es granular por descarga.** Varias descargas por máquina/turno son válidas. Cero también.
4. **Título y tipo pueden cambiar dentro de un turno.** Cada descarga lleva el suyo.
5. **Peso neto siempre calculado por el sistema.** Nunca se ingresa directamente.
6. **Avance valida producción.** El peso descargado en avance debe coincidir con la suma de descargas.
7. **Madejeras es estructuralmente distinto.** No usa husos, tara, ni carro. Usa cantidad de madejas y peso unitario.
8. **Desperdicio por grupo de máquinas.** No por máquina individual.
9. **Madejeras fuera de especificación NO es desperdicio.** Vuelve a etapa anterior para reproceso.
10. **Records are editable under policy.** Corrections within the operational window preserve actor, timestamp, reason, and before/after values. The correction history is append-only.

---

## 6. Related Documents

- `docs/prd/operation/yarn-spinning.md` — Source PRD
- `docs/prd/operation/overview.md` — Operation unit PRD
- `docs/domain/operation/lot-processing.md` — Downstream domain (Lot Processing)
- `docs/domain/warehouse.md` — Upstream domain (Warehouse)
