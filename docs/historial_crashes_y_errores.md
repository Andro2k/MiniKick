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

## 📌 Guía de Actualización para Desarrolladores y Agentes de IA

Siempre que se reciba un nuevo reporte de fallo (`.log`), crash dump o issue de usuario:
1. **Consultar este documento primero**: Buscar coincidencias de trazas o mensajes de error en la tabla superior.
2. Si el fallo ya está catalogado como `✅ Solventado`, verificar la versión del usuario contra el commit o walkthrough del fix.
3. Si es un fallo no registrado o nuevo:
   - Diagnosticar y resolver bajo el flujo estricto (Plan de Implementación $\to$ Pruebas $\to$ Walkthrough).
   - **Agregar obligatoriamente una nueva entrada `INC-XXX` en este archivo** detallando la causa raíz, archivos modificados y pruebas asociadas.
