# WT-1.5.9_01 — Fix: TikTok WebSocket `InvalidStatusCode: HTTP 400`

**Versión:** v1.5.9  
**Fecha:** 2026-09-10  
**Reportado por:** JosueGMN (via log `minikick_JosueGMN_v1.5.8.log`)  
**Prioridad:** Alta — el error impide conectar TikTok Live por completo

---

## Problema

Al intentar conectar el chat de TikTok Live, el app lanzaba:

```
[ERROR] [TikTokChatProvider] Excepción general de conexión (InvalidStatusCode):
server rejected WebSocket connection: HTTP 400
```

El error ocurría consistentemente cuando el stream estaba activo y el usuario intentaba
conectar (especialmente luego de un intento fallido previo por `UserOfflineError`).

## Causa raíz

`TikTokLive v7.0.0` usa un **sign server externo** (`api.eulerstream.com`) para obtener
una URL de WebSocket firmada. Esta URL **expira en ~30 segundos**.

El flujo que producía el 400:

1. `start_chat()` llamado
2. `fetch_room_id_from_html()` (~2–5 s)
3. `fetch_is_live()` (~1–2 s)
4. `fetch_signed_websocket()` — URL firmada válida por ~30 s
5. [demora acumulada > 30 s]
6. WebSocket connect — TikTok responde HTTP 400 (token expirado)

El problema se amplificaba porque el código anterior capturaba `InvalidStatusCode`
dentro del `except Exception` genérico, sin retry ni mensaje claro al usuario.

---

## Cambios implementados

### `backend/providers/chat/tiktok_chat_provider.py`

**Constantes de clase:** `_WS_MAX_RETRIES = 2` y `_WS_RETRY_DELAY = 5.0`

**Nuevo método `_build_client()`:** Extrae la construcción del `TikTokLiveClient` y el
registro de handlers. El counter `msg_seq` se pasa como `list[int]` (holder mutable) para
ser continuo entre reintentos.

**Retry loop en `start_chat()`:**
- Máx. 3 intentos totales (2 reintentos)
- En cada intento se recrea el cliente completo → fresh sign-server call → URL no expirada
- 5 segundos de espera entre intentos
- Jerarquía de excepciones de más específico a más genérico (Guard Clause pattern)

### `locales/en.json` y `locales/es.json`

Nuevas claves bajo `logs.tiktok`:
- `ws_rejected_400` — notificación de reintento (warn)
- `ws_rejected_400_final` — error final tras agotar reintentos
- `ws_rejected` — otros códigos HTTP del WebSocket

---

## Verificación

- Sintaxis Python: OK
- JSON locales: OK
- Zero hardcoded strings: OK
- SoR: retry en provider (infra), no en worker (aplicación)
- SRP: `_build_client()` tiene un solo propósito
