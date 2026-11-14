# Walkthrough Técnico — MiniKick v1.6.8 (Paso 08)

Los archivos de `backend/` siguen una sola convención de nombres (`<tema>_<rol>.py`), `services/system/` se reparte por dominio y todos los módulos quedan documentados con una cabecera de ruta y un docstring de una línea.

---

## Novedades

- **Convención de nombres:** cada archivo se llama `<tema>_<rol>.py` con el rol siempre como sufijo: `service`, `storage`, `worker`, `controller`, `handler`, `provider`, `interface`, `utils`, `connection`, `core`. `chat_pipeline`, `connection_hub` y los archivos de `overlay/` conservan un nombre de rol propio.
- **46 archivos renombrados o movidos**, en cuatro tandas. Todos los imports (absolutos, relativos, strings de `patch(...)` en pruebas y referencias en `.md`) se reescribieron con un script, sin ediciones manuales de los llamadores.
- **`services/system/` desaparece.** Sus 15 archivos y tres de `services/chat/` se reparten en carpetas por dominio: `app`, `logs`, `updates`, `security`, `settings`, `media` y `voice`.
- **Documentación en el código:** 164 de los 165 archivos tenían la ruta en la primera línea (`# backend\...`) y 18 estaban corruptos (`\t` o `\a` dentro de la ruta). Se regeneraron todos. Cada módulo (salvo los `__init__`) tiene además un docstring de una línea.

## Mejoras

- **Tanda 1 — interfaces y utils:** las 9 `i_*.py` pasan a `*_interface.py` (`i_tts` → `tts_interface`). En `utils/`: `paths`, `perf`, `emote_parser`, `speech_text`, `latency_monitor` y `youtube_url` pasan a `*_utils.py` (`emote_parser` → `emote_utils`, `speech_text` → `speech_utils`, `latency_monitor` → `latency_utils`, `youtube_url` → `youtube_url_utils`).
- **Tanda 2 — providers y connections:** `kick_provider` y `twitch_provider` eran clientes REST y pasan a `kick_api_provider` y `twitch_api_provider` (los websocket siguen en `*_ws_provider`). Los dos `youtube_provider` pasan a `youtube_chat_provider` y `youtube_music_provider`; `tiktok_provider` a `tiktok_chat_provider`; `audio/devices` a `audio_devices_provider`. En `connections/`: `kick`, `twitch` y `live_chat` pasan a `*_connection`.
- **Tanda 3 — `services/` por dominio:**
  - `app/`: `identity_service` (antes `identity`), `instance_service`, `clock_service`, `browser_service`, `backup_service`, `db_maintenance_service`.
  - `logs/`: `log_writer_service` (antes `log_writer`), `logs_service`.
  - `updates/`: `updater_service`, `whats_new_service`.
  - `security/`: `secret_cipher_service` (antes `secret_cipher`).
  - `settings/`: `settings_service`, `translation_service`, `widgets_service`.
  - `media/`: `avatar_service` (antes `dashboard_service`, que solo contenía `AvatarService`) y `giphy_service`.
  - `voice/`: `tts_service` y `piper_manager_service` (antes `piper_manager`).
  - `chat/` conserva `chat_service`, `commands_service`, `chat_pipeline`, `spam_service` y `timers_service`.
  - `from backend.services import X` sigue funcionando; los imports de `backend.services.system.*` y `backend.services.chat.*` apuntan a la carpeta nueva y cada subpaquete tiene su `__init__` con `__all__`.
- **Tanda 4 — resto:** `utils/db_background` y `utils/io_background` pasan a `*_utils`; `core/log_format` a `log_format_core`; `connections/hub` a `connection_hub` (era el único archivo sin cabecera de ruta).
- **Regla del auditor:** un primer intento dejó los helpers de hilos en `utils/concurrency/`, y `project_file_placement_auditor` lo marcó (`SCATTERED_BACKEND_UTIL`: las utilidades deben estar directamente en `backend/utils`). Se dejaron planos en `utils/`.
- **`backend/README.md`:** la tabla de estructura refleja los patrones `*_interface.py`, `*_provider.py` y `*_utils.py`, los dominios nuevos de `services/` y las carpetas `connections/` y `models/`.
- **Verificación:** se importan los 310 módulos de `backend`, `frontend` y `bootstrap` con Qt (modo offscreen) sin fallos, `resources/tests` da 286 aprobadas y `project_quality_suite.py --quick` da 14/14.

## Limitaciones conocidas

- Los nombres de logger (`"minikick.services.system.backup"`, `"minikick.utils.db_background"`, etc.) no se tocaron: cambiarlos altera la salida y los filtros de logs. Varios siguen mostrando la ruta anterior.
- `services/webhooks/*` conserva el prefijo `webhook_`: sin él quedarían nombres genéricos (`sender`, `signer`, `transport`) más difíciles de buscar.
- `config/webhook_endpoint_store.py` sigue en `config/`: guarda en el `IConfigProvider` (clave cifrada), no en SQLite, así que `database/` no le corresponde.
- Los docstrings se tradujeron al español y los de controllers, storages y workers describen el módulo a partir del nombre de sus clases, sin detalle de comportamiento.
- Los walkthroughs anteriores y `docs/historial_crashes_y_errores.md` no se reescribieron y siguen mencionando los nombres antiguos.
- El `frontend/` no se revisó con esta convención.
