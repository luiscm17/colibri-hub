---
document_type: technical-spec
status: active
implementation: not-applicable
scope: frontend/design-system
authority: explanatory
owner: frontend
last_reviewed: 2026-08-11
---

# Colibri Hub Visual Identity

This document defines the frontend's visual principles and semantic tokens for
light and dark presentation. [Frontend Styling](../../../docs/dev-guide/frontend-styling.md)
owns how tokens are applied. [Accessibility](../accessibility.md) owns contrast,
color-independence, and motion constraints.

## 1. Principles

- Use cyan as the single interaction and brand accent across capabilities.
- Use neutral surfaces and restrained elevation so operational data remains the
  visual focus.
- Assign semantic colors by meaning, never by business capability.
- Preserve the same semantic hierarchy in light and dark modes.
- Keep typography compact and legible for data-dense operational work.

## 2. Brand Scale

The logo color is brand `300` (`#4EFFF9`).

| Token | Hex | HSL |
| --- | --- | --- |
| `brand-50` | `#E5FCFA` | `178deg 85% 95%` |
| `brand-100` | `#C4F7F3` | `178deg 80% 90%` |
| `brand-200` | `#85F0E9` | `178deg 75% 80%` |
| `brand-300` | `#4EFFF9` | `178deg 100% 65%` |
| `brand-400` | `#14E3D9` | `178deg 85% 52%` |
| `brand-500` | `#15BDB5` | `178deg 80% 42%` |
| `brand-600` | `#169A94` | `178deg 75% 34%` |
| `brand-700` | `#147A75` | `178deg 70% 26%` |
| `brand-800` | `#105955` | `178deg 65% 18%` |
| `brand-900` | `#0A3533` | `178deg 60% 10%` |

## 3. Neutral Colors

Neutral token names keep the same meaning across modes.

| Token | Light | Dark |
| --- | --- | --- |
| `surface-page` | `#FAFAFA` | `#0D1117` |
| `surface-raised` | `#FFFFFF` | `#161B22` |
| `surface-sidebar` | `#F5F5F5` | `#0D1117` |
| `surface-hover` | `#F0F0F0` | `#1C2333` |
| `border-default` | `#E0E0E0` | `#30363D` |
| `border-strong` | `#BDBDBD` | `#484F58` |
| `text-primary` | `#212121` | `#E1E4E8` |
| `text-secondary` | `#616161` | `#8B949E` |
| `text-placeholder` | `#9E9E9E` | `#484F58` |
| `text-disabled` | `#BDBDBD` | `#30363D` |
| `icon-default` | `#757575` | `#8B949E` |
| `icon-disabled` | `#BDBDBD` | `#30363D` |

## 4. Semantic Colors

Semantic colors communicate general interface meaning. Feature specifications
map business states to these meanings when needed.

| Meaning | Light base | Light surface | Light foreground | Dark base | Dark surface | Dark foreground |
| --- | --- | --- | --- | --- | --- | --- |
| Success | `#2E7D32` | `#C8E6C9` | `#1B5E20` | `#3FB950` | `#1B362A` | `#3FB950` |
| Warning | `#F57F17` | `#FFF8E1` | `#E65100` | `#D29922` | `#2D2414` | `#D29922` |
| Error | `#C62828` | `#FFEBEE` | `#B71C1C` | `#F85149` | `#2D1518` | `#F85149` |
| Information | `#1565C0` | `#E3F2FD` | `#0D47A1` | `#58A6FF` | `#0B1E33` | `#58A6FF` |

## 5. Typography

| Token | Family | Weight | Size | Line height |
| --- | --- | --- | --- | --- |
| `type-page-title` | System sans-serif | 600 | `24px` | `1.3` |
| `type-section-title` | System sans-serif | 600 | `18px` | `1.4` |
| `type-body` | System sans-serif | 400 | `14px` | `1.5` |
| `type-body-small` | System sans-serif | 400 | `12px` | `1.5` |
| `type-data` | System monospace | 400 | `13px` | `1.4` |
| `type-table-header` | System sans-serif | 600 | `12px` | `1.2` |
| `type-table-cell` | System sans-serif | 400 | `14px` | `1.4` |
| `type-label` | System sans-serif | 500 | `12px` | `1.2` |

The system sans-serif family is `system-ui`, `-apple-system`, `Segoe UI`,
`Roboto`, and `Helvetica Neue`. The data family is `ui-monospace`, `SF Mono`,
`Cascadia Code`, and `Consolas`. Decorative and brand fonts are not defined.

## 6. Spacing And Shape

| Token | Value |
| --- | --- |
| `space-xxs` | `4px` |
| `space-xs` | `8px` |
| `space-sm` | `12px` |
| `space-md` | `16px` |
| `space-lg` | `24px` |
| `space-xl` | `32px` |
| `space-xxl` | `48px` |
| `radius-sm` | `4px` |
| `radius-md` | `6px` |
| `radius-lg` | `8px` |
| `radius-full` | `9999px` |
| `border-width` | `1px` |
| `border-width-thick` | `2px` |

## 7. Elevation

| Token | Light | Dark |
| --- | --- | --- |
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.06)` | `0 1px 2px rgba(0,0,0,0.3)` |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | `0 4px 6px rgba(0,0,0,0.4)` |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | `0 10px 15px rgba(0,0,0,0.5)` |

## 8. Motion

| Token | Value |
| --- | --- |
| `motion-fast` | `150ms ease` |
| `motion-normal` | `200ms ease` |
| `motion-slow` | `300ms ease` |

Motion reinforces state change and spatial continuity; it must not be required to
understand an outcome. Applied motion follows the reduced-motion requirements in
the Accessibility Guidelines.
