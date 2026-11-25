# Walkthrough Técnico — MiniKick v1.6.9 (Paso 05)

Revisión de bugs de los overlays y corrección de cinco hallazgos: XSS en el widget de Emote Combo, arranque silencioso del servidor de overlays con el puerto ocupado, HTML sin escapar en las alertas, frames WebSocket sin tope de tamaño y topics WebSocket desconocidos aceptados, reloj sin reconexión, carpeta completa de las alertas HTML expuesta, rangos de sufijo mal resueltos y estado de replay mutado entre hilos.

---

## Contexto

La revisión cubrió `backend/services/overlay/` (manager, routes, cliente WebSocket) y los HTML/JS de `assets/overlays/`.

- **XSS en Emote Combo.** `_KICK_EMOTE_REGEX` (`backend/utils/emote_utils.py`) acepta cualquier carácter salvo `]` en el nombre del emote, y `widgets/emote_combo.html` lo interpolaba en `innerHTML` (`alt="${emoteName}"`). El combo cuenta repeticiones aunque sean del mismo usuario, así que un solo espectador alcanzaba `min_combo` y ejecutaba JS en el navegador de OBS. El chat, las encuestas y los chatters ya escapaban con `escapeHtml`.
- **Arranque silencioso.** `OverlayServerManager.start()` solo registraba el `OSError` cuando el puerto 8090 estaba ocupado. La app seguía mostrando URLs de overlay muertas (o que apuntaban a otro proceso con otro token) sin avisar.

- **HTML sin escapar en alertas.** `alerts.html` asignaba `formatted_text` a `innerHTML`, y `AlertService` lo construía con `display_name` y `message` crudos. Era explotable con plantillas que incluyan `{message}` y con nombres de YouTube/TikTok que admiten símbolos. `formatted_text` también alimenta al TTS, por lo que no se puede escapar en origen.
- **WebSocket sin límites.** `WebSocketClient.read_frame` leía `payload_len` completo en memoria (hasta 2⁶⁴ bytes), y `_handle_websocket_upgrade` respondía 101 antes de validar el topic: un topic desconocido quedaba conectado sin registrarse ni recibir eventos.
- **Reloj sin reconexión.** `widgets/clock.html` abría el WebSocket sin `onclose`: tras reiniciar MiniKick no recibía más `widget_toggle` ni el replay hasta refrescar OBS.
- **Carpeta de alertas HTML expuesta.** `trigger_alert` registra el directorio completo del `.html` y `/user_media` servía cualquier archivo dentro; con el token (por ejemplo si la URL de OBS se ve en pantalla) se podían leer `.env`, `.txt`, `.db`, etc.
- **Rango de sufijo.** `Range: bytes=-500` devolvía los primeros 501 bytes en vez de los últimos 500.
- **Estado de replay.** `_last_death_data` y `_last_score_data` se mutaban con `update()` mientras otro hilo los expandía con `{**dict}`, lo que podía lanzar `RuntimeError` y cortar al cliente.

## Cambios por capa

**Overlays (assets)**
- `overlays/widgets/clock.html`: `connectWS`/`scheduleReconnect` con reintento a 3 s, igual que los demás widgets.
- `overlays/widgets/deaths.html` y `score.html`: se quita la constante `eventSourceUrl`, que nunca se usaba.
- `overlays/alerts/alerts.html`: el título usa `formatted_html`; si falta, escapa `formatted_text` (o el texto por defecto) con el nuevo `escapeHtml`, y el nombre de usuario se escapa antes de armar la expresión del resaltado.
- `overlays/widgets/emote_combo.html`: el `<img>` y el `<span>` del combo se construyen con `createElement`, asignando `alt`, `src` y `textContent`, y se montan con `replaceChildren`. Los datos del chat nunca se interpretan como HTML.

**Backend**
- `services/alerts/alerts_service.py`: el payload incluye `formatted_html`, con la plantilla del streamer intacta y los valores `str` escapados con `html.escape` (los numéricos conservan su tipo para formatos como `{amount:,}`). `formatted_text` sigue crudo para el TTS.
- `services/overlay/overlay_manager.py`: `trigger_widget_event` reemplaza `_last_death_data` y `_last_score_data` con un dict nuevo en vez de mutarlos; `start()` devuelve `bool`, limpia `server` y `thread` si falla y guarda el mensaje en `start_error`; nueva propiedad `is_running`; nuevo `has_ws_topic`.
- `services/overlay/overlay_ws_client.py`: `read_frame` corta la conexión y registra un aviso si `payload_len` supera 1 MiB (`_MAX_INCOMING_FRAME_BYTES`).
- `services/overlay/overlay_routes.py`: `/user_media` solo sirve extensiones web (`_USER_MEDIA_ALLOWED_EXTENSIONS`: html, css, js, json, imágenes, audio, video y fuentes) y responde 403 al resto; `_serve_file` resuelve `bytes=-N` como los últimos N bytes; `_handle_websocket_upgrade` responde 400 ante un topic desconocido, antes del 101; el topic rechazado se registra truncado y con `repr`.

**Frontend**
- `window/startup_coordinator.py`: `_warn_if_overlay_server_down` se ejecuta al inicio de `_finish_settings_hydration` y muestra un toast de error (8 s) con el puerto afectado.
- `assets/i18n/{es,en}/main.ftl`: claves `main-toast-overlay_server_down_title` y `main-toast-overlay_server_down_msg`.

**Pruebas**
- `resources/tests/test_overlay_widget_reconnect.py` (nuevo): todo overlay HTML/JS con `new WebSocket` debe tener `onclose` y `setTimeout`.
- `resources/tests/test_overlay_media_http.py` (nuevo): pruebas HTTP reales; `/user_media` sirve `alert.html` y `pic.png` pero responde 403 para `secret.env` y `notes.txt`, y `bytes=-100`, `bytes=10-19` y `bytes=1000-` devuelven el trozo correcto.
- `resources/tests/test_overlay_replay_state.py` (nuevo): una referencia tomada antes de un `death_update`/`score`/`widget_toggle` no cambia.
- `resources/tests/test_overlay_ws_hardening.py` (nuevo): frame de 2⁴⁰ bytes corta al cliente, un frame enmascarado pequeño se sigue leyendo, el manager solo conoce sus topics y el upgrade con topic desconocido responde 400 sin 101.
- `resources/tests/test_alert_html_escaping.py` (nuevo): escape de `{user}` y `{message}` con la plantilla intacta, `formatted_text` crudo para el TTS y `{amount:,}` sin romperse.
- `resources/tests/test_overlay_widget_html_safety.py` (nuevo): falla si `emote_combo.html` vuelve a interpolar `emoteName` o `emoteSrc` dentro de `innerHTML`.
- `resources/tests/test_overlay_server_start.py` (nuevo): `start()` devuelve `False` con el puerto ocupado y `True` con uno libre, limpiando `start_error`.

## Archivos afectados

`assets/overlays/widgets/emote_combo.html`, `assets/overlays/alerts/alerts.html`, `backend/services/alerts/alerts_service.py`, `backend/services/overlay/overlay_manager.py`, `backend/services/overlay/overlay_ws_client.py`, `backend/services/overlay/overlay_routes.py`, `frontend/window/startup_coordinator.py`, `assets/i18n/es/main.ftl`, `assets/i18n/en/main.ftl`, `resources/tests/test_overlay_widget_html_safety.py`, `resources/tests/test_overlay_server_start.py`, `resources/tests/test_alert_html_escaping.py`, `resources/tests/test_overlay_ws_hardening.py`, `assets/overlays/widgets/clock.html`, `assets/overlays/widgets/deaths.html`, `assets/overlays/widgets/score.html`, `resources/tests/test_overlay_widget_reconnect.py`, `resources/tests/test_overlay_media_http.py`, `resources/tests/test_overlay_replay_state.py`.

## Verificación

- `pytest` sobre los siete archivos nuevos, `test_overlay_client_diagnostics.py`, `test_chat_overlay_load_limits.py` y `test_startup_coordinator.py`: 46 en verde. Las pruebas nuevas fallan sin su cambio (se comprobó para el widget, alertas, `clock.html`, `/user_media`, rango de sufijo y estado de replay).
- `resources/tools/project_quality_suite.py --quick`: 13 auditores en PASS; `Frontend QSS Roles` y `Frontend Qt Windows` fallan igual que en el commit base `6b01cdcb`.
- Contra un servidor real: los 5 topics que usan los overlays (`rewards`, `chat`, `music`, `widgets`, `alerts`) siguen respondiendo 101, `bogus` responde 400 y un frame de 2⁴⁰ bytes deja 0 clientes conectados.
- `clock.html` simulado en node con un WebSocket falso: se oculta con el toggle, programa la reconexión a 3 s y recupera el estado tras reconectar; `node --check` sobre los scripts de `clock`, `deaths` y `score`.
- No se probó visualmente en OBS (ni el combo ni una alerta con HTML en el nombre) ni con una instancia real de MiniKick ocupando el puerto.

## Notas

Hallazgos de la revisión que **no** se corrigen:

- Los endpoints SSE (`/events`, `/chat_events`, `/music_events`, `/widget_events`) y las listas `clients`/`alert_clients` se conservan: el README los menciona y `test_sse_broadcast_never_blocks_on_a_full_client_queue` los cubre. Ningún overlay propio los usa, así que quitarlos depende de si hay overlays personalizados apuntando a ellos.
- `trigger_rewards` con `filepath` vacío no ocurre: su único llamador (`trigger_preview`) valida con `is_file_valid`.
- Los overlays usan `localhost` y el servidor escucha solo en `127.0.0.1`; si `localhost` resuelve a `::1` y el cliente no hace fallback, no conecta. No se cambió.
