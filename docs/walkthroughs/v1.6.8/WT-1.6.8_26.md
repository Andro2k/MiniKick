# Walkthrough Técnico — MiniKick v1.6.8 (Paso 26)

El frontend se hizo más responsivo tomando como referencia el sistema de layout de `sonorahq/sonora` (rama `main`): una sola escalera de anchos, un tamaño mínimo de ventana, un sidebar que se adapta al ancho y una regla de auditoría que impide volver a los números sueltos. Antes, 9 umbrales distintos (480, 620, 650, 680, 900, 950, 1000, 1080 y 1280 px) estaban repetidos en 10 archivos, la ventana no tenía tamaño mínimo y el sidebar solo cambiaba de forma manual.

---

## Mejoras

### Capa `frontend/common`

- **Escalera `Room`** (`layout_utils.py`): `TIGHT` 0, `SNUG` 480, `ROOMY` 650, `WIDE` 950, `VAST` 1100 y `HUGE` 1280 px. Se usa como `Room.of(width).fits(Room.WIDE)` o `.below(...)`. Se exporta desde `frontend.common`.
- **Tokens de ventana** (`theme.py`): `Size.WINDOW_MIN_WIDTH = 900` y `Size.WINDOW_MIN_HEIGHT = 600`.

### Capa `frontend/views` y `frontend/components`

- Los 17 literales `width < N` de alerts, chat, music, schedule, stats y dashboard (y sus componentes) pasaron a `Room`. Cada vista cambia de layout como máximo 50 px antes o después que hasta ahora:

| Antes (px) | Ahora |
| --- | --- |
| 480 | `SNUG` |
| 620, 650, 680 | `ROOMY` (650) |
| 900, 950, 1000 | `WIDE` (950) |
| 1080 | `VAST` (1100) |
| 1280 | `HUGE` (1280, sin cambio) |

### Capa `frontend/window` y `frontend/navigation`

- **Tamaño mínimo:** `MainWindowCore._init_geometry()` aplica `setMinimumSize(900, 600)` junto con el tamaño inicial de 1200×800. Con el sidebar expandido (230 px) quedan 670 px de contenido, escalón `ROOMY` o superior.
- **Sidebar adaptable:** `Sidebar.fit_to_window(ancho)` colapsa la barra por debajo de 1100 px (`Room.VAST`) y restaura la elección del usuario al ensancharse. Solo actúa al cruzar el umbral, así que un clic manual dentro de una ventana estrecha se respeta hasta el siguiente cruce. Decide por el ancho de la ventana y no del contenido, para no entrar en bucle con el ancho del propio sidebar. `toggle_sidebar` recuerda la elección manual y delega en `_set_expanded`, que admite cambio sin animación. `MainWindowCore.resizeEvent` lo invoca. Al mínimo de 900 px el contenido pasa de 670 a 840 px.

### Capa `resources`

- **Regla `HARDCODED_BREAKPOINT`** en `frontend_design_token_auditor.py`: con `ast` detecta comparaciones de un ancho (`width`, `self.width()`, `w`) contra un entero de 300 o más y sugiere `Room`. Las comparaciones con constantes pequeñas, con otras variables o sin relación con el ancho no se marcan. El mensaje de éxito conserva "Cero colores" para el evaluador de `project_quality_suite.py`.

## Archivos afectados

- `frontend/common/layout_utils.py` (nuevo), `frontend/common/__init__.py`, `frontend/common/theme.py` (parches `0001` y `0002`).
- `frontend/views/{alerts,chat,dashboard,music,schedule,stats}_view.py` y `frontend/components/{alerts/event_card,music/stats_panel,schedule/quick_change_panel,stats/chatters_table_card}.py` (parche `0001`).
- `frontend/window/main_window_core.py` (parches `0002` y `0003`), `frontend/navigation/sidebar_component.py` (parche `0003`).
- `resources/tools/frontend_design_token_auditor.py` (parche `0004`).
- Pruebas nuevas: `test_layout_room.py` (14), `test_sidebar_auto_collapse.py` (4), `test_design_token_auditor.py` (10) y una prueba más en `test_main_window_core.py` (parches `0001` a `0004`).

## Verificación

| Comprobación | Resultado |
| --- | --- |
| Pruebas de `Room`, ventana, sidebar, dashboard y auditor | 47 pasan |
| Redimensionado de 400 a 1400 px de dashboard, stats, chat, schedule, alerts y music | Sin errores |
| `project_quality_suite.py --quick` | Mismo resultado que antes de los cambios: `Frontend Design Tokens` en PASS y dos fallas previas (`Frontend QSS Roles` y `Frontend Qt Windows`), no relacionadas |
| `git am` de cada parche sobre un clon limpio de `release/v1.6.8` | Aplica sin conflictos |
| Prueba visual en la app real (colapso del sidebar, animación y badges entre 900 y 1200 px) | Pendiente |
