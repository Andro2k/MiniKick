# 🔧 MiniKick — Correcciones & Revisión de Código

> Documento de seguimiento de revisiones técnicas para el proyecto MiniKick.
> Marca cada archivo con su estado usando los badges: ✅ Revisado | ⚠️ Pendiente | 🔴 Crítico | 🔵 Mejora

---

## 🏷️ Convención de Nombres (Naming Convention)

Patrón definido por capa: **`{dominio}_{sufijo_de_capa}.py`**

| Capa | Patrón | Ejemplo |
|---|---|---|
| `controllers/` | `{domain}_controller.py` | `alerts_controller.py` |
| `core/` | `{name}_core.py` | `app_container_core.py` |
| `database/` | `{domain}_storage.py` / `{domain}_manager.py` | `commands_storage.py` |
| `handlers/` | `{domain}_handler.py` | `tts_handler.py` |
| `interfaces/` | `i_{domain}.py` | `i_auth.py` |
| `models/` | `{domain}_models.py` | `command_models.py` |
| `providers/chat/` | `{platform}_provider.py` | `kick_provider.py` |
| `providers/music/` | `{platform}_provider.py` | `youtube_provider.py` |
| `providers/voices/` | `{engine}_provider.py` | `piper_provider.py` |
| `services/` | `{domain}_service.py` | `schedule_service.py` |
| `utils/` | `{domain}_utils.py` | `json_utils.py` |
| `workers/` | `{domain}_worker.py` | `kick_chat_worker.py` |
| `views/` | `{domain}_view.py` (plural) | `commands_view.py` |
| `dialogs/` | `{domain}_dialog.py` | `timer_dialog.py` |
| `navigation/` | `{domain}_component.py` | `sidebar_component.py` |
| `components/*/` | `{domain}_{tipo}.py` (tipo: panel, card, item, settings, mockup) | `event_card.py` |
| `widgets/` | `{name}_widget.py` | `table_widget.py` |

> **Reglas generales:**
> - Usar **snake_case** siempre.
> - El **dominio va primero**, el **sufijo de capa va al final**.
> - Nombres en **plural** para módulos que representan colecciones (`alerts`, `commands`, `rewards`, `timers`, `widgets`).
> - Nombres en **singular** para conceptos únicos (`schedule`, `dashboard`, `music`, `spam`).
> - **Nunca** mezclar palabras extra innecesarias en el medio (`tts_voice_handler` → `tts_handler`).

---

## 📋 Renombres Propuestos

### 🔧 Backend

#### `controllers/` — Inconsistencia singular/plural

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `command_controller.py` | `commands_controller.py` | Singular vs plural del resto |
| `log_controller.py` | `logs_controller.py` | Singular vs plural del resto |
| `timer_controller.py` | `timers_controller.py` | Singular vs plural del resto |
| `update_controller.py` | `updater_controller.py` | Inconsistente con `updater_service.py` |
| `widget_controller.py` | `widgets_controller.py` | Singular vs plural del resto |

#### `database/` — `manager.py` sin dominio + `cache_manager.py` inconsistente

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `manager.py` | `db_manager.py` | Sin prefijo de dominio — ambiguo al importar |
| `cache_manager.py` | `cache_storage.py` | Rompe el patrón `_storage` del resto |

#### `handlers/` — Palabras intermedias que oscurecen el dominio

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `chat_filter_handler.py` | `spam_handler.py` | "filter" es redundante; el dominio es spam |
| `music_command_handler.py` | `music_handler.py` | "command" es redundante; el dominio es music |
| `tts_voice_handler.py` | `tts_handler.py` | "voice" es redundante; el dominio es tts |

#### `interfaces/` — 3 convenciones distintas

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `alert_interfaces.py` | `i_alert.py` | Sufijo `_interfaces` (plural) |
| `auth_interfaces.py` | `i_auth.py` | Sufijo `_interfaces` (plural) |
| `browser_interface.py` | `i_browser.py` | Sufijo `_interface` (singular) |
| `chat_provider.py` | `i_chat_provider.py` | Sin sufijo ni prefijo |
| `chat_service.py` | `i_chat_service.py` | Colisiona con `services/chat/chat_service.py` |
| `instance_interfaces.py` | `i_instance.py` | Sufijo `_interfaces` (plural) |
| `music_provider.py` | `i_music_provider.py` | Sin sufijo ni prefijo |
| `settings_interfaces.py` | `i_settings.py` | Sufijo `_interfaces` (plural) |
| `tts_interfaces.py` | `i_tts.py` | Sufijo `_interfaces` (plural) |
| `updater_interfaces.py` | `i_updater.py` | Sufijo `_interfaces` (plural) |

#### `providers/chat/` — Mezcla `_client`, `_websocket`, `_provider`

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `kick_client.py` | `kick_provider.py` | `_client` vs `_provider` inconsistente |
| `kick_websocket.py` | `kick_ws_provider.py` | Rol de WebSocket no diferenciado como provider |
| `tiktok_chat_provider.py` | `tiktok_provider.py` | "chat" es redundante en este directorio |
| `twitch_client.py` | `twitch_provider.py` | `_client` vs `_provider` inconsistente |
| `twitch_websocket.py` | `twitch_ws_provider.py` | Rol de WebSocket no diferenciado como provider |
| `youtube_chat_provider.py` | `youtube_provider.py` | "chat" es redundante en este directorio |

#### `providers/voices/` — Prefijo `tts_` delante del nombre del engine

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `tts_local.py` | `local_provider.py` | Dominio antes que engine; sufijo `_provider` ausente |
| `tts_online.py` | `online_provider.py` | Dominio antes que engine; sufijo `_provider` ausente |
| `tts_piper.py` | `piper_provider.py` | Dominio antes que engine; sufijo `_provider` ausente |

#### `services/` — Inconsistencias puntuales

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `oauth_service.py` | `auth_service.py` | Carpeta es `auth/`, servicio debería coincidir |
| `pipeline.py` | `chat_pipeline.py` | Sin prefijo de dominio — ambiguo |
| `piper_voice_manager.py` | `piper_manager.py` | "voice" redundante en contexto de `voices/` |
| `instance_services.py` | `instance_service.py` | Plural `_services` vs singular del resto |
| `websocket_client.py` (overlay) | `overlay_ws_client.py` | Sin prefijo de dominio — colisiona con otros |

#### `workers/` — Inconsistencias de plural y convención

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `timers_worker.py` | `timer_worker.py` | Plural vs singular del resto de workers |
| `twitch_reward_worker.py` | `twitch_rewards_worker.py` | Singular vs `rewards_worker.py` (plural) |
| `update_worker.py` | `updater_worker.py` | Inconsistente con `updater_service.py` |

---

### 🎨 Frontend

#### `views/` — Inconsistencia singular/plural

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `command_view.py` | `commands_view.py` | Singular vs plural del resto |
| `log_view.py` | `logs_view.py` | Singular vs plural del resto |

#### `dialogs/` — Sufijos dobles o palabras intermedias

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `message_editor_dialog.py` | `message_dialog.py` | "editor" es redundante |
| `visual_positioner_dialog.py` | `positioner_dialog.py` | "visual" es redundante |
| `platform_connect_dialog.py` | `platform_dialog.py` | "connect" es redundante |
| `piper_voices_dialog.py` | `piper_dialog.py` | "voices" redundante en contexto de TTS |
| `tiktok_connect_dialog.py` | `tiktok_dialog.py` | "connect" es redundante |
| `youtube_connect_dialog.py` | `youtube_dialog.py` | "connect" es redundante |

#### `components/widgets/` — Sufijo `_component` inconsistente

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `widget_card_component.py` | `widget_card.py` | Sufijo `_component` no existe en ningún otro componente |

#### `widgets/` (primitivas UI) — Sin patrón de sufijo

| Nombre actual | Nombre propuesto | Problema |
|---|---|---|
| `blocks.py` | `block_widget.py` | Sin sufijo de capa |
| `controls.py` | `controls_widget.py` | Sin sufijo de capa |
| `table.py` | `table_widget.py` | Sin sufijo de capa |
| `pagination.py` | `pagination_widget.py` | Sin sufijo de capa |
| `base_view.py` | `base_widget.py` | Confuso: está en `widgets/` pero se llama `_view` |

> **Nota:** Los demás archivos de `widgets/` (`category_search.py`, `color_picker.py`, `flow_layout.py`, etc.)
> son descriptivos y self-documenting — **no requieren renombre**.

---

## 📦 Backend

### `config/`

| Archivo | Estado | Notas |
|---|---|---|
| `api_keys.py` | ⚠️ | |
| `default_en_locale.py` | ⚠️ | |
| `version.py` | ⚠️ | |

---

### `controllers/`

| Archivo | Estado | Notas |
|---|---|---|
| `alerts_controller.py` | ⚠️ | |
| `chat_controller.py` | ⚠️ | |
| `commands_controller.py` | ⚠️ | |
| `dashboard_controller.py` | ⚠️ | |
| `logs_controller.py` | ⚠️ | |
| `music_controller.py` | ⚠️ | |
| `rewards_controller.py` | ⚠️ | |
| `schedule_controller.py` | ⚠️ | |
| `settings_controller.py` | ⚠️ | |
| `spam_controller.py` | ⚠️ | |
| `timer_controller.py` | ⚠️ | |
| `widget_controller.py` | ⚠️ | |

---

### `core/`

| Archivo | Estado | Notas |
|---|---|---|
| `app_container_core.py` | ⚠️ | |
| `app_logger_core.py` | ⚠️ | |
| `main_window_core.py` | ⚠️ | |

---

### `database/`

| Archivo | Estado | Notas |
|---|---|---|
| `manager.py` | ⚠️ | |
| `alert_storage.py` | ⚠️ | |
| `avatar_storage.py` | ⚠️ | |
| `cache_storage.py` | ⚠️ | |
| `commands_storage.py` | ⚠️ | |
| `music_storage.py` | ⚠️ | |
| `rewards_storage.py` | ⚠️ | |
| `schedule_storage.py` | ⚠️ | |
| `settings_storage.py` | ⚠️ | |
| `spam_storage.py` | ⚠️ | |
| `system_log_storage.py` | ⚠️ | |
| `timers_storage.py` | ⚠️ | |
| `token_storage.py` | ⚠️ | |
| `widgets_storage.py` | ⚠️ | |

---

### `handlers/`

| Archivo | Estado | Notas |
|---|---|---|
| `chat_filter_handler.py` | ⚠️ | |
| `log_handler.py` | ⚠️ | |
| `music_command_handler.py` | ⚠️ | |
| `tts_voice_handler.py` | ⚠️ | |

---

### `interfaces/`

| Archivo | Estado | Notas |
|---|---|---|
| `alert_interfaces.py` | ⚠️ | |
| `auth_interfaces.py` | ⚠️ | |
| `browser_interface.py` | ⚠️ | |
| `chat_provider.py` | ⚠️ | |
| `chat_service.py` | ⚠️ | |
| `instance_interfaces.py` | ⚠️ | |
| `music_provider.py` | ⚠️ | |
| `settings_interfaces.py` | ⚠️ | |
| `tts_interfaces.py` | ⚠️ | |
| `updater_interfaces.py` | ⚠️ | |

---

### `models/`

| Archivo | Estado | Notas |
|---|---|---|
| `alert_models.py` | ⚠️ | |

---

### `providers/`

#### `providers/chat/`

| Archivo | Estado | Notas |
|---|---|---|
| `kick_client.py` | ⚠️ | |
| `kick_websocket.py` | ⚠️ | |
| `tiktok_chat_provider.py` | ⚠️ | |
| `twitch_client.py` | ⚠️ | |
| `twitch_websocket.py` | ⚠️ | |
| `youtube_chat_provider.py` | ⚠️ | |

#### `providers/music/`

| Archivo | Estado | Notas |
|---|---|---|
| `youtube_client.py` | ⚠️ | |

#### `providers/voices/`

| Archivo | Estado | Notas |
|---|---|---|
| `tts_local.py` | ⚠️ | |
| `tts_online.py` | ⚠️ | |
| `tts_piper.py` | ⚠️ | |

---

### `services/`

#### `services/alerts/`

| Archivo | Estado | Notas |
|---|---|---|
| `alert_queue.py` | ⚠️ | |
| `alert_service.py` | ⚠️ | |

#### `services/auth/`

| Archivo | Estado | Notas |
|---|---|---|
| `oauth_service.py` | ⚠️ | |

#### `services/chat/`

| Archivo | Estado | Notas |
|---|---|---|
| `chat_service.py` | ⚠️ | |
| `command_service.py` | ⚠️ | |
| `pipeline.py` | ⚠️ | |
| `piper_voice_manager.py` | ⚠️ | |
| `spam_service.py` | ⚠️ | |
| `timer_service.py` | ⚠️ | |
| `tts_service.py` | ⚠️ | |

#### `services/overlay/`

| Archivo | Estado | Notas |
|---|---|---|
| `overlay_manager.py` | ⚠️ | |
| `overlay_routes.py` | ⚠️ | |
| `websocket_client.py` | ⚠️ | |

#### `services/rewards/`

| Archivo | Estado | Notas |
|---|---|---|
| `rewards_service.py` | ⚠️ | |
| `thumbnail_service.py` | ⚠️ | |

#### `services/schedule/`

| Archivo | Estado | Notas |
|---|---|---|
| `schedule_service.py` | ⚠️ | |

#### `services/system/`

| Archivo | Estado | Notas |
|---|---|---|
| `backup_service.py` | ⚠️ | |
| `browser_service.py` | ⚠️ | |
| `dashboard_service.py` | ⚠️ | |
| `instance_services.py` | ⚠️ | |
| `log_service.py` | ⚠️ | |
| `settings_service.py` | ⚠️ | |
| `translation_service.py` | ⚠️ | |
| `updater_service.py` | ⚠️ | |
| `widget_service.py` | ⚠️ | |

---

### `utils/`

| Archivo | Estado | Notas |
|---|---|---|
| `json_utils.py` | ⚠️ | |

---

### `workers/`

| Archivo | Estado | Notas |
|---|---|---|
| `bug_report_worker.py` | ⚠️ | |
| `crash_report_worker.py` | ⚠️ | |
| `global_media_worker.py` | ⚠️ | |
| `kick_auth_worker.py` | ⚠️ | |
| `kick_chat_worker.py` | ⚠️ | |
| `music_worker.py` | ⚠️ | |
| `rewards_worker.py` | ⚠️ | |
| `schedule_worker.py` | ⚠️ | |
| `tiktok_chat_worker.py` | ⚠️ | |
| `timers_worker.py` | ⚠️ | |
| `twitch_auth_worker.py` | ⚠️ | |
| `twitch_chat_worker.py` | ⚠️ | |
| `twitch_reward_worker.py` | ⚠️ | |
| `update_worker.py` | ⚠️ | |
| `voice_worker.py` | ⚠️ | |
| `youtube_chat_worker.py` | ⚠️ | |

---

## 🎨 Frontend

### `common/`

| Archivo | Estado | Notas |
|---|---|---|
| `icons.py` | ⚠️ | |
| `markdown.py` | ⚠️ | |
| `paths.py` | ⚠️ | |
| `theme.py` | ⚠️ | |
| `validators.py` | ⚠️ | |

---

### `components/`

#### `components/alerts/`

| Archivo | Estado | Notas |
|---|---|---|
| `alert_mockup.py` | ⚠️ | |
| `event_card.py` | ⚠️ | |
| `overlay_card.py` | ⚠️ | |
| `responsive_stack.py` | ⚠️ | |
| `sidebar_panel.py` | ⚠️ | |
| `variant_item.py` | ⚠️ | |

#### `components/chat/`

| Archivo | Estado | Notas |
|---|---|---|
| `bot_mute.py` | ⚠️ | |
| `chat_display.py` | ⚠️ | |
| `chat_mockup.py` | ⚠️ | |
| `overlay_settings.py` | ⚠️ | |
| `tts_settings.py` | ⚠️ | |

#### `components/dashboard/`

| Archivo | Estado | Notas |
|---|---|---|
| `distribution_bar.py` | ⚠️ | |
| `platform_card.py` | ⚠️ | |

#### `components/dialogs/`

| Archivo | Estado | Notas |
|---|---|---|
| `draggable_box.py` | ⚠️ | |
| `image_dropzone.py` | ⚠️ | |
| `piper_voice_item.py` | ⚠️ | |
| `severity_card.py` | ⚠️ | |

#### `components/log/`

| Archivo | Estado | Notas |
|---|---|---|
| `log_controls.py` | ⚠️ | |

#### `components/music/`

| Archivo | Estado | Notas |
|---|---|---|
| `commands_panel.py` | ⚠️ | |
| `music_mockup.py` | ⚠️ | |
| `music_settings_panel.py` | ⚠️ | |
| `player_settings.py` | ⚠️ | |
| `queue_panel.py` | ⚠️ | |
| `stats_panel.py` | ⚠️ | |

#### `components/schedule/`

| Archivo | Estado | Notas |
|---|---|---|
| `quick_change_panel.py` | ⚠️ | |
| `schedule_form_panel.py` | ⚠️ | |
| `schedule_table_panel.py` | ⚠️ | |

#### `components/widgets/`

| Archivo | Estado | Notas |
|---|---|---|
| `widget_card_component.py` | ⚠️ | |

---

### `dialogs/`

| Archivo | Estado | Notas |
|---|---|---|
| `already_running_dialog.py` | ⚠️ | |
| `base_dialog.py` | ⚠️ | |
| `bug_report_dialog.py` | ⚠️ | |
| `command_dialog.py` | ⚠️ | |
| `crash_report_dialog.py` | ⚠️ | |
| `message_editor_dialog.py` | ⚠️ | |
| `piper_voices_dialog.py` | ⚠️ | |
| `platform_connect_dialog.py` | ⚠️ | |
| `release_notes_dialog.py` | ⚠️ | |
| `rewards_dialog.py` | ⚠️ | |
| `tiktok_connect_dialog.py` | ⚠️ | |
| `timer_dialog.py` | ⚠️ | |
| `update_dialog.py` | ⚠️ | |
| `visual_positioner_dialog.py` | ⚠️ | |
| `youtube_connect_dialog.py` | ⚠️ | |

---

### `navigation/`

| Archivo | Estado | Notas |
|---|---|---|
| `sidebar_component.py` | ⚠️ | |
| `toast_component.py` | ⚠️ | |
| `tray_menu_component.py` | ⚠️ | |

---

### `views/`

| Archivo | Estado | Notas |
|---|---|---|
| `alerts_view.py` | ⚠️ | |
| `chat_view.py` | ⚠️ | |
| `command_view.py` | ⚠️ | |
| `dashboard_view.py` | ⚠️ | |
| `log_view.py` | ⚠️ | |
| `music_view.py` | ⚠️ | |
| `rewards_view.py` | ⚠️ | |
| `schedule_view.py` | ⚠️ | |
| `settings_view.py` | ⚠️ | |
| `spam_view.py` | ⚠️ | |
| `timers_view.py` | ⚠️ | |
| `widgets_view.py` | ⚠️ | |

---

### `widgets/`

| Archivo | Estado | Notas |
|---|---|---|
| `base_view.py` | ⚠️ | |
| `blocks.py` | ⚠️ | |
| `category_search.py` | ⚠️ | |
| `clearable_line_edit.py` | ⚠️ | |
| `color_picker.py` | ⚠️ | |
| `controls.py` | ⚠️ | |
| `filter_header.py` | ⚠️ | |
| `flow_layout.py` | ⚠️ | |
| `no_wheel.py` | ⚠️ | |
| `pagination.py` | ⚠️ | |
| `platform_controls.py` | ⚠️ | |
| `scalable_illustration.py` | ⚠️ | |
| `search_bar.py` | ⚠️ | |
| `searchable_combo_box.py` | ⚠️ | |
| `segmented_control.py` | ⚠️ | |
| `table.py` | ⚠️ | |

