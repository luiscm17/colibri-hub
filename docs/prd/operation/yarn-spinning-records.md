---
document_type: prd
status: active
implementation: not-started
scope: operation/yarn-spinning
authority: normative
owner: product
last_reviewed: 2026-07-27
---

# Registros Funcionales — Hilatura (`Yarn Spinning`)

> **Encadenado desde:** `docs/prd/operation/yarn-spinning.md`
> **Relacionados:** `docs/prd/operation.md`, `docs/prd/access-control.md`

---

## 1. Propósito

Este documento describe los **registros funcionales** que existen dentro del
proceso de **Hilatura (`Yarn Spinning`)**.

Su objetivo es servir como puente entre:

- el PRD del negocio
- el futuro diseño del dominio
- el posterior modelado de datos
- el diseño de formularios, validaciones y pantallas

Este documento **no define tablas, columnas técnicas ni esquema de base de
datos**. Define qué información necesita registrar el negocio y con qué
granularidad debe hacerlo.

---

## 2. Regla transversal de uso

Los registros descritos aquí reflejan la operación actual esperada de Hilatura.

- El **registrador actual** indica qué rol hoy carga ese tipo de información.
- Esa asignación **no es rígida**: puede cambiar según la política de acceso
  definida en `docs/prd/access-control.md`.
- Cada registro debe distinguir entre:
  - **fecha de negocio** ingresada por el usuario responsable
  - **turno** ingresado por el usuario responsable
  - **timestamp de registro** capturado automáticamente por el sistema

Por lo tanto, este documento describe:

1. **qué se registra**
2. **con qué propósito se registra**
3. **quién lo registra hoy**

pero no congela de forma permanente la asignación de permisos.

---

## 3. Familias de registros en Hilatura

Dentro de Hilatura existen cuatro familias principales de registros:

1. **Registro de producción por descarga**
2. **Registro de avance**
3. **Registro de calidad de proceso**
4. **Registro de desperdicio**

No todas las secciones usan todas las familias.

> **Importante:** En Hilatura no existe todavía el lote como entidad conceptual
> del proceso. La continuidad operativa se construye por sección, máquina,
> turno, fecha de negocio y título; no mediante un timeline de lote.

---

## 4. Registros por sección

## 4.1 Preparación

### A. Registro de producción por descarga

- **Qué representa:** una descarga de producción realizada por una máquina FIN.
- **Granularidad:** 1 descarga × 1 máquina × 1 turno × 1 fecha × 1 título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - supervisor de turno
  - título producido
  - peso bruto total
  - tara por huso
  - número de husos operativos
  - peso del carro o contenedor
- **Datos opcionales/contextuales:**
  - observaciones operativas
  - motivo de corrección si hubo edición posterior
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:**
  - peso en kg
  - producción complementada con número de mechas según corresponda
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### B. Registro de avance

- **Qué representa:** resumen de entrada, producción y salida por máquina.
- **Granularidad:** 1 máquina × 1 turno × 1 fecha × 1 título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - título
  - peso de entrada
  - peso total descargado
  - peso de salida
- **Datos opcionales/contextuales:**
  - observaciones
  - notas de consistencia
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg; peso calculado por muestreo de huso cuando aplica
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### C. Registro de calidad de proceso

- **Qué representa:** control de consistencia del proceso en la sección.
- **Granularidad:** 1 control × 1 máquina × 1 turno × 1 fecha × 1 tipo de muestra.
- **Datos obligatorios:**
  - sección
  - máquina
  - turno
  - fecha de negocio
  - tipo de muestra
  - resultados de prueba
- **Datos opcionales/contextuales:**
  - observaciones
  - fuera de tolerancia
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** según el tipo de prueba
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### D. Registro de desperdicio

- **Qué representa:** desperdicio real asociado al grupo de máquinas.
- **Granularidad:** 1 registro × 1 grupo de máquinas × 1 turno × 1 fecha.
- **Datos obligatorios:**
  - sección
  - grupo de máquinas
  - turno
  - fecha de negocio
  - peso del desperdicio
  - tipo de desperdicio
- **Datos opcionales/contextuales:**
  - observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg
- **Registrador actual:** Inventario
- **Nota de permisos:** configurable por política de acceso

---

## 4.2 Continuas

### A. Registro de producción por descarga

- **Qué representa:** una descarga de hilado producida por máquina.
- **Granularidad:** 1 descarga × 1 máquina × 1 turno × 1 fecha × 1 título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - supervisor de turno
  - título
  - peso bruto total
  - tara por huso
  - número de husos operativos
  - peso del carro o contenedor
- **Datos opcionales/contextuales:** observaciones operativas
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg + número de husos
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### B. Registro de avance

- **Qué representa:** consolidado operativo de la máquina durante el turno.
- **Granularidad:** 1 máquina × 1 turno × 1 fecha × 1 título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - título
  - peso de entrada
  - peso neto en máquina
  - peso total descargado
  - número de husos
  - horas trabajadas
  - peso de salida
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg, husos, horas
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### C. Registro de calidad de proceso

- **Qué representa:** control por muestras de la calidad del hilado.
- **Granularidad:** 1 control × 1 máquina × 1 turno × 1 fecha × 1 tipo de hilado.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - tipo de muestra
  - resultados individuales
  - medidas consolidadas (por ejemplo consistencia, tenacidad, elongación)
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** según el ensayo aplicado
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### D. Registro de desperdicio

- mismo patrón funcional que en Preparación
- **Registrador actual:** Inventario

---

## 4.3 Bobinados

### A. Registro de producción por descarga

- **Qué representa:** descarga de producción de la sección Bobinados.
- **Granularidad:** pendiente de cerrar con exactitud operativa; al menos debe
  quedar asociada a máquina, turno, fecha y título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - supervisor de turno
  - título
  - peso neto
  - número de husos
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg + husos
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### B. Registro de avance

- **No aplica** en la definición actual.

### C. Registro de calidad de proceso

- **Qué representa:** registro de datos de máquina para control del proceso.
- **Granularidad:** pendiente de precisión final (por descarga, por máquina/turno
  u otro corte operativo).
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - body
  - kilómetros
  - cortes por bobina
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** según el indicador registrado por la máquina
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### D. Registro de desperdicio

- mismo patrón funcional que en otras secciones
- **Registrador actual:** Inventario

---

## 4.4 Retorcido

### A. Registro de producción por descarga

- **Qué representa:** descarga de producción de retorcedoras.
- **Granularidad:** 1 descarga × 1 máquina × 1 turno × 1 fecha × 1 título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - supervisor de turno
  - título
  - peso bruto total
  - tara por huso
  - número de husos operativos
  - peso del carro o contenedor
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg + husos
- **Registrador actual:** Inventario
- **Nota de permisos:** configurable por política de acceso

### B. Registro de avance

- **Qué representa:** resumen de entrada, producción y salida por máquina.
- **Granularidad:** 1 máquina × 1 turno × 1 fecha × 1 título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - título
  - peso de entrada
  - peso neto en máquina
  - peso total descargado
  - número de husos
  - horas trabajadas
  - peso de salida
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg, husos, horas
- **Registrador actual:** Inventario
- **Nota de permisos:** configurable por política de acceso

### C. Registro de calidad de proceso

- **Qué representa:** control aleatorio de calidad del proceso.
- **Granularidad:** 1 control × 1 máquina × 1 turno × 1 fecha.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - resultados de prueba
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** según el ensayo aplicado
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### D. Registro de desperdicio

- mismo patrón funcional que en otras secciones
- **Registrador actual:** Inventario

---

## 4.5 Madejeras

### A. Registro de producción por descarga

- **Qué representa:** producción de madejas por descarga o corte operativo.
- **Granularidad:** 1 descarga × 1 máquina × 1 turno × 1 fecha × 1 título.
- **Datos obligatorios:**
  - máquina
  - turno
  - fecha de negocio
  - supervisor de turno
  - título
  - número de madejas producidas
  - peso unitario estimado
- **Datos opcionales/contextuales:**
  - observaciones
  - aclaración de variación de peso por requerimiento del título
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** número de madejas + peso estimado por madeja o conjunto definido
- **Registrador actual:** Inventario
- **Nota de permisos:** configurable por política de acceso

### B. Registro de avance

- **No aplica** en la definición actual.

### C. Registro de calidad de proceso

- **Qué representa:** control aleatorio del resultado de la sección.
- **Granularidad:** 1 control × 1 turno × 1 fecha.
- **Datos obligatorios:**
  - turno
  - fecha de negocio
  - resultados de prueba
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** según el ensayo aplicado
- **Registrador actual:** Control de Calidad
- **Nota de permisos:** configurable por política de acceso

### D. Registro de desperdicio

- **Qué representa:** desperdicio real de la sección.
- **Granularidad:** 1 registro × 1 turno × 1 fecha.
- **Datos obligatorios:**
  - turno
  - fecha de negocio
  - peso del desperdicio
  - tipo
- **Datos opcionales/contextuales:** observaciones
- **Datos técnicos automáticos:**
  - timestamp de registro en el sistema
- **Unidades / medición:** kg
- **Registrador actual:** Inventario
- **Nota de permisos:** configurable por política de acceso

### E. Regla de frontera

- Madejeras **no arma lotes** dentro de Hilatura.
- Madejeras produce madejas con determinado peso.
- El armado físico del lote ocurre en el proceso posterior.

---

## 5. Reglas transversales de los registros

1. **Sin lote en Hilatura:** los registros de este documento no usan al lote como
   entidad física del proceso.
2. **Tiempo de negocio vs tiempo de sistema:** cada registro debe guardar la
   fecha de negocio y el turno ingresados por el usuario, además del timestamp
   automático del sistema.
3. **Corrección con auditoría:** si existe error de carga, el registro puede
   corregirse con auditoría completa.
4. **Ventana operativa:** la corrección por roles operativos solo aplica dentro
   de la ventana definida por la política vigente.
5. **Restricción posterior:** fuera de la ventana operativa, solo SysAdmin puede
   editar.
6. **Permisos configurables:** el registrador actual no equivale a permiso fijo.

---

## 6. Cómo usar este documento más adelante

Este documento debe alimentar, en ese orden:

1. **modelo de dominio**
   - qué conceptos merecen entidad, value object o evento
2. **modelado de datos**
   - qué información persistir
   - qué agrupaciones lógicas existen
   - qué relaciones conceptuales deben preservarse
3. **formularios y UI**
   - qué pantallas necesita cada sección
   - qué datos son obligatorios
   - qué validaciones deben existir
4. **reglas de validación**
   - secuencia
   - unidades
   - consistencia entre producción, avance, calidad y desperdicio

No debe usarse directamente como diseño de tablas. Su función es cerrar el
significado funcional de los datos antes del diseño técnico.

---

## 7. Ambigüedades todavía abiertas

1. La granularidad exacta del registro de Bobinados para body/km/cortes todavía
   debe cerrarse.
2. Debe definirse con más precisión cómo se representa el peso unitario en
   Madejeras cuando cambia por requerimiento del título.
