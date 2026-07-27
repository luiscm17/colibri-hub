---
document_type: technical-spec
status: active
implementation: partial
scope: frontend/design-system
authority: explanatory
owner: frontend
last_reviewed: 2026-07-27
---

# Colibri Hub — Visual Identity

> Paleta de color, tipografía y tokens visuales del sistema de gestión de
> producción textil. Soporta modo claro y modo oscuro.

---

## 1. Color primario

El color del logo es `#4EFFF9` (cian brillante). A partir de él se define
la escala completa del primario, con variantes para fondo, borde, texto y
elementos interactivos en ambos modos.

### 1.1 Escala del primario

| Token | Hex | HSL |
|---|---|---|
| 50 | `#E5FCFA` | `178°, 85%, 95%` |
| 100 | `#C4F7F3` | `178°, 80%, 90%` |
| 200 | `#85F0E9` | `178°, 75%, 80%` |
| **300** | **`#4EFFF9`** | **`178°, 100%, 65%`** — logo / brand |
| 400 | `#14E3D9` | `178°, 85%, 52%` |
| 500 | `#15BDB5` | `178°, 80%, 42%` |
| 600 | `#169A94` | `178°, 75%, 34%` |
| 700 | `#147A75` | `178°, 70%, 26%` |
| 800 | `#105955` | `178°, 65%, 18%` |
| 900 | `#0A3533` | `178°, 60%, 10%` |

### 1.2 Asignación por modo

| Elemento | Modo claro | Modo oscuro |
|---|---|---|
| Logo / brand | `300` (#4EFFF9) | `300` (#4EFFF9) |
| Botón primario | `500` (#15BDB5) | `400` (#14E3D9) |
| Botón primario hover | `600` (#169A94) | `300` (#4EFFF9) |
| Texto de acento / enlace | `700` (#147A75) | `300` (#4EFFF9) |
| Enlace hover | `500` (#15BDB5) | `200` (#85F0E9) |
| Borde activo / foco | `400` (#14E3D9) | `400` (#14E3D9) |
| Fondo de fila seleccionada | `50` (#E5FCFA) | `800` (#105955) translúcido |
| Badge informativo | fondo `100`, texto `700` | fondo `800`, texto `200` |
| Indicador de etapa activa | `400` (#14E3D9) | `300` (#4EFFF9) |
| Hover en tabla / lista | `50` (#E5FCFA) | `800` al 40% |

---

## 2. Modo claro — paleta neutra

| Token | Hex | Uso |
|---|---|---|
| `surface-page` | `#FAFAFA` | Fondo de página |
| `surface-raised` | `#FFFFFF` | Tarjetas, paneles, inputs, modales |
| `surface-sidebar` | `#F5F5F5` | Fondo de la barra lateral |
| `surface-hover` | `#F0F0F0` | Hover en filas de tabla, items de lista |
| `border-default` | `#E0E0E0` | Bordes de tabla, inputs, separadores |
| `border-strong` | `#BDBDBD` | Bordes en foco, bordes de modales |
| `text-primary` | `#212121` | Texto principal |
| `text-secondary` | `#616161` | Metadatos, descripciones, labels |
| `text-placeholder` | `#9E9E9E` | Placeholder en inputs, iconos inactivos |
| `text-disabled` | `#BDBDBD` | Texto deshabilitado |
| `icon-default` | `#757575` | Iconos en toolbar |
| `icon-disabled` | `#BDBDBD` | Iconos deshabilitados |

---

## 3. Modo oscuro — paleta neutra

| Token | Hex | Uso |
|---|---|---|
| `surface-page` | `#0D1117` | Fondo de página |
| `surface-raised` | `#161B22` | Tarjetas, paneles, inputs, modales |
| `surface-sidebar` | `#0D1117` | Fondo de la barra lateral |
| `surface-hover` | `#1C2333` | Hover en filas de tabla, items de lista |
| `border-default` | `#30363D` | Bordes de tabla, inputs, separadores |
| `border-strong` | `#484F58` | Bordes en foco, bordes de modales |
| `text-primary` | `#E1E4E8` | Texto principal |
| `text-secondary` | `#8B949E` | Metadatos, descripciones, labels |
| `text-placeholder` | `#484F58` | Placeholder en inputs, iconos inactivos |
| `text-disabled` | `#30363D` | Texto deshabilitado |
| `icon-default` | `#8B949E` | Iconos en toolbar |
| `icon-disabled` | `#30363D` | Iconos deshabilitados |

---

## 4. Colores semánticos

Para estados, notificaciones y validación. Cada color tiene variante clara
(para fondos de badge) y variante oscura (para texto/icono/borde), ajustadas
por modo.

### 4.1 Éxito

| Token | Claro | Oscuro |
|---|---|---|
| Hex base | `#2E7D32` | `#3FB950` |
| Badge fondo | `#C8E6C9` | `#1B362A` |
| Badge texto | `#1B5E20` | `#3FB950` |
| Uso | Disponible, completado, confirmación | |

### 4.2 Advertencia

| Token | Claro | Oscuro |
|---|---|---|
| Hex base | `#F57F17` | `#D29922` |
| Badge fondo | `#FFF8E1` | `#2D2414` |
| Badge texto | `#E65100` | `#D29922` |
| Uso | Observado, condición, alerta | |

### 4.3 Error

| Token | Claro | Oscuro |
|---|---|---|
| Hex base | `#C62828` | `#F85149` |
| Badge fondo | `#FFEBEE` | `#2D1518` |
| Badge texto | `#B71C1C` | `#F85149` |
| Uso | Defectuoso, bloqueante, error de validación | |

### 4.4 Información

| Token | Claro | Oscuro |
|---|---|---|
| Hex base | `#1565C0` | `#58A6FF` |
| Badge fondo | `#E3F2FD` | `#0B1E33` |
| Badge texto | `#0D47A1` | `#58A6FF` |
| Uso | Pendiente, informativo, en espera | |

---

## 5. Color por dominio de negocio

> **Deprecado.** Con RBAC los usuarios pueden operar en múltiples dominios,
> por lo que el color por contexto de negocio no se aplica en la navegación.
> El color primario cian es el único color de interacción del sistema.

~~Cada contexto tiene un color asociado para navegación, badges y encabezados
de sección. Se usan con moderación: el color dominante sigue siendo el
primario cian.

| Contexto | Claro | Oscuro | Nota |
|---|---|---|---|
| Almacén | `#147A75` | `#4EFFF9` | Variante del primario |
| Hilatura | `#D97706` | `#FBBF24` | Ámbar — proceso continuo, calor |
| Proceso por Lotes | `#7C3AED` | `#A78BFA` | Violeta — trazabilidad de lote |
| Reportes | `#52525B` | `#A1A1AA` | Zinc — neutral, datos |
| Admin | `#78716C` | `#D6D3D1` | Piedra — utilitario, baja prioridad |~~

---

## 6. Estados operativos del PT (Almacén)

| Estado | Claro | Oscuro |
|---|---|---|
| Disponible | Verde éxito `#2E7D32` | Verde éxito `#3FB950` |
| Observado | Ámbar advertencia `#F57F17` | Ámbar `#D29922` |
| Disponible con condición | Ámbar `#F57F17` | Ámbar `#D29922` |
| Defectuoso | Rojo error `#C62828` | Rojo `#F85149` |
| Entregado / Despachado | Neutro `#9E9E9E` | Neutro `#484F58` |

---

## 7. Estados de etapa de lote

| Estado | Claro | Oscuro |
|---|---|---|
| Completado | Verde éxito `#2E7D32` | Verde éxito `#3FB950` |
| Activo (etapa actual) | Primario 500 `#15BDB5` | Primario 300 `#4EFFF9` |
| Pendiente | Borde `#E0E0E0` | Borde `#30363D` |
| Con observaciones | Ámbar `#F57F17` | Ámbar `#D29922` |
| En espera de Almacén | Info `#1565C0` | Info `#58A6FF` |

---

## 8. Tipografía

### 8.1 Family

- **Interfaz:** sistema sans-serif del sistema operativo (`system-ui`,
  `-apple-system`, `Segoe UI`, `Roboto`, `Helvetica Neue`)
- **Datos técnicos:** monospace del sistema (`ui-monospace`, `SF Mono`,
  `Cascadia Code`, `Consolas`)
- No se definen fuentes decorativas ni de marca

### 8.2 Jerarquía

| Elemento | Peso | Tamaño | Interlineado | Uso |
|---|---|---|---|---|
| Título de página | Semibold (600) | 24px | 1.3 | Encabezado de cada pantalla |
| Título de sección | Semibold (600) | 18px | 1.4 | Encabezado de bloque dentro de una pantalla |
| Subtítulo / metadato | Regular (400) | 14px | 1.4 | Información secundaria, etiquetas de campo |
| Cuerpo | Regular (400) | 14px | 1.5 | Texto general, celdas de tabla, labels |
| Cuerpo pequeño | Regular (400) | 12px | 1.5 | Metadatos, timestamps, notas al pie |
| Monospace | Regular (400) | 13px | 1.4 | Códigos de lote, identificadores técnicos |
| Tabla encabezado | Semibold (600) | 12px | 1.2 | Headers de columna |
| Tabla celda | Regular (400) | 14px | 1.4 | Datos en tabla |
| Badge | Medium (500) | 12px | 1.2 | Etiquetas de estado, contadores |

---

## 9. Espaciado

| Token | Valor | Uso |
|---|---|---|
| `space-xxs` | 4px | Padding interno de badges, iconos, gap mínimo |
| `space-xs` | 8px | Gap entre elementos relacionados, padding de celdas |
| `space-sm` | 12px | Padding de inputs, gap en formularios |
| `space-md` | 16px | Padding de tarjetas, gap entre secciones |
| `space-lg` | 24px | Margen entre secciones principales |
| `space-xl` | 32px | Padding de página, separación de paneles |
| `space-xxl` | 48px | Separación de rutas visuales mayores |

---

## 10. Sombras

En modo oscuro las sombras se atenúan: se reduce la opacidad y se usa negro
puro en lugar de negro con saturación.

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.06)` | `0 1px 2px rgba(0,0,0,0.3)` | Tarjetas, paneles elevados ligeramente |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | `0 4px 6px rgba(0,0,0,0.4)` | Modales, dropdowns, tooltips |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | `0 10px 15px rgba(0,0,0,0.5)` | Diálogos de confirmación, notificaciones |

---

## 11. Bordes

| Token | Valor | Uso |
|---|---|---|
| `radius-sm` | 4px | Inputs, botones pequeños, badges |
| `radius-md` | 6px | Tarjetas, paneles, tablas |
| `radius-lg` | 8px | Modales, diálogos |
| `radius-full` | 9999px | Avatares, indicadores de estado circulares |
| `border-width` | 1px | Ancho estándar de borde |
| `border-width-thick` | 2px | Bordes en foco, bordes activos |

---

## 12. Transiciones

| Token | Valor | Uso |
|---|---|---|
| `transition-fast` | 150ms ease | Hover, active, feedback inmediato |
| `transition-normal` | 200ms ease | Cambios de estado, apertura de dropdowns |
| `transition-slow` | 300ms ease | Sidebar collapse, expansión de paneles |
