# Walkthrough Técnico — MiniKick v1.6.6 (Paso 03)

Refactorización profunda del ciclo de vida y concurrencia del backend como resultado de la auditoría completa de `backend/core` y `backend/workers`. Se desacopla la señal de resultado de los workers respecto a la señal nativa `QThread.finished` para prevenir la destrucción prematura de hilos, se implementa cancelación cooperativa y retención segura en búsquedas musicales, se introduce espera cooperativa fraccionada en bucles de reconexión de chat y eventos eliminando bloqueos de hasta 30 segundos, se estandarizan los contratos `stop()` con interrupción formal y salida del bucle de eventos Qt, se garantiza la limpieza del subsistema COM en Windows para el sintetizador de voz, se dota de aislamiento de excepciones e idempotencia al apagado del contenedor y servicios de voz, y se corrigen fugas de recursos en el sistema de logging. Módulos afectados: `backend/core/app_container_core.py`, `backend/core/app_logger_core.py`, `backend/services/chat/tts_service.py`, `backend/utils/worker_utils.py`, `backend/workers/*`, `backend/providers/music/youtube_provider.py`, `backend/controllers/updater_controller.py`, `frontend/dialogs/bug_report_dialog.py`, `frontend/dialogs/crash_report_dialog.py` y `resources/tests/test_worker_and_core_lifecycle.py`.

Validado con 12 pruebas automatizadas de ciclo de vida (`test_worker_and_core_lifecycle.py`), 19 pruebas de integración de hilos y ventana principal, y ejecución de la suite de calidad del proyecto.

---

## Novedades

- **Señales de finalización explícitas en workers asíncronos**: introducción de señales semánticas de resultado (`report_completed`, `search_completed`, `download_completed`) separadas de la señal nativa `finished` de `QThread`.
- **Utilidad de espera cooperativa (`cooperative_sleep`)**: función utilitaria en `backend/utils/worker_utils.py` que fracciona lapsos de espera en intervalos de 50 ms evaluando `isInterruptionRequested()` y estados de parada (`_is_stopped`, `_running`), permitiendo abortos inmediatos sin bloquear el hilo.
- **Suite de pruebas de ciclo de vida (`test_worker_and_core_lifecycle.py`)**: 12 pruebas unitarias y de integración que verifican firmas de señales Qt en metadatos, cancelación de peticiones en vuelo, retención de workers en el proveedor, aislamiento de fallos en el contenedor, idempotencia de cierre de TTS, flushing seguro a `stderr`, parada cooperativa inmediata, contratos `stop()` de workers y desinicialización de COM.

## Mejoras

- **Ciclo de vida en `YouTubeMusicProvider`**:
  - Desacoplamiento entre la recepción de la canción (`search_completed`) y la eliminación de la instancia (`deleteLater` enlazado a `finished`).
  - Registro de workers activos en `_ACTIVE_SEARCH_WORKERS` con `weakref` para evitar recolección de basura prematura mientras el hilo corre.
  - Cancelación cooperativa en `shutdown()` que interrumpe y detiene todas las búsquedas pendientes.
- **Cancelación cooperativa en `YouTubeSearchWorker`**: comprobaciones de `isInterruptionRequested()` antes de interactuar con red, durante reintentos y en esperas `msleep(100)`, evitando emitir señales hacia componentes destruidos.
- **Espera cooperativa en reconexiones de chat y recompensas**:
  - `KickChatWorker` y `TwitchChatWorker` sustituyen el `msleep` indivisible del backoff exponencial por `cooperative_sleep`, permitiendo detener el hilo en menos de 50 ms en lugar de esperar hasta 30 segundos.
  - `KickPollSyncWorker` reemplaza el sleep indivisible de 2000 ms por espera cooperativa en tramos de 50 ms.
  - `TwitchRewardWorker` fracciona la espera por falta de token (5000 ms) y el retardo por backoff.
  - `TimerWorker` implementa evaluación de interrupción en su bucle principal y desvía la pausa entre revisiones a `cooperative_sleep`.
- **Estandarización de contratos `stop()`**:
  - `KickChatWorker.stop()`, `TwitchChatWorker.stop()`, `TwitchRewardWorker.stop()` y `KickPollSyncWorker.stop()` invocan formalmente `self.requestInterruption()` y `self.quit()`, garantizando la salida limpia del bucle de eventos y de hilos nativos.
- **Supresión de señales en workers efímeros cancelados**:
  - `FetchRewardsWorker`, `CreateRewardWorker`, `UpdateRewardWorker`, `UpdateCheckWorker`, `UpdateDownloadWorker`, `ReleaseNotesWorker` y `WhatsNewWorker` verifican `isInterruptionRequested()` antes de emitir señales de éxito o error, evitando despachar eventos a vistas o controladores ya destruidos.
- **Hook multimedia en Windows (`GlobalMediaWorker`)**:
  - Migración de bandera booleana a `threading.Event` (`_stop_requested`).
  - Creación garantizada de la cola de mensajes de Windows mediante `PeekMessageW` antes de iniciar el bucle `GetMessageW`.
  - Verificación y reintento en el envío de `WM_QUIT` mediante `PostThreadMessageW` en `stop()`.
- **Idempotencia y aislamiento en `AppContainerCore`**:
  - `shutdown()` protegido contra múltiples ejecuciones simultáneas (`_is_shutdown`).
  - Desconexión aislada por componente con captura individual de excepciones, impidiendo que un fallo en un servicio detenga el apagado de los demás.
  - Invocación directa a `tts_manager.shutdown()` en lugar de `stop()`.
- **Limpieza y diagnóstico en `app_logger_core.py`**:
  - `_reset_handlers` vacía (`flush()`) y cierra (`close()`) formalmente cada handler reemplazado.
  - Sustitución de bloques `except: pass` en `flush_all_logs` por emisión directa a `sys.__stderr__`.
- **Desbloqueo de UI en diálogos**: eliminación de esperas síncronas `self.worker.wait(...)` en los diálogos de reporte de errores y fallos, delegando la gestión de recursos a la señal `finished` nativa.

## Correcciones

- **Fallo por destrucción prematura de `QThread`**: `BugReportWorker`, `CrashReportWorker`, `YouTubeSearchWorker` y `UpdateDownloadWorker` sobreescribían la señal nativa `finished` de Qt, lo que disparaba la destrucción del objeto antes de que el método `run()` terminara de ejecutarse.
- **Retardo de hasta 30 segundos en el cierre por sleeps bloqueantes**: sockets en reconexión de Kick y Twitch bloqueaban el hilo en `msleep` extensos, provocando avisos de tiempo límite excedido en el coordinador de cierre al salir de la aplicación.
- **Fuga de recursos COM en Windows (`VoiceFetcherWorker`)**: `VoiceFetcherWorker` inicializaba el subsistema COM con `pythoncom.CoInitialize()`, pero omitía `CoUninitialize()` al terminar, reteniendo el estado de apartamento de hilos en Windows.
- **Fuga de hilos en búsquedas canceladas**: búsquedas musicales continuaban ejecutándose y procesando resultados en segundo plano incluso tras haber cerrado la aplicación.
- **Bloqueo potencial al cerrar `GlobalMediaWorker`**: `stop()` enviaba `WM_QUIT` a un identificador de hilo antes de que Windows creara su cola de mensajes, provocando fallos silenciosos y retención indefinida del hilo en el cierre.
