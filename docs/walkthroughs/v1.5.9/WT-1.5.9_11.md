# Walkthrough WT-1.5.9_11: Control de TTS por Plataforma y Comandos de Moderación en Chat

## Novedades

- **Control Granular de TTS por Plataforma**:
  - Se añadieron switches independientes en el panel de configuración de TTS ([`tts_settings.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)) para activar o pausar la lectura de mensajes por voz de forma selectiva por plataforma: **Kick**, **Twitch**, **YouTube** y **TikTok**.
  - Los switches están acompañados de sus respectivos logos SVG y colores corporativos oficiales (#53FC18 para Kick, #9146FF para Twitch, #FF0000 para YouTube y #00F2FE para TikTok).
  - La selección por plataforma es independiente y complementa la asignación de voces y roles por jerarquía (broadcaster, moderator, vip, subscriber, everyone).

- **Comandos de Moderación de Chat en Tiempo Real**:
  - Registro automático en `CommandService` con nivel de permisos de moderador (`permission="moderator"`) y cooldown de 2 segundos:
    - `!ttsmute <usuario>` (alias: `!mutetts`, `!silenciartts`): Añade al usuario objetivo a la lista de bots/usuarios ignorados por el TTS y actualiza la lista visual y la base de datos SQLite.
    - `!ttsunmute <usuario>` (alias: `!unmutetts`, `!desilenciartts`): Remueve al usuario de la lista de silenciados y actualiza los tags de la interfaz gráfica en tiempo real.
    - `!ttsblock <palabra>` (alias: `!blockword`, `!censurartts`): Añade la palabra indicada a la lista de palabras censuradas del TTS.
    - `!ttsunblock <palabra>` (alias: `!unblockword`, `!descensurartts`): Elimina la palabra de la lista de términos censurados y sincroniza la UI.
  - Respuestas automáticas localizadas enviadas a la plataforma de origen confirmando la acción, alertando si el elemento ya existía o notificando si no fue encontrado.

- **Sincronización Dinámica de Tags en la UI**:
  - Métodos `remove_bot_tag` y `remove_word_tag` agregados en [`bot_mute.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py) y delegados en [`chat_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py) para remover visualmente los chips/tags cuando un moderador ejecuta un comando desde el chat mientras la aplicación está abierta.

---

## Mejoras

- **Eficiencia $\mathcal{O}(1)$ en Pipeline de Chat**:
  - Verificación en tiempo constante $\mathcal{O}(1)$ en `_step_tts` y `_handle_plugin_tts` dentro de [`chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) usando el prefijo `platform_{platform}`.
  - Si la plataforma del mensaje está inactiva en la configuración, el pipeline aborta la síntesis de inmediato antes de procesar expresiones regulares de emoticonos o enviar peticiones al motor TTS.

- **Internacionalización Rigurosa (i18n)**:
  - Todas las cadenas para nombres, descripciones y respuestas de chat fueron añadidas en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) bajo los namespaces `chat.platforms.*` y `chat.commands.*`.
  - Cero cadenas de texto hardcodeadas y cero valores por defecto usando `or` inline en la UI.
  - Validación completa con `test_i18n_integrity.py` verificando paridad 100% entre archivos de idioma y presencia de todas las claves requeridas.

- **Persistencia de Configuración**:
  - `ChatService.get_settings()` y `ChatService.save_settings()` soportan `platform_kick`, `platform_twitch`, `platform_youtube` y `platform_tiktok` manteniendo consistencia total con SQLite.

---

## Correcciones

- **Inicialización Headless y Manejo Seguro de Vista**:
  - Corrección de excepción `AttributeError: 'NoneType' object has no attribute 'clear_bots_list'` en `ChatFilterHandler.initialize_from_settings()` cuando se ejecuta el controlador en entornos sin vista (pruebas unitarias o modo headless).
  - Garantía de que `_tts_settings_cache` y los filtros de moderación se inicializan correctamente al instanciar `ChatController` incluso antes de adjuntar una vista.

- **Filtrado Consecuente en Invocaciones por Comando**:
  - Se corrigió `_handle_plugin_tts` para validar `platform_{platform}` de la misma manera que el procesamiento directo en `_step_tts`, impidiendo que mensajes con `!tts` se sinteticen si la plataforma está desactivada.
