# 🛡️ Historial Maestro de Crashes, Excepciones y Correcciones — MiniKick

> **Documento de Referencia y Trazabilidad de Errores**  
> Este documento centraliza el registro histórico de incidentes críticos, fallos fatales, excepciones y bloqueos reportados por usuarios o descubiertos en telemetría/logs.  
> **Propósito**: Permitir al equipo de desarrollo y asistentes de IA verificar de inmediato ($\mathcal{O}(1)$) si un fallo reportado ya fue diagnosticado y solventado, en qué archivo/línea reside la solución y qué prueba automatizada garantiza su estabilidad.

---

## 📋 Índice Rápido de Incidentes

| ID | Incidente / Error | Reporte de Origen | Versión Reportada | Estado | Módulo / Archivo Afectado | Versión / WT Fix |
|---|---|---|---|---|---|---|
| **INC-001** | `TypeError: ToastManager.show_toast() got an unexpected keyword argument 'role'` | `minikick_crash_DeyDeyLove_v1.5.9.log` / `minikick_JosueGMN_v1.5.9.log` | v1.5.9 | `✅ Solventado` | `backend/controllers/widgets_controller.py`, `frontend/navigation/toast_component.py` | v1.5.9 (`WT-1.5.9_35`) |
| **INC-002** | `ConnectionResetError: [WinError 10054]` (Pérdida de mensajes en `KickAPIClient`) | `minikick_crash_DeyDeyLove_v1.5.9.log` | v1.5.9 | `✅ Solventado` | `backend/providers/chat/kick_provider.py` | v1.6.0 (`WT-1.6.0_12`) |
| **INC-003** | `sqlite3.OperationalError: database is locked` en `ScheduleWorker` | `minikick_crash_DeyDeyLove_v1.5.9.log` | v1.5.9 | `✅ Solventado` | `backend/services/schedule/schedule_service.py`, `backend/workers/schedule_worker.py`, `backend/database/database_manager.py` | v1.6.0 (`WT-1.6.0_12`) |
| **INC-004** | `Windows fatal exception: access violation` en Garbage Collector / `yt_dlp` | `minikick_crash_DeyDeyLove_v1.5.9.log` | v1.5.9 (Dump 15/09) | `ℹ️ Mitigado / Monitoreado` | `backend/workers/music_worker.py` | CPython / yt-dlp low-level |
| **INC-005** | Reseteo a valores por defecto en Overlay de Chat OBS (`chat.html`) al arrancar la app | Reporte de Usuario / Feedback v1.6.0 | v1.6.0 | `✅ Solventado` | `backend/services/chat/chat_service.py`, `backend/controllers/chat_controller.py` | v1.6.0 (`WT-1.6.0_14`) |
| **INC-006** | Ocultamiento indebido de tablas y visualización errónea del estado vacío (Empty State de creación) al filtrar 0 elementos | Reporte de Usuario / Feedback v1.6.0 | v1.6.0 | `✅ Solventado` | `frontend/widgets/table_widget.py`, `frontend/views/commands_view.py`, `frontend/views/rewards_view.py`, `frontend/components/schedule/schedule_table_panel.py` | v1.6.0 (`WT-1.6.0_21`) |
| **INC-007** | `RuntimeError: libshiboken: Internal C++ object (PySide6.QtWidgets.QWidget) already deleted` en `ModernTableCard.resizeEvent` | Log de Usuario `minikick.log` (Línea 794) | v1.6.0 | `✅ Solventado` | `frontend/widgets/table_widget.py`, `frontend/components/music/queue_panel.py` | v1.6.0 (`WT-1.6.0_21`) |
| **INC-008** | Micro-ventana fantasma ('python' / 'pyt...') proyectada en segundo plano por precalentamiento prematuro de `QCalendarPopup` y falta de `parent` | Captura de Evidencia de Usuario / minikick.log | v1.6.0 | `✅ Solventado` | `frontend/widgets/no_wheel.py`, `frontend/components/schedule/schedule_form_panel.py`, `frontend/views/schedule_view.py`, `frontend/views/dashboard_view.py`, `frontend/components/dashboard/platform_card.py` | v1.6.0 (`WT-1.6.0_22`) |
| **INC-009** | `TypeError: TranslationService.get() got an unexpected keyword argument 'version'` en arranque de `SystemTrayManager` | Log de Usuario `minikick.log` (Línea 2397) | v1.6.0 | `✅ Solventado` | `backend/services/system/translation_service.py`, `frontend/navigation/tray_menu_component.py` | v1.6.0 (`WT-1.6.0_23`) |
| **INC-010** | `HTTP Error 414: URI Too Long` en `GiphyService` e Inclusión Indebida de Bots (`@MiniKick`) en Top Chatters | Log de Usuario `minikick.log` (Línea 555) / Feedback v1.6.0 | v1.6.0 | `✅ Solventado` | `backend/services/chat/giphy_service.py`, `backend/controllers/chat_controller.py`, `backend/controllers/widgets_controller.py`, `backend/handlers/spam_handler.py` | v1.6.0 (`WT-1.6.0_25`) |
| **INC-011** | Recuadros blancos y popups desalineados en Windows Light Theme (`SearchableComboBox`, `VariableTextEdit`, `QCalendarWidget`) | Capturas de Evidencia de Usuario / Feedback v1.6.0 | v1.6.0 | `✅ Solventado` | `frontend/common/theme.py`, `main.py`, `frontend/widgets/searchable_combo_box.py`, `frontend/widgets/controls_widget.py`, `frontend/widgets/no_wheel.py` | v1.6.0 (`WT-1.6.0_33`) |

---

## 🔍 Detalle Técnico por Incidente

---

### INC-001: Crash Fatal al Reiniciar Top Chatters (`TypeError` en `show_toast`)

* **Estado**: `✅ Solventado`
* **Severidad**: **CRÍTICA** (Cierre abrupto de la aplicación / Fatal Crash Handler activado).
* **Reportes Asociados**:
  - `minikick_crash_DeyDeyLove_v1.5.9.log` (Línea 3469)
  - `minikick_JosueGMN_v1.5.9.log`
* **Fecha y Versión del Fallo**: 2026-09-18 en MiniKick `v1.5.9`.
* **Traza de la Excepción**:
  ```text
  [CRITICAL] [FATAL CRASH] Unhandled exception caught by global excepthook:
  Traceback (most recent call last):
    File "backend\controllers\widgets_controller.py", line 696, in handle_chatters_reset
  TypeError: ToastManager.show_toast() got an unexpected keyword argument 'role'
  ```
* **Causa Raíz**:
  En la vista de Widgets, al pulsar el botón **Reiniciar** del ranking de Top Chatters, `WidgetsController.handle_chatters_reset` invocaba `self.toast.show_toast(self.i18n.get("widgets.chatters.reset_success"), role="success")`.
  En `v1.5.9`, la firma de `ToastManager.show_toast` esperaba el parámetro `state: str` y no aceptaba `role` ni `**kwargs`, provocando un `TypeError` fatal que interrumpía el `QEventLoop` de Qt.
* **Archivos y Líneas Modificadas**:
  1. [`backend/controllers/widgets_controller.py:L694-L703`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py#L694-L703):
     - Se corrigió la invocación para pasar los parámetros explícitos requeridos:
       ```python
       def handle_chatters_reset(self):
           self.reset_chatters_counts()
           if self.toast:
               self.toast.show_toast(
                   title=self.i18n.get("widgets.chatters.title"),
                   message=self.i18n.get("widgets.chatters.reset_success"),
                   state="success",
                   tag="widget_chatters_reset"
               )
       ```
  2. [`frontend/navigation/toast_component.py:L148-L151`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py#L148-L151):
     - Blindaje defensivo en la firma: `show_toast(self, title: str, message: str = "", state: str = "success", duration: int = 3500, tag: str = "", **kwargs)`.
     - Mapeo retrocompatible automático de `role` hacia `state` y absorción de `**kwargs` para prevenir cualquier crash futuro por invocaciones legacy.
* **Prueba Automatizada de Cobertura**:
  - `resources/tests/backend/controllers/test_chatters_widget.py` (`test_handle_chatters_reset_from_ui`)
  - `resources/tests/frontend/navigation/test_toast_and_widget_sync.py` (`test_toast_manager_handles_backward_compatible_kwargs_and_role`)
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.5.9/WT-1.5.9_35.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.5.9/WT-1.5.9_35.md) (Commit `1dbc269`).

---

### INC-002: Pérdida Silenciosa de Mensajes del Bot por Desconexión TCP (`ConnectionResetError 10054`)

* **Estado**: `✅ Solventado`
* **Severidad**: **ALTA** (Mensajes de timers y respuestas a comandos descartados en silencio sin llegar al chat).
* **Reportes Asociados**:
  - `minikick_crash_DeyDeyLove_v1.5.9.log` (8 incidencias: 12:35, 12:47, 12:59, 13:05, 13:20, 13:34, 13:48, 14:36)
* **Fecha y Versión del Fallo**: 2026-09-18 en MiniKick `v1.5.9`.
* **Traza del Error**:
  ```text
  [ERROR] [KickAPI] Error posting chat message: ('Connection aborted.', ConnectionResetError(10054, 'Se ha forzado la interrupción de una conexión existente por el host remoto', None, 10054, None))
  ```
* **Causa Raíz**:
  `KickAPIClient` utiliza un pool de conexiones persistentes (HTTP Keep-Alive con `cloudscraper` / `requests.Session`). Cuando transcurren varios minutos sin enviar mensajes al chat (por ejemplo, intervalos de 10 a 15 minutos entre timers), Cloudflare o los balanceadores de Kick cierran silenciosamente el socket TCP remoto inactivo.
  Al intentar reutilizar el socket cerrado, el sistema operativo en Windows genera `WSAECONNRESET (10054)`. Como no existía lógica de reintento automático ante socket stale, la petición fallaba y el mensaje se perdía definitivamente.
* **Archivos y Líneas Modificadas**:
  1. [`backend/providers/chat/kick_provider.py:L69-L87`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_provider.py#L69-L87):
     - Se encapsuló la petición en `KickAPIClient._request` bajo un bucle de reintento transparente (`max_attempts = 2`).
     - Se capturan `(requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError, ConnectionResetError)`.
     - Ante desconexión, se cierra la sesión contaminada (`self.scraper.close()`), se genera una sesión fresca con `ScraperFactory.create()` y se reintenta inmediatamente en $< 100\text{ ms}$.
* **Prueba Automatizada de Cobertura**:
  - `resources/tests/test_network_and_db_resiliency.py` (`test_kick_api_client_reconnects_on_connection_reset_10054` y `test_kick_api_client_handles_persistent_network_error`)
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_12.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_12.md).

---

### INC-003: Excepciones por Bloqueo de Base de Datos (`database is locked`) en `ScheduleWorker`

* **Estado**: `✅ Solventado`
* **Severidad**: **MEDIA** (Fallo en la verificación periódica de horarios por contención en SQLite).
* **Reportes Asociados**:
  - `minikick_crash_DeyDeyLove_v1.5.9.log` (Líneas 292-293)
* **Fecha y Versión del Fallo**: 2026-09-18 en MiniKick `v1.5.9`.
* **Traza del Error**:
  ```text
  [2026-09-18 12:25:07] [ERROR] [ScheduleWorker] Error checking schedules: database is locked
  [2026-09-18 12:25:17] [ERROR] [ScheduleWorker] Error checking schedules: database is locked
  ```
* **Causa Raíz**:
  `ScheduleWorker` ejecutaba una consulta SQLite (`SELECT * FROM stream_schedules`) en segundo plano **cada 1 segundo (1000 ms)** ininterrumpidamente (3,600 queries/hora). Paralelamente, el hilo principal y otros workers escribían ráfagas intensas en SQLite (logs de sistema, eventos de chat, transiciones de spam).
  Además, `DatabaseManager.get_connection()` sobrescribía el timeout con `PRAGMA busy_timeout=5000` (5 segundos). Si una transacción o checkpoint de WAL tardaba más de 5 segundos, la consulta del schedule abortaba por contención.
* **Archivos y Líneas Modificadas**:
  1. [`backend/services/schedule/schedule_service.py:L227-L260`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/schedule/schedule_service.py#L227-L260):
     - Se implementó un **In-Memory Cache $\mathcal{O}(1)$** (`_schedules_cache`) protegido por `threading.Lock`.
     - `get_all_schedules(force_reload=False)` entrega copias en memoria RAM sin acceder al disco.
     - Se implementó invalidación atómica (`invalidate_schedules_cache()`) en `save_schedule()`, `delete_schedule()`, `toggle_schedule()` y `mark_schedule_executed()`.
  2. [`backend/workers/schedule_worker.py:L60-L65`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/schedule_worker.py#L60-L65):
     - El worker ahora consume el caché en memoria $\mathcal{O}(1)$ y delega a `self.service.mark_schedule_executed(...)` en lugar de acceder a la capa de base de datos directamente (SoR).
  3. [`backend/database/database_manager.py:L68-L70`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/database_manager.py#L68-L70):
     - Se aumentó `PRAGMA busy_timeout=30000` (30 segundos) y el timeout de conexión a `30.0` segundos para absorber picos de escritura concurrentes.
* **Prueba Automatizada de Cobertura**:
  - `resources/tests/test_network_and_db_resiliency.py` (`test_schedule_service_in_memory_caching_and_invalidation` y `test_database_manager_busy_timeout_setting`)
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_12.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_12.md).

---

### INC-004: Violación de Acceso Nativo en Garbage Collection / `yt_dlp`

* **Estado**: `ℹ️ Mitigado / Monitoreado`
* **Severidad**: **MEDIA** (Crash nativo CPython durante recolección cíclica de basura).
* **Reportes Asociados**:
  - `minikick_crash_DeyDeyLove_v1.5.9.log` (Dump de Faulthandler del 2026-09-15)
* **Traza de la Excepción**:
  ```text
  Windows fatal exception: access violation
  Current thread 0x000014c0 [YouTubeResolveWorker] (most recent call first):
    Garbage-collecting
    File "urllib\parse.py", line 997 in quote_from_bytes
    File "yt_dlp\utils\_utils.py", line 2619 in update_url
    File "backend\workers\music_worker.py", line 122 in run
  ```
* **Causa Raíz**:
  Colisión en el Garbage Collector cíclico de Python 3.14 (build pre-release) al liberar estructuras de extensiones C de sockets/urllib durante la ejecución concurrente en hilos secundarios de `YoutubeDL`.
* **Acción de Mitigación**:
  En `backend/workers/music_worker.py`, las opciones de extracción y aislamiento de sesión se ejecutan con context managers acotados (`with yt_dlp.YoutubeDL(...) as ydl:`) y reintentos con backoff exponencial.

---

### INC-005: Reseteo a Valores por Defecto en Overlay de Chat OBS (`chat.html`) al Arrancar MiniKick

* **Estado**: `✅ Solventado`
* **Severidad**: **MEDIA** (Pérdida de presentación visual personalizada: tema, tamaño de fuente, desvanecimiento y orientación volvían a defaults en OBS tras reiniciar la app).
* **Reportes Asociados**:
  - Reporte directo de usuario en v1.6.0 (Chat overlay arranca con estilos de fábrica hasta que se edita manualmente en la UI).
* **Fecha y Versión del Fallo**: 2026-09-19 en MiniKick `v1.6.0`.
* **Causa Raíz**:
  1. `ChatService.save_settings()` persistía correctamente en SQLite las 23 claves `chat_overlay_*` (`chat_overlay_vertical_theme`, `chat_overlay_horizontal_size`, etc.).
  2. Sin embargo, `ChatService.get_settings()` únicamente cargaba y retornaba las claves de voz y TTS (`tts_enabled`, `tts_volume`, etc.), omitiendo todas las claves de overlay.
  3. Al iniciar la aplicación, `MainWindowCore._load_settings_into_ui()` ejecutaba `chat_controller.sync_settings_cache()`, que poblaba `self._tts_settings_cache` exclusivamente desde `get_settings()`.
  4. Inmediatamente después, `ChatController.get_active_overlay_config()` leía dicho caché y, al no encontrar las claves de overlay, recaía en los fallbacks por defecto (`theme="glass"`, `size="14"`, `fade="15"`, etc.).
  5. Este payload con valores por defecto era transmitido a `OverlayServerManager.trigger_chat_config_update()`, el cual por WebSocket enviaba `chat_config` a OBS, forzando a `chat.js` (`applyLiveConfig`) a sobreescribir la configuración visual guardada del streamer por los estilos por defecto.
* **Archivos y Líneas Modificadas**:
  1. [`backend/services/chat/chat_service.py:L30-L163`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_service.py#L30-L163):
     - Se incluyeron todas las 23 claves `chat_overlay_*` dentro del diccionario devuelto por `get_settings()`.
     - Se refactorizó `get_overlay_settings()` para derivar directamente de `get_settings()`, eliminando código redundante y manteniendo adherencia estricta al principio DRY.
  2. [`backend/controllers/chat_controller.py:L143-L153`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py#L143-L153), [`L780-L790`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py#L780-L790):
     - Inyección corregida de `giphy_service` (`giphy_service or GiphyService()`).
     - Invocación de `sync_settings_cache()` en `__init__` para garantizar que `_tts_settings_cache` esté hidratado desde el arranque.
     - Fallback defensivo en `get_active_overlay_config()` hacia `self.service.get_overlay_settings()` si la clave de orientación no está en el caché.
* **Prueba Automatizada de Cobertura**:
  - `resources/tests/test_chat_overlay_controls.py`:
    - `test_chat_service_get_settings_contains_overlay_keys`
    - `test_chat_controller_get_active_overlay_config_preserves_custom_settings_on_startup`
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_14.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_14.md).

---

### INC-006: Ocultamiento Indebido de Tablas y Disparo del Empty State Inicial al Filtrar Cero Resultados

* **Estado**: `✅ Solventado`
* **Severidad**: **MEDIA / UX CRÍTICA** (La tabla, cabeceras y barra de búsqueda desaparecían al no haber coincidencias de filtro o búsqueda, impidiendo limpiar o ajustar los filtros).
* **Reportes Asociados**:
  - Reporte de Usuario en v1.6.0 ("cuando no existe nada que filtrar o digamos que el filtro es 0 la tabla desaparece y solo me sale la sugerencia de crear").
* **Fecha y Versión del Fallo**: 2026-09-21 en MiniKick `v1.6.0`.
* **Causa Raíz**:
  En `commands_view.py`, `rewards_view.py` y `schedule_table_panel.py`, la llamada `self.table_card.set_empty(...)` recibía la condición `len(filtered) == 0` en lugar de evaluar si el sistema contenía registros totales (`len(raw) == 0`). Al aplicar un filtro de columna o búsqueda que dejaba 0 coincidencias, `set_empty(True)` conmutaba el `QStackedWidget` al índice 1 (el estado vacío inicial con ilustración y botón `+ Crear`). Esto ocultaba la tabla completa con sus cabeceras interactivas, imposibilitando al usuario restablecer los filtros desde la UI.
* **Archivos y Líneas Modificadas**:
  1. [`frontend/widgets/table_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py):
     - Se incorporó `no_results_overlay` en `ModernTableCard` sobre el viewport de la tabla, con mensaje claro (`common.no_results_filter`) y botón de acción interactivo `[Limpiar filtros]` (`common.buttons.clear_filters`).
     - Se agregó el método `clear_filters()` que resetea la barra de búsqueda y los filtros de columna mediante `reset_filters()`.
     - Se agregó `set_no_results(show: bool)` para alternar la visualización del overlay sin ocultar la cabecera ni la tarjeta de la tabla.
  2. [`frontend/widgets/filter_header.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/filter_header.py):
     - Se añadieron `reset_filters()` y `has_active_filters()` a `FilterHeaderView` para restaurar todas las opciones activas y notificar a la vista reactivamente.
  3. [`frontend/views/commands_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py), [`frontend/views/rewards_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py), [`frontend/components/schedule/schedule_table_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_table_panel.py):
     - `set_empty(is_empty_system)` ahora evalúa exclusivamente el total de elementos (`len(raw) == 0`).
     - `set_no_results(has_no_matches)` activa el overlay con el botón `Limpiar filtros` cuando `len(filtered) == 0 and not is_empty_system`.
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_21.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_21.md).

---

### INC-007: Crash Fatal al Navegar a Música (`libshiboken: Internal C++ object already deleted` en `ModernTableCard.resizeEvent`)

* **Estado**: `✅ Solventado`
* **Severidad**: **CRÍTICA** (Cierre abrupto de la aplicación / Fatal Crash Handler al cambiar de pestaña).
* **Reportes Asociados**:
  - `minikick.log` (Línea 794, 2026-09-21 10:30:58)
* **Fecha y Versión del Fallo**: 2026-09-21 en MiniKick `v1.6.0`.
* **Traza de la Excepción**:
  ```text
  [CRITICAL] [FATAL CRASH] Unhandled exception caught by global excepthook:
  Traceback (most recent call last):
    File "backend/core/main_window_core.py", line 382, in _handle_navigation
      self.content_stack.setCurrentWidget(target_view)
    File "frontend/widgets/block_widget.py", line 329, in viewportEvent
      res = super().viewportEvent(event)
    File "frontend/widgets/table_widget.py", line 346, in resizeEvent
      if hasattr(self, "no_results_overlay") and self.no_results_overlay.isVisible():
  RuntimeError: Error calling Python override of QScrollArea::viewportEvent(): Error calling Python override of QScrollArea::viewportEvent(): Error calling Python override of QFrame::resizeEvent(): libshiboken: Internal C++ object (PySide6.QtWidgets.QWidget) already deleted.
  ```
* **Causa Raíz**:
  1. En `ModernTableCard.__init__`, el widget de overlay `self.no_results_overlay = QWidget(self.table)` se asociaba como hijo de `self.table`.
  2. En `frontend/components/music/queue_panel.py`, para implementar la tabla de cola con soporte drag-and-drop (`DragDropQueueTable`), el panel obtenía `old_table = self.card_queue.table` y ejecutaba `old_table.deleteLater()`, reemplazando la tabla por `self.queue_table`.
  3. Al destruir `old_table` en C++, Qt eliminaba en cascada a todos sus hijos, incluyendo `self.no_results_overlay`.
  4. Cuando el usuario navegaba a la pestaña de Música, el layout de la ventana disparaba `resizeEvent` sobre `card_queue`. En `table_widget.py:346`, la comprobación `hasattr(self, "no_results_overlay")` resultaba `True` (el wrapper de Python aún existía), pero al invocar `self.no_results_overlay.isVisible()`, Shiboken lanzaba `RuntimeError` por objeto C++ ya eliminado.
* **Archivos y Líneas Modificadas**:
  1. [`frontend/widgets/table_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py):
     - Se añadió soporte para `custom_table: QTableWidget = None` en el constructor de `ModernTableCard`, permitiendo inyectar tablas especializadas desde el inicio sin necesidad de destruir tablas predeterminadas.
     - Se implementó la función helper `_is_valid_widget(widget)` utilizando `shiboken6.isValid()` y captura defensiva de `RuntimeError`.
     - Se blindaron `resizeEvent`, `eventFilter`, `_update_no_results_geometry`, `set_empty` y `set_no_results` comprobando `self._is_valid(...)` y envolviendo en bloques `try ... except RuntimeError: pass`.
  2. [`frontend/components/music/queue_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/queue_panel.py):
     - Se eliminó el flujo destructivo `old_table.deleteLater()`. Ahora `self.queue_table = DragDropQueueTable(...)` se instancia directamente y se inyecta como `custom_table` en `ModernTableCard(...)`.
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_21.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_21.md).

---

### INC-008: Micro-Ventana Fantasma ('python' / 'pyt...') por Precalentamiento de `QCalendarPopup` y Controles sin `parent`

* **Estado**: `✅ Solventado`
* **Severidad**: **ALTA** (Anomalía visual/DWM: proyección fugaz de ventana nativa de nivel superior vacía con título de proceso `python` al precalentar o cambiar de vista).
* **Reportes Asociados**:
  - Evidencia visual capturada por usuario (v1.6.0, ventana de ~180x100 px con título `pyt...` sobre Dashboard/Stream Info).
  - Traza de inicialización en `minikick.log` a los ~3.75 segundos de arranque (`_schedule_view_prewarming`).
* **Fecha y Versión del Fallo**: 2026-09-21 en MiniKick `v1.6.0`.
* **Causa Raíz**:
  1. **Invocación Prematura de `calendarWidget()`**:
     En [`frontend/components/schedule/schedule_form_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_form_panel.py), la llamada ansiosa `cal = self.date_edit.calendarWidget()` durante el constructor forzaba a Qt a instanciar internamente `QCalendarPopup` (`qt_datetimedit_calendar`) y el menú `QMenu` del mes (`qt_calendar_monthbutton`).
  2. **Creación de HWND Nativo sin Ancestro Mapeado**:
     Al ejecutarse el precalentador (`_schedule_view_prewarming`) en segundo plano a los ~3.75s, `ScheduleView` no estaba mapeada en la pantalla. Qt asignó a estos popups banderas nativas `0x800f009` (`WindowTitleHint`, `WindowMinimizeButtonHint`, `WindowMaximizeButtonHint`, `WindowCloseButtonHint`). Windows DWM detectó el nuevo `HWND`, titulándolo con el nombre del ejecutable (`python`, truncado a `pyt...`) y proyectando brevemente su superficie gris vacía en pantalla.
  3. **Widgets Huérfanos sin Parent**:
     En `PlatformStatusCard` y `DashboardView`, varios botones (`btn_action`, `btn_tab_kick`, `btn_tab_twitch`) y marcos de banners se instanciaban sin `parent=self` antes de ser agregados a layouts.
* **Solución Implementada**:
  1. **Lazy Initialization en `NoWheelDateEdit`**:
     En [`frontend/widgets/no_wheel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/no_wheel.py), la personalización de estilos del calendario se encapsuló en `_configure_calendar_widget()`, ejecutándose bajo demanda únicamente cuando el usuario despliega o interactúa con el selector de fechas.
  2. **Eliminación de la llamada ansiosa**:
     Se eliminó `cal = self.date_edit.calendarWidget()` en `ScheduleFormPanel`.
  3. **Jerarquía Explícita (`parent=self`)**:
     Se vincularon explícitamente como hijos `parent=self` todos los sub-controles en `ScheduleFormPanel`, `ScheduleView`, `PlatformStatusCard` y `DashboardView`.
  4. **Herramienta Automatizada de Diagnóstico**:
     Se creó [`resources/tools/window_audit_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/window_audit_manager.py) para auditar tanto estáticamente (AST) como dinámicamente (Runtime) todas las vistas y el prewarming, garantizando 0 ventanas fantasma (`0 HWND leaks`).
* **Archivos Modificados**:
  - [`frontend/widgets/no_wheel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/no_wheel.py)
  - [`frontend/components/schedule/schedule_form_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_form_panel.py)
  - [`frontend/views/schedule_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/schedule_view.py)
  - [`frontend/components/dashboard/platform_card.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dashboard/platform_card.py)
  - [`frontend/views/dashboard_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py)
  - [`resources/tools/window_audit_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/window_audit_manager.py)
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_22.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_22.md).

---

### INC-009: Excepción Fatal por kwargs Inesperados en `TranslationService.get()`

* **Estado**: `✅ Solventado`
* **Severidad**: **CRÍTICA** (Cierre prematuro de la aplicación durante la inicialización de la bandeja del sistema en `MainWindowCore.__init__`).
* **Reportes Asociados**:
  - `minikick.log` (Línea 2397): `TypeError: TranslationService.get() got an unexpected keyword argument 'version'`
* **Fecha y Versión del Fallo**: 2026-09-21 en MiniKick `v1.6.0`.
* **Causa Raíz**:
  `SystemTrayManager._setup_ui()` invocaba `self.i18n.get("main.tray.tooltip", version="1.6.0")`. La firma original de `TranslationService.get(self, key: str) -> str` no aceptaba `**kwargs`, causando un `TypeError` no controlado durante el ciclo de arranque (`bootstrap`).
* **Solución Implementada**:
  1. En [`backend/services/system/translation_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/translation_service.py), se dotó a `TranslationService.get(self, key: str, **kwargs) -> str` de soporte para `**kwargs` con interpolación segura (`str.format(**kwargs)` y fallback defensivo con `replace`).
  2. En [`frontend/navigation/tray_menu_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/tray_menu_component.py), se eliminó cualquier llamada a `setStyleSheet` y se aseguró el formateo seguro del tooltip.
  3. En [`frontend/widgets/table_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py), se reemplazó el uso ad-hoc de `setStyleSheet` por el rol formal `table_no_results` sincronizado con [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py).
* **Archivos Modificados**:
  - [`backend/services/system/translation_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/translation_service.py)
  - [`frontend/navigation/tray_menu_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/tray_menu_component.py)
  - [`frontend/widgets/table_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py)
  - [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)
* **Prueba Automatizada de Cobertura**:
  - `resources/tests/test_tray_and_slider_debouncing.py` (`test_system_tray_manager_playback_toggle_and_tooltip`)
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_23.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_23.md).

---

### INC-010: Error HTTP 414 en `GiphyService` por Enlaces Largos e Inclusión de Bots en Top Chatters

* **Estado**: `✅ Solventado`
* **Severidad**: **MEDIA** (Advertencias y peticiones HTTP 414 innecesarias en Giphy por auto-embed erróneo; distorsión del widget overlay de Top Chatters por mensajes de timers del bot).
* **Reportes Asociados**:
  - `minikick.log` (Líneas 555, 563, 574, 582): `[WARNING] [GiphyService] Error searching Giphy for query '🖤Aquí está el enlace de TikTok!: https://www.tiktok.com/...': HTTP Error 414: URI Too Long`
  - Feedback de Usuario: Inclusión del bot `@MiniKick` en el ranking del widget OBS `assets/overlays/widgets/chatters.html`.
* **Fecha y Versión del Fallo**: 2026-09-21 en MiniKick `v1.6.0`.
* **Causa Raíz**:
  1. En `ChatController._step_ui_render`, al evaluar mensajes con `http://` o `https://`, se invocaba `self.giphy_service.resolve_gif(dto.content.strip())`. En `GiphyService`, al no coincidir con una URL directa de imagen, el método asumía que toda la cadena (incluyendo enlaces largos de TikTok y emojis) era una consulta de búsqueda de texto en la API de Giphy. Al codificar dicha URL con caracteres especiales y longitud excesiva, la API de Giphy retornaba `HTTP 414: URI Too Long`.
  2. En `WidgetsController._record_chatter_message`, el conjunto `_IGNORED_CHATTER_BOTS` no contenía `"minikick"`, no se eliminaba el prefijo `@` (`user.lstrip('@')`) y no se comprobaba la presencia de `"bot"` en `badges`, permitiendo que `@MiniKick` se contabilizara en el ranking de chatters más activos.
* **Solución Implementada**:
  1. En [`backend/services/chat/giphy_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/giphy_service.py):
     - Se introdujo `extract_gif_url(self, text: str) -> Optional[str]` con complejidad $\mathcal{O}(N)$ sin llamadas de red para extraer URLs auténticas de GIFs (`.gif`, `.webp`) o páginas/medios canónicos de Giphy.
     - Se blindó `resolve_gif` para rechazar URLs que no sean GIFs (como enlaces a TikTok o YouTube), limitar consultas a $\le 80$ caracteres y rechazar queries con esquemas `http`.
  2. En [`backend/controllers/chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py):
     - En `_step_ui_render`, se omite el procesamiento de GIFs si el usuario es un bot (`not self.filter_handler.is_bot(dto.user, badges)`) y se invoca `extract_gif_url` en lugar de una búsqueda de texto.
  3. En [`backend/controllers/widgets_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py):
     - Retorno temprano si `badges` contiene `"bot"`.
     - Normalización $\mathcal{O}(1)$ del nombre (`user.strip().lstrip('@').lower()`).
     - Ampliación de `_IGNORED_CHATTER_BOTS` con `minikick`, `wizebot`, `kofi`, etc., y verificación cruzada contra `spam_service.storage` (`tts_ignored_users`).
  4. En [`backend/handlers/spam_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/spam_handler.py):
     - Normalización en `is_bot` para evaluar nombres con o sin `@` contra `_DEFAULT_BOTS` y `muted_bots`.
* **Pruebas Automatizadas de Cobertura**:
  - `resources/tests/test_giphy_and_tts_filter.py`:
    - `test_extract_gif_url_and_non_gif_rejection`
    - `test_resolve_gif_blocks_long_queries_and_arbitrary_urls`
    - `test_widgets_controller_ignores_minikick_and_bots_in_top_chatters`
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_25.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_25.md).

---

### INC-011: Bordes Blancos y Desincronización de Tema en Popups con Windows en Tema Claro

* **Estado**: `✅ Solventado`
* **Severidad**: **MEDIA** (Defectos visuales notorios, recuadros blancos rígidos y textos ilegibles en selectores de voces, autocompletado y calendario para usuarios con tema claro en Windows).
* **Reportes Asociados**:
  - Capturas de usuario de `SearchableComboBox`, `VariableTextEdit` y `QDateEdit` calendario.
* **Fecha y Versión del Fallo**: 2026-09-22 en MiniKick `v1.6.0`.
* **Causa Raíz**:
  1. MiniKick no asignaba una paleta nativa `QApplication.setPalette()`. Si Windows estaba en Tema Claro, Qt inicializaba `QPalette.Base` y `QPalette.Window` en `#ffffff` / `#f0f0f0`.
  2. `SearchableComboPopup` fijaba explícitamente `WA_TranslucentBackground = False`. Al tener `border-radius: 8px` en un marco frameless, el fondo exterior de la ventana nativa se pintaba blanco (`#ffffff`).
  3. `VariableTextEdit.popup` era un `QListWidget` sin rol ni estilos QSS, mostrándose como una ventana blanca nativa.
  4. `QDateEdit` utiliza `QCalendarPopup` (`QWidget#qt_datetimedit_calendar`) y el viewport de `QTableView` con `autoFillBackground=True`. Ambos se pintaban con la paleta clara nativa, dejando el encabezado blanco sobre fondo blanco.
* **Solución Implementada**:
  1. En [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py):
     - Creación de `create_dark_palette() -> QPalette` para forzar roles oscuros nativos en toda la aplicación.
     - Reglas QSS para `QWidget#qt_datetimedit_calendar`, `QCalendarWidget QTableView QWidget`, `QListWidget[role="variable_autocomplete_popup"]`, `QMenu` y `QToolTip`.
  2. En [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py):
     - Inyección de `app.setPalette(create_dark_palette())` en el arranque de la app y en el manejador de crash global.
  3. En [`frontend/widgets/searchable_combo_box.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/searchable_combo_box.py):
     - Activación de `self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)`.
  4. En [`frontend/widgets/controls_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls_widget.py):
     - Asignación de rol `variable_autocomplete_popup`, `WA_TranslucentBackground = True` y políticas de scroll.
  5. En [`frontend/widgets/category_search.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/category_search.py):
     - Activación de `WA_TranslucentBackground = True` en `CategorySuggestionsPopup`.
  6. En [`frontend/widgets/no_wheel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/no_wheel.py):
     - Aplicación de `dark_pal` en `QCalendarWidget`, `popup` y `table.viewport()`.
* **Prueba Automatizada de Cobertura**:
  - `resources/tests/test_antigravity_ui_theme.py` (`test_dark_palette_and_popup_translucency_standards`).
* **Walkthrough de Referencia**: [`docs/walkthroughs/v1.6.0/WT-1.6.0_33.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.0/WT-1.6.0_33.md).

---

## 📌 Guía de Actualización para Desarrolladores y Agentes de IA

Siempre que se reciba un nuevo reporte de fallo (`.log`), crash dump o issue de usuario:
1. **Consultar este documento primero**: Buscar coincidencias de trazas o mensajes de error en la tabla superior.
2. Si el fallo ya está catalogado como `✅ Solventado`, verificar la versión del usuario contra el commit o walkthrough del fix.
3. Si es un fallo no registrado o nuevo:
   - Diagnosticar y resolver bajo el flujo estricto (Plan de Implementación $\to$ Pruebas $\to$ Walkthrough).
   - **Agregar obligatoriamente una nueva entrada `INC-XXX` en este archivo** detallando la causa raíz, archivos modificados y pruebas asociadas.
