# Walkthrough Técnico — MiniKick v1.6.6 (Paso 04)

Aplicación de la revisión del backend y la auditoría de proveedores sobre el HEAD `01dc7ee` de `release/v1.6.6`. Se corrige el `TypeError` de `!commands <categoría>` introducido en el merge anterior, se alinea el contrato `IMusicProvider` con la API que el código realmente usa, se elimina la lógica duplicada de filtrado de texto en los proveedores de voz y se añade un test de contrato que impide que protocolos y proveedores vuelvan a divergir.

Validado con 6 pruebas nuevas de contrato (`test_provider_contracts.py`), las pruebas de formateo de comandos, handler y controlador de música, y los auditores del proyecto (hardcode, fronteras de arquitectura, DRY, ubicación de archivos, código muerto y tokens de diseño), todos en verde. El parche se entrega como `0005-provider-contracts-and-help-fix.patch` y aplica limpio sobre `01dc7ee`.

---

## Novedades

- **Contrato real de `IMusicProvider`** (`backend/interfaces/i_music_provider.py`): el protocolo declara ahora los 12 métodos que consumen `MusicController` y `MusicCommandHandler` (`add_to_queue`, `get_current_song`, `get_queue`, `remove_from_queue`, `move_in_queue`, `skip_current`, `pause_playback`, `resume_playback`, `seek`, `set_volume`, `set_ducking`, `shutdown`) y los 3 atributos `queue_updated`, `resolve_error_occurred` y `auto_resume`. `add_to_queue` refleja la firma real y devuelve `tuple[bool, str]`. Las señales Qt se tipan como `Any` para que la capa `interfaces/` no dependa de PySide6.
- **Utilidad compartida `is_speakable_text`** (`backend/utils/text_utils.py`): función única con el patrón de URL precompilado, exportada desde `backend/utils/__init__.py`.
- **Test de contrato por reflexión** (`resources/tests/test_provider_contracts.py`): comprueba, sin instanciar Qt, que `YouTubeMusicProvider` cumple `IMusicProvider` y que `PiperTTSProvider`, `WebTTSProvider` y `LocalTTSProvider` cumplen `ITTSProvider`. Valida métodos, orden y tipo de parámetros, y atributos declarados (leyendo las asignaciones `self.x` con `ast`). Se toleran únicamente nombres con prefijo `_` y parámetros extra con valor por defecto. Incluye un caso negativo que garantiza que el propio chequeo detecta divergencias.

## Mejoras

- **Inversión de dependencias (DIP)**: `MusicController` y `MusicCommandHandler` dependen ahora de un protocolo que describe al proveedor real, en lugar de una API implícita no declarada.
- **Eliminación de `hasattr` redundantes**:
  - `MusicController.handle_seek` ya no recorre la cadena `seek` / `set_position` / `player.setPosition`, que terminaba accediendo al `QMediaPlayer` interno; llama únicamente a `provider.seek(position_ms)`.
  - `MusicCommandHandler` elimina los `hasattr` sobre `get_queue`, `pause_playback` y `resume_playback`, métodos que el contrato ya garantiza y que se ejecutan tras `_require_active_provider`.
- **DRY en proveedores de voz**: `PiperTTSProvider` y `WebTTSProvider` dejan de mantener copias idénticas de `_is_speakable_text` y usan `is_speakable_text`. Se retiran los dos `import re` que quedaron sin uso.
- **Patrón de URL precompilado**: se compila una vez a nivel de módulo en lugar de resolverse por la caché interna de `re` en cada llamada de `speak` y `prepare`. La ganancia es marginal; el motivo principal del cambio es DRY.
- **Documentación del contrato**: el protocolo incluye docstring que explica por qué las señales se tipan como `Any`.

## Correcciones

- **`TypeError` en `!commands <categoría>`** (`backend/handlers/command_help_formatter.py`): `format()` llamaba a `_category_messages(target_cat, categories[target_cat], labels[target_cat])` con 3 argumentos cuando la firma vigente acepta 2 (`buckets`, `label`). Quedó mezclada la llamada antigua con la firma nueva. Corregido a `_category_messages(categories[target_cat], labels[target_cat])`, lo que recupera 4 pruebas que fallaban (`test_command_help_formatter` y `test_commands_help`).
- **Divergencia silenciosa entre protocolo y proveedor**: `IMusicProvider` exigía 5 métodos que `YouTubeMusicProvider` no implementa (`get_now_playing`, `is_authenticated`, `play_pause`, `search_song`, `skip_song`) y describía `add_to_queue` con otra firma. El nuevo test de contrato falla con 3 errores contra el protocolo anterior y pasa con el nuevo.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_provider_contracts.py` | 6 pasan (3 fallan con el protocolo anterior) |
| `test_command_help_formatter.py` / `test_commands_help.py` | 9 y 7 pasan (antes 3 y 1 fallos) |
| `test_music_command_handler.py` / `test_music_controller_chat_context.py` | 8 y 4 pasan |
| `test_architecture_and_placement_auditors.py` / `test_quality_auditors.py` | 9 y 6 pasan |
| Auditores CLI (hardcode, fronteras, DRY, ubicación, código muerto, tokens) | Sin hallazgos |

**Fallos preexistentes, sin relación con este paso:**

- `test_giphy_and_tts_filter.py` (3 pruebas): dependen de la API key y de red de Giphy, que no están disponibles en el entorno de validación.
- `test_worker_and_core_lifecycle.py::test_chat_and_reward_workers_stop_sets_interruption_and_quit`: intermitente. Con `channel_name=""`, `TwitchChatWorker.run()` termina antes de que el test invoque `stop()` y Qt limpia el flag de interrupción; es un defecto del test, no del código.
- La suite completa produce *segmentation fault* en el entorno de validación (Qt sin pantalla), por lo que las pruebas se ejecutaron por archivo. Conviene correr la suite completa en la máquina de desarrollo.

## Pendiente (no incluido en este paso)

- **(c) Inyección de dependencias** de `TranslationService`, `PiperVoiceManager` y `SQLiteMusicStorage` en los proveedores, en lugar de importarlos directamente. Es el siguiente paso recomendado para cerrar la violación crítica de DIP.
- **(a) División de `music/youtube_provider.py`** (693 líneas, 35 métodos) en reproductor, cola y resolución.
- **(b) Trocear funciones largas** de los proveedores de chat (`TikTokChatProvider._build_client`, `YouTubeChatProvider.start_chat`, `TwitchEventSubProvider._handle_notification`).
- **Contrato ampliable**: `set_audio_device` y `set_loudness_normalization` se invocan con `hasattr` sobre un proveedor sin tipar en `settings_controller`; declararlos en `IMusicProvider` es un cambio menor si se quiere que el protocolo sea la única fuente de verdad.
- **Manejo de errores**: los `except Exception: pass` en teardown de proveedores de voz, música y chat siguen sin registrar nada; basta `logger.debug(..., exc_info=True)`.
