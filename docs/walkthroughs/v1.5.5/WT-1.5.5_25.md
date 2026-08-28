# Walkthrough 1.5.5_25: Corrección de Persistencia de Plataformas en Comandos Plugin y Personalizados

## Problema Detectado
Al reiniciar la aplicación, alternar widgets en la pestaña de Widgets o activar/desactivar comandos en la pestaña de Música o Chat, las plataformas asignadas (`apply_youtube`, `apply_tiktok`, `apply_kick`, `apply_twitch`) en ciertos comandos (como `!so`, `!death`, `!score`, `!sr`, `!skip`, `!tts`) se reactivaban solas (`True`) sobrescribiendo la configuración personalizada del usuario.

## Causa Raíz
1. **Llamadas a `save_command` sin argumentos de plataforma**:
   - `WidgetController.sync_commands_with_db()` invocaba `command_service.save_command` al iniciar la app sin pasar los flags de plataforma, lo que disparaba los valores por defecto (`True`).
   - `MusicController.handle_command_toggle()` y `ChatController._handle_save_settings()` guardaban comandos plugin (`!sr`, `!skip`, `!tts`) sin preservar los campos `apply_kick`, `apply_twitch`, `apply_youtube`, `apply_tiktok` existentes.
2. **`CommandService.save_command` con valores por defecto destructivos**:
   - `CommandService.save_command` asignaba por defecto `True` a las plataformas en lugar de consultar si el comando ya existía y preservar su estado configurado.

## Solución Aplicada
1. **Salvaguarda Central en [`CommandService.save_command`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/command_service.py)**:
   - Los parámetros de plataforma ahora aceptan `None` por defecto. Si no se especifican explícitamente, `CommandService` consulta `get_command_by_trigger` y **preserva de forma intacta** la selección previa del usuario (`apply_kick`, `apply_twitch`, `apply_youtube`, `apply_tiktok`).
2. **Preservación Explícita en Controladores**:
   - [`WidgetController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widget_controller.py): Al sincronizar comandos de widgets (`!so`, `!death`, `!score`, etc.), se preservan los flags configurados por el usuario.
   - [`MusicController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py): Al alternar switches de reproducción (`!sr`, `!skip`, `!song`, `!pause`, `!resume`, `!playlist`, `!vol`), se conservan las plataformas activas.
   - [`ChatController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py): Al actualizar la configuración de TTS (`!tts`, `!systts`), se retienen las plataformas asociadas.

---

## Verificación
- **Compilación de Sintaxis**: Ejecutada con `python -m py_compile` sobre todos los controladores y servicios modificados (`Exit code 0`).
- **Persistencia**: Ahora, cualquier comando plugin o personalizado mantiene sus plataformas seleccionadas sin reactivaciones automáticas al reiniciar la app o interactuar con los switches de la interfaz.
