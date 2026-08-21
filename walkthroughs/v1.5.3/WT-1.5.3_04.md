# Walkthrough - Blindaje de Telemetría, Diagnósticos y Optimización de Señales PySide6

Documento de referencia: `WT-1.5.3_04`  
Versión: `v1.5.3`  
Módulos modificados: `locales/es.json`, `locales/en.json`, `backend/core/app_logger_core.py`, `main.py`, `backend/providers/voices/tts_local.py`, `backend/providers/voices/tts_online.py`, `backend/services/chat/chat_service.py`, `backend/providers/chat/kick_client.py`, `backend/providers/chat/twitch_client.py`, `backend/services/schedule/schedule_service.py`, `backend/controllers/timer_controller.py`, `backend/controllers/command_controller.py`, `backend/controllers/spam_controller.py`, `backend/controllers/schedule_controller.py`, `backend/controllers/rewards_controller.py`, `backend/controllers/widget_controller.py`, `backend/controllers/music_controller.py`, `backend/controllers/settings_controller.py`, `backend/controllers/network_controller.py`, `backend/controllers/log_controller.py`, `backend/core/main_window_core.py`, `frontend/views/log_view.py`, `frontend/views/chat_view.py`, `frontend/views/settings_view.py`, `frontend/views/spam_view.py`, `frontend/views/timers_view.py`, `frontend/components/chat/tts_settings.py`, `frontend/components/schedule/quick_change_panel.py`, `frontend/components/schedule/schedule_form_panel.py`, `frontend/dialogs/timer_dialog.py`, `frontend/dialogs/bug_report_dialog.py`, `frontend/dialogs/release_notes_dialog.py`, `frontend/dialogs/crash_report_dialog.py`, `frontend/widgets/category_search.py`, `frontend/widgets/no_wheel.py`, `frontend/widgets/blocks.py`, `frontend/common/theme.py`, `frontend/navigation/sidebar_component.py`, `backend/workers/*`, `backend/controllers/*`, `backend/handlers/*`

---

## 📋 Resumen

Se implementó un sistema integral para la captura y persistencia de fallos y diagnósticos en **MiniKick**, se completó la optimización de tipado de señales y slots en PySide6/Qt (`Signal(object)` / `@Slot(object)`), se silenciaron a nivel nativo C los volcados informativos de FFmpeg (`avutil.av_log_set_level`) en consola, se calibró el dimensionamiento responsivo de los ComboBoxes, se alinearon con precisión de cuadrícula (`QGridLayout`) todos los campos de las tarjetas de protección anti-spam, se resolvieron los errores multiplataforma reportados en **Ubuntu / Linux**, se blindó la sincronización de voces al alternar entre motores TTS, se rediseñó por completo el sistema de búsqueda y selección de categorías (Kick y Twitch) con un componente moderno reutilizable (`CategorySearchComboBox`), se realizó un desacoplamiento arquitectónico estricto (Separation of Responsibilities) eliminando el 100% de las importaciones a nivel de módulo desde `backend` en todo el paquete `frontend/`, se instrumentó un **sistema exhaustivo de auditoría y telemetría de acciones de usuario (`[User Action]`)**, y se corrigió el aislamiento de workers en el desvinculado de cuentas para mantener las sesiones de Twitch activas al desvincular Kick.

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
  - Controladores y Handlers: `DashboardController`, `UpdateController`, `ScheduleController`, `WidgetController`, `MusicController`, `RewardsController`, `SpamController`, `ChatController`, `TTSVoiceHandler`, `TimerController`, `SettingsController`, `NetworkController`, `LogController`.
  - Vistas y componentes: `FilterHeaderView`, `LogView`, `ScheduleView`, `SpamView`, `WidgetsView`, `TimersView`, `SettingsView`, `ScheduleTablePanel`, `ScheduleFormPanel`, `QuickChangePanel`, `WidgetCard`.
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
- **Validador y Fallback de Voz en `WebTTSProvider` (`tts_online.py:50`)**: Se añadió `_resolve_valid_voice()` en el motor online para verificar que la voz sea una voz Neural válida de Edge TTS.

### 12. Modernización del Selector y Búsqueda de Categorías (Kick & Twitch)
- **Componente Reutilizable `CategorySearchComboBox` ([frontend/widgets/category_search.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/category_search.py))**:
  - Estética moderna tipo Combobox con campo de entrada, botón de borrado (`x`) / búsqueda, debounce integrado (300ms) y navegación por teclado (Arriba, Abajo, Enter, Escape).
  - Menú desplegable flotante enriquecido con badges de plataforma (`[KICK]` verde `#2ECD70` y `[TWITCH]` morado `#9146FF`).
  - Flag `WindowStaysOnTopHint` y `raise_()` para que el menú emergente flote siempre sobre diálogos modales sin ser ocultado.
  - **100% Integrado al Sistema de Temas (`theme.py`)**: Cero `setStyleSheet` inline; utiliza `role="category_dropdown"`, `role="category_list"`, `role="badge_kick"`, `role="badge_twitch"` y `role="body"`.

### 13. Desacoplamiento Total y SoR en Todo el Paquete `frontend/`
- **Zero Importaciones a Nivel de Módulo desde `backend` en `frontend/`**:
  - [sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py): Eliminada la importación `APP_VERSION`, inyectada vía `app_version`.
  - [bug_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/bug_report_dialog.py): Eliminado `from backend.workers import BugReportWorker`, inyectado vía `worker_class`.
  - [release_notes_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/release_notes_dialog.py): Eliminado `from backend.workers import ReleaseNotesWorker`, inyectado vía `worker_class`.
  - [crash_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py): Eliminadas todas las importaciones fijas de `backend`, inyectando `webhook_url` y `worker_class` desde `main.py`.
  - [timer_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timer_dialog.py): Cero backend, comunicación por señales Qt puras.

### 14. Instrumentación Exhaustiva de Logs de Acciones de Usuario (`[User Action]`)
Se agregaron trazas estructuradas con formato parametrizado $\mathcal{O}(1)$ en todos los controladores:
- **`MainWindowCore`**: Navegación entre vistas (`[User Action] Navigated to view: '...'`), minimizar/restaurar de la bandeja, confirmar/cancelar salida.
- **`TimerController`**: Apertura de modales, creación, edición, eliminación, alternancia de estado y búsqueda de categorías.
- **`CommandController`**: Creación, edición, renombramiento, eliminación, activación/desactivación y filtrado.
- **`SpamController`**: Modificación de filtros individuales con parámetros y estados previos/nuevos.
- **`ScheduleController`**: Actualización rápida de stream (Kick / Twitch), guardado, eliminación y alternancia de slots de horario.
- **`RewardsController`**: Creación en API/Local, edición, eliminación y previsualización de overlays.
- **`WidgetController`**: Activación/desactivación, comandos, cooldowns, y cambios manuales en contadores de muertes y marcador de victorias/derrotas.
- **`MusicController`**: Cambio de volumen, play/pause, saltar canción, mover/eliminar ítems de cola, alternar comandos `!sr` y auto-resume.
- **`SettingsController`**: Cambio de idioma, fuente, dispositivos de audio (TTS y Música), exportar/importar configuraciones y modales de feedback.
- **`ChatController` / `TTSVoiceHandler`**: Guardado de configuración de chat/TTS, lista de bots silenciados, palabras prohibidas, cambio de motor y pruebas de voz.
- **`NetworkController`**: Solicitud manual de chequeo de conectividad.
- **`LogController`**: Filtrado por nivel, fecha, texto, carga de históricos y apertura de directorios.

### 15. Corrección de Aislamiento de Desvinculación de Cuentas (`MainWindowCore`)
- En `_handle_unlink_account` en [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py), se reemplazó la llamada destructiva `_stop_all_workers()` por `_stop_kick_connection_workers()`.
- Al desvincular Kick, la conexión de Twitch (`Worker_Twitch_Chat_Socket`), el servicio de horarios y los mensajes entrantes de Twitch permanecen completamente activos e intactos.

---

## 🧪 Pruebas Realizadas

1. **Prueba de `faulthandler`**: Verificado `faulthandler.is_enabled() == True` y persistencia en `minikick_crash.log`.
2. **Prueba de Auto-Flush**: Validación de persistencia inmediata en disco de mensajes `CRITICAL` y `ERROR`.
3. **Prueba de Excepciones en Hilos**: Disparo de excepción no controlada en un hilo secundario y verificación del traceback completo en `minikick.log`.
4. **Prueba de Compilación y Limpieza de Terminal**: Verificación de ejecución limpia sin advertencias de Shiboken ni texto verboso de FFmpeg.
5. **Prueba Multiplataforma y Alternancia TTS**: Validación de `tts_local.py`, `tts_online.py` y `kick_client.py` en Linux y Windows.
6. **Prueba de Búsqueda y Relevancia de Categorías**: Validación del algoritmo de ordenamiento con `PEAK`, visualización de insignias de plataforma y scroll para listas de hasta 50 resultados en las 3 vistas.
7. **Prueba MVC End-to-End en Diálogo de Temporizadores**: Verificación del flujo desacoplado `TimerConfigWizard -> TimersView -> TimerController -> ScheduleService -> CategorySearchComboBox` con despliegue interactivo del popup y asignación de datos.
8. **Prueba de Frontend Puro**: Verificación con script automatizado de que todos los diálogos y componentes del frontend instancian limpiamente con cero dependencias duras de backend a nivel de módulo.
9. **Prueba de Trazabilidad $\mathcal{O}(1)$**: Verificación de que todas las acciones de navegación, edición y configuración emiten eventos `[User Action]` inmediatos y seguros en el archivo de registro.
10. **Prueba de Independencia Multi-Plataforma**: Desvinculación de Kick manteniendo `TwitchChatWorker` activo y escuchando eventos en segundo plano.
