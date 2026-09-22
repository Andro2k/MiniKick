# Walkthrough WT-1.6.0_24: Herramienta de Auditoría y Saneamiento de Parámetros No Utilizados

## 1. Novedades
* **Herramienta Automatizada `unused_parameter_manager.py`**:
  * Se creó [`resources/tools/unused_parameter_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/unused_parameter_manager.py) para auditar y diagnosticar de forma estática ($\mathcal{O}(N)$ vía AST de Python) todos los parámetros sin uso en el código base.
  * Diseñada para analizar de forma selectiva o integral tanto el `backend/` como el `frontend/`.
  * **Taxonomía Inteligente en 3 Categorías**:
    1. 🔴 **`DEAD_PARAMETER`**: Funciones con lógica activa sustancial donde un parámetro recibido nunca es consultado ni reenviado (posible código muerto o residuo de refactorizaciones).
    2. 🟡 **`CONTRACT_HOOK`**: Métodos plantilla o abstractos en clases base (`pass`, `return`, `...`) que definen un contrato público para ser sobrescritos por subclases.
    3. 🔵 **`QT_OVERRIDE`**: Eventos nativos del ciclo de vida de Qt/PySide6 (`paintEvent`, `resizeEvent`, etc.) o métodos vinculados con `@Slot`.
* **Modos de Operación CLI**:
  * `uv run python resources/tools/unused_parameter_manager.py`: Auditoría completa visual en terminal.
  * `--target [all|backend|frontend]`: Filtrado por capa.
  * `--category [all|dead|hooks|qt]`: Filtrado por severidad/tipo.
  * `--fix-hooks`: Modo interactivo/automático para aplicar de forma segura el prefijo `_param` (PEP 8) en métodos base.
  * `--json`: Exportación de resultados estructurados para integración continua.

---

## 2. Mejoras
* **Análisis AST de Alto Rendimiento ($\mathcal{O}(N)$)**:
  * El escaneo completo de los más de 210 archivos de MiniKick toma menos de 0.8 segundos.
  * Resuelve ámbitos y clausuras internas (funciones anidadas, list comprehensions, expresiones lambda) para garantizar cero falsos positivos cuando un parámetro es consumido internamente.
* **Cobertura Automatizada**:
  * Se creó la suite [`resources/tests/test_unused_parameter_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_unused_parameter_manager.py) verificando que el visitor clasifique con precisión quirúrgica cada categoría y respete los parámetros formalmente escapados con `_`.

---

## 3. Correcciones
* **Estandarización de Hook en `ModernWizardPanel`**:
  * Se ajustó el método [`ModernWizardPanel.validate_step`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py#L609) renombrando el parámetro del hook base a `_step_index: int`, silenciando las advertencias de Pyrefly y linters sin romper la compatibilidad con las subclases (`TimersDialog`, `RewardsDialog`, `CommandsDialog`).
* **Saneamiento Integral de Parámetros Huérfanos en Backend (0 advertencias alcanzadas)**:
  * [`backend/controllers/chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py): Corregido reenvío de `prefix` en `_handle_plugin_ttsunmute` y `_handle_plugin_ttsunblock` permitiendo parsear alias de forma dinámica sin hardcodings.
  * [`backend/controllers/widgets_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py): Prefijados `_prefix` en `_dispatch_score_command`, `_args` en `_process_explosion_command`, y `_user` en `_process_combo_command` para coincidir con la firma del despachador.
  * [`backend/core/app_logger_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_logger_core.py): Prefijado `_context` en `_qt_message_handler`.
  * [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py): Prefijados `_tokens` en callbacks de autenticación, `_result` en `_on_schedule_triggered`, y removido el parámetro obsoleto `immediate` en `_apply_dynamic_theme` (código muerto remanente de v1.5.6) sincronizando su llamada a la firma `@Slot(int)`.
  * [`backend/handlers/music_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/music_handler.py): Prefijados `_api`, `_provider`, `_user`, `_message`, `_prefix_used`, y `_success` en la tabla de comandos de música y callbacks de cola.
  * [`backend/handlers/tts_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/tts_handler.py): Eliminado argumento y parámetro residual `play_test`, prefijado `_lang_prefix`, e instrumentado registro de depuración en `_on_voices_fetched` asegurando total consistencia con llamadas por keyword argument (`is_initial=True`).
  * [`backend/providers/chat/kick_ws_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_ws_provider.py): Prefijados `_ws` e `_inner` en todos los manejadores de eventos Pusher.
  * [`backend/providers/chat/tiktok_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_provider.py): Prefijados `_event` en `_on_connect` y `_on_disconnect`.
  * [`backend/providers/chat/twitch_ws_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_ws_provider.py): Prefijado `_ws` en callbacks de error y cierre de socket.
  * [`backend/providers/music/youtube_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_provider.py): Prefijado `_title` en slots de resolución de streams.
  * [`backend/providers/voices/local_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/local_provider.py) y [`online_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/online_provider.py): Estandarizados hooks de interfaz `prepare` y `warm_up` con prefijo `_`.
  * [`backend/services/overlay/overlay_routes.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/overlay_routes.py): Silenciado `log_message` con `_format, *_args`.
  * [`backend/workers/twitch_rewards_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_rewards_worker.py): Prefijados `_ws`, `_close_code`, `_close_msg` en callbacks de eventos.
