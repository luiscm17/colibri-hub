---
document_type: prd
status: active
implementation: partial
scope: global/ui
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Colibri Hub — UI Requirements

> Requisitos de interfaz de usuario para el sistema de gestión de producción textil.
> Este documento define qué pantallas, navegación y patrones de UI necesita el
> sistema, sin prescribir tecnologías ni contratos de API.

---

## 1. Principios de UI

1. **Cada contexto de negocio es una sección de navegación independiente.**
   Almacén, Hilatura y Proceso por Lotes aparecen como áreas separadas porque
   sus conceptos, timelines y usuarios son distintos.

2. **La fecha de negocio y el turno son estado de sesión.** La mayor parte de la
   captura ocurre al cierre del turno, no en tiempo real. El turno y la fecha
   de negocio se proveen mediante contexto compartido, y cada pantalla los
   incorpora según los necesite (dashboard, formularios, reportes). No forman
   parte del chrome global (top bar).

3. **La captura tipo planilla es el modo principal para datos repetitivos.**
   Hilatura (descargas por máquina) y ciertos registros de calidad requieren
   ingreso de múltiples filas en una sesión. La UI debe priorizar navegación
   por teclado, entrada rápida y feedback inline.

4. **Los formularios guiados corresponden a objetos de negocio ricos.**
   Recepciones, identidad de producción, movimientos de Almacén y registros
   de etapa de lote tienen estructura compleja y campos condicionales.

5. **La edición controlada es visible, no silenciosa.** El usuario debe saber
   si un registro es editable, si requiere motivo de corrección y cuándo la
   ventana operativa está cerrada.

6. **La autorización se expresa como capacidades, no como roles fijos.** La UI
   puede ocultar o deshabilitar acciones según permisos, pero nunca asumir
   que un rol específico (Supervisor, Calidad) es el único que puede hacer X.

7. **Los estados del producto se muestran como dimensiones separadas.**
   Calidad, disponibilidad en Almacén y presentación física son conceptos
   distintos y deben aparecer como campos o badges separados, no como un
   único estado compuesto.

---

## 2. Layout global

El layout se organiza en tres zonas permanentes:

```
┌─────────────────────────────────────────────────┐
│  Top bar                                         │
│ [☰] [Logo]                  [🌙] [Usuario ▼] │
├──────────┬──────────────────────────────────────┤
│ Sidebar  │  Main content area                    │
│          │                                       │
│ Almacén  │  (ruta activa)                        │
│ Hilatura │                                       │
│ Lotes    │                                       │
│ Reportes │                                       │
│ Admin    │                                       │
│          │                                       │
└──────────┴──────────────────────────────────────┘
```

### 2.1 Top bar

| Elemento | Comportamiento |
|---|---|
| Logo / nombre del sistema | Enlace a dashboard o ruta por defecto |
| Toggle sidebar | Botón para colapsar/expandir la navegación |
| Toggle de tema | Modo claro / oscuro |
| Usuario actual | Nombre + avatar. Menú de perfil/cierre de sesión |

### 2.2 Sidebar

Navegación principal organizada por bounded context. Cada contexto puede
expandir sub-ítems. La sección activa se resalta visualmente.

- **Almacén**
  - Recepción de fardos
  - Identidad de producción
  - Emisión a Operación
  - Recepción de PT
  - Clasificación / disponibilidad
  - Salidas y devoluciones
  - Insumos
  - Stock e historial

- **Hilatura**
  - Dashboard por sección
  - Descargas (producción)
  - Avance
  - Calidad de proceso
  - Desperdicio
  - Disponibilidad de madejas
  - Consolidado por turno

- **Proceso por Lotes**
  - Cola de lotes
  - Detalle del lote

- **Reportes**
  - Consolidado diario
  - Producción vs plan
  - Trazabilidad de lote

- **Admin**
  - Datos maestros

### 2.3 Main content

Área variable donde se renderiza la pantalla activa. Soporta:
- Vista de lista/tabla con filtros
- Formulario de captura
- Detalle de registro
- Dashboard con métricas

---

## 3. Pantallas por contexto

### 3.1 Almacén

#### Recepción de fardos

Registro de ingreso de materia prima desde proveedor.

- Formulario con: proveedor, factura, peso bruto, título, color/fibra,
  número de camión, fecha de recepción
- Tabla de fardos ingresados con historial filtrable
- Cada fardo es una fila. Se pueden registrar múltiples fardos por camión

#### Identidad de producción

Definición de la identidad única del lote antes de que exista físicamente.

- Formulario con: `lot_code`, `production_identity_id`, título, color,
  cliente/destino, especificaciones del pedido
- Lista de identidades definidas con su estado (pendiente de emisión, etc.)

#### Emisión a Operación

Registro de salida de MP desde Almacén hacia Producción.

- Selector de fardo a emitir (solo fardos completos, no emitidos antes)
- Fecha, responsable que entrega, responsable que recibe
- Confirmación: una vez emitido, no se revierte sin corrección controlada

#### Recepción de PT

Recepción de producto terminado desde Operación.

- Lista de lotes en espera de validación (enviados por Calidad)
- Detalle del lote con datos de operación (solo lectura)
- Verificación física: documentar inconsistencias si las hay
- Confirmación de recepción

#### Clasificación / disponibilidad

Gestión de estado operativo del PT en Almacén.

- Selector de lote
- Campos separados para:
  - Estado de calidad (heredado de Operación, solo lectura)
  - Disponibilidad en Almacén (disponible, observado, disponible con
    condición, defectuoso, entregado)
  - Presentación física (bolsa, suelto, cono, ovillo)
- Historial de cambios de estado

#### Salidas y devoluciones

Registro de venta directa, transferencia a Comercialización y devoluciones.

- Selector de tipo de movimiento
- Formulario según tipo: cliente, cantidad (kg), factura, fecha
- Devolución referencia a la venta original
- Autorización visible (requiere Jefe de Producción)

#### Insumos

Gestión de insumos de producción (colorantes, químicos, empaque, etc.).

- Categorías configurables
- Recepción, consumo y devolución por categoría
- Tabla de existencias por categoría

#### Stock e historial

Consulta de saldos y movimientos.

- Filtros por subdominio (MP, PT, insumos), fecha, lote
- Saldo calculado: anterior + entradas − salidas
- Historial de movimientos por lote o ítem

---

### 3.2 Hilatura

#### Dashboard por sección

Vista resumen de producción por sección, turno y fecha.

- Tarjetas o tabla por sección (Preparación, Continuas, Bobinados,
  Retorcido, Madejeras)
- Métricas por sección: total descargado, productividad (kg/h), merma
- Selector de turno y fecha (usa el contexto de sesión)

#### Descargas (producción)

Captura tipo planilla de descargas por máquina.

- Tabla editable donde cada fila es una descarga:
  Máquina, título, peso bruto, No. husos, tara por huso, peso carro,
  peso neto (calculado automáticamente)
- Madejeras tiene filas distintas: madejas, peso unitario
- Soporta agregar múltiples filas en una sesión
- Validación inline: neto > 0, husos > 0
- Totales calculados al pie

#### Avance

Resumen por máquina al finalizar el turno.

- Formulario por máquina: entrada, salida, peso descargado (suma de
  descargas del turno), horas trabajadas
- Peso de muestra bruto y tara para cálculo de salida
- Solo aplica a Preparación, Continuas y Retorcido (Bobinados y Madejeras
  no tienen avance)

#### Calidad de proceso

Registro de controles de calidad por sección y máquina.

- Selector de sección y máquina
- Campos dinámicos según el método:
  - **Muestras** (Preparación, Continuas): valores individuales, CV%
  - **Registro de máquina** (Bobinados): body, km, cortes
  - **Aleatorio** (Retorcido, Madejeras): resultado de prueba
- Historial de controles por máquina

#### Desperdicio

Registro de desperdicio por grupo de máquinas.

- Selector de sección, grupo de máquinas
- Peso, tipo (real / acumulado)
- Madejeras fuera de especificación: no se registra como desperdicio,
  se marca para reproceso

#### Disponibilidad de madejas

Vista de madejas producidas disponibles para armado de lotes.

- Tabla por título: cantidad de madejas, peso total
- Filtro por fecha de producción

#### Consolidado por turno

Resumen de producción del turno para el Supervisor.

- Producción total por sección
- Calidad: controles realizados, resultados
- Desperdicio total
- Vista imprimible o exportable

---

### 3.3 Proceso por Lotes

#### Cola de lotes

Lista de lotes activos organizados por etapa actual.

- Tabla con: código de lote, título, etapa actual, responsable,
  última actualización
- Filtros por etapa, título, fecha
- Click en un lote abre su detalle

#### Detalle del lote

Vista unificada del historial completo del lote.

- Timeline vertical con las 6 etapas
- Cada etapa muestra: responsable, fecha/turno, datos técnicos,
  observaciones
- La etapa activa (actual) está resaltada y permite edición/ingreso
- Etapas completadas son solo lectura
- Botón para registrar avance a la siguiente etapa

#### Registro por etapa

Cada etapa tiene su propio formulario especializado. Todos comparten:

- Fecha de negocio y turno
- Responsable y supervisor
- Datos técnicos específicos de la etapa
- Selector de categoría de inconveniente (opcional)
- Campo de detalle para observaciones (texto libre opcional)

**Inventario** — armado del lote:
- Título (heredado), cantidad de madejas, peso total

**Tintorería** — aplicación de color:
- Madejas recibidas, peso neto, número de tina, temperatura

**Secado** — eliminación de humedad:
- Madejas ingresadas, peso total

**Devanado / Ovillado** — conversión a formato final:
- Formato (cono / ovillo), madejas procesadas, unidades producidas,
  desperdicio en kg

**Embolsado** — empaque:
- Bolsas utilizadas, unidades por bolsa, desperdicio en kg

**Calidad** — inspección final:
- Defectos visuales e internos (checkboxes categorizados)
- Nomenclatura especial (si aplica)
- Clasificación final: estándar, con nomenclatura, observado
- Confirmación de envío a Almacén

---

### 3.4 Reportes

#### Consolidado diario

Vista del Jefe de Producción con producción del día.

- Producción por sección vs. plan
- Estado de lotes activos
- Desperdicio acumulado
- Alertas de desviación significativa

#### Producción vs plan

Comparativa por título y período.

- Gráfico de barras o tabla: planificado vs real
- Filtro por título, rango de fechas
- Métrica principal: kg producidos vs kg planificados

#### Trazabilidad de lote

Recorrido completo del lote cross-context.

- Timeline desde definición en Almacén hasta estado actual
- Datos de Almacén y Operación combinados en vista de solo lectura

---

## 4. Patrones de UI

### 4.1 Captura tipo planilla (spreadsheet)

Para Hilatura — descargas, avance, desperdicio.

- Tabla con filas agregables dinámicamente
- Navegación por teclado (Tab, Enter, flechas)
- Celdas con validación inline al perder el foco
- Totales calculados automáticamente al pie
- Botón "Agregar fila" y "Eliminar fila"
- Paste desde portapapeles externo

### 4.2 Timeline de lote

Para Proceso por Lotes — historial visual.

- Línea vertical con nodos para cada etapa
- Nodos: completado (check), activo (resaltado), pendiente (atenuado)
- Click en nodo completado expande detalle
- Nodo activo muestra formulario de registro

### 4.3 Formulario guiado

Para Almacén y registros de etapa.

- Paso único o multi-sección en una página
- Campos obligatorios marcados
- Validación al enviar, no en cada campo
- Resumen antes de confirmar cuando el registro es crítico

### 4.4 Edición controlada

Para corrección de registros existentes.

- Indicador visual de editable / no editable
- Modal de corrección con:
  - Valores anteriores visibles
  - Campos editables
  - Campo obligatorio de motivo de corrección
  - Confirmación con advertencia de auditoría

### 4.5 Selector de turno y fecha

Componente de contexto de sesión. Cada pantalla lo ubica donde corresponda
(junto a formularios, en dashboard o en encabezados de sección). No forma
parte del chrome global.

- Turno: dropdown con A/B/C y opción de "todos"
- Fecha negocio: date picker con atajo para "hoy"
- Cambios actualizan todas las pantallas que usan estos valores mediante
  un contexto de sesión compartido

---

## 5. Estados globales de UI

| Estado | Ámbito | Propósito |
|---|---|---|
| `activeShift` | Sesión | Turno activo para captura y consultas |
| `businessDate` | Sesión | Fecha de negocio activa |
| `currentUser` | Sesión | Usuario autenticado con capacidades |
| `sidebarCollapsed` | UI local | Estado de la barra lateral |
| `filters` | Por pantalla | Filtros activos (sección, título, fecha, etc.) |
