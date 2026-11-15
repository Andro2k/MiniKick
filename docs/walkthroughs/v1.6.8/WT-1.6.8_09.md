# Walkthrough Técnico — MiniKick v1.6.8 (Paso 09)

El `frontend/` adopta la misma convención de nombres que el backend (`<tema>_<rol>.py`), la ventana principal queda agrupada en `window/` y todos los módulos tienen cabecera de ruta y docstring en español.

---

## Novedades

- **40 archivos renombrados o movidos** en `frontend/`. Los imports se reescribieron con un script (absolutos, relativos, strings lazy de los `__init__`, pruebas y `README`), sin ediciones manuales de los llamadores.
- **El sufijo del archivo es el rol de su clase principal.** `window/` pasa de nombres sueltos (`startup`, `rewards`, `tray`…) a `startup_coordinator`, `rewards_handler`, `tray_presenter`, etc.
- **117 módulos con docstring** de una línea en español. Las cabeceras `# frontend\...` ya existían y se conservan (los renombres las actualizan).

## Mejoras

- **`window/`:** `composition`, `shutdown`, `startup`, `wiring`, `navigation` y `updates` pasan a `*_coordinator`; `overlay_events`, `schedule`, `tray` y `whats_new` a `*_presenter`; `media_keys`, `platform_connections` y `rewards` a `*_handler`; `messages` a `messages_router`; `window_state` a `window_state_manager`; `session_metrics` a `session_metrics_tracker`; `integrations_status` a `integrations_protocols`.
- **Raíz de `frontend/`:** `main_window`, `main_window_views`, `recent_redemptions` y `view_prewarmer` se mueven a `window/` como `main_window_core`, `view_factory`, `recent_redemptions_cache` y `view_prewarmer`.
- **`components/`:** `responsive_stack` → `responsive_stack_widget`; `variants_tab_bar` → `variants_tab_bar_card`; `bot_mute`, `chat_display`, `overlay_settings`, `tts_settings` y `player_settings` → `*_panel`; `chatters_table` → `chatters_table_card`; `platform_distribution_ring` → `platform_distribution_ring_widget`; `mockup_helpers` → `mockup_utils`.
- **`components/dialogs/` → `components/dialog_parts/`:** se evita la confusión con `frontend/dialogs/`. Sus cuatro archivos pasan a `draggable_box_widget`, `image_dropzone_widget`, `piper_voice_item_widget` y `severity_card`.
- **Helpers:** `common/gui_bridge`, `linkify`, `markdown` y `qt_debounce` pasan a `*_utils` (esto también evita que `markdown.py` comparta nombre con el paquete `markdown`); `widgets/layout_helpers` pasa a `layout_utils`.
- **Dos puntos que un script de reemplazo de rutas no cubre solo:** el mapa `_EXPORTS` con strings (`".startup"`) de `window/__init__.py` y un `from frontend.common import gui_bridge` dentro de `test_gui_bridge.py`. Se corrigieron y se comprobó cada export lazy (139 en total).
- **`frontend/README.md`:** nueva sección con el sufijo esperado por carpeta.
- **Verificación:** se importan los 310 módulos de `backend`, `frontend` y `bootstrap` con Qt (offscreen) sin fallos, `resources/tests` da 286 aprobadas, `project_quality_suite.py --quick` da 14/14 y `project_file_placement_auditor.py` no reporta violaciones.

## Limitaciones conocidas

- Los nombres de logger (por ejemplo `"minikick.frontend.view_prewarmer"`) no se tocaron.
- `dialogs/splash_screen.py` y `dialogs/update_flow.py` conservan su nombre: el rol (pantalla de inicio, flujo) ya está en él.
- `widgets/` mantiene nombres al estilo de Qt (`flow_layout`, `no_wheel`, `color_picker`).
- El auditor de ubicación solo exige `*_view.py` en `views/` en el frontend; el resto de la convención no se valida automáticamente.
- Siguen existiendo archivos muy grandes (`event_card` con más de 1000 líneas, `theme`, `base_dialog`, `rewards_dialog`, `dashboard_view`); partirlos queda fuera de este paso.
- Los walkthroughs anteriores conservan los nombres antiguos.
