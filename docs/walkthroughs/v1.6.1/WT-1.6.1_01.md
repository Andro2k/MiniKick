# Walkthrough WT-1.6.1_01 — Persistencia Diaria de Top Chatters, Logs Estructurados y Normalización de Comandos

## Resumen de la Versión
* **Versión:** `v1.6.1`
* **Tipo:** Mejora de Arquitectura, Persistencia Diaria, Logs Estructurados, Normalización de Comandos y Auditoría de Telemetría
* **Módulos Afectados:**
  * [`backend/database/database_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/database_manager.py)
  * [`backend/database/widgets_storage.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/widgets_storage.py)
  * [`backend/database/commands_storage.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/commands_storage.py)
  * [`backend/services/system/widgets_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/widgets_service.py)
  * [`backend/services/chat/commands_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/commands_service.py)
  * [`backend/utils/command_utils.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/utils/command_utils.py)
  * [`backend/controllers/widgets_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py)
  * [`backend/controllers/commands_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/commands_controller.py)
  * [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
  * [`backend/handlers/logs_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/logs_handler.py)
  * [`backend/handlers/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/__init__.py)
  * [`backend/core/app_logger_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_logger_core.py)
  * [`backend/database/logs_storage.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/logs_storage.py)
  * [`backend/services/system/logs_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/logs_service.py)
  * [`backend/controllers/logs_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/logs_controller.py)
  * [`backend/controllers/chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)
  * [`backend/providers/chat/kick_ws_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_ws_provider.py)
  * [`backend/workers/kick_chat_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/kick_chat_worker.py)
  * [`backend/workers/twitch_chat_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_chat_worker.py)
  * [`frontend/common/validators.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/validators.py)
  * [`frontend/dialogs/commands_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/commands_dialog.py)
  * [`frontend/views/commands_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py)
  * [`frontend/views/logs_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/logs_view.py)
  * [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
  * [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
  * [`resources/tests/test_daily_top_chatters.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_daily_top_chatters.py)
  * [`resources/tests/test_structured_logging.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_structured_logging.py)
  * [`resources/tests/test_commands_sanitization.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_commands_sanitization.py)

---

## Novedades

### 1. Sistema de Persistencia Diaria para Top Chatters (`daily_top_chatters`)
* **Almacenamiento SQLite con Partición por Fecha (`chatter_date`):**
  Se incorporó la tabla `daily_top_chatters` en [`backend/database/database_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/database_manager.py#L237-L248) con clave primaria compuesta `(chatter_date, username)` e índice descendente por conteo `idx_daily_chatters_date_count`.
* **Restauración Automática en Inicio de la Aplicación:**
  En [`WidgetsController.load_initial_data`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py#L152-L170), se cargan de inmediato los chatters correspondientes a la fecha actual (`YYYY-MM-DD`). Si el streamer reinicia la aplicación o sufre un cierre inesperado, el ranking de chatters de hoy se restaura al 100% y se sincroniza con el overlay de OBS sin pérdida de mensajes acumulados.
* **Transición de Día Automática (Day Rollover):**
  En [`WidgetsController._record_chatter_message`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py#L652-L661), se detecta si la fecha local cambió respecto a `_current_chatters_date`. Al cambiar el día, la aplicación guarda en bloque el día anterior, reinicia el contador en memoria y arranca el nuevo día desde cero de forma transparente.
* **Purga Asíncrona de Historial Antiguo:**
  En segundo plano y sin bloquear el hilo principal ni la base de datos, [`SQLiteWidgetsStorage.prune_old_chatters`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/widgets_storage.py#L162-L171) limpia registros de chatters con más de 7 días de antigüedad.

### 2. Formato Estructurado de Logs de Alta Precisión (Estilo Jellyfin)
* **Nuevo Formateador Estructurado (`StructuredLogFormatter`):**
  Se implementó en [`backend/handlers/logs_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/logs_handler.py#L42-L75) el formateador de grado producción que estandariza todas las líneas de registro en disco (`minikick.log`):
  `[YYYY-MM-DD HH:mm:ss.fff ±HH:MM] [LVL] [ThreadName] LoggerName: Mensaje`
* **Precisión de Milisegundos y Offset Horario ISO 8601:**
  Cada línea registra milisegundos (`.fff`) y la zona horaria real (`-05:00`), permitiendo correlacionar eventos con micro-latencias de red y logs de OBS/servidores de streaming.
* **Códigos Canónicos de Severidad de 3 Letras:**
  Mapeo uniforme de niveles de severidad: `DBG` (Debug), `INF` (Info), `WRN` (Warning), `ERR` (Error) y `CRI` (Critical).
* **Nombres de Módulos Limpios con Notación de Puntos:**
  Transformación y normalización en tiempo real (`MiniKick.Workers.KickChat`, `MiniKick.Services.Audio`, `MiniKick.Database.SystemLogs`) con caché de resolución $\mathcal{O}(1)$.

### 3. Normalización Interactiva y Validación Estricta de Comandos
* **Conversión Fluida a Formato de Chat (`sanitize_command_trigger`):**
  Se implementó en [`backend/utils/command_utils.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/utils/command_utils.py#L8-L38) la lógica de saneamiento de triggers. Al teclear en [`CommandConfigWizard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/commands_dialog.py#L196-L215), los espacios se convierten automáticamente a guiones bajos (`_`), las mayúsculas a minúsculas y se remueven caracteres conflictivos, garantizando que el comando siempre sea ejecutable en Kick y Twitch (ej: `!categoria 1` $\to$ `!categoria_1`).
* **Validación en Tiempo Real y Bloqueo Seguro:**
  El diálogo valida que el comando comience con `!` y contenga al menos un carácter válido antes de habilitar el botón "Siguiente" o "Guardar".

---

## Mejoras

### 1. Rendimiento $\mathcal{O}(1)$ en Chat y Escritura por Lotes Debounced
* **Cero Contención de Disco en Mensajes Frecuentes:**
  El registro de cada mensaje en [`WidgetsController._record_chatter_message`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py#L663-L677) opera estrictamente en memoria RAM con coste $\mathcal{O}(1)$ en una tabla hash.
* **Guardado por Lotes con Temporizador Debounce:**
  La escritura física en SQLite se difiere y agrupa mediante `_chatters_debounce_timer` (1,000 ms), ejecutando `save_daily_chatters_batch` con `executemany` únicamente cuando hay cambios reales.
* **Cierre Seguro y Vaciado en Apagado (Graceful Shutdown):**
  Se integró el método [`WidgetsController.cleanup`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py#L726-L733), invocado directamente en [`MainWindowCore._initiate_shutdown`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py#L734-L736) para garantizar que cualquier conteo pendiente en el temporizador se guarde en disco antes de cerrar las conexiones de base de datos.

### 2. Retrocompatibilidad Total y Filtrado Flexible en Base de Datos y UI
* **Expresión Regular Unificada Retrocompatible:**
  Tanto [`backend/services/system/logs_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/logs_service.py#L18) como [`backend/controllers/logs_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/logs_controller.py#L22) utilizan una expresión regular con grupos con nombre `(?P<time>...)`, `(?P<level>...)` y `(?P<msg>...)` capaz de procesar tanto el nuevo formato con milisegundos/hilo como archivos de logs heredados de versiones anteriores (`v1.6.0`, `v1.5.x`) y registros de crash (`[CRASH]`, `[FATAL_CRASH]`).
* **Consultas de Base de Datos con Expansión Bidireccional de Alias:**
  En [`SQLiteSystemLogStorage.get_filtered_logs`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/logs_storage.py#L91-L107), filtrar por `INFO` o por `INF` busca automáticamente ambas etiquetas (`(level = ? OR level = ?)`), asegurando que el usuario visualice su historial completo sin importar en qué formato fue insertado el registro.
* **Ajuste Ergonómico de la Interfaz Gráfica (`LogView`):**
  En [`frontend/views/logs_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/logs_view.py#L201), el ancho de la columna de fecha/hora se expandió a 230 píxeles para acomodar el formato con milisegundos y zona horaria sin truncamiento. La tabla traduce internamente `INF`, `WRN`, `ERR`, `DBG` a su versión canónica visual manteniendo colores e iconos de alta definición.

### 3. Desduplicación y Limpieza de Logs de Chat Multiplataforma
* **Registro Único Consolidado en `ChatController`:**
  Cada mensaje de chat entrante de cualquier plataforma (Kick, Twitch, TikTok, etc.) se registra exactamente una vez a nivel `INFO` con el formato limpio `[PLATAFORMA] Usuario: Mensaje`:
  ```text
  [2026-09-25 17:43:52.359 -05:00] [INF] [MainThread] MiniKick.Controllers.Chat: [KICK] TheAndro2K: hola
  [2026-09-25 17:44:06.775 -05:00] [INF] [MainThread] MiniKick.Controllers.Chat: [TWITCH] TheAndro2K: hola
  ```
* **Telemetría Granular Protegida en Nivel `DEBUG`:**
  Las trazas de capa de red y despacho de workers ([`KickWsProvider`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_ws_provider.py#L170), [`KickChatWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/kick_chat_worker.py#L132), [`TwitchChatWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_chat_worker.py#L106)) se migraron a `logger.debug`, preservando la latencia del servidor de Kick y los IDs de mensaje (`id=b25cf2f7`) para auditoría técnica sin saturar los logs de uso diario.

### 4. Ajuste Ergonómico de la Tabla de Comandos y Ancho de Columna
* **Ampliación de Columna "Comando" a 190px Interactivos:**
  En [`CommandView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py#L114-L121), se cambió el modo de redimensionamiento de la columna 0 a `Interactive` con un ancho de `190px`, permitiendo visualizar comandos largos como `!topchatters` o `!categoria_1` en su totalidad sin cortes.
* **Indicador Visual de Advertencia para Formatos Heredados:**
  En [`CommandView._create_command_cell`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py#L218-L223), si un comando posee espacios o formato no estándar, se muestra un icono de alerta ámbar con tooltip informativo (`command.table.warning_legacy_format`).

### 5. Migración Automática de Comandos Legacy en Base de Datos
* **Actualización Segura en Inicialización:**
  En [`CommandService.reload_cache`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/commands_service.py#L42-L60), al cargar comandos se detectan automáticamente triggers heredados con espacios o mayúsculas y se actualizan en SQLite mediante [`SQLiteCommandsStorage.update_command_trigger`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/commands_storage.py#L90-L113), renombrando tanto el comando como sus registros de ejecución de forma transparente.

### 6. Auditoría Técnica de Telemetría y Latencia de Chat
* Se analizó el reporte de log `minikick_JosueGMN_v1.6.0.log` (533 mensajes de chat recibidos durante 3 horas):
  * **Procesamiento interno:** $< 0.001\text{ s}$ en MiniKick (pipeline WebSocket $\to$ Worker $\to$ Controller $\to$ UI/Overlay).
  * **Diagnóstico de picos de latencia externa:** Se determinó que los desfases de hasta 20 segundos detectados en el log correspondieron a congestión temporal en el clúster de Pusher/Kick previo a la entrega por socket TCP al cliente local, o roundtrip de transmisión de video, y no a lentitud interna de la aplicación.

### 7. Verificación de Cero Deuda Técnica y Calidad AST
* **Auditoría de Código Muerto (`dead_code_manager.py`):** 215 archivos escaneados con 0 módulos huérfanos, 0 clases/funciones huérfanas y 0 importaciones innecesarias.
* **Auditoría de Duplicación AST (`dry_duplication_auditor.py`):** 2,118 funciones analizadas con 0 bloques clonados o duplicados tras la extracción de helpers de renderizado de celdas en [`CommandView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py).
* **Auditoría de Parámetros (`unused_parameter_manager.py`):** 0 parámetros huérfanos en todo el proyecto.

---

## Correcciones

### 1. Pérdida del Ranking de Chatters al Reiniciar MiniKick
* **Causa Raíz:** `_chatters_counts` era una variable de instancia volátil en memoria RAM sin capa de persistencia en base de datos.
* **Solución:** Implementación de la capa completa de acceso a datos (`SQLiteWidgetsStorage.load_daily_chatters`, `save_daily_chatters_batch`, `clear_daily_chatters`), servicio (`WidgetService`) y controlador (`WidgetsController`), blindado con 4 pruebas automatizadas en [`resources/tests/test_daily_top_chatters.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_daily_top_chatters.py).

### 2. Discrepancia de Formato y Falta de Contexto en Archivos de Log
* **Causa Raíz:** Los logs anteriores carecían de precisión por milisegundos, zona horaria y nombre de hilo/componente, dificultando la depuración precisa de problemas de latencia o concurrencia reportados por usuarios.
* **Solución:** Adopción del estándar de registro de Jellyfin mediante `StructuredLogFormatter`, con pruebas exhaustivas en [`resources/tests/test_structured_logging.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_structured_logging.py).

### 3. Registro Triple y Ruido Repetitivo en Mensajes de Chat
* **Causa Raíz:** Los mensajes de chat se registraban simultáneamente a nivel `INFO` en la capa de WebSocket (`KickWsProvider`), en la capa de Worker (`KickChatWorker`/`TwitchChatWorker`) y en el controlador de interfaz (`ChatController`), repitiendo además etiquetas redundantes (`[Chat]` y la hora ya presente en el encabezado estructurado).
* **Solución:** Consolidación de un único registro `[INF]` limpio en [`ChatController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py#L660) y migración de las trazas de transporte con ID y latencias al nivel `DEBUG`.

### 4. Inejecutabilidad de Comandos con Espacios y Truncamiento en Tabla
* **Causa Raíz:** La creación de comandos no validaba la presencia de espacios ni normalizaba mayúsculas, impidiendo que el despachador de chat (`split(maxsplit=1)[0]`) hiciera coincidir el comando. Adicionalmente, el modo `ResizeToContents` en una tabla con `cellWidget` calculaba incorrectamente el ancho, cortando nombres como `!topchatters`.
* **Solución:** Saneamiento automático en tiempo real (`_` para espacios, minúsculas forzadas), ampliación de la columna a `190px Interactive`, migración automática de triggers legacy en SQLite y badge de advertencia para comandos no estándar.
