# Walkthrough - Blindaje de Telemetría, Diagnósticos y Optimización de Señales PySide6

Documento de referencia: `WT-1.5.3_04`  
Versión: `v1.5.3`  
Módulos modificados: `backend/core/app_logger_core.py`, `main.py`, `backend/providers/voices/tts_local.py`, `backend/providers/voices/tts_online.py`, `backend/services/chat/chat_service.py`, `backend/providers/chat/kick_client.py`, `frontend/views/log_view.py`, `frontend/views/chat_view.py`, `frontend/views/settings_view.py`, `frontend/views/spam_view.py`, `frontend/components/chat/tts_settings.py`, `frontend/widgets/no_wheel.py`, `frontend/widgets/blocks.py`, `frontend/common/theme.py`, `frontend/navigation/sidebar_component.py`, `backend/workers/*`, `backend/controllers/*`, `backend/handlers/*`

---

## 📋 Resumen

Se implementó un sistema integral para la captura y persistencia de fallos y diagnósticos en **MiniKick**, se completó la optimización de tipado de señales y slots en PySide6/Qt (`Signal(object)` / `@Slot(object)`), se silenciaron a nivel nativo C los volcados informativos de FFmpeg (`avutil.av_log_set_level`) en consola, se calibró el dimensionamiento responsivo de los ComboBoxes, se alinearon con precisión de cuadrícula (`QGridLayout`) todos los campos de las tarjetas de protección anti-spam, se resolvieron los errores multiplataforma reportados en **Ubuntu / Linux**, y se blindó la sincronización de voces al alternar entre motores TTS Local y Web/Neural.

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
- Se implementó `_silence_ffmpeg_native_logging()` en `backend/core/app_logger_core.py` utilizando la DLL nativa `avutil-59.dll` (`avutil.av_log_set_level(16)`) para suprimir las salidas de sondeo e inspección de metadatos de audios mp3 (TTS) y videos mp4 (YouTube Music) en la terminal.

### 7. Calibración Responsiva de ComboBoxes
- `NoWheelComboBox`: Se estableció `setMinimumWidth(130)` y política `AdjustToContentsOnFirstShow` como estándar global, garantizando que textos como *"Español"*, *"Normal"* y *"(Predeterminado)"* se muestren completos y sin truncarse en [SettingsView](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py).
- `VoiceSettingRow`: Se configuró la política elástica `AdjustToMinimumContentsLengthWithIcon` (`setMinimumWidth(0)`) exclusivamente para las filas de selección de voces TTS.

### 8. Alineación de Cuadrícula en Tarjetas de Filtros Anti-Spam (`ExpandableSettingCard`)
- **Migración a `QGridLayout`**: Se reemplazaron las dos columnas independientes de `QVBoxLayout` por un `QGridLayout` de 4 filas y 2 columnas con espaciado vertical de `4px` y horizontal de `16px`.
- **Creación de `NoWheelSpinBox`**: Se creó la clase `NoWheelSpinBox` en `frontend/widgets/no_wheel.py` para prevenir saltos de valores accidentales con la rueda del ratón.
- **Corrección de Padding en Estado Deshabilitado (`theme.py:339`)**: Se separó la regla QSS para que los SpinBoxes conserven su padding específico al deshabilitarse.

### 9. Optimización Visual de la Barra Lateral Colapsada (`Sidebar`)
- **Supresión de Scrollbar Visible en Modo Colapsado**: En [sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py#L317), al colapsar la barra lateral se establece `setVerticalScrollBarPolicy(ScrollBarAlwaysOff)` y al expandirla se restaura `ScrollBarAsNeeded`.
- **Centrado Perfecto de Íconos**: En [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py#L296), se actualizó el padding del botón colapsado a `10px 0px`.

### 10. Compatibilidad Multiplataforma para Linux / Ubuntu
- **Blindaje de COM en TTS Local (`tts_local.py`)**: `pythoncom` condicionado a `sys.platform == "win32"`. En Ubuntu/Linux, `pyttsx3` opera con el driver `espeak`.
- **Cabeceras de Navegador en CloudScraper (`kick_client.py`)**: Se reforzó `ScraperFactory.create()` con cabeceras completas de cliente moderno para evitar bloqueos 403 de Cloudflare en Linux.

### 11. Sincronización y Validación de Voces entre Motores TTS
- **Sincronización de Voz al Cambiar Proveedor (`chat_service.py:72`)**: Al cambiar entre `local` y `web`, `set_provider()` ahora restaura y sincroniza inmediatamente la voz correspondiente guardada para ese proveedor en `TTSManager`.
- **Validador y Fallback de Voz en `WebTTSProvider` (`tts_online.py:50`)**: Se añadió `_resolve_valid_voice()` en el motor online para verificar que la voz sea una voz Neural válida de Edge TTS. Si contiene un ID local (como `jpx/ja` o `roa/es`), automáticamente recurre a la voz online por defecto (`es-ES-AlvaroNeural`) en lugar de arrojar error `Invalid voice`.

---

## 🧪 Pruebas Realizadas

1. **Prueba de `faulthandler`**: Verificado `faulthandler.is_enabled() == True` y persistencia en `minikick_crash.log`.
2. **Prueba de Auto-Flush**: Validación de persistencia inmediata en disco de mensajes `CRITICAL` y `ERROR`.
3. **Prueba de Excepciones en Hilos**: Disparo de excepción no controlada en un hilo secundario y verificación del traceback completo en `minikick.log`.
4. **Prueba de Compilación y Limpieza de Terminal**: Verificación de ejecución limpia sin advertencias de Shiboken ni texto verboso de FFmpeg.
5. **Prueba de Conmutación de Voces TTS**: Validación de alternancia bidireccional (`local` $\leftrightarrow$ `web`) asegurando que `WebTTSProvider` y `LocalTTSProvider` reciban siempre sus respectivos IDs válidos.
