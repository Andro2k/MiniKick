# Walkthrough - WT-1.5.0_06: Internacionalización y Estandarización de Logs y Webhooks

## Resumen

Se completó la refactorización e internacionalización (i18n) de los 21 archivos backend, providers, servicios y workers del sistema MiniKick, eliminando fallbacks hardcodeados inline (`or "default"`) y aplicando strictly la **Regla 7 de i18n**.

## Cambios Realizados

### Locales
- `locales/es.json` y `locales/en.json`:
  - Añadidas las secciones `common`, `crash`, `logs` y `moderation.reasons` con todas las llaves necesarias para reportes de bugs, reportes de crash, bootstrap, autenticación y razones de moderación.

### Core & Bootstrap
- `main.py`: Reemplazadas las advertencias impresas en español por llaves i18n en `_get_safe_i18n` y `global_crash_handler`.
- `backend/core/app_container_core.py`: Estandarizados los logs de carga de `api_keys.py` y `.install_lang` mediante `TranslationService`.
- `backend/core/main_window_core.py`: Actualizados los toasts e impresiones de error de autenticación en Twitch (`_handle_twitch_auth_process`, `_on_twitch_auth_error`) usando `container.i18n`.

### Providers
- `backend/providers/chat/twitch_client.py`: Refactorizado `TwitchAPIClient` para soportar `i18n`. Reemplazadas excepciones hardcodeadas en español y razones de moderación (timeout/ban) por llaves i18n o inglés neutro.
- `backend/providers/chat/twitch_websocket.py`: Refactorizado `TwitchSocketManager` para aceptar `i18n`. Reemplazado fallback `"Anónimo"` por `common.anonymous` y logs en español por inglés estandarizado.
- `backend/providers/chat/kick_client.py`: Estandarizados los logs internos de `KickAPIClient`.
- `backend/providers/music/youtube_client.py`: Pasada la instancia `i18n` a `YouTubeResolveWorker` en llamadas de precarga y reproducción.

### Services
- `backend/services/chat/command_service.py`: Estandarizados los logs de envío de mensajes a Twitch y Kick.
- `backend/services/system/instance_services.py`: Estandarizado el log de limpieza de socket de instancia.

### Workers
- `backend/workers/bug_report_worker.py`: Reemplazada la plantilla de Discord Webhook hardcodeada en español por llaves dinámicas i18n (`dialogs.bug_report.*`) y fallback de usuario anónimo `common.anonymous`.
- `backend/workers/crash_report_worker.py`: Refactorizado `_get_text()` para eliminar fallbacks inline con `or` (Regla 7). Toda la plantilla del reporte de fallos ahora se construye mediante `self.i18n.get("crash.*")`.
- `backend/workers/music_worker.py`: Añadido soporte de `i18n` en `YouTubeResolveWorker` y reemplazada la cadena hardcodeada `'Unknown Title'` por `music.player.unknown_song`.

## Verificación

- Se ejecutó la compilación de sintaxis Python (`py_compile`) sobre los 21 archivos sin ningún error:
  `uv run python -m py_compile main.py backend/core/app_container_core.py backend/core/main_window_core.py backend/providers/chat/kick_client.py backend/providers/chat/twitch_client.py backend/providers/chat/twitch_websocket.py backend/providers/music/youtube_client.py backend/providers/voices/tts_local.py backend/providers/voices/tts_online.py backend/services/chat/command_service.py backend/services/chat/spam_service.py backend/services/chat/tts_service.py backend/services/rewards/media_trigger.py backend/services/system/instance_services.py backend/services/system/translation_service.py backend/workers/bug_report_worker.py backend/workers/crash_report_worker.py backend/workers/music_worker.py backend/workers/rewards_worker.py backend/workers/timers_worker.py`
  - **Resultado**: Código de salida 0.
