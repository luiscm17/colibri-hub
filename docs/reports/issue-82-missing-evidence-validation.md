# Evidencia de cierre pendiente del issue #82

Manual ejecutable para reunir **solo** la evidencia de navegador que aún falta. Las pruebas de implementación y el build ya pasaron: no deben volver a ejecutarse. No se validan backend, issue #84 ni otros escenarios fuera de alcance.

## Resultados y privacidad

| Resultado | Definición |
|---|---|
| PASS | Lo observado coincide con todo lo esperado y la evidencia requerida está registrada. |
| FAIL | Al menos una observación contradice lo esperado; registrar la diferencia. |
| BLOCKED | Una dependencia del entorno impide completar el caso; identificarla sin exponer datos privados. |
| NOT RUN | El caso no se ejecutó; registrar el motivo. |

- Sustituir nombres visibles e identificadores de usuarios por `<USER>` y `<ID>` antes de pegar evidencia.
- Conservar solo URL sanitizada y método/ruta/estado de Network. No registrar headers, bodies, cookies, tokens ni datos de sesión.
- No versionar YAML que contenga nombres personales o nombres visibles. Se permite pegar en este archivo la salida sanitizada de los comandos.
- En los comandos, definir `BASE_URL` con el origen local autorizado y reemplazar `<ROLE_ID>`, `<PRESET_ID>` y `<ref>` con valores del entorno. No pegar esos valores en el reporte final.

Preparación mínima:

```bash
playwright-cli open "$BASE_URL"
playwright-cli resize 1440 900
```

Para cada bloque de Network, instalar el colector antes de navegar:

```bash
playwright-cli run-code "async page => { page.__issue82 = []; page.on('response', response => { const url = new URL(response.url()); if (url.pathname.startsWith('/api/')) page.__issue82.push({ method: response.request().method(), path: url.pathname + url.search, status: response.status() }); }); }"
```

Leer URL y Network sin contenido sensible:

```bash
playwright-cli eval "location.pathname + location.search"
playwright-cli run-code "async page => console.log(JSON.stringify(page.__issue82, null, 2))"
```

## 1. Rutas directas y recarga

Ejecutar cada fila aplicable. Antes de cada ruta, vaciar el colector; después de `goto` y después de `reload`, registrar por separado URL sanitizada y Network.

```bash
playwright-cli run-code "async page => { page.__issue82 = []; }"
playwright-cli goto "$BASE_URL/access/roles/new"
playwright-cli find "Create role"
playwright-cli eval "location.pathname + location.search"
playwright-cli run-code "async page => console.log(JSON.stringify(page.__issue82, null, 2))"
playwright-cli run-code "async page => { page.__issue82 = []; }"
playwright-cli reload
playwright-cli find "Create role"
playwright-cli eval "location.pathname + location.search"
playwright-cli run-code "async page => console.log(JSON.stringify(page.__issue82, null, 2))"
```

Repetir la secuencia cambiando ruta y encabezado:

| Ruta sanitizada | Encabezado semántico esperado |
|---|---|
| `/access/presets/new` | `Create preset` |
| `/access/roles/<ROLE_ID>` | detalle del rol |
| `/access/roles/<ROLE_ID>/edit` | `Edit role` |
| `/access/presets/<PRESET_ID>` | detalle del preset |
| `/access/presets/<PRESET_ID>/edit` | `Edit preset` |

Esperado: la ruta directa y la recarga conservan el flujo; la evidencia identifica método, path y status de cada request y no muestra mutaciones.

| Ruta | Directa: resultado | Directa: URL + Network | Recarga: resultado | Recarga: URL + Network |
|---|---|---|---|---|
| Roles/new |  |  |  |  |
| Presets/new |  |  |  |  |
| Rol/detalle |  |  |  |  |
| Rol/edición |  |  |  |  |
| Preset/detalle |  |  |  |  |
| Preset/edición |  |  |  |  |

## 2. Copia ajustable de preset

Desde el detalle de un preset, activar `Start adjustable draft`. Usar `snapshot` solo para obtener refs; no conservar el YAML sin sanitizar.

```bash
playwright-cli snapshot
playwright-cli click <ref-Start-adjustable-draft>
playwright-cli eval "(() => { const u = new URL(location.href); const clean = value => value && value.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi, '<ID>'); return clean(u.pathname + u.search); })()"
playwright-cli eval "(() => { const raw = new URL(location.href).searchParams.get('_origin'); return raw && raw.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi, '<ID>'); })()"
playwright-cli run-code "async page => console.log(JSON.stringify({ code: await page.getByRole('textbox', { name: 'Role code' }).inputValue(), name: await page.getByRole('textbox', { name: 'Role name' }).inputValue(), description: await page.getByRole('textbox', { name: 'Description' }).inputValue(), permissions: await page.getByRole('button', { name: /^Remove / }).evaluateAll(nodes => nodes.map(node => node.getAttribute('aria-label')?.replace(/^Remove /, ''))) }, null, 2))"
playwright-cli run-code "async page => { page.__issue82 = []; }"
playwright-cli reload
playwright-cli find "Create role"
playwright-cli eval "location.pathname + location.search.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi, '<ID>')"
playwright-cli run-code "async page => console.log(JSON.stringify({ code: await page.getByRole('textbox', { name: 'Role code' }).inputValue(), name: await page.getByRole('textbox', { name: 'Role name' }).inputValue(), description: await page.getByRole('textbox', { name: 'Description' }).inputValue(), permissions: await page.getByRole('button', { name: /^Remove / }).evaluateAll(nodes => nodes.map(node => node.getAttribute('aria-label')?.replace(/^Remove /, ''))) }, null, 2))"
playwright-cli run-code "async page => console.log(JSON.stringify(page.__issue82, null, 2))"
playwright-cli snapshot
playwright-cli click <ref-Cancel>
playwright-cli eval "location.pathname + location.search.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi, '<ID>')"
```

Esperado: URL y `_origin` contienen el preset sanitizado; el snapshot textual del borrador coincide antes y después de recargar; la recarga hace solo GET de reconstrucción y ninguna mutación; `Cancel` vuelve al detalle del preset de origen.

| Resultado | URL + `_origin` sanitizados | Borrador antes/después | GET de recarga sin mutación | Destino de Cancel |
|---|---|---|---|---|
|  |  |  |  |  |

## 3. Salida con cambios y foco

Ejecutar en los cuatro flujos. Modificar un campo, activar `Cancel` en creación o `Back to Roles` / `Back to Role presets` en edición, y obtener una captura nominal del modal:

```bash
playwright-cli snapshot
playwright-cli fill <ref-editable-field> "Draft change"
playwright-cli click <ref-Cancel-or-Back>
playwright-cli find "Discard changes"
playwright-cli snapshot
playwright-cli screenshot <ref-dirty-dialog> --filename=issue-82-<flow>-dirty-modal.png
playwright-cli click <ref-Keep-editing>
playwright-cli eval "JSON.stringify({ tag: document.activeElement?.tagName, role: document.activeElement?.getAttribute('role'), name: document.activeElement?.getAttribute('aria-label') || document.activeElement?.textContent?.trim() })"
```

Reabrir el modal sin recargar y descartar:

```bash
playwright-cli click <ref-Cancel-or-Back>
playwright-cli find "Discard changes"
playwright-cli snapshot
playwright-cli click <ref-Discard-changes>
playwright-cli eval "JSON.stringify({ url: location.pathname + location.search, tag: document.activeElement?.tagName, text: document.activeElement?.textContent?.trim() })"
```

Esperado: el modal expone los botones semánticos `Keep editing` y `Discard changes`. Tras Keep, el foco vuelve a `Cancel`, `Back to Roles` o `Back to Role presets`, según el flujo, y el cambio sigue visible. Tras Discard, navega a la colección y el foco queda en el heading `Roles` o `Role presets`.

| Flujo | Resultado | Captura nominal del modal | activeElement tras Keep + borrador | activeElement tras Discard + destino |
|---|---|---|---|---|
| Rol/create |  |  |  |  |
| Rol/edit |  |  |  |  |
| Preset/create |  |  |  |  |
| Preset/edit |  |  |  |  |

## 4. Identificadores malformados

Vaciar Network antes de cada navegación y conservar el resultado completo sanitizado:

```bash
playwright-cli run-code "async page => { page.__issue82 = []; }"
playwright-cli goto "$BASE_URL/access/roles/not-a-uuid"
playwright-cli eval "location.pathname + location.search"
playwright-cli run-code "async page => console.log(JSON.stringify({ detailRequestCount: page.__issue82.filter(item => item.path.includes('not-a-uuid')).length, requests: page.__issue82 }, null, 2))"
```

Repetir con `/access/roles/not-a-uuid/edit`, `/access/presets/not-a-uuid`, `/access/presets/not-a-uuid/edit` y `/access/users/not-a-uuid`.

Esperado: URL retenida en la colección correspondiente y `detailRequestCount: 0`; no existe request de detalle para el ID malformado.

| Ruta | Resultado | URL retenida sanitizada | Lista Network | Conteo de detalle |
|---|---|---|---|---|
| Rol/detalle |  |  |  |  |
| Rol/edición |  |  |  |  |
| Preset/detalle |  |  |  |  |
| Preset/edición |  |  |  |  |
| Usuario/detalle |  |  |  |  |

## 5. Paginación fuera de rango

Usar un criterio sanitizado cuyo total sea positivo y cuya página solicitada exceda la última. El colector debe estar vacío antes de navegar.

```bash
playwright-cli run-code "async page => { page.__issue82 = []; }"
playwright-cli goto "$BASE_URL/access/roles?q=<SANITIZED_QUERY>&page=999"
playwright-cli eval "location.pathname + location.search"
playwright-cli run-code "async page => { const requests = page.__issue82.filter(item => item.method === 'GET' && item.path.startsWith('/api/v1/access/roles?')); console.log(JSON.stringify({ count: requests.length, requests }, null, 2)); }"
```

Esperado: lista y conteo muestran exactamente dos GET: página inicial `999` y última página calculada como `max(1, ceil(total/page_size))`; URL final conserva `q` y usa la última página, omitiendo `page=1` si es el valor canónico; no hay páginas intermedias ni cascada.

| Resultado | Total/page_size/última calculada | Lista + conteo de requests | URL/query final | Evidencia de ausencia de cascada |
|---|---|---|---|---|
|  |  |  |  |  |

## 6. Filas responsivas pendientes

Validar únicamente estas dos filas. Para overflow y viewport:

```bash
playwright-cli eval "JSON.stringify({ viewport: { width: innerWidth, height: innerHeight }, document: { scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }, horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth })"
```

**Edición de rol, 390 x 844:**

```bash
playwright-cli resize 390 844
playwright-cli goto "$BASE_URL/access/roles/<ROLE_ID>/edit"
playwright-cli find "Edit role"
playwright-cli eval "JSON.stringify({ viewport: { width: innerWidth, height: innerHeight }, document: { scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }, horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth })"
```

**Edición de preset con modal dirty, 1440 x 900:**

```bash
playwright-cli resize 1440 900
playwright-cli goto "$BASE_URL/access/presets/<PRESET_ID>/edit"
playwright-cli find "Edit preset"
playwright-cli snapshot
playwright-cli fill <ref-editable-field> "Draft change"
playwright-cli click <ref-Back-to-Role-presets>
playwright-cli find "Discard changes"
playwright-cli snapshot --boxes
playwright-cli eval "JSON.stringify({ viewport: { width: innerWidth, height: innerHeight }, document: { scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }, horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth })"
playwright-cli eval "JSON.stringify(document.querySelector('[role=dialog]')?.getBoundingClientRect().toJSON())"
```

Esperado: viewport exacto, `horizontalOverflow: false`, controles visibles; en preset/edit el bounding box del modal queda completamente dentro de `1440 x 900` y el diálogo contiene `Keep editing` y `Discard changes`.

| Fila | Resultado | Viewport + overflow | Bounding box del modal | Controles/heading observados |
|---|---|---|---|---|
| Rol/edit 390x844 |  |  | No aplica |  |
| Preset/edit dirty 1440x900 |  |  |  |  |

## 7. Control de privacidad

Antes del cierre, revisar toda la evidencia pegada y cualquier archivo generado. Sustituir nombres visibles e IDs, eliminar headers, bodies y datos de sesión, y no agregar YAML con nombres personales o visibles.

| Resultado | Nombres/IDs sanitizados | Sin headers, bodies ni sesión | YAML privado no versionado | Evidencia revisada |
|---|---|---|---|---|
|  |  |  |  |  |

## Cierre

Cerrar el navegador al terminar:

```bash
playwright-cli close
```

### Plantilla de respuesta final

```text
Issue #82 - evidencia de navegador pendiente
Fecha y entorno sanitizado:
Responsable (iniciales, sin nombre privado):

1. Rutas directas/recarga: [PASS|FAIL|BLOCKED|NOT RUN] - evidencia:
2. Copia ajustable: [PASS|FAIL|BLOCKED|NOT RUN] - evidencia:
3. Salida dirty y foco (4 flujos): [PASS|FAIL|BLOCKED|NOT RUN] - evidencia:
4. IDs malformados: [PASS|FAIL|BLOCKED|NOT RUN] - evidencia:
5. Paginación fuera de rango: [PASS|FAIL|BLOCKED|NOT RUN] - evidencia:
6. Responsive pendiente (2 filas): [PASS|FAIL|BLOCKED|NOT RUN] - evidencia:
7. Privacidad verificada: [PASS|FAIL|BLOCKED|NOT RUN] - evidencia:

Conteo: PASS __ / FAIL __ / BLOCKED __ / NOT RUN __
Veredicto global:
Observaciones:
```
