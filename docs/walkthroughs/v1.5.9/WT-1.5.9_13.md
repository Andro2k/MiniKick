# Walkthrough WT-1.5.9_13: Consolidación a 2 Comandos de Moderación, Sincronización Reactiva y Prevención de Crash en QThread

## Novedades

- **Consolidación de Comandos de Moderación a 2 Comandos Maestros (`!ttsmute` y `!ttsblock`)**:
  - Se unificaron los 4 comandos previos de moderación de chat en sólo 2 comandos maestros en [`chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py), siguiendo el patrón consolidado de `!score`:
    - **`!ttsmute`**: Permite silenciar usuarios por defecto (`!ttsmute @usuario` o `!ttsmute add @usuario`), y desilenciarlos mediante subcomandos (`!ttsmute unmute @usuario`, `!ttsmute remove @usuario`, `!ttsmute - @usuario`) o alias dedicados (`!unmutetts`, `!desilenciartts`).
    - **`!ttsblock`**: Permite censurar palabras o frases por defecto (`!ttsblock palabra` o `!ttsblock add palabra`), y desbloquearlas mediante subcomandos (`!ttsblock unblock palabra`, `!ttsblock remove palabra`, `!ttsblock - palabra`) o alias dedicados (`!unblockword`, `!descensurartts`).
  - Previene la fragmentación de comandos en la base de datos y evita desincronizaciones si el usuario eliminaba un comando individual.
- **Sincronización Reactiva Bidireccional y Regeneración Automática de Comandos de Moderación**:
  - Se implementó el patrón de sincronización reactiva equivalente al de música (`MusicCommandsPanel` / `MusicController`):
    - Si `!ttsmute` o `!ttsblock` son eliminados de la base de datos (por ejemplo, desde la vista general de Comandos), los switches correspondientes (`sw_cmd_mute` y `sw_cmd_block`) en [`bot_mute.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py) se desactivan automáticamente (`False`).
    - Si el usuario vuelve a encender el switch en la interfaz, `ChatController._sync_command_active_state()` regenera de forma autónoma el comando en la base de datos con sus metadatos por defecto intactos (permiso `"moderator"`, cooldown de 2s, alias completos y plataformas activas) a través de `_DEFAULT_MOD_COMMANDS`.
- **Migración y Limpieza Automática en SQLite**:
  - Al iniciar la aplicación, `ChatController._register_system_commands()` detecta y remueve comandos obsoletos (`[PLUGIN_CHAT_TTS_UNMUTE]` y `[PLUGIN_CHAT_TTS_UNBLOCK]`) de la base de datos de comandos, y actualiza de manera segura los alias unificados en los registros de `!ttsmute` y `!ttsblock`.

---

## Mejoras

- **Señal `view_shown` y Refresco Automático al Navegar a Chat**:
  - Se añadió `view_shown = Signal()` y `showEvent()` a [`chat_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py), conectándose a `_sync_tts_command_from_db()` en [`chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py). Cada vez que el streamer accede a la pestaña de Chat, los estados de los switches se sincronizan directamente con la base de datos en $\mathcal{O}(1)$.
- **Tabla Declarativa Centralizada `_DEFAULT_MOD_COMMANDS`**:
  - Se centralizó la definición de los metadatos de los comandos de moderación en la constante `_DEFAULT_MOD_COMMANDS` en `ChatController`, garantizando DRY y consistencia tanto en el registro del arranque como en la regeneración en caliente.
- **Separación de Responsabilidades en el Ciclo de Vida de ChatController (SoR)**:
  - Se desacopló la inicialización del backend (`_init_backend_state`) de la hidratación de la interfaz de usuario (`_populate_view`).
  - Al llamarse a `attach_view(view)`, solo se hidrata la vista sin re-consultar la base de datos de comandos ni reiniciar peticiones de red para obtener voces.
- **Idempotencia de Señales en ChatController**:
  - Se añadió la bandera `_view_connected` en `ChatController._connect_signals()`, asegurando que llamadas repetidas a `attach_view()` no dupliquen conexiones de slots en Qt.
- **Despacho Eficiente $\mathcal{O}(1)$ con Frozensets Nativos**:
  - Se definieron estructuras nativas inmutables (`_MUTE_REMOVE_KEYWORDS`, `_MUTE_REMOVE_ALIASES`, `_MUTE_ADD_KEYWORDS`, `_BLOCK_REMOVE_KEYWORDS`, `_BLOCK_REMOVE_ALIASES`, `_BLOCK_ADD_KEYWORDS`) para la resolución instantánea en tiempo constante de subcomandos y prefijos.
- **Estandarización Rigurosa de i18n**:
  - Se actualizaron las cadenas de ayuda `chat.commands.ttsmute_usage` y `chat.commands.ttsblock_usage` en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) para instruir sobre la nueva sintaxis consolidada. Cero textos hardcodeados y cero fallbacks inline con `or`.

---

## Correcciones

- **Corrección de Desincronización y Pérdida de Comandos al Reactivar Switches en Chat**:
  - **Causa Raíz**: `_sync_tts_command_from_db()` no inspeccionaba `[PLUGIN_CHAT_TTS_MUTE]` ni `[PLUGIN_CHAT_TTS_BLOCK]`, manteniendo los switches activos en la interfaz gráfica aún si los comandos habían sido eliminados de SQLite. Además, `_sync_command_active_state()` ignoraba las activaciones cuando el comando no existía en la base de datos, imposibilitando su regeneración.
  - **Resolución**: Se implementó la detección de ausencia en `_sync_tts_command_from_db` (apagando el switch visual de forma atómica y sin emitir falsos eventos) y la regeneración automática con metadatos completos en `_sync_command_active_state` al encender el toggle.
- **Corrección de Crash Fatal al Abrir la Aplicación (`QThread: Destroyed while thread 'Worker_Voice_Fetcher' is still running`)**:
  - **Causa Raíz**: Durante el arranque, `ChatController.__init__` iniciaba un `VoiceFetcherWorker` para consultar voces en la nube. Inmediatamente después, `MainWindowCore` invocaba `chat_controller.attach_view()`, el cual volvía a ejecutar `_load_initial_data()`. `TTSVoiceHandler.load_voices()` sobreescribía la referencia a `_voice_worker` y llamaba a `deleteLater()` mientras el hilo de sistema operativo continuaba ejecutándose en C++, provocando que Qt abortara la aplicación con pantalla en blanco y terminación forzosa.
  - **Resolución**:
    1. En [`voice_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/voice_worker.py): Se agregaron comprobaciones `isInterruptionRequested()` antes y después de consultar las voces en el hilo de trabajo.
    2. En [`tts_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/tts_handler.py): Se implementó deduplicación idempotente (si ya existe un worker activo para el mismo proveedor, se reutiliza sin duplicar) y el contenedor `_retiring_workers` para retener referencias vivas hasta que el hilo termine con su señal `finished`.
    3. En [`chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py): `attach_view()` ya no reinicia workers ni re-registra comandos.
    4. En [`main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py): Se incorporó `self.chat_controller.cleanup()` en `_stop_all_workers()` para garantizar una parada ordenada y limpia al salir de la aplicación.
