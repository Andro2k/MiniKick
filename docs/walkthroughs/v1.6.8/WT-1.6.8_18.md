# Walkthrough Técnico — MiniKick v1.6.8 (Paso 18)

Los iconos de la aplicación pasan a ser los de Lucide (trazo 2) y se nombran como en Lucide. Se retira el pack `outline`, que mezclaba iconos de varios sets.

---

## Novedades

- **Pack `assets/icons/lucide/`:** 79 iconos generados con `project_icon_fetch_tool.py` desde el set `lucide` de Iconify (`24×24`, `fill="none"`, `stroke="currentColor"`, trazo 2), con el `LICENSE` de Lucide (ISC) junto al pack.
- **Nombres de Lucide:** el nombre del archivo es el nombre canónico del icono en Lucide (`settings.svg`, `chevron-down.svg`). Para añadir un icono basta buscarlo en Lucide y ejecutar `python resources/tools/project_icon_fetch_tool.py <nombre>`; sin nombres actualiza todo el pack. Los alias se guardan con su nombre canónico.

## Mejoras

- **Migración de referencias:** 270 referencias en 59 archivos (código, pruebas y `whats_new_service`) pasan del nombre antiguo al de Lucide, verificadas con `project_icon_integrity_tool.py` (0 iconos sin uso y 0 referencias rotas).
- **`frontend/common/icons.py`:** `ACTIVE_ICON_PACK` y `BASE_ICON_PACK` pasan a `lucide`. `radio-dot.svg` (punto relleno del indicador de QSS) pasa a `common/` porque Lucide no tiene equivalente; las marcas `block-*`, las ilustraciones y `logo.svg` siguen en `common/`.
- **`project_icon_fetch_tool.py`:** deja de usar tabla de equivalencias y trabaja con nombres de Lucide.
- **`project_icon_integrity_tool.py`:** solo considera `.svg` y `.ico`, por lo que admite el `LICENSE` del pack.
- **`project_icon_grid_tool.py`:** `OPTICAL_CENTER_EXEMPT` usa `play` (Lucide lo coloca 1u a la derecha a propósito).
- **Iconos de botones:** `configure_icon_only_button` pierde el parámetro `icon_size`, que no tenía efecto tras retirar `setIconSize` (lo marcaba `project_unused_parameter_auditor`). `ModernButton` conserva `icon_size`, que sigue definiendo la resolución del pixmap. Se retira `test_sidebar_and_icon_only_buttons_use_explicit_icon_sizes`: se decidió no restaurar `setIconSize`.
- **Verificación:** `resources/tests` da 423 aprobadas, `project_quality_suite.py --quick` pasa 15 de 16 auditores y el check de cuadrícula analiza 79 iconos con 0 fuera de cuadrícula. Se comparó el sidebar y una fila de botones con el QSS real antes y después.

## Renombres

Los 39 iconos cuyo nombre en Lucide no es el antiguo sin el sufijo `-outline` (los demás solo pierden el sufijo):

| Antes | Lucide |
| --- | --- |
| `alarm-outline` | `alarm-clock` |
| `album-outline` | `disc-album` |
| `alert-circle-outline` | `circle-exclamation-point` |
| `alert-triangle-outline` | `triangle-exclamation-point` |
| `align-left-outline` | `text-align-start` |
| `angles-left-outline` | `chevrons-left` |
| `angles-right-outline` | `chevrons-right` |
| `bolt-circle-outline` | `zap` |
| `browser-code-outline` | `app-window` |
| `carousel-h-outline` | `gallery-horizontal` |
| `carousel-v-outline` | `gallery-vertical` |
| `check-circle-outline` | `circle-check-big` |
| `circle-info-outline` | `info` |
| `code-square-outline` | `square-code` |
| `crosshairs-outline` | `crosshair` |
| `dialog-outline` | `messages-square` |
| `dots-horizontal-outline` | `ellipsis` |
| `edit-outline` | `square-pen` |
| `element-outline` | `layout-dashboard` |
| `emoji-circle-outline` | `smile` |
| `filter-outline` | `funnel` |
| `gear-outline` | `settings` |
| `hashtag-outline` | `hash` |
| `music-notes-outline` | `music` |
| `prism-outline` | `gem` |
| `refresh-outline` | `refresh-cw` |
| `restart-outline` | `rotate-cw` |
| `skip-next-outline` | `skip-forward` |
| `squares-outline` | `squares-unite` |
| `text-outline` | `type` |
| `textalign-center-outline` | `text-align-center` |
| `textalign-justifycenter-outline` | `text-align-justify` |
| `textalign-left-outline` | `text-align-start` |
| `textalign-right-outline` | `text-align-end` |
| `transfer-v-outline` | `arrow-up-down` |
| `treasure-chest-outline` | `package-open` |
| `volume-up-outline` | `volume-2` |
| `webhooks-outline` | `webhook` |
| `widget-add-outline` | `blocks` |

`align-left` y `textalign-left` eran el mismo icono y se fusionan en `text-align-start`.

## Limitaciones conocidas

- La API real de Iconify no estaba accesible desde el entorno de desarrollo; el pack se generó con los datos de `@iconify-json/lucide` (npm, 1.2.155) servidos en local. Conviene ejecutar `python resources/tools/project_icon_fetch_tool.py` (sin nombres) para confirmar que reproduce los mismos archivos.
- Con el tamaño por defecto de Qt (16 px) el trazo 2 equivale a 1.33 px; el aspecto es más fino que con tamaños mayores.
- `smile` y `music` figuran como obsoletos (`hidden`) en esa versión del set y no tienen reemplazo visible; Iconify permite usarlos por nombre.
- Equivalencias por criterio visual y revisables: `bolt-circle` → `zap` (sin círculo), `browser-code` → `app-window` (sin `</>`), `squares` → `squares-unite`, `treasure-chest` → `package-open`, `widget-add` → `blocks`.
- Cambia el aspecto de toda la interfaz; el pack `outline` solo se recupera desde el historial de Git.
- `Frontend Qt Windows` sigue fallando como antes de estos cambios.
