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

## 📌 Guía de Actualización para Desarrolladores y Agentes de IA

Siempre que se reciba un nuevo reporte de fallo (`.log`), crash dump o issue de usuario:
1. **Consultar este documento primero**: Buscar coincidencias de trazas o mensajes de error en la tabla superior.
2. Si el fallo ya está catalogado como `✅ Solventado`, verificar la versión del usuario contra el commit o walkthrough del fix.
3. Si es un fallo no registrado o nuevo:
   - Diagnosticar y resolver bajo el flujo estricto (Plan de Implementación $\to$ Pruebas $\to$ Walkthrough).
   - **Agregar obligatoriamente una nueva entrada `INC-XXX` en este archivo** detallando la causa raíz, archivos modificados y pruebas asociadas.
