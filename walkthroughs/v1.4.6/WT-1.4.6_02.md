# Walkthrough v1.4.6 (02) - Comando `!systts` para Moderadores y Mensajería Secundaria para Colas Largas de Usuarios

**Fecha:** 31 de Julio, 2026  
**Versión Target:** v1.4.6  
**Ubicación del Documento:** `c:\Users\TheAn\Desktop\python\Kick\walkthroughs\v1.4.6\WT-1.4.6_02.md`

---

## 1. Resumen de Cambios

En esta actualización se incorporan dos nuevas funcionalidades requeridas para el bot de Kick:

- **Comando `!systts on/off` de Control Global de TTS (Moderadores)**:
  - **Restricción de Permisos (`permission="moderator"`)**: Comando exclusivo para moderadores y el broadcaster/streamer.
  - **Manejo de Subcomandos (`on`/`off`/`status`)**: Permite activar (`!systts on`/`1`/`activar`), desactivar (`!systts off`/`0`/`desactivar`) o consultar el estado del sintetizador TTS desde el chat.
  - **Persistencia y Sincronización GUI**: Sincroniza la configuración en la base de datos SQLite (`settings["enabled"]`), emite la señal `tts_state_changed` para refrescar la interfaz gráfica y el System Tray, y envía una respuesta informativa en el chat de Kick.
  - **Recreación Automática al Guardar Ajustes**: En `_handle_settings_save()`, se verifica que el comando `[PLUGIN_CHAT_SYSTTS]` se re-cree en la base de datos de comandos si fue eliminado manualmente por el usuario.

- **Paginación / Mensajes Secundarios para Colas Extensas (`!playlist` / `!queue`)**:
  - **Fragmentación en Bloques (`MAX_PER_MSG = 8`)**: En `MusicController._handle_plugin_playlist()`, las posiciones asignadas a un usuario en la cola de reproducción se dividen en fragmentos de máximo 8 posiciones por mensaje.
  - **Respuestas Secundarias en Chat**: Si un usuario tiene más de 8 canciones en cola (por ejemplo, al solicitar una lista de reproducción larga), el bot publica un primer mensaje con las primeras 8 posiciones y el conteo total, seguido inmediatamente por mensajes secundarios numerados (`pt. 2/3`, `pt. 3/3`, etc.) conteniendo los números de posición restantes, evitando truncados o límites de caracteres en Kick chat.

---

## 2. Detalles de los Archivos Modificados

### A. Idiomas y Traducciones (Locales)
- **Archivos:** [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json), [default_en_locale.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py)
- **Cambios:**
  - Añadidas las claves de traducción para el estado del TTS: `chat.status.systts_on`, `chat.status.systts_off`, `chat.status.systts_status`, `chat.status.systts_usage`, `chat.status.enabled_upper` y `chat.status.disabled_upper`.
  - Añadida la clave `music.chat.playlist_user_songs_more` para las respuestas secundarias de posiciones en cola.

- **[chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)**:
  - Registrado el comando por defecto `!systts` asociado a `[PLUGIN_CHAT_SYSTTS]` con permiso `moderator` y cooldown de 3 segundos en `_load_initial_data()`.
  - En `_step_commands()`, capturado `[PLUGIN_CHAT_SYSTTS]` y manejado a través del método `_handle_systts_command(user, arg)`.
  - `_handle_systts_command`: Permite encender (`on`/`1`/`activar`), apagar (`off`/`0`/`desactivar`) o consultar el estado (`status`). Sincroniza la configuración persistente en SQLite, emite la señal `tts_state_changed` y envía una respuesta al chat.
  - En `_handle_settings_save()`, verificación y re-creación automática del comando `[PLUGIN_CHAT_SYSTTS]` si fue eliminado de la tabla de comandos.
  - **Lectura TTS en Comandos Regex**: Ajustado `_step_commands()` para que las coincidencias por Expresiones Regulares (regex commands como `!hola` con patrones `hola|saludos|buenas`) **no** marquen el mensaje como `is_command = True`. De esta manera, el bot envía la respuesta automática del comando en el chat y al mismo tiempo lee el mensaje del usuario por TTS (ej. "hola como estas").

### C. Controlador de Música (`MusicController`)
- **Archivo:** [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py)
- **Cambios:**
  - En `_handle_plugin_playlist()`, implementación de la fragmentación de posiciones del usuario en bloques de 8 y emisión de mensajes de continuación (`playlist_user_songs_more`).

---

## 3. Lista de Archivos Modificados

- [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
- [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
- [backend/config/default_en_locale.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py)
- [backend/controllers/chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)
- [backend/controllers/music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py)

---

## 4. Verificación y Validación

- **Compilación de Sintaxis**: Se ejecutó `python -m py_compile` validando que todos los archivos modificados sintácticamente son 100% válidos.
- **Verificación de Lógica de Fragmentación**: Se validó mediante un script de prueba que listas largas de cola de usuario (ej. 21 canciones) generan correctamente mensajes secuenciales numerados (`pt 1/3`, `pt 2/3`, `pt 3/3`).
