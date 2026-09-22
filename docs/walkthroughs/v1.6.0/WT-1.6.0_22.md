# Walkthrough Técnico — MiniKick v1.6.0 (Entrega WT-1.6.0_22)

> **Resolución de Micro-Ventana Fantasma 'python' (INC-008), Lazy Initialization en NoWheelDateEdit y Herramienta Centralizada `window_audit_manager.py`**

---

## 1. Novedades

* **Herramienta de Auditoría Centralizada `window_audit_manager.py`**:
  - Implementada en [`resources/tools/window_audit_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/window_audit_manager.py).
  - Capacidades clave:
    1. **Auditoría Dinámica (Runtime)**: Ejecuta una instancia de prueba en modo headless/offscreen que audita las 12 vistas principales de la aplicación (`DashboardView`, `ChatView`, `AlertsView`, `WidgetsView`, `SettingsView`, `ScheduleView`, `CommandView`, `TimersView`, `SpamView`, `MusicView`, `RewardsView`, `LogView`) y la secuencia de precalentamiento (`Prewarm`), comprobando la lista de `QApplication.topLevelWidgets()` y detectando cualquier `HWND` nativo con banderas de ventana (`WindowTitleHint`, `WindowCloseButtonHint`), título `python`/`minikick` o visibilidad no esperada.
    2. **Auditoría Estática (AST)**: Inspecciona los 92 archivos fuente de `frontend/` para detectar llamadas de riesgo (como `.calendarWidget()` fuera de su clase base) y widgets de control instanciados sin `parent` explícito.
    3. **Soporte CLI / CI**: Parámetros `--verbose`, `--runtime-only`, `--static-only` y `--json` con códigos de salida normalizados (0 en éxito, 1 ante violaciones críticas).

---

## 2. Mejoras

* **Inicialización Perezosa (Lazy Initialization) en [`NoWheelDateEdit`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/no_wheel.py)**:
  - Se encapsuló la configuración y formateo de texto del calendario (`QCalendarWidget`) dentro del método `_configure_calendar_widget()`.
  - La llamada interna a `super().calendarWidget()` se pospone hasta el momento exacto en que el usuario interactúa con el selector de fecha (vía `mousePressEvent`, `keyPressEvent` o consulta explícita), evitando la creación anticipada de `QCalendarPopup` y `QMenu` durante la carga o precalentamiento de la vista.
* **Reducción de Complejidad Big-O y Carga del SO**:
  - Eliminación de llamadas síncronas bloqueantes a la API de ventanas de Windows (`CreateWindowEx` / `DWM`) durante el precalentamiento en segundo plano de `ScheduleView`.
  - El tiempo de inicialización de `ScheduleFormPanel` se mantiene en $\mathcal{O}(1)$ puro sin efectos secundarios de sistema operativo.
* **Consistencia en la Jerarquía de Widgets (`parent=self`)**:
  - Saneamiento del 100% de advertencias de jerarquía (24 widgets en 7 componentes y 4 vistas):
    - [`frontend/components/chat/bot_mute.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py): `btn_add_bot`, `btn_add_word` vinculados con `parent=self`.
    - [`frontend/components/chat/overlay_settings.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py): `btn_copy_overlay_obs` vinculado con `parent=self`.
    - [`frontend/components/music/commands_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/commands_panel.py): switches de comandos con `parent=self`.
    - [`frontend/components/music/music_settings_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/music_settings_panel.py): `sw_auto_resume`, `sw_media_keys` con `parent=self`.
    - [`frontend/components/music/player_settings.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/player_settings.py): `btn_play_pause`, `btn_skip`, `btn_copy_music_url` con `parent=self`.
    - [`frontend/components/music/stats_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/stats_panel.py): `sw_music_service` con `parent=self`.
    - [`frontend/components/schedule/quick_change_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/quick_change_panel.py): `switch_kick`, `switch_twitch`, `btn_apply` con `parent=self`.
    - [`frontend/views/dashboard_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py): `sw_autostart`, `btn_open_channel` con `parent=self`.
    - [`frontend/views/logs_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/logs_view.py): `combo_date` y botones de acción con `parent=self`.
    - [`frontend/views/rewards_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py): `btn_copy_url` con `parent=self`.
    - [`frontend/views/settings_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py): `combo_browser`, `btn_export`, `btn_import`, `btn_update`, `btn_release_notes`, `btn_feedback` con `parent=self` / `parent=browser_container`.

---

## 3. Correcciones

* **Solución al Incidente INC-008 (Micro-Ventana Fantasma 'python' / 'pyt...')**:
  - **Problema**: Al cabo de ~3.75 segundos del arranque, el precalentador en segundo plano (`_schedule_view_prewarming`) inicializaba `ScheduleView`. En `ScheduleFormPanel`, la llamada ansiosa `cal = self.date_edit.calendarWidget()` forzaba a Qt a crear un `QCalendarPopup` y el menú de navegación de meses con banderas nativas `0x800f009` sin un ancestro visible mapeado en pantalla. Windows DWM asignaba al `HWND` el título de proceso `python` (mostrado como `pyt...` en pantallas compactas) y proyectaba momentáneamente la superficie gris vacía sobre el Dashboard o la vista activa.
  - **Corrección**: Se eliminó la llamada prematura `cal = self.date_edit.calendarWidget()` en `ScheduleFormPanel` y se delegó la configuración a la lógica perezosa de `NoWheelDateEdit`.
* **Registro de Incidencias**:
  - Documentado en [`docs/historial_crashes_y_errores.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/historial_crashes_y_errores.md) con trazabilidad de causa raíz, archivos modificados y pruebas asociadas.

---

## 4. Resultados de Verificación y Validación

1. **Auditor de Ventanas (`window_audit_manager.py`)**:
   - Vistas del sistema auditadas (Runtime): **12 / 12 limpias**.
   - Archivos frontend escaneados (AST): **92 / 92 limpios**.
   - Violaciones críticas (Ghost Windows): **0**.
   - Advertencias de jerarquía / Parent: **0**.
   - Estado: **✅ ESTADO PERFECTO**.
2. **Suite de Pruebas Automatizadas (`pytest`)**:
   - **43 passed** en 2.07s (100% de la suite de pruebas operativa y sin regresiones).
3. **Auditoría de Código Muerto (`dead_code_manager.py`)**:
   - 0 archivos huérfanos, 0 símbolos top-level no usados, 0 imports innecesarios.
4. **Sincronización QSS (`role_manager.py -v`)**:
   - 65 roles definidos / 65 roles en uso (0 faltantes, 0 sin uso).
   - 20 estados definidos / 20 estados en uso (0 faltantes, 0 sin uso).
