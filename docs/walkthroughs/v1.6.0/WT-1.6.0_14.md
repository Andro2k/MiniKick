# Walkthrough: Corrección del Reseteo de Configuración en el Overlay de Chat (`chat.html`) al Iniciar la App

Documento de cambios y validación técnica para la solución de la anomalía de pérdida de configuración visual en el Overlay de Chat para OBS al reiniciar la aplicación MiniKick.

---

## 1. Novedades

* **Hidratación Reactiva Inmediata de Configuración de Overlay**:
  - `ChatController` ahora inicializa su caché `_tts_settings_cache` de forma síncrona en el momento de su instanciación (`__init__`), permitiendo que cualquier componente que consulte la configuración activa del overlay reciba los valores reales persistidos desde el primer milisegundo de ejecución.

---

## 2. Mejoras

* **Unificación Arquitectónica DRY en `ChatService`**:
  - Se eliminó la duplicación de lecturas a disco entre `get_settings()` y `get_overlay_settings()`. `ChatService.get_settings()` centraliza la carga de las 23 propiedades de overlay (`chat_overlay_*`) junto a los parámetros de voz y TTS.
  - `get_overlay_settings()` reutiliza directamente los datos estructurados devueltos por `get_settings()`, asegurando una única fuente de verdad (Single Source of Truth) y consultas a almacenamiento en tiempo constante $\mathcal{O}(1)$.
* **Inyección Defensiva de Dependencias en `ChatController`**:
  - Se corrigió la inicialización de `self.giphy_service = giphy_service or GiphyService()`, permitiendo inyección de mocks o instancias personalizadas durante pruebas unitarias.
  - Se agregó un fallback defensivo en `ChatController.get_active_overlay_config()` hacia `self.service.get_overlay_settings()` para garantizar que, incluso si el caché en memoria estuviera desprovisto de claves de overlay, jamás se emitan valores por defecto vacíos a OBS si existen datos guardados en SQLite.

---

## 3. Correcciones

* **Solución al Reseteo de Estilos en `chat.html` (`INC-005`)**:
  - **Problema previo**: Al arrancar MiniKick, `MainWindowCore._load_settings_into_ui()` ejecutaba `chat_controller.sync_settings_cache()`. Al no incluir `get_settings()` las claves de overlay, el caché quedaba vacío de estilos visuales. Cuando `MainWindowCore` invocaba `overlay_server.trigger_chat_config_update(chat_controller.get_active_overlay_config())`, se transmitían a OBS valores de fábrica (`glass`, 14px, 15s fade, orientación vertical bottom-to-top), sobreescribiendo visualmente el tema (ej. `neon`, `minimal`, `cyberpunk`, fuentes, animaciones y orientaciones) guardado por el usuario.
  - **Solución implementada**: `ChatService.get_settings()` ahora incluye todas las claves `chat_overlay_*`. Al iniciar la app, el payload emitido a `OverlayServerManager` y transmitido por WebSocket hacia `chat.js` (`applyLiveConfig`) contiene fielmente las preferencias personalizadas del usuario, preservando intactos sus temas, tamaños, desvanecimientos, flujos y filtros.

---

## 4. Pruebas Automatizadas y Verificación

Se añadieron y ejecutaron pruebas de regresión en `resources/tests/test_chat_overlay_controls.py` y `resources/tests/test_chat_controller.py`:

```powershell
uv run pytest resources/tests/ -v
```

### Resultados de Ejecución:
* `test_chat_service_get_settings_contains_overlay_keys`: **PASSED** (Verifica que `get_settings()` devuelve todas las 23 claves de overlay guardadas).
* `test_chat_controller_get_active_overlay_config_preserves_custom_settings_on_startup`: **PASSED** (Verifica que tras la hidratación inicial al arrancar la app, la configuración activa enviada al overlay preserva la orientación, tema, tamaño, fade y animaciones personalizadas).
* `test_chat_controller_init_and_system_command_upsert`: **PASSED** (Verifica inyección de dependencias y registro de comandos de sistema).
* Total suite: **28 passed, 0 failed** en 1.73s.
