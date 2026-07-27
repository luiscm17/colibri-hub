---
document_type: technical-spec
status: active
implementation: partial
scope: warehouse/bales
authority: explanatory
owner: frontend
last_reviewed: 2026-07-27
---

> **Normative PRD:** [Bale Management](../../../docs/prd/warehouse/bale-management.md)
>
> This document is a **frontend technical specification**. Business rules, state definitions,
> identity constraints, and acceptance criteria are defined in the normative PRD linked above.
> Any business rule referenced here is explanatory context only — the PRD is authoritative.

# Frontend Technical Spec — Gestión de fardos

Frontend de recepción, inventario, consulta y entrega a Producción

**Producto:** Colibri Hub · Contexto Warehouse

**Tipo:** Frontend Technical Specification (formerly Product Requirements Document — Frontend)

**Estado:** Propuesto para implementación

**Base técnica:** Repositorio luiscm17/colibri-hub · rama main · commit
447ee79

**Fecha:** 26 de julio de 2026

  -----------------------------------------------------------------------
  **Decisión de producto:** El módulo se organizará en dos páginas:
  Recepción de fardos para la carga masiva de una partida y Inventario de
  fardos para métricas agregadas, consulta individual y cambio
  irreversible a delivered. No se mostrará un listado exhaustivo de
  fardos.
  -----------------------------------------------------------------------

> ⚠️ **Business rule sourced from PRD.** The two-page structure, irreversibility of delivery,
> and prohibition of exhaustive bale listing are business decisions defined in
> [bale-management.md](../../../docs/prd/warehouse/bale-management.md). This spec
> implements those decisions in the frontend — it does not redefine them.

  -----------------------------------------------------------------------

# 1. Resumen ejecutivo

El frontend existente contiene una primera pantalla funcional de
recepción con Mantine y react-data-grid, pero su modelo aún corresponde
a un contrato anterior: registra patente, transportista, material y
lote; envía pesos como números; usa una ruta API provisional; y no
implementa confirmaciones, validación por celda ni consultas. El
objetivo de este PRD es transformar esa base en una experiencia
operativa coherente con el modelo de RawMaterialBatch y Bale.

La solución objetivo permitirá registrar de forma atómica una partida de
hasta aproximadamente 100 fardos, consultar indicadores agregados con
filtros, localizar un fardo mediante shipment_number y bale_number, y
actualizar su estado de in_warehouse a delivered. La carga masiva
conservará la interacción tipo Excel; las consultas históricas serán
resueltas por el backend y presentadas como resúmenes, no mediante la
descarga de todas las entidades.

# 2. Estado actual del frontend

## 2.1 Base tecnológica confirmada

  -------------------------------------------------------------------------
  **Área**        **Tecnología          **Implicación para este PRD**
                  existente**           
  --------------- --------------------- -----------------------------------
  Aplicación      React 19, TypeScript  Mantener el feature modular y el
                  6 y Vite 8            alias @/; no introducir otro
                                        framework.

  UI              Mantine 9: Core,      Usar formularios, modales, estados,
                  Form, Hooks y         badges y notificaciones existentes.
                  Notifications         

  Grilla          react-data-grid       Conservarla como superficie de
                  7.0.0-beta.61         captura masiva; no reemplazarla.

  Navegación      React Router 7 con    Agregar rutas lazy y navegación
                  carga diferida        bajo Almacén.

  Iconografía     Tabler Icons React    Reutilizar el sistema de iconos
                                        vigente.

  Autenticación   ProtectedRoute,       Integrar páginas y acciones sin
                  AuthProvider y filtro codificar roles fijos.
                  por resourceType      

  Calidad         TypeScript build y    Son puertas obligatorias; hoy no
                  ESLint                existe un framework de pruebas
                                        frontend.

  Diseño          Tema Mantine, modo    Aplicar la identidad visual
                  claro/oscuro y paleta existente también a la grilla y
                  cian                  estados.
  -------------------------------------------------------------------------

## 2.2 Hallazgos funcionales

- ReceptionPage ya separa formulario y grilla, pero usa un modelo de
  camión y lote incompatible con la partida de materia prima actual.

- BaleDataGrid es reutilizable como contenedor, aunque sus columnas,
  tipos, cálculos y tratamiento de errores deben rediseñarse.

- La grilla agrega filas vacías automáticamente, pero considera vacía
  una fila con criterios incompletos y actualmente envía todas las
  filas.

- El cliente HTTP usa /api/warehouse/receptions, no normaliza el
  contrato de errores y no existe configuración de proxy local.

- La respuesta exitosa se descarta; no hay modal de confirmación ni
  modal de resultado.

- Las rutas placeholder de Almacén reutilizan WarehousePage y muestran
  contenido de demostración que no representa funcionalidades reales.

- No existen dashboard, filtros, consulta individual, detalle de fardo
  ni actualización de estado.

- La documentación frontend de recepción conserva campos y supuestos que
  ya no corresponden al modelo aprobado.

# 3. Objetivos y métricas de éxito

## 3.1 Objetivos

- Reducir la recepción de una partida completa a una única operación
  guiada y verificable.

- Permitir la captura eficiente de hasta 100 fardos con teclado y pegado
  desde una planilla.

- Detectar errores de celda antes del envío y representar errores
  globales mediante un único popup.

- Ofrecer visibilidad de existencias mediante métricas agregadas
  calculadas en backend.

- Permitir una consulta inequívoca usando shipment_number y bale_number.

- Ejecutar la única transición permitida, in_warehouse → delivered, con
  confirmación explícita.

## 3.2 Indicadores de aceptación del producto

  -----------------------------------------------------------------------
  **Indicador**         **Meta de aceptación**
  --------------------- -------------------------------------------------
  Capacidad de captura  Una partida de 100 fardos puede editarse,
                        validarse y enviarse como una sola operación.

  Precisión             Dtex y pesos conservan la representación decimal
                        acordada; el payload los envía como strings.

  Prevención de errores No se envían filas vacías; las filas parciales y
                        duplicadas se identifican por celda.

  Recuperación          Ningún error de red, 409, 422 o 500 elimina la
                        información ingresada.

  Consulta              Los filtros actualizan métricas agregadas sin
                        descargar una colección completa de fardos.

  Estado                La entrega exitosa actualiza detalle y resumen;
                        no se ofrece reversión ni edición libre.

  Calidad técnica       Build, lint, pruebas acordadas y validación
                        manual de integración aprobados.
  -----------------------------------------------------------------------

# 4. Alcance

> ⚠️ **Business scope derived from PRD.** The capability boundaries below reflect decisions
> in the [normative PRD](../../../docs/prd/warehouse/bale-management.md). Additions or
> removals to scope must be resolved there first.

  -----------------------------------------------------------------------
  **Incluido**                        **Fuera de alcance**
  ----------------------------------- -----------------------------------
  Rediseño de la pantalla de          Implementación o rediseño interno
  recepción y su contrato de datos.   del backend.

  Grilla tipo Excel, fórmulas         Agregar fardos a una partida ya
  visuales, resumen y validación por  registrada.
  celda.                              

  Dashboard agregado con filtros.     Listado exhaustivo o paginado de
                                      todos los fardos.

  Consulta individual por partida +   Historial de movimientos o
  número de fardo.                    auditoría de correcciones.

  Actualización de estado a           Devoluciones, entrega parcial o
  delivered.                          tercer estado.

  Popups de confirmación, éxito y     Catálogos de proveedor o material
  fallo global.                       no expuestos por contrato.

  Normalización del cliente HTTP y de RBAC backend, login real o
  errores.                            administración de permisos.

  Rutas, navegación, estados          Cambios a Producto Terminado,
  responsive y pruebas frontend.      Hilatura o Proceso por Lotes.
  -----------------------------------------------------------------------

# 5. Arquitectura de información y navegación

El módulo de fardos se presentará bajo Almacén con dos entradas
funcionales. Las rutas placeholder no deben seguir apuntando a una
página genérica que muestra el título «Recepción de fardos».

  ---------------------------------------------------------------------------
  **Página**         **Ruta objetivo**      **Responsabilidad**
  ------------------ ---------------------- ---------------------------------
  Recepción de       /warehouse/reception   Registrar una partida completa
  fardos                                    con su cabecera y grilla de
                                            fardos.

  Inventario de      /warehouse/bales       Mostrar resumen agregado, buscar
  fardos                                    un fardo y entregarlo a
                                            Producción.
  ---------------------------------------------------------------------------

La entrada «Inventario de fardos» deberá ser nueva y específica. No se
recomienda reutilizar «Stock e historial» porque esa denominación puede
abarcar en el futuro Producto Terminado e Insumos. Tampoco se recomienda
mantener una página separada de «Emisión a Operación» para una única
acción sobre el detalle; la entrega se realizará desde el fardo
consultado.

# 6. Experiencia de recepción

## 6.1 Cabecera de partida

La cabecera contendrá únicamente datos compartidos por todos los fardos.
Deben eliminarse patente, transportista, código de material global,
lot_code, factura y observaciones mientras no exista un contrato
aprobado que los soporte.

  -----------------------------------------------------------------------
  **Campo**        **Control y comportamiento**      **Validación**
  ---------------- --------------------------------- --------------------
  Número de        Entrada de texto; normalización   Obligatorio; el
  partida          visual consistente.               backend garantiza
                                                     unicidad global.

  Fecha de         Selector de fecha sin hora; fecha Obligatoria; formato
  recepción        actual por defecto y modificable. de fecha ISO al
                                                     enviar.

  Proveedor        Entrada de texto en el alcance    Obligatorio; no
                   actual.                           anticipar catálogo
                                                     inexistente.
  -----------------------------------------------------------------------

## 6.2 Grilla de fardos

react-data-grid seguirá siendo la superficie principal. La interacción
debe sentirse como una planilla: navegación por teclado, pegado de
múltiples celdas, encabezado fijo, filas consecutivas y feedback
inmediato sin abrir un formulario por fardo.

  -----------------------------------------------------------------------
  **Columna**     **Edición**      **Regla principal**
  --------------- ---------------- --------------------------------------
  \#              Solo visual      Número de fila; no se envía.

  Número de fardo Texto            Obligatorio y único dentro de la
                                   partida.

  Tipo de         Texto            Obligatorio; no introducir catálogo
  material                         todavía.

  Dtex            Decimal como     Obligatorio, finito y mayor que cero.
                  texto            

  Peso bruto (kg) Decimal como     Obligatorio y mayor que cero.
                  texto            

  Tara (kg)       Decimal como     Obligatoria, no negativa y menor al
                  texto            peso bruto.

  Peso neto (kg)  Calculado, solo  Peso bruto menos tara; no se envía.
                  lectura          

  Estado de fila  Indicador visual Resume errores sin convertirse en dato
                                   del payload.
  -----------------------------------------------------------------------

- Cada fila mantendrá un identificador temporal estable para relacionar
  errores del backend con la celda original.

- Los valores decimales permanecerán como texto durante la edición; no
  deben convertirse prematuramente a number.

- La grilla iniciará con un conjunto pequeño de filas y conservará filas
  vacías de continuación sin imponer 100 filas visibles desde el inicio.

- Una fila totalmente vacía se ignorará. Una fila parcialmente
  completada se considerará inválida y permanecerá visible.

- La selección, eliminación y pegado no deben alterar el orden relativo
  de las filas válidas.

- Durante el envío se bloqueará la edición para impedir que la vista
  diverja del snapshot enviado.

- La columna de número de fardo y, cuando sea viable, la numeración de
  fila permanecerán visibles durante el desplazamiento horizontal.

## 6.3 Fórmulas y resumen visual

Los cálculos de esta pantalla son ayudas previas al registro. Se
recalcularán al editar, pegar, agregar o eliminar filas; no reemplazan
la validación ni las reglas del backend.

  ------------------------------------------------------------------------
  **Indicador**      **Fuente**               **Tratamiento**
  ------------------ ------------------------ ----------------------------
  Fardos válidos     Filas completas sin      Conteo local.
                     errores locales          

  Peso bruto total   Pesos brutos válidos     Suma decimal local.

  Tara total         Taras válidas            Suma decimal local.

  Peso neto total    Peso bruto menos tara    Suma decimal local; no se
                     por fila                 envía.

  Filas con error    Estado de validación de  Conteo y acceso a la primera
                     la grilla                celda inválida.
  ------------------------------------------------------------------------

El resumen debe permanecer visible al trabajar con muchas filas,
preferentemente mediante una summary row de react-data-grid o un footer
inmediatamente asociado a la grilla.

## 6.4 Guardado y popups

1.  El usuario solicita guardar. La página valida cabecera y grilla, y
    enfoca la primera celda inválida si corresponde.

2.  Si todo es válido, un popup de confirmación resume partida, fecha,
    proveedor, cantidad de fardos y peso neto total.

3.  Al confirmar, se crea un snapshot, se bloquean cambios y se muestra
    «Registrando N fardos...».

4.  Ante 201, un popup de resultado muestra partida, fecha, proveedor y
    bale_count. El UUID técnico no se presenta.

5.  La cabecera y la grilla se limpian únicamente cuando el usuario
    cierra o confirma el popup de éxito.

6.  Ante error, la operación termina sin limpiar datos y la interfaz
    habilita el reintento.

# 7. Experiencia de inventario y consulta

## 7.1 Dashboard agregado

La página Inventario de fardos abrirá con un panel de filtros y tarjetas
de resumen. No cargará ni renderizará todos los fardos. Cada cambio
confirmado de filtros solicitará un nuevo agregado al backend.

  -----------------------------------------------------------------------
  **Filtros iniciales**               **Métricas**
  ----------------------------------- -----------------------------------
  Fecha de recepción desde / hasta    Total de fardos recibidos

  Número de partida                   Fardos en almacén

  Estado                              Fardos entregados

  Proveedor                           Peso neto recibido

  Tipo de material                    Peso neto disponible

  Dtex                                Peso neto entregado
  -----------------------------------------------------------------------

- Los filtros se aplicarán mediante acción explícita o con una
  estrategia de actualización controlada que evite solicitudes por cada
  pulsación.

- La página ofrecerá «Limpiar filtros» y mostrará los criterios activos.

- Los pesos se formatearán de manera consistente en kilogramos y los
  conteos como enteros.

- Carga, error y ausencia de resultados reutilizarán los patrones
  PageSkeleton, ErrorState y EmptyState.

- Un filtro sin coincidencias mostrará métricas en cero y un estado
  informativo, no se tratará como error.

## 7.2 Consulta individual

> ⚠️ **Identity rule sourced from PRD.** The compound lookup requirement
> (shipment_number + bale_number) derives from the identity constraint that bale numbers
> are unique only within a batch — defined in the
> [normative PRD](../../../docs/prd/warehouse/bale-management.md).

La misma página contendrá una sección de búsqueda específica. El usuario
deberá ingresar shipment_number y bale_number; ambos son necesarios
porque el número de fardo solo es único dentro de la partida.

  -----------------------------------------------------------------------
  **Bloque de         **Contenido**
  detalle**           
  ------------------- ---------------------------------------------------
  Identidad           Número de partida y número de fardo.

  Recepción           Proveedor y fecha de recepción.

  Características     Tipo de material y dtex.

  Pesos               Peso bruto, tara y peso neto.

  Estado              Badge «En almacén» o «Entregado».

  Acción              «Entregar a Producción» únicamente cuando el estado
                      sea in_warehouse.
  -----------------------------------------------------------------------

El detalle permanecerá vacío hasta una búsqueda válida. Un 404 deberá
producir un estado «Fardo no encontrado» en la sección de consulta, sin
afectar el dashboard.

## 7.3 Entrega a Producción

> ⚠️ **Business rule sourced from PRD.** The irreversibility of delivery, the single
> permitted transition (in_warehouse → delivered), and the absence of partial delivery
> or third states are business rules defined in the
> [normative PRD](../../../docs/prd/warehouse/bale-management.md). This section
> describes only the frontend UX implementation of those rules.

- La interfaz no ofrecerá un dropdown ni un editor genérico de estado.

- El botón abrirá un popup que confirma partida, número de fardo y el
  carácter irreversible de la acción.

- Al confirmar se enviará exclusivamente el cambio a delivered usando el
  id técnico obtenido en el detalle.

- Durante la solicitud, la acción quedará bloqueada para evitar dobles
  envíos.

- Ante éxito se mostrará un popup y se actualizarán el badge, la
  disponibilidad de la acción y las métricas del dashboard.

- Un conflicto por fardo ya entregado refrescará el detalle y mostrará
  un único popup informativo.

# 8. Requerimientos funcionales

  -----------------------------------------------------------------------
  **ID**       **Requerimiento**
  ------------ ----------------------------------------------------------
  FE-RCP-01    Alinear la cabecera de recepción con shipment_number,
               received_at como fecha y provider_name.

  FE-RCP-02    Validar cabecera antes del envío y conservar sus valores
               ante cualquier fallo.

  FE-GRD-01    Permitir captura masiva con teclado, pegado, selección y
               edición de hasta 100 fardos.

  FE-GRD-02    Distinguir filas vacías, parciales y válidas sin descartar
               información parcialmente ingresada.

  FE-GRD-03    Mostrar errores por celda y detectar duplicados de
               bale_number dentro de la partida.

  FE-GRD-04    Calcular peso neto y totales únicamente para presentación;
               excluirlos del request.

  FE-RCP-03    Confirmar la operación antes del POST y mostrar un popup
               de resultado después de la respuesta.

  FE-RCP-04    Enviar una única operación atómica y prevenir envíos
               duplicados.

  FE-INV-01    Mostrar métricas agregadas según filtros sin solicitar la
               colección completa de fardos.

  FE-INV-02    Permitir limpiar filtros y representar carga, cero
               resultados y errores de forma diferenciada.

  FE-DTL-01    Consultar un fardo exclusivamente con shipment_number +
               bale_number.

  FE-DTL-02    Mostrar detalle completo y estado con etiquetas traducidas
               para el usuario.

  FE-STS-01    Permitir la transición in_warehouse → delivered mediante
               PATCH y confirmación.

  FE-STS-02    Ocultar o deshabilitar la acción cuando el fardo ya está
               delivered.

  FE-INT-01    Centralizar base URL, serialización, lectura segura de
               respuestas y normalización de errores.

  FE-INT-02    Mapear rutas bales.n.campo del backend a rowId y celda
               usando el snapshot enviado.

  FE-NAV-01    Añadir la ruta lazy y navegación «Inventario de fardos»
               bajo Almacén.

  FE-A11Y-01   Mantener navegación por teclado, foco visible, etiquetas
               accesibles y comunicación no dependiente del color.
  -----------------------------------------------------------------------

# 9. Validación y tratamiento de errores

La representación del error se decide por su alcance. Las celdas
explican qué dato debe corregirse; el popup comunica si la operación
completa tuvo éxito o no.

  -------------------------------------------------------------------------------
  **Situación**               **Representación requerida**    **Persistencia de
                                                              datos**
  --------------------------- ------------------------------- -------------------
  Campo de cabecera inválido  Mensaje junto al campo; foco al Conservar.
                              primer error.                   

  Celda o fila inválida       Celda resaltada, mensaje breve  Conservar.
                              e indicador de fila.            

  Duplicado local de fardo    Marcar todas las celdas         Conservar.
                              bale_number involucradas.       

  409                         Popup global y shipment_number  Conservar.
  duplicate_shipment_number   marcado.                        

  422 con bales.n.campo       Mapear al rowId del snapshot y  Conservar.
                              marcar la celda.                

  422 duplicate_bale_number   Popup global y columna/números  Conservar.
  con ruta genérica           duplicados resaltados.          

  422 domain_validation_error Popup con mensaje de negocio y  Conservar.
  sin fields                  formulario intacto.             

  404 en consulta individual  Estado «Fardo no encontrado»    Conservar filtros.
                              dentro de la sección.           

  409 al entregar             Popup informativo y refresco    Conservar contexto.
                              del detalle.                    

  500 o fallo de red          Popup genérico, opción de       Conservar.
                              reintentar y sin detalle        
                              técnico.                        

  201 o PATCH exitoso         Popup de confirmación basado en Limpiar solo
                              el response.                    recepción exitosa.
  -------------------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Regla de seguridad UX:** La aplicación no mostrará mensajes de
  excepción, trazas, cuerpos no estructurados ni identificadores técnicos
  como explicación principal al usuario.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

# 10. Contratos consumidos y dependencias de backend

Este PRD no diseña la implementación backend. Define únicamente las
interfaces que el frontend necesita consumir. La integración final queda
bloqueada hasta que el backend publique los contratos objetivo.

  -------------------------------------------------------------------------------------------
  **Operación**   **Endpoint objetivo**                      **Estado al        **Uso
                                                             revisar el repo**  frontend**
  --------------- ------------------------------------------ ------------------ -------------
  Registrar       POST /api/v1/warehouse/bales               Existe, con        Recepción
  partida                                                    diferencias de     masiva.
                                                             fecha y response.  

  Resumen         GET /api/v1/warehouse/bales/summary        No implementado.   Dashboard y
                                                                                filtros.

  Detalle         GET /api/v1/warehouse/bales/detail         No implementado.   Búsqueda por
                                                                                dos query
                                                                                parameters.

  Cambiar estado  PATCH                                      No implementado.   Transición a
                  /api/v1/warehouse/bales/{bale_id}/status                      delivered.
  -------------------------------------------------------------------------------------------

## 10.1 Contrato objetivo de registro

> ⚠️ **Business contract sourced from PRD.** The required fields, decimal-as-string format,
> and exclusion of net_weight from the payload are business decisions documented in the
> [normative PRD](../../../docs/prd/warehouse/bale-management.md). This section describes
> the frontend's consumption of that contract.

  -----------------------------------------------------------------------
  **Parte**          **Campos requeridos**
  ------------------ ----------------------------------------------------
  Request de partida shipment_number, received_at como fecha,
                     provider_name y bales.

  Request por fardo  bale_number, material_type, dtex, gross_weight_kg y
                     container_weight_kg.

  Formato decimal    dtex y pesos como strings JSON.

  Response 201       raw_material_batch_id, shipment_number, received_at,
                     provider_name y bale_count.

  Exclusiones        Sin net_weight, sin ids temporales y sin arreglo
                     bales en la respuesta objetivo.
  -----------------------------------------------------------------------

## 10.2 Diferencias que bloquean la integración

- El backend actual tipa received_at como fecha-hora con zona; el
  contrato aprobado para el frontend es fecha simple.

- El backend actual devuelve el arreglo bales; el contrato aprobado
  devuelve únicamente bale_count y el resumen de la partida.

- El frontend actual usa /api/warehouse/receptions y debe migrar a
  /api/v1/warehouse/bales.

- Los endpoints de summary, detail y PATCH aún no existen.

- Vite no tiene proxy local configurado y el backend no expone una
  política CORS en la composición revisada.

# 11. Diseño técnico frontend

La implementación seguirá la organización feature-oriented existente. La
página orquestará; componentes, hooks, mappers y clientes HTTP tendrán
responsabilidades separadas. No se incorporará una librería de server
state en esta fase: el volumen de cuatro operaciones puede administrarse
con hooks y fetch, siempre que la normalización de estados y errores sea
centralizada.

  -----------------------------------------------------------------------
  **Responsabilidad**   **Decisión**
  --------------------- -------------------------------------------------
  Modelo de edición     Tipos específicos de UI separados de los DTO de
                        API.

  Mapeo                 Transformación explícita camelCase ↔ snake_case y
                        exclusión de campos visuales.

  HTTP                  Cliente común por feature con base URL
                        configurable, error tipado y control de aborto.

  Estado de recepción   Cabecera, filas, errores, snapshot y resultado
                        separados.

  Estado de inventario  Filtros aplicados, resumen, consulta individual y
                        mutación separados.

  Concurrencia          Ignorar respuestas obsoletas de filtros y evitar
                        doble submit/PATCH.

  Fechas                Fecha de negocio sin conversiones UTC ni
                        invención de hora.

  Decimales             Edición como strings y operaciones decimales
                        deterministas.

  Tema de grilla        Wrapper o estilos que traduzcan tokens Mantine a
                        react-data-grid en claro y oscuro.
  -----------------------------------------------------------------------

## 11.1 Dependencias frontend

Se reutilizarán React, Mantine, react-data-grid, React Router y Tabler
Icons. No se requiere \@mantine/dates: el selector puede resolverse con
un control de fecha nativo presentado mediante Mantine. Para precisión
decimal, se deberá adoptar una utilidad decimal determinista; se
recomienda decimal.js si la política de dependencias lo aprueba. Para
pruebas automatizadas, el proyecto deberá incorporar Vitest, React
Testing Library y user-event, ya que actualmente no existe un runner
frontend.

Toda incorporación debe respetar pnpm-workspace.yaml: minimumReleaseAge
de 24 horas y política trustPolicy no-downgrade. No deben introducirse
secretos en variables VITE\_\*.

# 12. Requerimientos no funcionales

  ------------------------------------------------------------------------
  **Atributo**     **Requisito**
  ---------------- -------------------------------------------------------
  Rendimiento      Edición fluida con 100 filas; cálculos lineales;
                   filtros sin ráfagas de requests; sin descargar
                   entidades para sumar.

  Accesibilidad    Foco visible, navegación completa por teclado, labels,
                   mensajes asociados y estados no dependientes solo del
                   color.

  Responsive       Dashboard y detalle adaptables a móvil; recepción
                   priorizada para escritorio/tablet con scroll horizontal
                   controlado.

  Fiabilidad       Snapshot por envío, idempotencia visual, prevención de
                   doble acción y datos conservados ante fallo.

  Seguridad        No exponer secretos, trazas ni mensajes internos;
                   respetar ProtectedRoute y capacidades existentes.

  Compatibilidad   Modo claro y oscuro; navegadores modernos soportados
                   por Vite/React; formato de fecha estable.

  Observabilidad   Mensajes accionables y códigos de error normalizados;
  UX               sin registrar payloads sensibles en consola.

  Mantenibilidad   Tipos de UI y API separados, nombres de dominio
                   explícitos y componentes pequeños dentro del feature.
  ------------------------------------------------------------------------

# 13. Estrategia de pruebas y calidad

## 13.1 Pruebas automatizadas mínimas

- Mapper de recepción: exclusión de filas vacías, preservación de
  strings decimales y ausencia de campos visuales.

- Validador de grilla: fila parcial, duplicados, dtex, pesos y relación
  peso bruto/tara.

- Cálculos: neto por fila y totales con precisión decimal.

- Normalizador de errores: cabecera, bales.n.campo, ruta genérica y
  error sin cuerpo JSON.

- Flujo de recepción: confirmación, bloqueo, éxito, fallo y conservación
  de datos.

- Dashboard: filtros, carga, cero resultados, error y descarte de
  respuestas obsoletas.

- Consulta y PATCH: búsqueda compuesta, 404, confirmación, éxito y
  conflicto por delivered.

- Navegación: nueva ruta lazy, breadcrumb y visibilidad según
  resourceType.

## 13.2 Puertas de calidad

- pnpm build aprobado.

- pnpm lint aprobado.

- Suite frontend aprobada una vez incorporado el runner.

- Prueba manual con 100 filas, pegado desde Excel y navegación por
  teclado.

- Prueba manual en modos claro y oscuro.

- Prueba responsive de dashboard y detalle; verificación del scroll de
  la grilla.

- Integración real contra PostgreSQL local para POST, GET summary, GET
  detail y PATCH.

- Verificación de conservación de datos ante 409, 422, 500 y fallo de
  red.

# 14. Criterios de aceptación

  -----------------------------------------------------------------------
  **ID**      **Criterio**
  ----------- -----------------------------------------------------------
  AC-01       La cabecera solo contiene partida, fecha y proveedor.

  AC-02       La grilla acepta hasta 100 fardos y mantiene
              navegación/pegado tipo planilla.

  AC-03       Solo filas completas se serializan; las parciales se
              señalan y las vacías se ignoran.

  AC-04       Los decimales se envían como strings y net_weight no forma
              parte del request.

  AC-05       El usuario confirma antes de registrar y recibe un popup
              resumido tras 201.

  AC-06       Los errores por celda se muestran en la grilla; los
              globales se muestran en un único popup.

  AC-07       La información ingresada se conserva cuando la operación
              falla.

  AC-08       El dashboard muestra seis métricas agregadas y aplica los
              filtros definidos.

  AC-09       La consulta exige shipment_number y bale_number y presenta
              un único detalle.

  AC-10       Solo un fardo in_warehouse puede mostrar la acción Entregar
              a Producción.

  AC-11       PATCH exitoso actualiza detalle y dashboard; no existe
              reversión desde la UI.

  AC-12       La navegación no utiliza WarehousePage como placeholder
              para las nuevas funcionalidades.

  AC-13       Estados loading, empty, error y success son distinguibles y
              accesibles.

  AC-14       Build, lint, pruebas y validación manual contra backend
              están aprobados.
  -----------------------------------------------------------------------

# 15. Secuencia de implementación recomendada

  --------------------------------------------------------------------------
  **Fase**   **Capacidad**       **Resultado esperado**
  ---------- ------------------- -------------------------------------------
  1          Fundación de        Modelos UI/API, cliente HTTP, normalización
             integración         de errores, base URL/proxy y pruebas base.

  2          Recepción masiva    Cabecera, columnas, validación, cálculos,
                                 confirmación, POST y popup de resultado.

  3          Inventario agregado Ruta, navegación, filtros, estados y
                                 tarjetas de summary.

  4          Consulta individual Formulario compuesto, detalle, 404 y
                                 presentación de estado.

  5          Entrega             Confirmación, PATCH, conflictos y
                                 actualización de resumen/detalle.

  6          Endurecimiento      Accesibilidad, responsive, tema de grilla,
                                 pruebas con 100 filas e integración
                                 completa.
  --------------------------------------------------------------------------

Las fases 3 a 5 pueden desarrollarse con dobles de API, pero no pueden
considerarse terminadas hasta que los endpoints backend correspondientes
estén disponibles y la integración real haya sido verificada.

# 16. Riesgos y decisiones pendientes

  -----------------------------------------------------------------------
  **Riesgo o dependencia**      **Tratamiento requerido**
  ----------------------------- -----------------------------------------
  Contrato POST no alineado con Resolver en el PRD backend antes del
  fecha simple y response       cierre de integración.
  resumido                      

  GET summary, GET detail y     Acordar OpenAPI y respuestas de error
  PATCH ausentes                antes de congelar los tipos frontend.

  Ruta genérica                 Mantener detección local de duplicados y
  bales\[\].bale_number         fallback visual de columna.

  react-data-grid en beta       Conservar versión fijada, cubrir
                                pegado/edición con pruebas y no
                                actualizar durante esta entrega.

  Sin runner de pruebas         Agregar tooling de pruebas como
                                habilitador del feature.

  Sin proxy ni CORS             Definir proxy local /api y estrategia de
                                despliegue same-origin o base URL
                                pública.

  Catálogos no disponibles      Usar texto en proveedor y material; no
                                anticipar Select con datos ficticios.

  Mobile limitado para          Garantizar acceso y scroll, pero declarar
  planillas                     escritorio/tablet como superficie
                                operativa principal.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Cierre del alcance:** El frontend queda listo cuando recepción,
  resumen, consulta y entrega funcionan contra contratos reales, con
  errores representados según su alcance y sin depender de listados
  completos de fardos.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------


---

# Appendix A — Bale Reception Grid Specifics

> Bale-specific grid behavior extracted from the original `bale-reception-grid.md`.
> For reusable data-grid patterns, see `../patterns/data-grid.md`.

## A.1 Screen Layout

The bale reception screen is divided into two vertical sections:

1. **Header form** — Shared data for all bales in this reception (shipment number, date, provider).
2. **Editable grid** — Per-bale data entry using react-data-grid.

The form and grid are submitted together as a single atomic payload. The form is never submitted independently.

## A.2 Bale Grid Columns

| Column | Edit Type | Required | Validation |
| --- | --- | --- | --- |
| # (row number) | Read-only | — | Visual only; not sent to backend |
| Bale number | Text | Yes | Non-empty, unique within the reception |
| Material type | Text | Yes | Required; no catalog enforcement yet |
| Dtex | Decimal as text | Yes | Finite, greater than zero |
| Gross weight (kg) | Decimal as text | Yes | Greater than zero |
| Tare (kg) | Decimal as text | Yes | Non-negative, less than gross weight |
| Net weight (kg) | Computed (read-only) | — | Gross weight minus tare; not sent |
| Row status | Visual indicator | — | Summarizes row errors; not part of payload |

## A.3 Bale-Specific Validation Rules

- Each row must have bale number + material type + dtex + gross weight + tare.
- Bale numbers must be unique within the current reception (local duplicate detection).
- Tare must be non-negative and strictly less than gross weight.
- Net weight is a visual calculation only — excluded from the request payload.
- Dtex and weights are edited and transmitted as strings to preserve decimal precision.

## A.4 Bale Grid Formulas and Summary

Calculations are local display aids recalculated on every edit, paste, add, or remove:

| Indicator | Source | Treatment |
| --- | --- | --- |
| Valid bales | Complete rows without local errors | Count |
| Total gross weight | Valid gross weight values | Decimal sum |
| Total tare | Valid tare values | Decimal sum |
| Total net weight | Gross minus tare per row | Decimal sum; not sent |
| Rows with errors | Grid validation state | Count + navigation to first error |

The summary must remain visible when working with many rows (via react-data-grid summary row or an associated grid footer).

## A.5 Bale Reception Feature Architecture

```text
features/warehouse/
  pages/
    ReceptionPage.tsx             ← Full page (form + grid + toolbar)
  components/
    TruckReceptionForm.tsx        ← Header form (Mantine)
    BaleReceptionGrid.tsx         ← react-data-grid wrapper with bale columns and summary
    editors/
      TextCellEditor.tsx          ← Text editor (reusable)
      NumberCellEditor.tsx        ← Numeric editor, string-based (reusable)
      MaterialSelectEditor.tsx    ← Material type select (bale-specific)
  hooks/
    useBaleReceptionGrid.ts       ← Grid state (rows, local CRUD)
    useReceptionSubmit.ts         ← Validation + batch POST submission
    useMaterialCatalog.ts         ← Fetch material catalog
  types/
    reception-types.ts            ← BaleRow, TruckFormData, ReceptionPayload
  api/
    receptionApi.ts               ← POST /api/v1/warehouse/bales
```

## A.6 Bale Reception Payload Contract

```typescript
interface ReceptionPayload {
  shipment_number: string
  received_at: string           // ISO date (no time component)
  provider_name: string
  bales: {
    bale_number: string
    material_type: string
    dtex: string                // String for decimal precision
    gross_weight_kg: string     // String for decimal precision
    container_weight_kg: string // Tare, string for decimal precision
  }[]
}
```

Net weight is excluded from the payload — the backend computes it from gross weight and tare.

## A.7 Bale Reception Data Flow

1. User completes the header form (shipment number, date, provider).
2. User fills the grid row by row (spreadsheet-like interaction).
3. User can add rows, navigate with keyboard, paste from Excel, or remove selected rows.
4. All state lives in the frontend until "Save" is pressed.
5. On save: validate header + grid → confirmation popup → single POST → result popup.
6. Backend response: 201 (success), 422 (validation error), 409 (duplicate conflict).
7. On success: show result and clear form. On error: preserve data, show error, allow retry.

## A.8 Backend Dependencies for Bale Reception

| Endpoint | Purpose | Status |
| --- | --- | --- |
| `POST /api/v1/warehouse/bales` | Register complete reception (header + bales) | Exists (with differences) |
| `GET /api/v1/warehouse/bales/summary` | Aggregated dashboard metrics | Not implemented |
| `GET /api/v1/warehouse/bales/detail` | Individual bale lookup | Not implemented |
| `PATCH /api/v1/warehouse/bales/{bale_id}/status` | Transition to delivered | Not implemented |
