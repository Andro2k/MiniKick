# Walkthrough - WT-1.5.0_02: Integración Multi-Plataforma, Moderación Anti-Spam y Estabilización General (v1.5.0)

## Resumen General

Documento consolidado de la versión **v1.5.0** de MiniKick. Resume la totalidad de las características, mejoras arquitectónicas y soluciones a errores implementadas durante este ciclo:

1. **Moderación Anti-Spam Configurable por Plataforma (Kick & Twitch)**: Switches independientes por regla y enrutamiento dinámico de sanciones sin errores HTTP 404.
2. **Scopes de Moderación de Twitch y Consentimiento Forzado**: Integración de permisos de moderador (`moderator:manage:chat_messages`, `moderator:manage:banned_users`, `user:write:chat`), flag `force_verify=true` para re-autenticación limpia y banner unificado de permisos faltantes.
3. **Acumulación de Chat en Segundo Plano**: Búfer en memoria (`deque(maxlen=200)`) en `ChatController` para guardar y reproducir el historial recibido antes de abrir la pestaña de Chat.
4. **Aislamiento Estricto de Filtros Anti-Spam**: Sanitizador `_get_clean_text()` en `SpamService` que elimina emoticones (Kick y Twitch) y enlaces antes de evaluar mayúsculas, símbolos, párrafos o repeticiones, erradicando el 100% de los falsos positivos cruzados.
5. **Lectura Continua en TTS Local (SAPI5)**: Re-inicialización limpia de `pyttsx3` y la pila COM (`pythoncom`) por cada frase a sintetizar.
6. **Renderizado de Respuestas del Bot y Prevención de Duplicados**: Captura de respuestas generadas por comandos para Twitch (`_handle_bot_response`) respetando el eco nativo de Kick para evitar mensajes duplicados.
7. **Orden Cronológico de Chat e Identidad Dinámica**: Reordenamiento del pipeline (`_step_ui_render` antes que `_step_commands`) y resolución dinámica del nombre de la cuenta emisora (`TheAndro2K` / `bot_nick`).

---

## 1. Moderación Anti-Spam Configurable por Plataforma (Kick & Twitch)

### 1.1. Interfaz Gráfica (`frontend/widgets/blocks.py` & i18n)
- **[blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py):**
  - Incorporados switches independientes `switch_kick` y `switch_twitch` (`ModernSwitch`) en cada tarjeta expandible (`ExpandableSettingCard`).
  - Los eventos `updated` emiten el estado de activación por plataforma (`apply_kick` y `apply_twitch`).
  - `set_data()` carga y refleja los valores persistidos en la base de datos.
- **Traducciones ([es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) / [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)):**
  - Añadidas las claves i18n: `spam.card.platforms`, `spam.card.platform_kick` y `spam.card.platform_twitch`. Zero hardcoded UI text.

### 1.2. Base de Datos y Migración Automática (`backend/database/`)
- **[manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py):**
  - Añadidas las columnas `apply_kick INTEGER DEFAULT 1` y `apply_twitch INTEGER DEFAULT 1` a la tabla `spam_filters`.
  - Migración automática integrada en `_upgrade_schema()` mediante `ALTER TABLE` para esquemas existentes.
- **[spam_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/spam_storage.py):**
  - `load_all()` y `save_filter()` actualizados para soportar los flags de plataforma.

### 1.3. Servicio de Moderación y Enrutamiento (`backend/services/chat/spam_service.py`)
- **[spam_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/spam_service.py):**
  - `is_spam()` recibe el parámetro `platform` (e.g. `"kick"` o `"twitch"`) y omite reglas desactivadas para la plataforma del mensaje.
  - `_apply_penalty()` enruta las sanciones dinámicamente:
    - **Kick**: ejecuta peticiones HTTP mediante `KickAPIClient`.
    - **Twitch**: ejecuta peticiones HTTP vía `TwitchAPIClient` o comandos IRC vía `TwitchChatWorker`, previniendo errores HTTP 404 por solicitudes cruzadas.

---

## 2. Autenticación OAuth de Twitch, Scopes y Banner de Permisos Faltantes

### 2.1. Scopes y Consentimiento Forzado (`backend/services/auth/oauth_service.py`)
- **[oauth_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py):**
  - Agregados los alcances de moderación: `moderator:manage:chat_messages`, `moderator:manage:banned_users` y `user:write:chat`.
  - Implementados los métodos `get_missing_scopes()` y `has_missing_scopes()` en `TwitchAuthManager`.
  - Adición de `force=True` en `get_tokens()` para adjuntar `&force_verify=true` en la URL de OAuth, forzando la pantalla de autorización del navegador y evitando tokens antiguos.

### 2.2. Banner de Permisos y Diagnóstico (`frontend/core/main_window_core.py`)
- **[main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py):**
  - Botón de desvincular/re-vincular de Twitch ejecuta `_handle_twitch_auth_process(force=True)`.
  - `_on_twitch_connected()` evalúa de forma combinada los permisos faltantes de Kick y Twitch, actualizando la barra de notificación del Panel de Control.
  - El botón "Actualizar Permisos" del banner inicia un flujo directo con `force=True`.

---

## 3. Acumulación de Chat e Aislamiento de Filtros Anti-Spam

### 3.1. Búfer de Historial de Chat (`backend/controllers/chat_controller.py`)
- **[chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py):**
  - Inicializado `self._message_buffer = deque(maxlen=200)` en el constructor.
  - En `_step_ui_render`, cada mensaje procesado por el pipeline se registra en la cola con sus metadatos (usuario, contenido, color, timestamp, rol y plataforma).
  - Al invocar `attach_view(view)` (al abrir la pestaña Chat por primera vez), se reproducen todos los mensajes acumulados en `ChatView`.

### 3.2. Sanitización y Aislamiento de Filtros (`backend/services/chat/spam_service.py`)
- **[spam_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/spam_service.py):**
  - `_get_clean_text(message, emotes_tag, strip_urls)` remueve emoticones de Kick (`[emote:123:Name]`), emoticones de Twitch y enlaces URL.
  - **`caps_protection`**: Calcula mayúsculas sobre texto libre de emoticones y enlaces.
  - **`symbol_protection`**: Mide caracteres extraños omitiendo etiquetas de emotes.
  - **`paragraph_protection`**: Evalúa longitud de párrafo sobre texto limpio.
  - **`repetition_protection`**: Analiza repetición de palabras en texto limpio.

---

## 4. Síntesis de Voz Continua (TTS Local / SAPI5 Windows)

- **[tts_local.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_local.py):**
  - Se refactorizó `LocalTTSProvider.speak()` para crear y destruir una nueva instancia de `pyttsx3.init()` dentro de un bloque seguro por hilo con `pythoncom.CoInitialize()` y `pythoncom.CoUninitialize()` por cada frase.
  - Corrige el congelamiento del motor tras la primera frase y garantiza lectura continua de todos los mensajes.

---

## 5. Renderizado de Respuestas del Bot e Identidad de Emisor

### 5.1. Emisión de Respuestas y Prevención de Duplicados en Kick
- **[command_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/command_service.py):**
  - Añadida la señal `response_generated = Signal(str, str)`.
- **[chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py):**
  - `_handle_bot_response()` captura `response_generated` y restringe el renderizado local exclusivamente a Twitch (`if not text or platform != "twitch": return`).
  - Para Kick, la aplicación utiliza como fuente única su WebSocket oficial de Pusher (que retransmite los mensajes del bot automáticamente), eliminando entradas duplicadas.

### 5.2. Orden Cronológico del Pipeline de Chat
- **[chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py):**
  - `_build_pipeline()` reordenado a:
    1. `_step_spam`
    2. `_step_ui_render` (Despliega el mensaje del espectador en la UI)
    3. `_step_commands` (Ejecuta el comando y emite la respuesta del bot inmediatamente después)
    4. `_step_tts`
  - Garantiza que en `ChatDisplay` aparezca primero el comando del usuario y posteriormente la respuesta del bot.
- **Identidad Dinámica**: `_handle_bot_response` consulta dinámicamente `twitch_worker.bot_nick` o `channel_name` (ej. `TheAndro2K`), asociando el emisor real a la interfaz.

---

## 6. Pruebas Automatizadas (Pytest)

- **[test_spam_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_spam_service.py)**: Pruebas para filtrado específico por plataforma e inmunidad de emotes en mayúsculas.
- **[test_twitch_auth.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_twitch_auth.py)**: Pruebas de verificación de scopes faltantes de Twitch.
- **[test_tts_local.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_tts_local.py)**: Prueba de habla continua en `LocalTTSProvider`.
- **[test_command_parser.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_command_parser.py)**: Prueba de emisión de señales en `CommandService`.

### Resultado de la Suite Completa:
```powershell
uv run pytest
```
```text
============================= 31 passed in 7.58s ==============================
```
