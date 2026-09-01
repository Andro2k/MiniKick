# Walkthrough: Corrección de Crash en Inicio por Sesión/Token de Twitch Expirado

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_02.md`  
**Módulos Modificados:**
- [`backend/providers/chat/twitch_client.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_client.py)
- [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
- [`resources/tests/unit/providers/test_twitch_websocket.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/providers/test_twitch_websocket.py)

---

## 1. Resumen del Problema y Causa Raíz

Cuando un usuario tenía configurado el inicio automático (`autostart_enabled = True`) y su sesión previa de Twitch caducaba o era revocada por Twitch:
1. `_load_settings_into_ui` invocaba `_on_twitch_auth_success(twitch_tokens)` directamente dentro del constructor `__init__`.
2. La API Helix de Twitch respondía `HTTP 401 Unauthorized`.
3. Al intentar refrescar el token contra `https://id.twitch.tv/oauth2/token`, Twitch devolvía `HTTP 400 Bad Request` debido a la caducidad del refresh token.
4. `TwitchAPIClient.fetch_user_data` ejecutaba `raise_for_status()`, arrojando una excepción `requests.exceptions.HTTPError`.
5. Al no existir captura de excepciones en `fetch_full_channel_info`, `_on_twitch_auth_success` ni en `_load_settings_into_ui`, la excepción abortaba la inicialización del programa provocando un crash fatal.

---

## 2. Cambios Implementados

1. **Blindaje en `TwitchAPIClient.fetch_full_channel_info` (`twitch_client.py`)**:
   - Se envolvió la llamada a `self.fetch_user_data()` en un bloque `try...except Exception`. Si la solicitud falla o no está autorizado, se registra una advertencia en log y retorna un diccionario `{}` sin propagar excepciones no controladas.

2. **Control Seguro en `MainWindowCore._on_twitch_auth_success` (`main_window_core.py`)**:
   - Se protegió todo el bloque de conexión e inicialización de workers de Twitch en un `try...except Exception`.
   - En caso de fallo o datos vacíos, restablece `_twitch_connected = False`, actualiza el estado de las integraciones en la interfaz y muestra un toast de error no bloqueante.

3. **Protección Integral en Autoinicio (`_load_settings_into_ui`)**:
   - Cada inicialización de integración en el arranque (Kick, Twitch, YouTube, TikTok) ahora cuenta con captura de errores individualizada. Si una plataforma falla, las demás continúan iniciando normalmente y la aplicación se abre con éxito.

4. **Pruebas Automatizadas de Resiliencia (`test_twitch_websocket.py`)**:
   - Se añadió `test_twitch_api_client_fetch_full_channel_info_resilience_on_401` para certificar que respuestas 401 con fallo en el refresco retornan `{}` limpiamente sin excepciones no controladas.

---

## 3. Verificación y Resultados

```powershell
uv run pytest resources/tests/unit/providers/test_twitch_websocket.py
```
- **11/11 tests aprobados (100% PASSED)** incluyendo la prueba de resiliencia frente a tokens expirados 401/400.
