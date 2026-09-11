# 🚶 Walkthrough WT-1.5.9_10: Remoción de Alertas de Kick y Especialización Exclusiva para Twitch

## 🎯 Objetivo y Contexto

A raíz de reportes de usuarios donde las alertas de seguidores en Kick no se activaban en vivo, se realizó un análisis exhaustivo y pruebas de sniffing de paquetes en tiempo real sobre el WebSocket de Kick (`wss://ws-us2.pusher.com`) en el canal de `josuegmn` durante transmisiones activas con acciones de seguimiento en vivo.

**Hallazgo Clave:** El servidor Pusher de Kick no emite eventos nativos de nuevos seguidores (`channel.followed`, `FollowersUpdated` o similares no existen en los canales públicos de chatroom ni channel). Las únicas menciones provienen de mensajes regulares de chat generados por bots de terceros (`@Kicklet`, `BotRix`).

**Decisión:** Para evitar prometer funcionalidades inexistentes o confundir a los usuarios, se retiraron por completo las alertas de Kick en MiniKick, consolidando el sistema de alertas de forma exclusiva para **Twitch EventSub WebSocket**, donde sí existen eventos nativos fidedignos con metadatos completos.

---

### Novedades

- **[FEATURE] [ALERTS] Especialización Exclusiva de Alertas para Twitch EventSub:** El sistema de alertas se consolida exclusivamente para Twitch, soportando de forma nativa y en tiempo real sus 6 tipos de eventos principales (`follow`, `subscription`, `resub`, `sub_gift`, `raid`, `cheer`) a través de la conexión EventSub WebSocket sin intermediarios ni parsers de chat de terceros.

---

### Mejoras

- **[IMPROVEMENT] [ALERTS] Rediseño Unificado de AlertsView sin Pestañas Redundantes:** Se eliminaron los botones selectores de pestañas (`btn_tab_kick`, `btn_tab_twitch`) y se unificó [`AlertsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py) en un diseño directo maestro-detalle. Esto redujo a la mitad el árbol de widgets apilados en memoria y simplificó la lógica responsiva de `resizeEvent` operando directamente sobre `twitch_columns` y `twitch_sidebar`.
- **[IMPROVEMENT] [KICK] Optimización $\mathcal{O}(1)$ en Despacho de Frames de Kick:** Se depuraron 8 eventos inoperantes de la tabla de despacho `_dispatch_table` en [`KickWebSocketManager`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_ws_provider.py) (`channel.followed`, `FollowersUpdated`, `GoalProgressUpdate`, etc.), reduciendo el overhead de CPU por frame recibido y eliminando el descarte inútil de payloads JSON.
- **[IMPROVEMENT] [CLEAN CODE] Desacoplamiento de Señales en Workers y Orquestador:** Se eliminó la señal Qt `alert_received` en [`KickChatWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/kick_chat_worker.py) y su conexión en [`MainWindowCore`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py), preservando la alta cohesión del proveedor de chat y liberando ciclos en el bucle de eventos (`QEventLoop`).
- **[IMPROVEMENT] [i18n] Cumplimiento Estricto de Cero Textos Hardcodeados:** Se actualizaron los subtítulos en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) especificando el soporte para Twitch de forma transparente y sin cadenas inline en código.
- **[IMPROVEMENT] [TESTS] Batería de Pruebas Unitarias al 100%:** Se actualizaron y verificaron 31 pruebas en [`test_alerts_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/frontend/views/test_alerts_view.py) y [`test_alert_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/backend/services/test_alert_service.py), validando la ausencia de despachadores de alertas en Kick y la operatividad de Twitch.

---

### Correcciones

- **[FIX] [ALERTS] Eliminación de Alertas No Nativas e Inoperantes de Kick:** Se corrigió el problema donde la interfaz prometía alertas en vivo de Kick que nunca se disparaban debido a la ausencia de soporte nativo en el protocolo WebSocket de Kick. Se eliminaron de raíz los métodos zombies `_handle_followers_updated`, `_handle_goal_progress_update`, `_handle_subscription`, etc., garantizando que solo se ofrezcan características 100% funcionales y reales.

---

## 🔬 Verificación y Pruebas Automatizadas

```bash
uv run pytest resources/tests/frontend/views/test_alerts_view.py resources/tests/backend/services/test_alert_models.py resources/tests/backend/services/test_alert_queue.py resources/tests/backend/controllers/test_alerts_controller.py resources/tests/backend/services/test_alert_service.py resources/tests/backend/services/test_alert_storage.py
```
**Resultado:** `31 passed in 1.39s (100% PASS)`

