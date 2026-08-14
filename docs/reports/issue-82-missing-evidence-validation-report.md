# Issue #82 — Evidencia de cierre pendiente (manual de evidencia faltante)

Reporte de la ejecución del manual `docs/reports/issue-82-missing-evidence-validation.md`.

- **Fecha**: 2026-08-14
- **Entorno**: Linux, Node v24.19.0, pnpm 11.21.0, playwright-cli 0.1.18
- **Candidato**: rama `front/access-auth-foundation`, HEAD `4f0c6ed38fd0c765e40ed542243fbe9047a3541a`
- **Huella del patch**: SHA-256 `b2d52ba2cc9640c93d8afd5a1f330b8ad6fa6a50103b2be199182800d151bb0e` (idéntica al inicio y fin)
- **BASE_URL**: `http://127.0.0.1:5173` (Vite; proxy `/api` → backend :8000)
- **Test account**: An authorized test account was used; credentials are intentionally omitted.
- **IDs de prueba**: rol `section-responsible` → `<ROLE_ID>`; preset `Responsable de Sección` → `<PRESET_ID>` (sustituidos por `<ID>` en este reporte)
- **Responsable (iniciales)**: —

**Nota operativa**: el entorno de playwright-cli presentó dos comportamientos: (1) el browser no persistía entre invocaciones, por lo que cada caso se ejecutó en una sola secuencia encadenada; (2) el callback del colector de red ejecuta en un VM donde `URL` y `URLSearchParams` no están definidos, por lo que el parseo de la ruta se hizo con regex sobre `response.url()` y el código de browser se ejecutó con `page.evaluate`. Esto no cambia la evidencia recolectada: método, path y status provienen de los objetos `response` reales.

---

## 1. Rutas directas y recarga

Colector instalado antes de cada navegación; se registró la red después de `goto` y después de `reload` por separado.

### Roles/new — `/access/roles/new`
- **Directa**: PASS — URL `/access/roles/new`; heading `Create role`; Network solo referencias (sin colección, sin mutaciones).
- **Recarga**: PASS — URL y heading idénticos; Network solo referencias.

Network (directa y recarga; mismo conjunto, GET):
```
GET /api/v1/auth/me 200 (x2)
GET /api/v1/access/me 200 (x2)
GET /api/v1/access/scope-definitions 200 (x2)
GET /api/v1/access/scopes?page=1&page_size=100 200 (x2)
```
Observación: el duplicado de cada request corresponde al arranque doble del SPA sobre la ruta; no hay ninguna mutación.

### Presets/new — `/access/presets/new`
- **Directa**: PASS — URL `/access/presets/new`; heading `Create preset`; solo referencias.
- **Recarga**: PASS — idéntico.

Network: mismo conjunto de GET de referencias (auth/me, access/me, scope-definitions, scopes) sin colección ni mutación.

### Rol/detalle — `/access/roles/<ROLE_ID>`
- **Directa**: PASS — URL retenida; detalle del rol visible (nombre `Section Responsible`, botones Back/Cancel/Guardar); Network: GET del detalle + referencias.
- **Recarga**: PASS — idéntico.

Network:
```
GET /api/v1/auth/me 200 (x2)
GET /api/v1/access/me 200 (x2)
GET /api/v1/access/roles/<ROLE_ID> 200 (x2)
```

### Rol/edición — `/access/roles/<ROLE_ID>/edit`
- **Directa**: PASS — URL retenida; formulario `Edit role` visible (`Role name` = `Section Responsible`, botones `Back to Roles`, `Save role`, `Deactivate role`, permisos Remove).
- **Recarga**: PASS — idéntico.

Network:
```
GET /api/v1/auth/me 200 (x2)
GET /api/v1/access/me 200 (x2)
GET /api/v1/access/roles/<ROLE_ID> 200 (x2)
GET /api/v1/access/scope-definitions 200 (x2)
GET /api/v1/access/scopes?page=1&page_size=100 200 (x2)
```

### Preset/detalle — `/access/presets/<PRESET_ID>`
- **Directa**: PASS — URL retenida; detalle del preset visible (nombre `Responsable de Sección`); Network: GET del preset + referencias.
- **Recarga**: PASS — idéntico.

Network:
```
GET /api/v1/auth/me 200 (x2)
GET /api/v1/access/me 200 (x2)
GET /api/v1/access/role-presets/<PRESET_ID> 200 (x2)
```

### Preset/edición — `/access/presets/<PRESET_ID>/edit`
- **Directa**: PASS — URL retenida; formulario `Edit preset` visible.
- **Recarga**: PASS — idéntico.

Network:
```
GET /api/v1/auth/me 200 (x2)
GET /api/v1/access/me 200 (x2)
GET /api/v1/access/role-presets/<PRESET_ID> 200 (x2)
GET /api/v1/access/scope-definitions 200 (x2)
GET /api/v1/access/scopes?page=1&page_size=100 200 (x2)
```

| Ruta | Directa: resultado | Directa: URL + Network | Recarga: resultado | Recarga: URL + Network |
|---|---|---|---|---|
| Roles/new | PASS | URL + solo referencias GET | PASS | URL + solo referencias GET |
| Presets/new | PASS | URL + solo referencias GET | PASS | URL + solo referencias GET |
| Rol/detalle | PASS | URL + GET detalle/referencias | PASS | idéntico |
| Rol/edición | PASS | URL + GET detalle/referencias | PASS | idéntico |
| Preset/detalle | PASS | URL + GET detalle/referencias | PASS | idéntico |
| Preset/edición | PASS | URL + GET detalle/referencias | PASS | idéntico |

## 2. Copia ajustable de preset

Desde el detalle del preset → `Start adjustable draft`.

- **URL + `_origin` sanitizados**: PASS — `…/access/roles/new?preset=<ID>&_origin={"family":"presets","criteria":{},"page":1,"subjectId":"<ID>"}` (URL-encoded en el navegador; IDs sustituidos por `<ID>`).
- **Borrador antes/después**: PASS — idéntico tras recarga:
  - Role code: `section-responsible-preset-copy`
  - Role name: `Responsable de Sección copy`
  - Description: `Configuración inicial para un responsable de sección.`
  - Permisos: `edit:yarn_spinning.section.ring_spinning`, `read:yarn_spinning.section.ring_spinning`, `write:yarn_spinning.section.ring_spinning`
- **GET de recarga sin mutación**: PASS — Network de la recarga solo GET (auth/me x3, access/me x3, role-presets/<PRESET_ID> x3, scopes x3, scope-definitions x3); ninguna mutación.
- **Destino de Cancel**: PASS — `Cancel` navega a `/access/presets/<PRESET_ID>` (detalle del preset de origen).

| Resultado | URL + `_origin` sanitizados | Borrador antes/después | GET de recarga sin mutación | Destino de Cancel |
|---|---|---|---|---|
| PASS | sí (IDs → `<ID>`) | idéntico | sí (solo GET) | `/access/presets/<PRESET_ID>` |

## 3. Salida con cambios y foco (4 flujos)

Para cada flujo: `fill` de un campo editable → activar `Cancel`/`Back` → modal `Discard changes` → captura nominal del modal → `Keep editing` → evaluar `activeElement` y borrador → reabrir modal → `Discard changes` → evaluar `activeElement` y destino.

| Flujo | Resultado | Captura nominal del modal | activeElement tras Keep + borrador | activeElement tras Discard + destino |
|---|---|---|---|---|
| Rol/create | PASS | `issue-82-rol-create-dirty-modal.png` | BUTTON `Cancel` + borrador `Draft change` visible | H1 `Roles` en `/access/roles` |
| Rol/edit | PASS | `issue-82-rol-edit-dirty-modal.png` | BUTTON `Back to Roles` + borrador `Draft change` visible | H1 `Roles` en `/access/roles` |
| Preset/create | PASS | `issue-82-preset-create-dirty-modal.png` | BUTTON `Cancel` + borrador `Draft change` visible | H1 `Role presets` en `/access/presets` |
| Preset/edit | PASS | `issue-82-preset-edit-dirty-modal.png` | BUTTON `Back to Role presets` + borrador `Draft change` visible | H1 `Role presets` en `/access/presets` |

Todos los modales exponen los botones semánticos `Keep editing` y `Discard changes`. Tras Discard el foco queda en el heading de la colección (H1 `Roles` / `Role presets`).

Texto observado del modal (creación): `Discard unsaved changes? | You have unsaved changes in new role. Discard them and leave this page? | Keep editing | Discard changes`.
Texto del modal (edición): `You have unsaved changes in role <ROLE_NAME>` / `in preset <PRESET_NAME>` — nombre del catálogo, no datos personales.

## 4. Identificadores malformados

Colector vaciado antes de cada navegación; se contaron los requests cuyo path contiene `not-a-uuid`.

| Ruta | Resultado | URL retenida sanitizada | Lista Network | Conteo de detalle |
|---|---|---|---|---|
| Rol/detalle `/access/roles/not-a-uuid` | PASS | `/access/roles` | GET auth/me x2, access/me x2, roles?page=1&page_size=50 | 0 |
| Rol/edición `/access/roles/not-a-uuid/edit` | PASS | `/access/roles` | idéntico | 0 |
| Preset/detalle `/access/presets/not-a-uuid` | PASS | `/access/presets` | GET auth/me x2, access/me x2, role-presets?page=1&page_size=50 | 0 |
| Preset/edición `/access/presets/not-a-uuid/edit` | PASS | `/access/presets` | idéntico | 0 |
| Usuario/detalle `/access/users/not-a-uuid` | PASS | `/access/users` | GET auth/me x2, access/me x2, users?page=1&page_size=50 | 0 |

`detailRequestCount: 0` en las cinco rutas: no existe ningún request de detalle para el ID malformado; la app recupera a la colección permitida antes de solicitar datos.

## 5. Paginación fuera de rango

Criterio `q=supervisor` (total positivo), página solicitada `999`.

- **Total/page_size/última calculada**: total del criterio > 0; `page_size=50` (visible en la URL); última página = `max(1, ceil(total/50))` = 1 (canónica, omitida de la URL final).
- **Lista + conteo de requests**: exactamente **2 GET**:
  ```
  GET /api/v1/access/roles?page=999&page_size=50 200
  GET /api/v1/access/roles?page=1&page_size=50 200
  ```
- **URL/query final**: `/access/roles?q=supervisor` — conserva `q`, usa la última página y omite `page=1` por ser el valor canónico.
- **Evidencia de ausencia de cascada**: no hay requests intermedios; solo los dos GET esperados (el solicitado y la última calculada).

| Resultado | Total/page_size/última calculada | Lista + conteo de requests | URL/query final | Evidencia de ausencia de cascada |
|---|---|---|---|---|
| PASS | total > 0, 50, 1 | 2 GET (999 → 1) | `/access/roles?q=supervisor` | sin requests intermedios |

## 6. Responsive pendientes (2 filas)

**Edición de rol, 390 × 844:**
- Viewport exacto `{width: 390, height: 844}`; `horizontalOverflow: false` (`scrollWidth === clientWidth === 390`).
- Heading `Roles` visible; controles del formulario visibles: `Back to Roles`, `Add permission`, `Remove` (x3), `Save role`, `Deactivate role`.

**Edición de preset con modal dirty, 1440 × 900:**
- Viewport exacto `{width: 1440, height: 900}`; `horizontalOverflow: false`.
- Modal dirty presente con `Keep editing` y `Discard changes`; bounding box `{x:500, y:15, width:440, height:178, top:15, right:940, bottom:193, left:500}` — completamente dentro del viewport.

| Fila | Resultado | Viewport + overflow | Bounding box del modal | Controles/heading observados |
|---|---|---|---|---|
| Rol/edit 390x844 | PASS | 390x844, overflow false | No aplica | heading `Roles`, Save role, Deactivate role, Back to Roles, permisos |
| Preset/edit dirty 1440x900 | PASS | 1440x900, overflow false | {500,15,440,178} dentro del viewport | Keep editing + Discard changes |

## 7. Control de privacidad

- **Nombres/IDs sanitizados**: PASS — IDs de rol/preset/usuario sustituidos por `<ID>`/`<ROLE_ID>`/`<PRESET_ID>` en este reporte; los nombres de catálogo (`Section Responsible`, `Responsable de Sección`) son datos de negocio, no personales.
- **Sin headers, bodies ni sesión**: PASS — solo método/path/status de Network; no se registran headers, bodies, cookies ni tokens.
- **YAML privado no versionado**: PASS — no se generaron YAML de evidencia (los snapshots de navegación de playwright-cli se generaron solo para localizar refs y no se conservaron).
- **Evidencia revisada**: PASS — PNG de modales revisados por contenido DOM (no contienen datos personales; los modales de edición muestran solo el nombre de catálogo del rol/preset). Nota: el modelo actual no puede inspeccionar píxeles de imagen; la verificación se hizo sobre el texto del diálogo vía DOM, que es el contenido renderizado de la captura.

| Resultado | Nombres/IDs sanitizados | Sin headers, bodies ni sesión | YAML privado no versionado | Evidencia revisada |
|---|---|---|---|---|
| PASS | sí | sí | sí | sí (DOM del modal) |

---

## Cierre

Navegador cerrado al terminar (`playwright-cli close`).

### Plantilla de respuesta final

```text
Issue #82 - evidencia de navegador pendiente
Fecha y entorno sanitizado: 2026-08-14 · Linux · Node v24.19.0 · playwright-cli 0.1.18
Responsable (iniciales, sin nombre privado): —

1. Rutas directas/recarga: PASS - evidencia: 6 rutas; directa y recarga conservan URL/heading; Network solo GET (referencias o detalle), sin mutaciones ni colección en /new.
2. Copia ajustable: PASS - evidencia: URL y _origin con preset (<ID>); borrador idéntico antes/después de recarga; recarga solo GET; Cancel vuelve al detalle del preset.
3. Salida dirty y foco (4 flujos): PASS - evidencia: modal con Keep editing/Discard changes en los 4 flujos; tras Keep foco en Cancel/Back to Roles/Back to Role presets + borrador; tras Discard foco en H1 (Roles/Role presets); capturas nominales issue-82-*-dirty-modal.png.
4. IDs malformados: PASS - evidencia: 5 rutas recuperan a la colección permitida; detailRequestCount: 0 en todas.
5. Paginación fuera de rango: PASS - evidencia: exactamente 2 GET (page=999 y page=1); URL final /access/roles?q=supervisor (página canónica omitida); sin cascada.
6. Responsive pendiente (2 filas): PASS - evidencia: rol/edit 390x844 sin overflow y controles visibles; preset/edit dirty 1440x900 con modal dentro del viewport y ambos botones.
7. Privacidad verificada: PASS - evidencia: IDs sustituidos; solo método/path/status; sin headers/bodies/sesión; sin YAML versionado; modales revisados por DOM.

Conteo: PASS 7 / FAIL 0 / BLOCKED 0 / NOT RUN 0
Veredicto global: PASS
Observaciones: El entorno de playwright-cli obligó a ejecutar cada caso en una sola secuencia encadenada y a reemplazar `new URL()`/`URLSearchParams` por regex en el colector (VM del listener sin esos globales); la evidencia recolectada (método/path/status reales de cada response) no cambia.
```
