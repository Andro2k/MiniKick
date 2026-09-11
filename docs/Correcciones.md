# 🔧 MiniKick — Estandarización de Nombres & Auditoría Integral

> **Documento Maestro de Arquitectura y Naming**  
> Auditoría completa de los 179 archivos `.py` del proyecto MiniKick (Backend y Frontend).  
> **Badges de Acción:** `✅ Mantener` (cumple el estándar) | `🔄 Renombrar` (requiere cambio) | `📦 Reubicar` (mover de directorio)  
> **Badges de Estado:** `⚠️ Pendiente` (pendiente de refactor en código) | `✅ Aplicado` (cambio realizado y testeado)

---

## 📊 Tablero de Control y Métricas Generales

| Métrica | Backend | Frontend | Total Proyecto |
|---|---|---|---|
| **Total Archivos Auditados** | 100 | 79 | **179** |
| **Cumplen Convención (`✅ Mantener`)** | 68 | 61 | **129** (72.1%) |
| **Requieren Renombre (`🔄 Renombrar`)** | 32 | 17 | **49** (27.4%) |
| **Requieren Reubicación (`📦 Reubicar`)** | 0 | 1 | **1** (0.5%) |
| **Estado General** | 🔄 Fase 2 Completada | ⚠️ Pendiente | 🔄 **En Progreso (Fase 2 Lista)** |

---

## 🏷️ Convención Oficial de Nombres (Naming Standard)

### 1. Patrón Fundamental por Capa: `{dominio}_{sufijo_capa}.py`

| Capa | Patrón Oficial | Ejemplo | Razón Arquitectónica |
|---|---|---|---|
| `controllers/` | `{domain}_controller.py` | `commands_controller.py` | Identifica orquestadores de presentación y flujo. |
| `core/` | `{name}_core.py` | `app_container_core.py` | Componentes críticos del ciclo de vida y DI central. |
| `database/` | `{domain}_storage.py` / `database_manager.py` | `timers_storage.py` | Capa de persistencia aislada por dominio. |
| `handlers/` | `{domain}_handler.py` | `spam_handler.py` | Procesadores de eventos específicos de dominio. |
| `interfaces/` | `i_{domain}.py` | `i_auth.py`, `i_chat_provider.py` | Contratos abstractos (DIP). Prefijo `i_` estándar. |
| `models/` | `{domain}_models.py` | `alerts_models.py` | Entidades y DTOs de dominio. |
| `providers/` | `{platform}_provider.py` | `kick_provider.py`, `piper_provider.py` | Adaptadores de servicios externos (Boundary Layer). |
| `services/` | `{domain}_service.py` | `commands_service.py` | Lógica de negocio pura independiente de UI y DB. |
| `workers/` | `{domain}_worker.py` | `updater_worker.py` | Tareas asíncronas y subprocesos QThread. |
| `views/` | `{domain}_view.py` | `commands_view.py` | Vistas completas de pantalla. |
| `dialogs/` | `{domain}_dialog.py` | `timers_dialog.py` | Ventanas modales e interacciones emergentes. |
| `navigation/` | `{domain}_component.py` | `sidebar_component.py` | Elementos estructurales de navegación. |
| `components/*/` | `{domain}_{tipo}.py` | `event_card.py`, `stats_panel.py` | Componentes reutilizables agrupados por vista. |
| `widgets/` | `{name}_widget.py` | `block_widget.py`, `table_widget.py` | Primitivas UI y controles base reutilizables. |

### 2. Reglas de Cohesión y Gramática:
- **Snake_case estricto:** Todo en minúsculas separado por guión bajo.
- **Dominio al inicio, rol al final:** Siempre `{dominio}_{rol}.py` para mantener agrupación alfabética natural en el explorador.
- **Plural vs Singular riguroso:**
  - **Plural** para dominios que manejan colecciones o entidades múltiples: `alerts`, `commands`, `logs`, `rewards`, `timers`, `tokens`, `widgets`.
  - **Singular** para entidades únicas, singleton o subsistemas no enumerables: `auth`, `backup`, `browser`, `chat`, `dashboard`, `music`, `schedule`, `settings`, `spam`, `updater`.
- **Cero Palabras Redundantes:** No duplicar el nombre de la carpeta dentro del nombre del archivo (ej. en `dialogs/`, `platform_connect_dialog.py` → `platform_dialog.py`; en `components/widgets/`, `widget_card_component.py` → `widget_card.py`).

---

## 📦 Inventario Maestro — Backend (100 Archivos)

### 1. `backend/config/` (3 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `api_keys.py` | `api_keys.py` | ✅ Mantener | ⚠️ | Nombre estándar y descriptivo para configuración de claves. |
| 2 | `default_en_locale.py` | `locale_defaults.py` | 🔄 Renombrar | ⚠️ | Evita adjetivo antes de sustantivo; centraliza valores por defecto. |
| 3 | `version.py` | `version.py` | ✅ Mantener | ⚠️ | Metadato de versión de la aplicación. Estándar Python. |

---

### 2. `backend/controllers/` (13 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `alerts_controller.py` | `alerts_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en plural. |
| 2 | `chat_controller.py` | `chat_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en singular. |
| 3 | `commands_controller.py` | `commands_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en plural. |
| 4 | `dashboard_controller.py` | `dashboard_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en singular. |
| 5 | `logs_controller.py` | `logs_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en plural. |
| 6 | `music_controller.py` | `music_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en singular. |
| 7 | `rewards_controller.py` | `rewards_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en plural. |
| 8 | `schedule_controller.py` | `schedule_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en singular. |
| 9 | `settings_controller.py` | `settings_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en plural. |
| 10 | `spam_controller.py` | `spam_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en singular. |
| 11 | `timers_controller.py` | `timers_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en plural. |
| 12 | `updater_controller.py` | `updater_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en singular. |
| 13 | `widgets_controller.py` | `widgets_controller.py` | ✅ Mantener | ⚠️ | Cumple 100% `{domain}_controller.py` en plural. |

---

### 3. `backend/core/` (3 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `app_container_core.py` | `app_container_core.py` | ✅ Mantener | ⚠️ | Contenedor de inyección de dependencias (IoC). |
| 2 | `app_logger_core.py` | `app_logger_core.py` | ✅ Mantener | ⚠️ | Sistema central de logging. |
| 3 | `main_window_core.py` | `main_window_core.py` | ✅ Mantener | ⚠️ | Coordinador central del ciclo de vida de la ventana. |

---

### 4. `backend/database/` (14 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `database_manager.py` | `database_manager.py` | ✅ Mantener | ⚠️ | Fachada principal de SQLite y transacciones. |
| 2 | `alert_storage.py` | `alerts_storage.py` | 🔄 Renombrar | ⚠️ | Plural para mantener paridad con `alerts_controller` y `alerts_view`. |
| 3 | `avatar_storage.py` | `avatar_storage.py` | ✅ Mantener | ⚠️ | Cache de avatares locales. |
| 4 | `cache_storage.py` | `cache_storage.py` | ✅ Mantener | ⚠️ | Almacenamiento genérico clave-valor de caché. |
| 5 | `commands_storage.py` | `commands_storage.py` | ✅ Mantener | ⚠️ | Persistencia de comandos personalizados. |
| 6 | `music_storage.py` | `music_storage.py` | ✅ Mantener | ⚠️ | Historial y configuración del reproductor. |
| 7 | `rewards_storage.py` | `rewards_storage.py` | ✅ Mantener | ⚠️ | Persistencia de recompensas por canal. |
| 8 | `schedule_storage.py` | `schedule_storage.py` | ✅ Mantener | ⚠️ | Persistencia del cronograma de streams. |
| 9 | `settings_storage.py` | `settings_storage.py` | ✅ Mantener | ⚠️ | Persistencia de configuración global. |
| 10 | `spam_storage.py` | `spam_storage.py` | ✅ Mantener | ⚠️ | Reglas y listas negras de moderación. |
| 11 | `system_log_storage.py` | `logs_storage.py` | 🔄 Renombrar | ⚠️ | Estandariza con `logs_controller` y `logs_view`. |
| 12 | `timers_storage.py` | `timers_storage.py` | ✅ Mantener | ⚠️ | Persistencia de temporizadores automáticos de chat. |
| 13 | `token_storage.py` | `tokens_storage.py` | 🔄 Renombrar | ⚠️ | Plural para coincidir con la naturaleza de colección de credenciales. |
| 14 | `widgets_storage.py` | `widgets_storage.py` | ✅ Mantener | ⚠️ | Persistencia de configuración de widgets de overlay. |

---

### 5. `backend/handlers/` (4 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `chat_filter_handler.py` | `spam_handler.py` | 🔄 Renombrar | ⚠️ | El dominio es spam/moderación; elimina "filter" redundante. |
| 2 | `log_handler.py` | `logs_handler.py` | 🔄 Renombrar | ⚠️ | Plural consistente con `logs_controller` y `logs_storage`. |
| 3 | `music_command_handler.py` | `music_handler.py` | 🔄 Renombrar | ⚠️ | El dominio es music; elimina "command" redundante. |
| 4 | `tts_voice_handler.py` | `tts_handler.py` | 🔄 Renombrar | ⚠️ | El dominio es tts; elimina "voice" redundante. |

---

### 6. `backend/interfaces/` (10 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `i_alerts.py` | `i_alerts.py` | ✅ Mantener | ✅ Aplicado | Adopta prefijo `i_` unificado; elimina sufijo `_interfaces`. |
| 2 | `i_auth.py` | `i_auth.py` | ✅ Mantener | ✅ Aplicado | Prefijo `i_` unificado. |
| 3 | `i_browser.py` | `i_browser.py` | ✅ Mantener | ✅ Aplicado | Prefijo `i_` unificado; elimina sufijo `_interface`. |
| 4 | `i_chat_provider.py` | `i_chat_provider.py` | ✅ Mantener | ✅ Aplicado | Agrega `i_` para explicitar que es una interfaz y no una implementación. |
| 5 | `i_chat_service.py` | `i_chat_service.py` | ✅ Mantener | ✅ Aplicado | Evita colisión de nombre con `services/chat/chat_service.py`. |
| 6 | `i_instance.py` | `i_instance.py` | ✅ Mantener | ✅ Aplicado | Prefijo `i_` unificado. |
| 7 | `i_music_provider.py` | `i_music_provider.py` | ✅ Mantener | ✅ Aplicado | Agrega `i_` para explicitar contrato de proveedor de música. |
| 8 | `i_settings.py` | `i_settings.py` | ✅ Mantener | ✅ Aplicado | Prefijo `i_` unificado. |
| 9 | `i_tts.py` | `i_tts.py` | ✅ Mantener | ✅ Aplicado | Prefijo `i_` unificado. |
| 10 | `i_updater.py` | `i_updater.py` | ✅ Mantener | ✅ Aplicado | Prefijo `i_` unificado. |

---

### 7. `backend/models/` (1 archivo)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `alert_models.py` | `alerts_models.py` | 🔄 Renombrar | ⚠️ | Plural consistente con `alerts_storage` y `alerts_controller`. |

---

### 8. `backend/providers/` (10 archivos)

#### `providers/chat/` (6 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `kick_client.py` | `kick_provider.py` | 🔄 Renombrar | ⚠️ | Estandariza con el sufijo `_provider` para la API de Kick. |
| 2 | `kick_websocket.py` | `kick_ws_provider.py` | 🔄 Renombrar | ⚠️ | Diferencia explícitamente el proveedor de socket en tiempo real. |
| 3 | `tiktok_chat_provider.py` | `tiktok_provider.py` | 🔄 Renombrar | ⚠️ | Elimina "chat" redundante dado que está en la carpeta `chat/`. |
| 4 | `twitch_client.py` | `twitch_provider.py` | 🔄 Renombrar | ⚠️ | Estandariza con el sufijo `_provider` para la API de Twitch. |
| 5 | `twitch_websocket.py` | `twitch_ws_provider.py` | 🔄 Renombrar | ⚠️ | Diferencia explícitamente el socket de Twitch. |
| 6 | `youtube_chat_provider.py` | `youtube_provider.py` | 🔄 Renombrar | ⚠️ | Elimina "chat" redundante en el nombre. |

#### `providers/music/` (1 archivo)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 7 | `youtube_client.py` | `youtube_provider.py` | 🔄 Renombrar | ⚠️ | Estandariza como proveedor de música según `i_music_provider.py`. |

#### `providers/voices/` (3 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 8 | `tts_local.py` | `local_provider.py` | 🔄 Renombrar | ⚠️ | Elimina prefijo redundante `tts_`; adopta sufijo `_provider`. |
| 9 | `tts_online.py` | `online_provider.py` | 🔄 Renombrar | ⚠️ | Elimina prefijo `tts_`; adopta sufijo `_provider`. |
| 10 | `tts_piper.py` | `piper_provider.py` | 🔄 Renombrar | ⚠️ | Elimina prefijo `tts_`; adopta sufijo `_provider`. |

---

### 9. `backend/services/` (25 archivos)

#### `services/alerts/` (2 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `alert_queue.py` | `alerts_queue.py` | 🔄 Renombrar | ⚠️ | Plural coherente con el subsistema `alerts`. |
| 2 | `alert_service.py` | `alerts_service.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `alerts_controller` y `alerts_storage`. |

#### `services/auth/` (1 archivo)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 3 | `oauth_service.py` | `auth_service.py` | 🔄 Renombrar | ⚠️ | Coincide exactamente con la carpeta `auth/` y la interfaz `i_auth.py`. |

#### `services/chat/` (7 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 4 | `chat_service.py` | `chat_service.py` | ✅ Mantener | ⚠️ | Servicio de mensajería en singular. |
| 5 | `command_service.py` | `commands_service.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `commands_controller` y `commands_storage`. |
| 6 | `pipeline.py` | `chat_pipeline.py` | 🔄 Renombrar | ⚠️ | Añade dominio al inicio para evitar ambigüedad. |
| 7 | `piper_voice_manager.py` | `piper_manager.py` | 🔄 Renombrar | ⚠️ | Elimina "voice" redundante en el contexto del motor Piper. |
| 8 | `spam_service.py` | `spam_service.py` | ✅ Mantener | ⚠️ | Servicio de moderación en singular. |
| 9 | `timer_service.py` | `timers_service.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `timers_controller` y `timers_storage`. |
| 10 | `tts_service.py` | `tts_service.py` | ✅ Mantener | ⚠️ | Servicio de síntesis de voz en singular. |

#### `services/overlay/` (3 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 11 | `overlay_manager.py` | `overlay_manager.py` | ✅ Mantener | ⚠️ | Gestor del servidor local de overlays. |
| 12 | `overlay_routes.py` | `overlay_routes.py` | ✅ Mantener | ⚠️ | Enrutador HTTP de endpoints para OBS. |
| 13 | `websocket_client.py` | `overlay_ws_client.py` | 🔄 Renombrar | ⚠️ | Agrega prefijo de dominio `overlay_` para no confundir con chat. |

#### `services/rewards/` (2 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 14 | `rewards_service.py` | `rewards_service.py` | ✅ Mantener | ⚠️ | Servicio de puntos y recompensas en plural. |
| 15 | `thumbnail_service.py` | `thumbnail_service.py` | ✅ Mantener | ⚠️ | Descargador y procesador de miniaturas de rewards. |

#### `services/schedule/` (1 archivo)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 16 | `schedule_service.py` | `schedule_service.py` | ✅ Mantener | ⚠️ | Servicio de planificación de streams en singular. |

#### `services/system/` (9 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 17 | `backup_service.py` | `backup_service.py` | ✅ Mantener | ⚠️ | Servicio de copias de seguridad de base de datos. |
| 18 | `browser_service.py` | `browser_service.py` | ✅ Mantener | ⚠️ | Apertura de URLs y navegación externa. |
| 19 | `dashboard_service.py` | `dashboard_service.py` | ✅ Mantener | ⚠️ | Agregador de métricas para la pantalla principal. |
| 20 | `instance_services.py` | `instance_service.py` | 🔄 Renombrar | ⚠️ | Singular consistente con todos los demás servicios (`_service.py`). |
| 21 | `log_service.py` | `logs_service.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `logs_controller` y `logs_storage`. |
| 22 | `settings_service.py` | `settings_service.py` | ✅ Mantener | ⚠️ | Servicio de configuración del sistema. |
| 23 | `translation_service.py` | `translation_service.py` | ✅ Mantener | ⚠️ | Motor de internacionalización (i18n). |
| 24 | `updater_service.py` | `updater_service.py` | ✅ Mantener | ⚠️ | Verificación de actualizaciones en GitHub. |
| 25 | `widget_service.py` | `widgets_service.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `widgets_controller` y `widgets_storage`. |

---

### 10. `backend/utils/` (1 archivo)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `json_utils.py` | `json_utils.py` | ✅ Mantener | ⚠️ | Utilidades seguras de serialización y lectura JSON. |

---

### 11. `backend/workers/` (16 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `bug_report_worker.py` | `bug_report_worker.py` | ✅ Mantener | ⚠️ | Envío asíncrono de reportes de errores. |
| 2 | `crash_report_worker.py` | `crash_report_worker.py` | ✅ Mantener | ⚠️ | Envío asíncrono de crash dumps. |
| 3 | `global_media_worker.py` | `global_media_worker.py` | ✅ Mantener | ⚠️ | Descarga de recursos multimedia en segundo plano. |
| 4 | `kick_auth_worker.py` | `kick_auth_worker.py` | ✅ Mantener | ⚠️ | Flujo OAuth y renovación de tokens Kick. |
| 5 | `kick_chat_worker.py` | `kick_chat_worker.py` | ✅ Mantener | ⚠️ | Conexión en hilo separado al chat de Kick. |
| 6 | `music_worker.py` | `music_worker.py` | ✅ Mantener | ⚠️ | Procesamiento de cola de reproducción de audio. |
| 7 | `rewards_worker.py` | `rewards_worker.py` | ✅ Mantener | ⚠️ | Escucha de eventos de recompensas. |
| 8 | `schedule_worker.py` | `schedule_worker.py` | ✅ Mantener | ⚠️ | Sincronización del calendario de transmisiones. |
| 9 | `tiktok_chat_worker.py` | `tiktok_chat_worker.py` | ✅ Mantener | ⚠️ | Conexión WebSocket al stream de TikTok. |
| 10 | `timers_worker.py` | `timers_worker.py` | ✅ Mantener | ⚠️ | Disparador de mensajes programados en chat. Plural coherente. |
| 11 | `twitch_auth_worker.py` | `twitch_auth_worker.py` | ✅ Mantener | ⚠️ | Flujo OAuth de Twitch en segundo plano. |
| 12 | `twitch_chat_worker.py` | `twitch_chat_worker.py` | ✅ Mantener | ⚠️ | Conexión IRC/WebSocket a Twitch. |
| 13 | `twitch_reward_worker.py` | `twitch_rewards_worker.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `rewards_worker.py`. |
| 14 | `update_worker.py` | `updater_worker.py` | 🔄 Renombrar | ⚠️ | Coherente con `updater_controller.py` y `updater_service.py`. |
| 15 | `voice_worker.py` | `voice_worker.py` | ✅ Mantener | ⚠️ | Sintetizador de audio en hilo separado. |
| 16 | `youtube_chat_worker.py` | `youtube_chat_worker.py` | ✅ Mantener | ⚠️ | Polling/Socket de Live Chat de YouTube. |

---

## 🎨 Inventario Maestro — Frontend (79 Archivos)

### 1. `frontend/common/` (5 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `icons.py` | `icons.py` | ✅ Mantener | ⚠️ | Catálogo centralizado de SVG y glifos. |
| 2 | `markdown.py` | `markdown.py` | ✅ Mantener | ⚠️ | Formateador e higienizador de texto Markdown. |
| 3 | `paths.py` | `paths.py` | ✅ Mantener | ⚠️ | Constantes de rutas estáticas y de recursos. |
| 4 | `theme.py` | `theme.py` | ✅ Mantener | ⚠️ | Tokens de diseño, paleta de colores y estilos globales. |
| 5 | `validators.py` | `validators.py` | ✅ Mantener | ⚠️ | Validadores de campos de texto y formularios UI. |

---

### 2. `frontend/components/` (28 archivos)

#### `components/alerts/` (6 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `alert_mockup.py` | `alert_mockup.py` | ✅ Mantener | ⚠️ | Previsualizador interactivo de alerta. |
| 2 | `event_card.py` | `event_card.py` | ✅ Mantener | ⚠️ | Tarjeta individual de evento de stream. |
| 3 | `overlay_card.py` | `overlay_card.py` | ✅ Mantener | ⚠️ | Tarjeta de configuración de overlay. |
| 4 | `responsive_stack.py` | `responsive_stack.py` | ✅ Mantener | ⚠️ | Contenedor dinámico adaptativo. |
| 5 | `sidebar_panel.py` | `sidebar_panel.py` | ✅ Mantener | ⚠️ | Panel lateral de opciones de alertas. |
| 6 | `variant_item.py` | `variant_item.py` | ✅ Mantener | ⚠️ | Elemento de variante de diseño de alerta. |

#### `components/chat/` (5 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 7 | `bot_mute.py` | `bot_mute.py` | ✅ Mantener | ⚠️ | Control rápido para silenciar el bot. |
| 8 | `chat_display.py` | `chat_display.py` | ✅ Mantener | ⚠️ | Vista de lista de mensajes en tiempo real. |
| 9 | `chat_mockup.py` | `chat_mockup.py` | ✅ Mantener | ⚠️ | Simulador visual de burbujas de chat. |
| 10 | `overlay_settings.py` | `overlay_settings.py` | ✅ Mantener | ⚠️ | Ajustes del widget de chat en stream. |
| 11 | `tts_settings.py` | `tts_settings.py` | ✅ Mantener | ⚠️ | Opciones de síntesis de voz en el chat. |

#### `components/dashboard/` (2 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 12 | `distribution_bar.py` | `distribution_bar.py` | ✅ Mantener | ⚠️ | Barra de porcentaje de actividad por plataforma. |
| 13 | `platform_card.py` | `platform_card.py` | ✅ Mantener | ⚠️ | Tarjeta de estado de conexión por servicio. |

#### `components/dialogs/` (4 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 14 | `draggable_box.py` | `draggable_box.py` | ✅ Mantener | ⚠️ | Cuadro de posicionamiento arrastrable. |
| 15 | `image_dropzone.py` | `image_dropzone.py` | ✅ Mantener | ⚠️ | Zona de arrastrar y soltar imágenes. |
| 16 | `piper_voice_item.py` | `piper_voice_item.py` | ✅ Mantener | ⚠️ | Fila individual para descargar voces de Piper. |
| 17 | `severity_card.py` | `severity_card.py` | ✅ Mantener | ⚠️ | Tarjeta para seleccionar severidad en reportes de fallos. |

#### `components/log/` (1 archivo)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 18 | `log_controls.py` | `logs_controls.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `logs_view.py`. |

#### `components/music/` (6 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 19 | `commands_panel.py` | `commands_panel.py` | ✅ Mantener | ⚠️ | Panel de comandos de control musical. |
| 20 | `music_mockup.py` | `music_mockup.py` | ✅ Mantener | ⚠️ | Vista previa del banner de canción en overlay. |
| 21 | `music_settings_panel.py` | `music_settings_panel.py` | ✅ Mantener | ⚠️ | Ajustes del motor de reproducción. |
| 22 | `player_settings.py` | `player_settings.py` | ✅ Mantener | ⚠️ | Opciones de volumen y salida de audio. |
| 23 | `queue_panel.py` | `queue_panel.py` | ✅ Mantener | ⚠️ | Lista de canciones en espera. |
| 24 | `stats_panel.py` | `stats_panel.py` | ✅ Mantener | ⚠️ | Estadísticas de peticiones musicales. |

#### `components/schedule/` (3 archivos)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 25 | `quick_change_panel.py` | `quick_change_panel.py` | ✅ Mantener | ⚠️ | Modificador rápido de horario de stream. |
| 26 | `schedule_form_panel.py` | `schedule_form_panel.py` | ✅ Mantener | ⚠️ | Formulario para añadir o editar emisiones. |
| 27 | `schedule_table_panel.py` | `schedule_table_panel.py` | ✅ Mantener | ⚠️ | Tabla visual del cronograma semanal. |

#### `components/widgets/` (1 archivo)
| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 28 | `widget_card_component.py` | `widget_card.py` | 🔄 Renombrar | ⚠️ | Elimina el sufijo redundante `_component`. |

---

### 3. `frontend/dialogs/` (15 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `already_running_dialog.py` | `already_running_dialog.py` | ✅ Mantener | ⚠️ | Modal de advertencia de instancia duplicada. |
| 2 | `base_dialog.py` | `base_dialog.py` | ✅ Mantener | ⚠️ | Clase base para modales personalizados. |
| 3 | `bug_report_dialog.py` | `bug_report_dialog.py` | ✅ Mantener | ⚠️ | Modal de envío de incidencias. |
| 4 | `command_dialog.py` | `commands_dialog.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `commands_controller` y `commands_view`. |
| 5 | `crash_report_dialog.py` | `crash_report_dialog.py` | ✅ Mantener | ⚠️ | Diálogo de informe de cierre inesperado. |
| 6 | `message_editor_dialog.py` | `message_dialog.py` | 🔄 Renombrar | ⚠️ | Elimina "editor" redundante. |
| 7 | `piper_voices_dialog.py` | `piper_dialog.py` | 🔄 Renombrar | ⚠️ | Elimina "voices" redundante en contexto de TTS. |
| 8 | `platform_connect_dialog.py` | `platform_dialog.py` | 🔄 Renombrar | ⚠️ | Elimina "connect" redundante. |
| 9 | `release_notes_dialog.py` | `release_notes_dialog.py` | ✅ Mantener | ⚠️ | Visualizador de notas de la nueva versión. |
| 10 | `rewards_dialog.py` | `rewards_dialog.py` | ✅ Mantener | ⚠️ | Modal de creación de recompensas de canal. |
| 11 | `tiktok_connect_dialog.py` | `tiktok_dialog.py` | 🔄 Renombrar | ⚠️ | Elimina "connect" redundante. |
| 12 | `timer_dialog.py` | `timers_dialog.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `timers_controller` y `timers_view`. |
| 13 | `update_dialog.py` | `updater_dialog.py` | 🔄 Renombrar | ⚠️ | Coherente con `updater_controller` y `updater_service`. |
| 14 | `visual_positioner_dialog.py` | `positioner_dialog.py` | 🔄 Renombrar | ⚠️ | Elimina "visual" redundante. |
| 15 | `youtube_connect_dialog.py` | `youtube_dialog.py` | 🔄 Renombrar | ⚠️ | Elimina "connect" redundante. |

---

### 4. `frontend/navigation/` (3 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `sidebar_component.py` | `sidebar_component.py` | ✅ Mantener | ⚠️ | Menú vertical principal de navegación. |
| 2 | `toast_component.py` | `toast_component.py` | ✅ Mantener | ⚠️ | Notificaciones flotantes no bloqueantes. |
| 3 | `tray_menu_component.py` | `tray_menu_component.py` | ✅ Mantener | ⚠️ | Menú contextual en la bandeja del sistema (System Tray). |

---

### 5. `frontend/views/` (12 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `alerts_view.py` | `alerts_view.py` | ✅ Mantener | ⚠️ | Vista principal de gestión de alertas. |
| 2 | `chat_view.py` | `chat_view.py` | ✅ Mantener | ⚠️ | Vista en vivo del chat unificado. |
| 3 | `command_view.py` | `commands_view.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `commands_controller` y colecciones. |
| 4 | `dashboard_view.py` | `dashboard_view.py` | ✅ Mantener | ⚠️ | Pantalla inicial de métricas y resumen. |
| 5 | `log_view.py` | `logs_view.py` | 🔄 Renombrar | ⚠️ | Plural coherente con `logs_controller` y `logs_storage`. |
| 6 | `music_view.py` | `music_view.py` | ✅ Mantener | ⚠️ | Vista del reproductor y peticiones de música. |
| 7 | `rewards_view.py` | `rewards_view.py` | ✅ Mantener | ⚠️ | Gestión de canjes y recompensas de canal. |
| 8 | `schedule_view.py` | `schedule_view.py` | ✅ Mantener | ⚠️ | Calendario y cronograma de directos. |
| 9 | `settings_view.py` | `settings_view.py` | ✅ Mantener | ⚠️ | Pantalla de configuración general de la aplicación. |
| 10 | `spam_view.py` | `spam_view.py` | ✅ Mantener | ⚠️ | Configuración de filtros antispam y moderación. |
| 11 | `timers_view.py` | `timers_view.py` | ✅ Mantener | ⚠️ | Vista de temporizadores programados de chat. |
| 12 | `widgets_view.py` | `widgets_view.py` | ✅ Mantener | ⚠️ | Galería y configuración de widgets para streaming. |

---

### 6. `frontend/widgets/` (16 archivos)

| # | Archivo Actual | Nombre Estandarizado | Acción | Estado | Justificación / Notas |
|---|---|---|---|---|---|
| 1 | `base_view.py` | `base_view.py` (en `views/`) | 📦 Reubicar | ⚠️ | Define `BaseView` para todas las vistas; pertenece a `frontend/views/`. |
| 2 | `blocks.py` | `block_widget.py` | 🔄 Renombrar | ⚠️ | Primitiva UI; adopta sufijo `_widget.py`. |
| 3 | `category_search.py` | `category_search.py` | ✅ Mantener | ⚠️ | Selector con autocompletado para categorías de stream. |
| 4 | `clearable_line_edit.py` | `clearable_line_edit.py` | ✅ Mantener | ⚠️ | Campo de texto con botón de borrado rápido. |
| 5 | `color_picker.py` | `color_picker.py` | ✅ Mantener | ⚠️ | Selector visual de paleta RGB / HEX. |
| 6 | `controls.py` | `controls_widget.py` | 🔄 Renombrar | ⚠️ | Primitiva UI; adopta sufijo `_widget.py`. |
| 7 | `filter_header.py` | `filter_header.py` | ✅ Mantener | ⚠️ | Cabecera con filtros y buscador integrado. |
| 8 | `flow_layout.py` | `flow_layout.py` | ✅ Mantener | ⚠️ | Layout dinámico de ajuste fluido estilo Flexbox. |
| 9 | `no_wheel.py` | `no_wheel.py` | ✅ Mantener | ⚠️ | Modificador para evitar scroll involuntario en ComboBox / SpinBox. |
| 10 | `pagination.py` | `pagination_widget.py` | 🔄 Renombrar | ⚠️ | Primitiva UI de paginación de tablas. |
| 11 | `platform_controls.py` | `platform_controls.py` | ✅ Mantener | ⚠️ | Barra de botones de filtro por plataforma (Kick, Twitch, etc.). |
| 12 | `scalable_illustration.py` | `scalable_illustration.py` | ✅ Mantener | ⚠️ | Renderizador de arte vectorial SVG escalable. |
| 13 | `search_bar.py` | `search_bar.py` | ✅ Mantener | ⚠️ | Barra de búsqueda estándar con debounce. |
| 14 | `searchable_combo_box.py` | `searchable_combo_box.py` | ✅ Mantener | ⚠️ | Menú desplegable con filtro en tiempo real. |
| 15 | `segmented_control.py` | `segmented_control.py` | ✅ Mantener | ⚠️ | Conmutador de pestañas segmentadas tipo iOS/macOS. |
| 16 | `table.py` | `table_widget.py` | 🔄 Renombrar | ⚠️ | Primitiva UI de tabla estilizada. |

---

## 🗺️ Hoja de Ruta de Ejecución por Fases (Migration Roadmap)

Para aplicar estos renombres en el código de forma segura sin romper imports ni tests:

### Fase 1: Interfaces & Contratos Base (Bajo Riesgo)
- Renombrar `backend/interfaces/` (10 archivos a `i_{dominio}.py`).
- Actualizar los imports en los 13 controllers y en `app_container_core.py`.
- **Comprobación:** `pytest resources/tests/backend/`.

### Fase 2: Providers & Handlers (Riesgo Medio)
- Renombrar providers de chat, music y voices (`{platform}_provider.py`).
- Renombrar los 4 handlers (`spam_handler.py`, `logs_handler.py`, `music_handler.py`, `tts_handler.py`).
- Actualizar contenedor de DI y llamadas en workers.

### Fase 3: Servicios & Workers (Riesgo Medio-Alto)
- Renombrar servicios inconsistentes (`commands_service.py`, `timers_service.py`, `chat_pipeline.py`, `logs_service.py`, `widgets_service.py`, `auth_service.py`, `instance_service.py`).
- Renombrar `twitch_rewards_worker.py` y `updater_worker.py`.
- Actualizar dependencias en controladores y servicios de segundo plano.

### Fase 4: Frontend — Dialogs, Views & Componentes (Riesgo Medio)
- Renombrar dialogs a `{dominio}_dialog.py` (eliminando `_connect_dialog` y `_editor_dialog`).
- Renombrar `command_view.py` -> `commands_view.py` y `log_view.py` -> `logs_view.py`.
- Renombrar `widget_card_component.py` -> `widget_card.py` y `log_controls.py` -> `logs_controls.py`.
- Actualizar enrutador en `main_window_core.py` y `sidebar_component.py`.

### Fase 5: Frontend — Primitivas UI & Reubicación (Riesgo Bajo-Medio)
- Reubicar `base_view.py` desde `widgets/` a `frontend/views/base_view.py`.
- Renombrar primitivas en `widgets/` (`block_widget.py`, `controls_widget.py`, `pagination_widget.py`, `table_widget.py`).
- Actualizar todos los imports de widgets en vistas y componentes.
- **Comprobación Final:** `python resources/tests/run_tests.py` completo.
