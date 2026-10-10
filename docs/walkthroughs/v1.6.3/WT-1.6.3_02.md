# Walkthrough Técnico - v1.6.3 / WT-1.6.3_02

**Versión**: v1.6.3
**Fecha**: 2026-10-09
**Origen**: Auditoría de rendimiento del backend sobre la ruta de recepción de mensajes (WebSockets de Kick, Twitch, YouTube y TikTok).
**Incidente**: INC-023

---

## Novedades

No se introducen funcionalidades nuevas de cara al usuario. El foco de este walkthrough es el rendimiento de la ruta de mensajes y la coherencia de los datos mostrados en el dashboard.

---

## Mejoras

### 1. Nivel de logging configurable (por defecto INFO)

**Archivo**: backend/core/app_logger_core.py

El logger raíz se fijaba incondicionalmente en `DEBUG`, por lo que la aplicación escribía a disco dos o más registros de depuración por cada mensaje de chat y cualquier guarda de depuración resultaba inútil. Ahora el nivel se resuelve mediante la variable de entorno `MINIKICK_LOG_LEVEL` (por defecto `INFO`), tanto para el logger raíz como para el manejador de archivo. Se fija el nivel una sola vez al inicializar y se registra el valor efectivo en el arranque.

### 2. Cálculo de latencia de Kick bajo demanda

**Archivo**: backend/providers/chat/kick_ws_provider.py

El parseo de `created_at` con `datetime.fromisoformat` y el cálculo de latencia se ejecutaban en cada mensaje aunque el log estuviera en INFO. Se envolvieron dentro de `if logger.isEnabledFor(logging.DEBUG)`, de modo que el costo solo se paga al depurar explícitamente.

### 3. Caché en memoria del set de bots ignorados

**Archivos**: backend/controllers/widgets_controller.py, backend/handlers/spam_handler.py, backend/controllers/chat_controller.py

`_record_chatter_message` realizaba una lectura SQLite (`SELECT`) del ajuste `tts_ignored_users` por cada mensaje recibido. Se reemplazó por una caché en memoria de búsqueda O(1) con vencimiento de 30 s y un método de invalidación explícito. La invalidación ahora depende de la nueva señal `ChatController.tts_ignored_users_changed`, que `ChatFilterHandler` emite al añadir, quitar o cargar la lista de bots silenciados. Con esto la señal se dispara en el origen real del dato, no en un evento no relacionado.

### 4. Refresco del dashboard coalescido y con ruta única

**Archivo**: backend/core/main_window_core.py

Cada mensaje repintaba cuatro tarjetas de métricas y la barra de plataformas del dashboard. Ahora los contadores se incrementan en memoria O(1) y el refresco visual se agrupa con un `QTimer` de disparo único de 300 ms, acotando la interfaz a un máximo de aproximadamente tres refrescos por segundo. Se unificó la escritura de UI en un único método `_refresh_dashboard_view()`, eliminando la duplicación que existía entre los dos puntos de actualización. El etiquetado del próximo horario se extrajo a `_sync_next_schedule_label()` y ya no se recalcula por mensaje.

### 5. Memoización del próximo horario con TTL

**Archivo**: backend/services/schedule/schedule_service.py

`get_next_schedule_text()` ordenaba la lista completa de horarios O(k log k) por cada mensaje. Se añadió una memoización con TTL de 30 s y su invalidación al modificar horarios. A diferencia del memo sin vencimiento, el TTL evita que la etiqueta de "próximo horario" quede obsoleta a medida que avanza el día.

### 6. Memoización del texto limpio en el filtro anti-spam

**Archivo**: backend/services/chat/spam_service.py

Varios filtros (caps, símbolos, párrafo y repetición) recalculaban el mismo texto limpio con las mismas expresiones regulares, hasta cuatro veces por mensaje. Ahora el texto se calcula como máximo una vez por variante (`strip_urls` activado o no), dentro de la propia llamada `is_spam`, sin introducir estado persistente.

---

## Correcciones

### 7. Invalidación del caché de bots conectada a un evento incorrecto

**Archivo**: backend/core/main_window_core.py

La invalidación del caché de bots ignorados estaba conectada a `chat_overlay_config_changed`, una señal de configuración del overlay de chat sin relación con la lista de usuarios silenciados. Además, ese flujo de guardado no se ejecuta al usar los comandos `!ttsmute` / `!ttsunmute`, por lo que la caché podía servir datos obsoletos hasta que venciera el TTL. Se corrigió conectándola a `tts_ignored_users_changed`, emitida desde el punto real de mutación de la lista.

### 8. Guarda de depuración sin efecto

**Archivos**: backend/core/app_logger_core.py, backend/providers/chat/kick_ws_provider.py

La guarda `logger.isEnabledFor(logging.DEBUG)` añadida en la ruta de Kick no tenía efecto porque el nivel raíz estaba fijado en `DEBUG`. Con el nivel por defecto en `INFO` (Mejora 1), la guarda ahora sí evita el trabajo cuando no se depura.

### 9. Falso positivo de i18n y test obsoleto

**Archivos**: resources/tests/test_twitch_ws_provider.py (nuevo), resources/tests/test_websocket_architecture.py (eliminado)

La auditoría de i18n reportaba tres claves faltantes (`common.follower`, `common.streamer`, `common.subscriber`) que no se usaban en código de producción: provenían únicamente de un test obsoleto que referenciaba una arquitectura retirada (`BaseChatSocketProvider`, `TwitchEventSubProvider`, `ExponentialBackoff`) y cuyas expectativas ya no coincidían con la implementación vigente. Ese mismo test rompía la colección de pytest. Se eliminó el test muerto y se conservó la cobertura válida en un test nuevo sobre el parseo real de `TwitchSocketManager`. No fue necesario modificar `en.json` ni `es.json`. En la misma pasada se limpiaron los `__pycache__` huérfanos (artefactos de bytecode sin módulo fuente, restos del refactor de renombrado).

---

## Notas de Diseño

- No se introdujo ningún import en el nivel superior del módulo que rompiera la frontera de dependencias. En concreto, `SpamService` mantiene el import diferido de `TwitchSocketManager`, ya que moverlo al nivel de módulo produciría un ciclo de importación real (`providers.chat` -> `services` -> `spam_service` -> `providers.chat`).
- El refresco del dashboard es un *throttle* acotado (300 ms), no un *debounce*: garantiza un máximo de refrescos por segundo independientemente del volumen, manteniendo la interfaz responsiva.

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| backend/core/app_logger_core.py | Mejora - nivel de logging configurable (MINIKICK_LOG_LEVEL, INFO por defecto) |
| backend/providers/chat/kick_ws_provider.py | Mejora - cálculo de latencia bajo guarda DEBUG |
| backend/controllers/widgets_controller.py | Mejora - caché O(1) del set de bots ignorados con invalidación |
| backend/handlers/spam_handler.py | Mejora - callback de cambio de lista de bots ignorados |
| backend/controllers/chat_controller.py | Mejora - nueva señal tts_ignored_users_changed |
| backend/core/main_window_core.py | Mejora/Corrección - refresco coalescido, ruta única y señal de invalidación correcta |
| backend/services/schedule/schedule_service.py | Mejora - memoización con TTL del próximo horario |
| backend/services/chat/spam_service.py | Mejora - memoización del texto limpio por mensaje |
| resources/tests/test_twitch_ws_provider.py | Pruebas - cobertura de TwitchSocketManager (reemplaza test obsoleto) |
| resources/tests/test_websocket_architecture.py | Corrección - eliminado (referenciaba arquitectura retirada) |

---

## Pruebas

- `resources/tests/test_message_path_performance.py` (7 casos): nivel de log por defecto y override, memoización y TTL del próximo horario, memoización del texto limpio del anti-spam, y caché con invalidación del set de bots ignorados.
- `resources/tests/test_twitch_ws_provider.py` (4 casos): parseo de emotes y de líneas PRIVMSG de `TwitchSocketManager`.
- Regresión completa: `resources/tests` en 168 pruebas superadas y 0 errores de colección. Los 2 fallos restantes (`test_daily_top_chatters.py::test_sqlite_widgets_storage_pruning` y `test_linux_auth_and_toast.py::test_modern_toast_dynamic_geometry_scaling`) son preexistentes y ajenos a estos cambios (dependencia de fecha y geometría de fuente, respectivamente).
- Auditoría i18n: 0 claves faltantes, 0 claves sin uso y 100% de paridad entre `en.json` y `es.json`, sin modificar los archivos de locales.
