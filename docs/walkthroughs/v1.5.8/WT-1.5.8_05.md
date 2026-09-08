# Walkthrough - WT-1.5.8_05: Integridad del Sistema de Comandos, Sincronización de Música y Estabilidad de Hilos

**Versión:** `v1.5.8`  
**Documento:** `WT-1.5.8_05.md`  
**Fecha:** 02 de Septiembre, 2026  

---

## 1. Resumen Ejecutivo

Este documento consolida las correcciones críticas en el motor de comandos multiplataforma, la sincronización bidireccional y regeneración de comandos de música, y la resolución de excepciones fatales de memoria en hilos de Qt (`RuntimeError: Internal C++ object already deleted`).

---

## 2. Correcciones en el Sistema de Comandos y Widgets

### A. Resolución de Acciones en Widgets de Marcador y Muerte ([widget_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widget_controller.py))
- **Problema previo:** `parts[0][len(prefix):].lower()` evaluaba a cadena vacía al invocar comandos que coincidían con alias directos (`!win`, `!loss`, `!death-`), sumando erróneamente en vez de restar o consultar.
- **Solución:** Se derivó `action_word = cmd_trigger or suffix` con comparaciones exactas contra `_SCORE_WIN_WORDS`, `_SCORE_LOSS_WORDS`, sufijos `+`/`-`, y palabras de decremento/reinicio.

### B. Protección de Plugins y Preservación de Plataformas ([command_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/command_dialog.py))
- Al editar comandos con plataformas desconectadas temporalmente, la UI solía deshabilitarlas permanentemente en base de datos.
- Se corrigió para respetar fielmente el valor persistido (`existing_config.get("apply_<plat>", True)`).
- En comandos de tipo plugin (`[PLUGIN_...`), se bloqueó la respuesta en modo solo lectura (`setReadOnly(True)`) con un badge distintivo para proteger hooks internos.

### C. Seguridad en Comando `!tts` ([chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py))
- Se blindó `_handle_plugin_tts` validando el estado activo global (`self._tts_enabled`), listas de bots ignorados y palabras prohibidas (`banned_words`), cerrando vulnerabilidades de elusión de moderación.

---

## 3. Sincronización Reactiva de Switches de Música ([commands_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/commands_panel.py), [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py))

1. **Refresco Instantáneo ante Eliminación**:
   - `set_switch_states` ahora evalúa `val = bool(states.get(cmd, False))`, apagando de inmediato el switch visual si el comando fue borrado desde la vista general de Comandos.
2. **Sincronización en Navegación**:
   - Se conectó `view_shown` con `_sync_switches_from_db` para refrescar los estados al entrar a la vista.
3. **Preservación de Metadatos al Regenerar**:
   - Se centralizó el diccionario `_DEFAULT_MUSIC_COMMANDS` con los roles, alias y cooldowns específicos de `!sr`, `!skip`, `!song`, `!pause`, `!resume`, `!playlist` y `!vol`, evitando que comandos regenerados pierdan sus privilegios de moderador.

---

## 4. Estabilidad de Hilos: Mitigación de 'Internal C++ object already deleted' ([main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py))

### Causa Raíz
Cuando un `QThread` invoca `deleteLater()` al finalizar, el puntero C++ subyacente es destruido por Shiboken. Sin embargo, la referencia en Python continuaba existiendo, por lo que invocar `worker.isRunning()` detonaba un `RuntimeError` irrecuperable en el hilo principal de la aplicación.

### Solución Implementada
1. **Helper Seguro Estático `_is_worker_running`**:
   ```python
   @staticmethod
   def _is_worker_running(worker) -> bool:
       if worker is None:
           return False
       try:
           return bool(worker.isRunning())
       except (RuntimeError, AttributeError):
           return False
   ```
2. **Auto-Limpieza en Señal `finished`**:
   - Conexión de `finished` en todos los workers transitorios (`kick_auth_worker`, `twitch_auth_worker`, `fetch_rewards_worker`, etc.) restableciendo sus referencias a `None` inmediatamente tras su finalización.

---

## 5. Verificación y Resultados

- Pruebas automatizadas de lógica de comandos con `test_commands_logic.py`.
- Pruebas unitarias de estabilidad de hilos en `resources/tests/unit/core/test_logging.py`.
- 100% de pruebas superadas sin excepciones de Shiboken ni desincronización de interfaz.
