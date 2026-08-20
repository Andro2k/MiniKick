# Walkthrough - Blindaje de Telemetría, Diagnósticos y Optimización de Señales PySide6

Documento de referencia: `WT-1.5.3_04`  
Versión: `v1.5.3`  
Módulos modificados: `backend/core/app_logger_core.py`, `main.py`, `frontend/views/log_view.py`, `backend/workers/*`, `backend/controllers/*`, `backend/handlers/*`, `frontend/components/*`

---

## 📋 Resumen

Se implementó un sistema integral para la captura y persistencia de fallos y diagnósticos en **MiniKick**, y se completó la optimización de tipado de señales y slots en PySide6/Qt (`Signal(object)` / `@Slot(object)`), eliminando por completo las advertencias de conversión de C++ de **Shiboken** (`Cannot copy-convert ... (dict/list) to C++`) y silenciando a nivel nativo C los volcados informativos de FFmpeg (`avutil.av_log_set_level`) en la consola.

---

## 🛠️ Mejoras y Cambios Implementados

### 1. `faulthandler` Nativo para Captura de Fallos de Memoria
- Se integró `faulthandler.enable(file=crash_log_file, all_threads=True)`.
- Si ocurre una violación de acceso (`STATUS_ACCESS_VIOLATION`), un fallo de segmentación o un crash a nivel C/C++ (Qt, FFmpeg o librerías dinámicas), Python intercepta la señal del sistema operativo y escribe la traza completa de todos los hilos en `%LOCALAPPDATA%/.Minikick/logs/minikick_crash.log` antes de que el proceso termine.

### 2. Auto-Flush Inmediato de Logs (`AutoFlushTimedRotatingFileHandler`)
- Se implementó un handler de logs que fuerza el vaciado inmediato a disco (`flush()`) para todos los registros de nivel `WARNING`, `ERROR` y `CRITICAL`.
- Se evita la pérdida de información crítica almacenada en buffers de memoria en caso de cierre abrupto.

### 3. Captura Global de Hilos Secundarios (`threading.excepthook`)
- En Python 3.8+, las excepciones no atrapadas en hilos secundarios no pasaban por `sys.excepthook`.
- Se configuró `threading.excepthook` para capturar cualquier excepción en hilos en segundo plano (TTS, WebSocket, Timers, Schedule, etc.), registrando el traceback completo y forzando el volcado a disco.

### 4. Soporte Completo del Nivel `CRITICAL` en Interfaz de Logs
- Se agregó el nivel `CRITICAL` con color rojo e ícono `alert-circle.svg` en `frontend/views/log_view.py`.
- Se habilitó la opción `CRITICAL` en el menú de filtrado por columna de la tabla de logs.

### 5. Optimización Integral de Señales y Slots Qt (Eliminación de Advertencias Shiboken)
- Se estandarizaron todas las señales y slots que transportan diccionarios y listas dinámicas de Python (`Signal(object)` / `@Slot(object)`):
  - Workers: `NetworkWorker`, `UpdateCheckWorker`, `ReleaseNotesWorker`, `AuthWorker`, `TwitchAuthWorker`, `ChatWorker`, `TwitchChatWorker`, `ScheduleWorker`, `FetchRewardsWorker`, `CreateRewardWorker`, `UpdateRewardWorker`, `VoiceFetcherWorker`.
  - Controladores y Handlers: `DashboardController`, `UpdateController`, `ScheduleController`, `WidgetController`, `MusicController`, `RewardsController`, `SpamController`, `ChatController`, `TTSVoiceHandler`.
  - Vistas y componentes: `FilterHeaderView`, `LogView`, `ScheduleView`, `SpamView`, `WidgetsView`, `ScheduleTablePanel`, `ScheduleFormPanel`, `QuickChangePanel`, `WidgetCard`.
- Esto garantiza que todas las colecciones pasen por **referencia directa de Python (`PyObject*`)**, evitando copias profundas defensivas y eliminando avisos de Shiboken.

### 6. Supresión Nativa C de Volcados de FFmpeg en Consola
- Se implementó `_silence_ffmpeg_native_logging()` en `backend/core/app_logger_core.py` utilizando la DLL nativa `avutil-59.dll` (`avutil.av_log_set_level(16)`) para suprimir las salidas de sondeo e inspección de metadatos de audios mp3 (TTS) y videos mp4 (YouTube Music) en la terminal, manteniendo intacta la captura de errores críticos.

---

## 🧪 Pruebas Realizadas

1. **Prueba de `faulthandler`**: Verificado `faulthandler.is_enabled() == True` y persistencia en `minikick_crash.log`.
2. **Prueba de Auto-Flush**: Validación de persistencia inmediata en disco de mensajes `CRITICAL` y `ERROR`.
3. **Prueba de Excepciones en Hilos**: Disparo de excepción no controlada en un hilo secundario y verificación del traceback completo en `minikick.log`.
4. **Prueba de Compilación y Limpieza de Terminal**: Verificación de ejecución limpia sin advertencias de Shiboken ni texto verboso de FFmpeg.
