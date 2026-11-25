# Walkthrough Técnico — MiniKick v1.6.9 (Paso 05)

Revisión de bugs de los overlays y corrección de los dos hallazgos de mayor prioridad: XSS en el widget de Emote Combo y arranque silencioso del servidor de overlays con el puerto ocupado.

---

## Contexto

La revisión cubrió `backend/services/overlay/` (manager, routes, cliente WebSocket) y los HTML/JS de `assets/overlays/`.

- **XSS en Emote Combo.** `_KICK_EMOTE_REGEX` (`backend/utils/emote_utils.py`) acepta cualquier carácter salvo `]` en el nombre del emote, y `widgets/emote_combo.html` lo interpolaba en `innerHTML` (`alt="${emoteName}"`). El combo cuenta repeticiones aunque sean del mismo usuario, así que un solo espectador alcanzaba `min_combo` y ejecutaba JS en el navegador de OBS. El chat, las encuestas y los chatters ya escapaban con `escapeHtml`.
- **Arranque silencioso.** `OverlayServerManager.start()` solo registraba el `OSError` cuando el puerto 8090 estaba ocupado. La app seguía mostrando URLs de overlay muertas (o que apuntaban a otro proceso con otro token) sin avisar.

## Cambios por capa

**Overlays (assets)**
- `overlays/widgets/emote_combo.html`: el `<img>` y el `<span>` del combo se construyen con `createElement`, asignando `alt`, `src` y `textContent`, y se montan con `replaceChildren`. Los datos del chat nunca se interpretan como HTML.

**Backend**
- `services/overlay/overlay_manager.py`: `start()` devuelve `bool`, limpia `server` y `thread` si falla y guarda el mensaje en `start_error`; nueva propiedad `is_running`.

**Frontend**
- `window/startup_coordinator.py`: `_warn_if_overlay_server_down` se ejecuta al inicio de `_finish_settings_hydration` y muestra un toast de error (8 s) con el puerto afectado.
- `assets/i18n/{es,en}/main.ftl`: claves `main-toast-overlay_server_down_title` y `main-toast-overlay_server_down_msg`.

**Pruebas**
- `resources/tests/test_overlay_widget_html_safety.py` (nuevo): falla si `emote_combo.html` vuelve a interpolar `emoteName` o `emoteSrc` dentro de `innerHTML`.
- `resources/tests/test_overlay_server_start.py` (nuevo): `start()` devuelve `False` con el puerto ocupado y `True` con uno libre, limpiando `start_error`.

## Archivos afectados

`assets/overlays/widgets/emote_combo.html`, `backend/services/overlay/overlay_manager.py`, `frontend/window/startup_coordinator.py`, `assets/i18n/es/main.ftl`, `assets/i18n/en/main.ftl`, `resources/tests/test_overlay_widget_html_safety.py`, `resources/tests/test_overlay_server_start.py`.

## Verificación

- `pytest` sobre los dos archivos nuevos, `test_overlay_client_diagnostics.py`, `test_chat_overlay_load_limits.py` y `test_startup_coordinator.py`: 18 en verde. El test del widget falla sin el cambio del HTML.
- `resources/tools/project_quality_suite.py --quick`: 13 auditores en PASS; `Frontend QSS Roles` y `Frontend Qt Windows` fallan igual que en el commit base `6b01cdcb`.
- No se probó visualmente en OBS ni con una instancia real de MiniKick ocupando el puerto.

## Notas

Hallazgos de la revisión que **no** se corrigen en este paso:

- `alerts.html:793` hace `innerHTML = formatted_text` y `alerts_service._format_template` no escapa `display_name` ni `message`; es explotable si la plantilla incluye `{message}` o si el nombre viene de YouTube/TikTok.
- `widgets/clock.html` abre el WebSocket sin `onclose` ni reconexión.
- `_handle_websocket_upgrade` responde 101 antes de validar el topic; un topic desconocido queda conectado sin recibir eventos.
- `WebSocketClient.read_frame` lee `payload_len` sin límite (hasta 2⁶⁴).
- `trigger_alert` registra el directorio completo de un alert `.html` como media servida.
- Código muerto probable: endpoints SSE (`/events`, `/chat_events`, `/music_events`, `/widget_events`) y las listas `clients`/`alert_clients`.
