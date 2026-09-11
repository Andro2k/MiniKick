# Walkthrough WT-1.5.9_12: Selectores de Comandos de Moderación de Chat (!ttsmute y !ttsblock)

## Novedades

- **Selectores de Comandos de Moderación en UI**:
  - Se incorporó una tarjeta de configuración en la parte superior de la pestaña **Silenciados / Bots** ([`bot_mute.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py)) con dos selectores (switches) independientes:
    1. **Comandos de silenciar usuarios (`!ttsmute` / `!ttsunmute`)**: Permite habilitar o inhabilitar la ejecución de los comandos de chat para silenciar o desilenciar usuarios del TTS en tiempo real.
    2. **Comandos de censurar palabras (`!ttsblock` / `!ttsunblock`)**: Permite habilitar o inhabilitar la ejecución de los comandos de chat para agregar o eliminar palabras bloqueadas del TTS.
  - Los switches están presentados con componentes `SettingRow`, acompañados de iconografía oficial (`shield-user-bold.svg` y `shield-duotone.svg`), títulos y descripciones explicativas.
- **Sincronización Bidireccional con `CommandService`**:
  - Al cambiar el estado de los switches en la interfaz gráfica, el estado `is_active` de los 4 comandos registrados en la base de datos de comandos (`!ttsmute`, `!ttsunmute`, `!ttsblock`, `!ttsunblock`) se actualiza atómicamente de forma sincronizada.

---

## Mejoras

- **Eficiencia $\mathcal{O}(1)$ en Validación de Comandos**:
  - Se introdujo validación en memoria en tiempo constante $\mathcal{O}(1)$ en `_handle_plugin_ttsmute`, `_handle_plugin_ttsunmute`, `_handle_plugin_ttsblock` y `_handle_plugin_ttsunblock` de [`chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) a través de `_mod_mute_command_enabled` y `_mod_block_command_enabled`.
  - Si un moderador intenta ejecutar un comando cuando está desactivado, el sistema responde inmediatamente notificando al usuario sin consultar estructuras de datos pesadas ni mutar listas.
- **Internacionalización Rigurosa (i18n)**:
  - Todas las cadenas fueron agregadas en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) bajo el espacio de nombres `chat.mod_commands.*`.
  - Cero cadenas hardcodeadas y cero fallbacks inline con `or`. Verificado con `test_i18n_integrity.py` con paridad del 100%.
- **Persistencia en Almacenamiento**:
  - `ChatService.get_settings()` y `ChatService.save_settings()` persisten `mod_mute_command_enabled` y `mod_block_command_enabled` en la base de datos SQLite sin inconsistencias.

---

## Correcciones

- **Protección contra Objetos Nulos en Modo Headless / Testing**:
  - Corrección en `ChatFilterHandler.add_bot()` y `ChatFilterHandler.add_word()` para verificar `if view is not None` antes de intentar invocar `view.add_bot_tag()` o `view.add_word_tag()`, evitando excepciones `AttributeError` en ejecuciones headless o pruebas unitarias automatizadas.
- **Sincronización de Caché Unificada (DRY)**:
  - Se refactorizó `ChatController._load_initial_data()` para utilizar internamente `self.sync_settings_cache()`, garantizando que todos los flags booleanos y configuraciones se inicialicen desde una única fuente de verdad.
