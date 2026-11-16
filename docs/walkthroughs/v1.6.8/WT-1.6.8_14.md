# Walkthrough Técnico — MiniKick v1.6.8 (Paso 14)

Los iconos pasan a organizarse en packs (referencia: `assets/icons` de sonora) y se añade una herramienta que mide y normaliza su cuadrícula, para que todos queden centrados y con el mismo lienzo.

---

## Novedades

- **Packs de iconos:** `assets/icons/outline/` (81 iconos tematizables) y `assets/icons/common/` (11 marcas e ilustraciones con su propio lienzo). `icon.ico` se queda en `assets/icons/` por ser el icono de la aplicación y no de la interfaz.
- **`project_icon_grid_tool.py`:** mide el área real que ocupa cada glifo con `QSvgRenderer` (cuadrícula 24u, área útil 22u, tolerancia 0.5u). `--check` falla si hay iconos descentrados, fuera del área útil o con lienzo distinto de 24×24; `--fix` los reescribe envolviendo el contenido en un `<g transform>` sin editar la geometría. Es idempotente.
- **Auditoría "Project Icon Grid"** registrada en `project_quality_suite.py`.

## Mejoras

- **Resolución por packs (`frontend/common/icons.py`):** `resolve_icon_path` busca en pack activo → `common` → pack base → raíz de `icons/`. Las constantes `ACTIVE_ICON_PACK`, `SHARED_ICON_PACK` y `BASE_ICON_PACK` definen la cadena; los nombres de archivo no cambian, así que los llamadores existentes siguen funcionando.
- **Llamadores:** los 8 diálogos pasan el nombre del icono en lugar de la ruta `icons/...`; `table_widget.py` y `theme.py` usan `resolve_icon_path`.
- **`project_icon_integrity_tool.py`:** recorre los packs y sus subcarpetas; el borrado de iconos sin uso elimina todas las copias.
- **Cuadrícula normalizada:** 9 iconos se recentran o reescalan (bot, calendar-days y prism descentrados hasta 1.3u; las 4 flechas chevron 0.8u; clock y browser-code excedían las 22u). Los 81 pasan a `width`/`height` 24 con `viewBox` 24 (antes 64, `1em`, 24 o ausente).
- **Verificación:** 72 de los 81 iconos renderizan píxel a píxel igual que antes y solo cambian los 9 ajustados. El tamaño propio del SVG no altera el render en QSS: un `QCheckBox::indicator` con `image` da el mismo resultado con `width` 64, 24, `1em` o ausente. `resources/tests` da 360 aprobadas (14 nuevas) y `project_quality_suite.py --quick` pasa 14 de 15 auditores.

## Limitaciones conocidas

- `Frontend Qt Windows` (`frontend_qt_window_lifecycle_auditor.py`) falla también sin estos cambios.
- En un entorno sin pantalla, `resources/tests/test_bug_report_view.py` puede cerrar Python con un segmentation fault cuando cambia el conjunto de pruebas recolectadas: la vista creada en `_setup` se destruye mientras `FadingScrollArea` aún procesa un evento de pintado. Ocurre con o sin estos cambios y no se corrigió aquí.
- Con un solo pack, `ACTIVE_ICON_PACK` y `BASE_ICON_PACK` valen lo mismo; el cambio de pack en tiempo de ejecución no está implementado (las rutas de `theme.py` se calculan al importar).
- Para clock y browser-code el reescalado fino (6 % y 2 %) adelgaza ligeramente el trazo; es el costo de respetar el área útil.
- Los SVG de `common/` (ilustraciones de 1000u, `youtube.svg`, `logo.svg`) no se normalizan.
- Pendiente (punto 3): script tipo `fetch-icons` con tabla de equivalencias desde Iconify.
