# Walkthrough: Estabilidad Multiplataforma, Optimizaciones de Rendimiento y Mejoras de Interfaz (v1.5.0)

## Resumen Ejecutivo

Este documento consolida las mejoras arquitectónicas, optimizaciones de rendimiento, correcciones de concurrencia y ajustes de interfaz implementados en la versión 1.5.0:

1. **Aislamiento y Autonomía de Autenticación** (Twitch Standalone / Kick Standalone).
2. **Control de Lectura TTS por Roles y Layout Responsivo de Chat**.
3. **Serialización Segura de Backups (Base64 para BLOBs y Programaciones)**.
4. **Optimización de Base de Datos SQLite (Concurrencia e Índices B-Tree)**.
5. **Renderizado Instantáneo de Chat y Poda por Lotes en UI**.
6. **Sincronización de Estado y Setters en ChatView (`!systts`)**.
7. **Persistencia de Filtros y Búsqueda en Vista de Comandos**.
8. **Enrutamiento Multiplataforma para Comandos de Widgets (Twitch / Kick)**.
9. **Componentes Especializados `NoWheelDateEdit` / `NoWheelTimeEdit` y Estilización de `QCalendarWidget`**.
10. **Estabilidad del WebSocket IRC de Twitch (Eliminación de Timeout y Keepalive Nativo)**.

---

## 1. Aislamiento de Autenticación de Plataformas

- **Desacoplamiento de `TwitchAuthManager` ([`oauth_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py))**:
  - `get_tokens()` opera de forma pasiva: si no existen credenciales, retorna `{}` sin abrir el navegador ni forzar inicios de sesión.
  - El flujo de login solo se dispara tras una acción explícita del usuario desde la vista de integraciones mediante [`TwitchAuthWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_auth_worker.py).
- **Protección en `TwitchAPIClient` ([`twitch_client.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_client.py))**:
  - `is_authenticated()` y verificación en `_request()` previenen peticiones salientes si no existe token válido.
- **Aislamiento en `ScheduleService` ([`schedule_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/schedule/schedule_service.py))**:
  - Las consultas y actualizaciones a Kick funcionan independientemente de si Twitch está conectado o desconectado.

---

## 2. Control de TTS por Roles y Rediseño de Layout en Chat

- **Switches de Activación por Rol ([`tts_settings.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py))**:
  - Cada rol cuenta con una fila compacta: `[ Switch On/Off ]` + `[ ComboBox de Voz ]` + `[ Botón Probar ]`.
  - Se eliminaron descripciones estáticas redundantes y anchos mínimos rígidos (`setMinimumWidth(180)`), permitiendo que la tarjeta se redimensione fluidamente sin desbordarse al cambiar el tamaño de la ventana.
- **Filtrado $O(1)$ en Tiempo Real ([`tts_voice_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/tts_voice_handler.py))**:
  - `is_role_enabled(badges, settings)` consulta los booleanos de cada rol (`tts_role_enabled_*`) antes de enviar texto a la síntesis de voz.

---

## 3. Serialización Segura de Backups (Base64)

- **Sanitización de BLOBs ([`backup_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/backup_service.py))**:
  - Se implementó `_sanitize_for_json()` para convertir datos binarios (`thumbnail_bytes` de recompensas OBS) en cadenas Base64 seguras para JSON, y `_restore_from_sanitized()` para decodificarlos en la restauración.
- **Respaldo de Programaciones (`stream_schedules`)**:
  - Se integró `schedule_storage` en el servicio de backup y se registró en [`app_container_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py).

---

## 4. Auditoría y Optimización de Base de Datos SQLite

- **Prevención de Bloqueos Multihilo ([`manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py))**:
  - Se configuró `PRAGMA busy_timeout = 5000` y `timeout = 10.0` en cada conexión SQLite, eliminando bloqueos `database is locked`.
- **Indexación B-Tree $O(\log n)$**:
  - Se crearon los índices `idx_system_logs_level_timestamp`, `idx_system_logs_timestamp` y `idx_youtube_cache_play_count`.
- **Límite Acotado en Búsqueda Difusa ([`music_storage.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/music_storage.py))**:
  - Se restringió el escaneo fuzzy a las 150 canciones más reproducidas (`ORDER BY play_count DESC LIMIT 150`), asegurando ejecución $\mathcal{O}(1)$ en memoria y CPU.

---

## 5. Renderizado Instantáneo de Chat y Poda por Lotes

- **Pipeline Optimizado ([`chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py))**:
  - `_step_ui_render()` se reubicó inmediatamente al inicio del pipeline. El mensaje se dibuja en pantalla en **0 ms** antes de ejecutar plugins, comandos y síntesis de voz.
- **Poda Atómica por Lotes ([`chat_display.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/chat_display.py))**:
  - `_trim_chat_history()` utiliza un búfer de holgura (+20 bloques) y selección atómica continua (`MoveMode.KeepAnchor`) en lugar de bucles iterativos bloqueantes en el hilo de la UI.

---

## 6. Sincronización de Estado y Setters en ChatView

- **Setters en `ChatView` ([`chat_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py))**:
  - Se implementaron `@tts_enabled.setter`, `@read_name_enabled.setter`, `@use_command_enabled.setter`, `@tts_command.setter` y `@tts_volume.setter`.
  - Permite que comandos de chat como `!systts on` y `!systts off` actualicen el switch de la interfaz gráfica sin lanzar excepciones de atributo.

---

## 7. Persistencia de Filtros y Búsqueda en Vista de Comandos

- **Sincronización en Memoria ([`command_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/command_view.py))**:
  - Al accionar el switch de activar/desactivar un comando dentro de una búsqueda filtrada, `self._raw_commands` se actualiza inmediatamente en memoria.
  - Al limpiar el buscador o cambiar filtros de rol/tipo, la tabla mantiene con precisión el estado actualizado de cada comando.

---

## 8. Enrutamiento Multiplataforma de Comandos de Widgets

- **Soporte Bidireccional Kick / Twitch ([`chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) & [`widget_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widget_controller.py))**:
  - La señal `widget_plugin_triggered` ahora incluye el parámetro `platform`.
  - Todos los comandos de widgets (`!muerte`, `!death`, `!so`, `!score`, `!win`) responden directamente por la plataforma desde la que se invocaron (Twitch IRC o Kick API).
  - La URL del widget de Shoutout genera el enlace correspondiente (`twitch.tv` o `kick.com`).

---

## 9. Controles `NoWheelDateEdit` / `NoWheelTimeEdit` y Estilización de Calendario

- **Aislamiento de Scroll y Subcontroles ([`utils.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/utils.py) & [`theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py))**:
  - Se crearon `NoWheelDateEdit` y `NoWheelTimeEdit` ignorando `wheelEvent`, impidiendo que el scroll del ratón altere accidentalmente la fecha o la hora.
  - Se anularon los subcontroles `::up-button` y `::down-button` de `QDateEdit` para evitar clics accidentales de incremento.
- **Estilización de `QCalendarWidget`**:
  - Iconos de navegación `chevron-left.svg` y `chevron-right.svg` actualizados a blanco brillante (`stroke="#FFFFFF"`).
  - Ocultación del `menu-indicator` nativo bajo el botón de mes.
  - Restablecimiento del color de texto de sábados y domingos a color neutral (`COLOR_NEUTRAL_200`), eliminando el texto rojo por defecto de Qt.

---

## 10. Estabilidad del WebSocket IRC de Twitch

- **Eliminación del Bucle de Desconexión ([`twitch_websocket.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_websocket.py))**:
  - Se configuró `run_forever(ping_interval=0)`, desactivando el timeout de ping WebSocket y delegando el keepalive al protocolo `PING`/`PONG` nativo de texto IRC de Twitch.
- **Sincronización en Tiempo Real ([`twitch_chat_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_chat_worker.py) & [`main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py))**:
  - Se agregaron las señales `connection_lost` y `connection_restored` para actualizar en tiempo real el indicador de estado de Twitch en la interfaz ante cualquier caída o reconexión de red.

---

## Verificación

- Suite completa de pruebas automatizadas (`uv run pytest`):
  - **57 / 57 pruebas unitarias aprobadas exitosamente** (100% de cobertura funcional).
