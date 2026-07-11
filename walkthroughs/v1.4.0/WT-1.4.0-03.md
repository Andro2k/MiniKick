---
id: WT-1.4.0-03
feature: Controller Lazy Loading, TTS Command Database Linkage, Chat History Fixes, and Input Validation
date: 2026-07-10
components: [chat_controller.py, chat_view.py, command_dialog.py, rewards_dialog.py, main_window_core.py]
description: Optimized application startup by lazy loading dependencies in controllers, integrated TTS command prefix with command database, enabled displaying command messages in room history, fixed HTML rendering for point redemptions, and implemented input validation alerts with disabled wizard buttons.
---

# Resumen de Cambios (Walkthrough) - Integración de Chat, Comandos y Validaciones

Se han realizado optimizaciones de rendimiento en la carga de módulos, validaciones en tiempo de escritura en formularios con bloqueo de navegación, vinculación del comando TTS en la base de datos e inclusión de los comandos en el historial de sala.

## Cambios Realizados

### 1. Lazy Loading (Carga Perezosa) en Controladores
- Modifiqué los 6 controladores principales en `backend/controllers/` para posponer la importación de clases pesadas (diálogos, asistentes visuales, proveedores de audio externos e hilos de procesamiento de fondo) hasta el método preciso en donde son instanciados.
- **Controladores optimizados**:
  - [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) (`VoiceFetcherWorker`)
  - [command_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/command_controller.py) (`CommandConfigWizard`)
  - [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py) (`SpotifyAuthWorker`, `SpotifyMusicProvider`, `YouTubeMusicProvider`)
  - [timer_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/timer_controller.py) (`TimerConfigWizard`)
  - [rewards_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/rewards_controller.py) (`RewardsConfigWizard`)
  - [update_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/update_controller.py) (`UpdateDialog`, `UpdateCheckWorker`, `UpdateDownloadWorker`)
- **Impacto**: Reduce notablemente los tiempos de carga inicial del programa y elimina el riesgo de importaciones circulares en el arranque.

### 2. Sincronización Bidireccional del Comando TTS
- Vinculé el comando TTS (`!tts`) con la base de datos de comandos administrada por `CommandService` usando el identificador de respuesta `[PLUGIN_CHAT_TTS]`.
- Se implementó sincronización bidireccional:
  - Guardar la configuración del Chat crea, actualiza, renombra o deshabilita este comando en la base de datos general.
  - Alternar o renombrar el comando desde la vista de Comandos (`command_view.py`) actualiza automáticamente los valores y controles de la pestaña Chat.

### 3. Comandos Visibles en el Historial de Sala
- Modifiqué el paso `_step_commands` en [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) para marcar los mensajes que coinciden con comandos como `dto.is_command = True` en lugar de abortar el pipeline con `dto.is_cancelled = True`.
- Esto permite que los mensajes de comando (`!sr`, `!skip`, comandos personalizados) fluyan hasta renderizarse en el panel del Historial de Sala de la UI, mientras que `_step_tts` los descarta para evitar que la voz automática los lea, excepto el comando TTS que se procesa y lee de forma limpia.

### 4. Renderizado HTML en Canjes de Puntos
- Actualicé la firma y comportamiento de `append_message` en [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py) para admitir un parámetro opcional `is_html: bool = False`.
- Modifiqué [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py) para procesar los canjes de recompensas escapando variables dinámicas de forma segura, y luego pintar el mensaje de canje estilizado en verde (`#00e701`) pasando `is_html=True`, evitando que se renderice el código HTML crudo en el chat.

### 5. Validación Visual y Desactivación de Botones en Asistentes
- **Borde Rojo en Prefijos**: Modifiqué la validación en caliente de prefijos en la pestaña Chat (`chat_view.py`) y en el asistente de creación de comandos (`command_dialog.py`). Si el texto no está vacío y no empieza con `!`, el campo de entrada (`QLineEdit`) se dibuja con un borde rojo (`border: 1px solid #ff4444;`).
- **Bloqueo en Diálogo de Comandos**: En [command_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/command_dialog.py), el botón "Save" / "Next" se mantiene deshabilitado hasta que el trigger comience con `!` y la respuesta no esté vacía.
- **Bloqueo en Diálogo de Recompensas**: En [rewards_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py), el botón "Next" se deshabilita si no hay una recompensa válida seleccionada (descartando selectores temporales de carga o sin datos) o si no se ha buscado y cargado un archivo multimedia.
