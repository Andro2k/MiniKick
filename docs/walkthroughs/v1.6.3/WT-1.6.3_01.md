# Walkthrough Tecnico - v1.6.3 / WT-1.6.3_01

**Version**: v1.6.3
**Fecha**: 2026-10-01
**Origen**: Logs minikick_JosueGMN_v1.6.2.log y minikick_Pipe_Cabrales_v1.6.2.log

---

## Novedades

No se introducen funcionalidades nuevas. El foco es estabilidad y correccion de fallos criticos de v1.6.2.

---

## Mejoras

### 1. Flush de Log en Nivel INFO (INC-019)

**Archivo**: backend/core/app_logger_core.py - AutoFlushTimedRotatingFileHandler

El umbral de flush automatico se redujo de logging.WARNING a logging.INFO.
Anteriormente, al cerrar abruptamente, los registros [INF] podian quedar en el buffer del SO
y no llegar al disco. Ahora los logs capturan la ultima accion del usuario antes del crash.

### 2. Robustez de KickAPIClient._request ante Timeouts (INC-020)

**Archivo**: backend/providers/chat/kick_provider.py - _request

Se aniadio requests.exceptions.Timeout a las excepciones de red recuperables.
El cliente recreara el scraper y reintentara (hasta 2 veces) antes de propagar el error.

### 3. Manejo Granular de Offline en TikTok

**Archivo**: backend/core/main_window_core.py - _on_tiktok_error

Cuando TikTok Live indica offline (keywords: offline, not live, no esta transmitiendo),
la severidad baja de [ERR] a [WRN] y el toast pasa de danger (rojo) a warning (amarillo).

---

## Correcciones

### 4. [CRI] QThread: Destroyed while thread is still running - Worker_Kick_Poll_Sync (INC-021)

**Archivo**: backend/workers/kick_chat_worker.py

**Causa raiz**: _stop_poll_sync_worker invocaba worker.wait(1000) bloqueante.
Si fetch_active_poll tardaba mas de 1000ms, la referencia se soltaba y el QThread
era destruido por el GC mientras el hilo corria, generando el [CRI] de Qt.

**Secuencia en logs**:
  [INF]  CommandService: Command executed - trigger=!skip, user=1KekeBoy
  [CRI]  QThread: Destroyed while thread is still running
  ...
  [INF]  TTS Manager: Enqueued text - WebTTS Playback Started
  [CRI]  QThread: Destroyed while thread Worker_Kick_Poll_Sync is still running

**Solucion**:
1. KickPollSyncWorker.run: El bucle verifica isInterruptionRequested() ademas de _is_stopped.
2. KickChatWorker._stop_poll_sync_worker: Se reemplazo wait(1000) por retiro asincrono
   via worker.finished signal + deleteLater().
3. KickChatWorker.__init__: Se aniade _retiring_poll_workers: set para mantener
   referencias vivas a workers en retiro y evitar su destruccion prematura por GC.

### 5. Senales Stale en YouTubeResolveWorker al Ser Cancelado (INC-022)

**Archivo**: backend/workers/music_worker.py

**Causa raiz**: El worker no verificaba isInterruptionRequested() en su pipeline.
Podia emitir resolved o error con datos de una cancion ya descartada al cambiar de cancion.

**Solucion**: 8 checkpoints isInterruptionRequested() en el flujo de extraccion/descarga,
incluyendo un progress_hook de yt-dlp activo. El sleep de backoff se fragmento en
sleeps de 0.1s en loop para ser interruptible. YouTubeSearchWorker recibe setObjectName().

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| backend/core/app_logger_core.py | Mejora - flush en INFO |
| backend/providers/chat/kick_provider.py | Mejora - retry en Timeout |
| backend/core/main_window_core.py | Mejora - offline TikTok como warning |
| backend/workers/kick_chat_worker.py | Correccion - lifecycle seguro KickPollSyncWorker |
| backend/workers/music_worker.py | Correccion - interrupciones en YouTubeResolveWorker |