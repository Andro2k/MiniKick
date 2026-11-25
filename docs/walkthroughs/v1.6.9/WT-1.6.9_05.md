# Walkthrough Técnico — MiniKick v1.6.9 (Paso 05)

Revisión de bugs de los overlays y corrección de cinco hallazgos: XSS en el widget de Emote Combo, arranque silencioso del servidor de overlays con el puerto ocupado, HTML sin escapar en las alertas, frames WebSocket sin tope de tamaño y topics WebSocket desconocidos aceptados.

---

## Contexto

La revisión cubrió `backend/services/overlay/` (manager, routes, cliente WebSocket) y los HTML/JS de `assets/overlays/`.

- **XSS en Emote Combo.** `_KICK_EMOTE_REGEX` (`backend/utils/emote_utils.py`) acepta cualquier carácter salvo `]` en el nombre del emote, y `widgets/emote_combo.html` lo interpolaba en `innerHTML` (`alt="${emoteName}"`). El combo cuenta repeticiones aunque sean del mismo usuario, así que un solo espectador alcanzaba `min_combo` y ejecutaba JS en el navegador de OBS. El chat, las encuestas y los chatters ya escapaban con `escapeHtml`.
- **Arranque silencioso.** `OverlayServerManager.start()` solo registraba el `OSError` cuando el puerto 8090 estaba ocupado. La app seguía mostrando URLs de overlay muertas (o que apuntaban a otro proceso con otro token) sin avisar.

- **HTML sin escapar en alertas.** `alerts.html` asignaba `formatted_text` a `innerHTML`, y `AlertService` lo construía con `display_name` y `message` crudos. Era explotable con plantillas que incluyan `{message}` y con nombres de YouTube/TikTok que admiten símbolos. `formatted_text` también alimenta al TTS, por lo que no se puede escapar en origen.
- **WebSocket sin límites.** `WebSocketClient.read_frame` leía `payload_len` completo en memoria (hasta 2⁶⁴ bytes), y `_handle_websocket_upgrade` respondía 101 antes de validar el topic: un topic desconocido quedaba conectado sin registrarse ni recibir eventos.

## Cambios por capa

**Overlays (assets)**
- `overlays/alerts/alerts.html`: el título usa `formatted_html`; si falta, escapa `formatted_text` (o el texto por defecto) con el nuevo `escapeHtml`, y el nombre de usuario se escapa antes de armar la expresión del resaltado.
- `overlays/widgets/emote_combo.html`: el `<img>` y el `<span>` del combo se construyen con `createElement`, asignando `alt`, `src` y `textContent`, y se montan con `replaceChildren`. Los datos del chat nunca se interpretan como HTML.

**Backend**
- `services/alerts/alerts_service.py`: el payload incluye `formatted_html`, con la plantilla del streamer intacta y los valores `str` escapados con `html.escape` (los numéricos conservan su tipo para formatos como `{amount:,}`). `formatted_text` sigue crudo para el TTS.
- `services/overlay/overlay_manager.py`: `start()` devuelve `bool`, limpia `server` y `thread` si falla y guarda el mensaje en `start_error`; nueva propiedad `is_running`; nuevo `has_ws_topic`.
- `services/overlay/overlay_ws_client.py`: `read_frame` corta la conexión y registra un aviso si `payload_len` supera 1 MiB (`_MAX_INCOMING_FRAME_BYTES`).
- `services/overlay/overlay_routes.py`: `_handle_websocket_upgrade` responde 400 ante un topic desconocido, antes del 101; el topic rechazado se registra truncado y con `repr`.

**Frontend**
- `window/startup_coordinator.py`: `_warn_if_overlay_server_down` se ejecuta al inicio de `_finish_settings_hydration` y muestra un toast de error (8 s) con el puerto afectado.
- `assets/i18n/{es,en}/main.ftl`: claves `main-toast-overlay_server_down_title` y `main-toast-overlay_server_down_msg`.

**Pruebas**
- `resources/tests/test_overlay_ws_hardening.py` (nuevo): frame de 2⁴⁰ bytes corta al cliente, un frame enmascarado pequeño se sigue leyendo, el manager solo conoce sus topics y el upgrade con topic desconocido responde 400 sin 101.
- `resources/tests/test_alert_html_escaping.py` (nuevo): escape de `{user}` y `{message}` con la plantilla intacta, `formatted_text` crudo para el TTS y `{amount:,}` sin romperse.
- `resources/tests/test_overlay_widget_html_safety.py` (nuevo): falla si `emote_combo.html` vuelve a interpolar `emoteName` o `emoteSrc` dentro de `innerHTML`.
- `resources/tests/test_overlay_server_start.py` (nuevo): `start()` devuelve `False` con el puerto ocupado y `True` con uno libre, limpiando `start_error`.

## Archivos afectados

`assets/overlays/widgets/emote_combo.html`, `assets/overlays/alerts/alerts.html`, `backend/services/alerts/alerts_service.py`, `backend/services/overlay/overlay_manager.py`, `backend/services/overlay/overlay_ws_client.py`, `backend/services/overlay/overlay_routes.py`, `frontend/window/startup_coordinator.py`, `assets/i18n/es/main.ftl`, `assets/i18n/en/main.ftl`, `resources/tests/test_overlay_widget_html_safety.py`, `resources/tests/test_overlay_server_start.py`, `resources/tests/test_alert_html_escaping.py`, `resources/tests/test_overlay_ws_hardening.py`.

## Verificación

- `pytest` sobre los cuatro archivos nuevos, `test_overlay_client_diagnostics.py`, `test_chat_overlay_load_limits.py` y `test_startup_coordinator.py`: 24 en verde. El test del widget y 2 de los 3 de alertas fallan sin el cambio.
- `resources/tools/project_quality_suite.py --quick`: 13 auditores en PASS; `Frontend QSS Roles` y `Frontend Qt Windows` fallan igual que en el commit base `6b01cdcb`.
- Contra un servidor real: los 5 topics que usan los overlays (`rewards`, `chat`, `music`, `widgets`, `alerts`) siguen respondiendo 101, `bogus` responde 400 y un frame de 2⁴⁰ bytes deja 0 clientes conectados.
- No se probó visualmente en OBS (ni el combo ni una alerta con HTML en el nombre) ni con una instancia real de MiniKick ocupando el puerto.

## Notas

Hallazgos de la revisión que **no** se corrigen en este paso:

- `widgets/clock.html` abre el WebSocket sin `onclose` ni reconexión.
- `trigger_alert` registra el directorio completo de un alert `.html` como media servida.
- Código muerto probable: endpoints SSE (`/events`, `/chat_events`, `/music_events`, `/widget_events`) y las listas `clients`/`alert_clients`.
