# Walkthrough Técnico - v1.6.3 / WT-1.6.3_03

**Versión**: v1.6.3
**Fecha**: 2026-10-09
**Origen**: "Plan 1 — Correcciones y refactor del backend". Alcance de este documento: **Fase 1 (Seguridad)** completa (tareas 1.1 a 1.6).
**Nota de proceso**: este walkthrough sustituye al archivo `NOTAS_PLAN1.md` (eliminado). Las Fases 2 y 3 generarán sus propios walkthroughs (`WT-1.6.3_04`, etc.).

---

## Novedades

### Cifrado de tokens OAuth en reposo

Los tokens se guardaban en texto plano en la tabla `tokens`. Ahora se cifran con la DPAPI de Windows
(`CryptProtectData`) mediante un cifrador inyectado, con migración transparente de los valores heredados.

- `backend/interfaces/i_secrets.py`: Protocol `SecretCipher` (`encrypt`/`decrypt`).
- `backend/services/system/secret_cipher.py`: `DPAPISecretCipher` (Windows, vía `ctypes`, sin dependencias
  nuevas) y `NoOpSecretCipher` (otros sistemas, con aviso único), más `create_secret_cipher()`.
- `backend/database/encrypted_token_storage.py`: `EncryptedTokenStorage`, decorador de `TokenStorage` que
  cifra `access_token` y `refresh_token` (prefijo `enc:v1:`) y migra en sitio los valores sin prefijo.
- Cableado en `AppContainerCore`, sin cambios en `KickAuthManager`/`TwitchAuthManager`.

### Nuevas capacidades del servidor de overlays

- `OverlayServerManager.register_media_root(path)`: autoriza el directorio de un archivo multimedia.
- `OverlayServerManager.regenerate_token()`: genera y persiste un nuevo token de sesión (método listo; sin
  botón de UI en esta fase, según el plan).

---

## Mejoras

### OAuth: protección CSRF con `state` por intento (1.1)

Las URLs de autorización de Kick y Twitch usaban `&state=random` fijo. Ahora cada intento genera
`secrets.token_urlsafe(32)`, se pasa a `OAuthCallbackServer.capture_auth_code(..., expected_state=...)` y el
callback solo acepta el `code` si el `state` coincide, usando `hmac.compare_digest`. En caso de discrepancia
se registra `logger.warning`, la página responde como error y no se captura el código.

### OAuth: callback solo en localhost y HTML escapado (1.2)

El servidor de callback se abría en `("", port)` (todas las interfaces). Ahora escucha en `("127.0.0.1", port)`.
Además, `provider`, `status` y `error_msg` (que proviene de la query) se escapan con `html.escape()` antes de
sustituirse en la plantilla `auth.html`, incluido el HTML de respaldo.

### Base de datos: recuperación de corrupción sin pérdida de datos (1.3)

`_handle_corrupt_database` borraba `.db`, `-wal` y `-shm`. Ahora los **renombra** a
`minikick.db.corrupt-YYYYmmdd-HHMMSS` (conservando solo los 3 más recientes) y registra la ruta con
`logger.error`. Se centraliza la detección en `_is_corruption_error(e)` (única fuente de verdad) y se extrae
`_open_connection()` para que el camino normal y el de recuperación compartan los mismos `PRAGMA`.

### Servidor de overlays: allowlist de medios y comparación de token (1.5)

- `allowed_media_roots` + `register_media_root()`; los generadores de URLs (`trigger_rewards`, `trigger_alert`)
  registran la raíz del archivo antes de emitir el overlay.
- Helper único `_is_allowed_media(manager, target)` con `os.path.realpath` + `os.path.commonpath` (captura
  `ValueError` por unidades distintas en Windows). `/media` y `/user_media` pasan por él; en `/user_media` el
  directorio decodificado debe ser una raíz permitida o se responde 403.
- El fallback de archivos estáticos usa `commonpath` en lugar de `startswith` (sibling-safe).
- El token de sesión se compara con `hmac.compare_digest` mediante `_token_ok()`.

---

## Correcciones

Bugs encontrados durante la ejecución del plan (se aplican en el mismo cambio por bloquear la funcionalidad):

1. **`DPAPISecretCipher`: `LocalFree` sin `argtypes`.** `kernel32.LocalFree` se resolvía como entero de 32 bits
   y truncaba el puntero de 64 bits devuelto por `CryptProtectData` (`OverflowError: int too long to convert`).
   Habría fallado en cualquier login real en Windows. Corregido fijando `argtypes=[c_void_p]` y
   `restype=c_void_p`. Detectado por el test de roundtrip.
2. **BD: la recuperación no marcaba la base como inicializada.** El camino de corrupción no añadía la ruta a
   `_initialized_dbs`, provocando reintentos de inicialización en cada `DatabaseManager()`.
3. **`_is_corruption_error` no reconocía `"file is not a database"`.** Un archivo con basura (no solo truncado)
   no se clasificaba como corrupción; se añadió el keyword.
4. **Conexiones sin `factory=AutoCloseConnection` en `_initialize_database`.** `with sqlite3.connect(...)` no
   cierra la conexión (solo hace commit/rollback); se usó la fábrica en los tres puntos.

---

## Bitácora de ejecución

### Fase 3.0 — Medición inicial (baseline)

```
imports de frontend desde backend:        7
PySide6 en services/providers/handlers:  11

wc -l (antes de Fase 1 → después):
  backend/core/main_window_core.py            1930
  backend/controllers/chat_controller.py      1241
  backend/database/database_manager.py         983 → 1036
  backend/services/auth/auth_service.py        353 →  381
  backend/services/overlay/overlay_routes.py   426 →  458
  backend/services/overlay/overlay_manager.py  282 →  316
```

### Discrepancia de proceso (rama y commits)

El plan asume la rama `main` limpia con un commit por tarea. La copia de trabajo está en
`release/v1.6.3` con el árbol sucio, incluidos cambios ya en el índice (`locales/en.json`, `locales/es.json`
reordenados por `i18n_manager`, `docs/historial_crashes_y_errores.md`, `docs/walkthroughs/v1.6.3/WT-1.6.3_02.md`,
`backend/controllers/widgets_controller.py`, `backend/providers/chat/kick_ws_provider.py`). Por ello **no se
crearon commits** automáticamente (un `git commit` arrastraría cambios staged ajenos al plan). Se recomienda
crear una rama dedicada (por ejemplo `bionic/plan1-seguridad`) desde el punto limpio deseado y commitear por
tarea.

---

## Informe Fase 1.6 — Secretos empaquetados

### (a) Dónde se usa cada secreto

| Secreto (en `backend/config/api_keys.py`, gitignored) | Usado en |
|---|---|
| `KICK_CLIENT_SECRET` | `backend/core/app_container_core.py` (construcción de `KickAuthManager`); `backend/services/auth/auth_service.py` (exchange y refresh). |
| `TWITCH_CLIENT_SECRET` | `backend/core/app_container_core.py`; `backend/services/auth/auth_service.py`. |
| `DISCORD_WEBHOOK_URL` | `backend/workers/bug_report_worker.py`; `backend/workers/crash_report_worker.py`. |
| `SIGN_API_KEY` | `backend/providers/chat/tiktok_provider.py`. |
| `GIPHY_API_KEY`, `KICK_PUSHER_KEY`, `KICK_PUSHER_CLUSTER` | `giphy_service`, `kick_ws_provider`/`kick_provider` (clave Pusher con plan propio: `plan_2_pusher_kick.md`). |

`api_keys.py` está en `.gitignore` pero **PyInstaller lo incluye en el `.exe`**, por lo que los secretos son
extraíbles del binario distribuido.

### (b) ¿Kick/Twitch permiten el flujo sin `client_secret` (PKCE público)?

- **Kick**: usa OAuth 2.1 con PKCE, pero la documentación oficial marca `client_secret` como **obligatorio** en
  `POST /oauth/token`. No hay flujo público sin secreto documentado.
- **Twitch**: el *authorization code grant* **exige `client_secret`** y Twitch **no admite PKCE** en ese flujo.
  La vía pública es el **Device Code Flow** (app registrada como *Public*), con tokens de refresco de un solo
  uso y expiración de 30 días.

Fuentes: [docs.kick.com — OAuth 2.1](https://docs.kick.com/getting-started/generating-tokens-oauth2-flow.md),
[dev.twitch.tv — Getting OAuth Access Tokens](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/),
[Twitch Dev Forums — PKCE en app nativa](https://discuss.dev.twitch.com/t/auth-flow-for-native-application-without-a-backend-server/64539).

### (c) Opciones recomendadas (sin cambios de código en esta fase)

1. **Proxy propio de intercambio de tokens** (recomendado para Kick y Twitch): el cliente envía `code` +
   `code_verifier` a un endpoint HTTPS propio; el backend hace el intercambio con el secreto y devuelve el token.
2. **Device Code Flow para Twitch** si se prioriza un cliente público sin backend.
3. **Webhook/API key (Discord / SIGN)**: mover el envío a un proxy propio para no distribuir esas claves.
4. **Mitigación inmediata**: rotar los secretos actuales y confirmar que `api_keys.py` nunca se commitea.

> Aviso de seguridad operativa: en esta sesión se leyó `backend/config/api_keys.py`. Se recomienda **rotar**
> `KICK_CLIENT_SECRET`, `TWITCH_CLIENT_SECRET`, `DISCORD_WEBHOOK_URL` y `SIGN_API_KEY` si el repositorio o los
> binarios se han compartido.

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| backend/services/auth/auth_service.py | Mejora - `state` por intento + validación; bind 127.0.0.1; HTML escapado |
| backend/database/database_manager.py | Mejora/Corrección - respaldo de BD corrupta, helper de corrupción, conexión PRAGMA compartida |
| backend/services/overlay/overlay_manager.py | Mejora - allowlist de medios, `regenerate_token` |
| backend/services/overlay/overlay_routes.py | Mejora - `_is_allowed_media`, `commonpath`, `compare_digest` |
| backend/core/app_container_core.py | Mejora - cableado de cifrado de tokens |
| backend/interfaces/i_secrets.py | Nuevo - Protocol `SecretCipher` |
| backend/interfaces/__init__.py | Mejora - export de `SecretCipher` |
| backend/services/system/secret_cipher.py | Nuevo - DPAPI + NoOp + factory |
| backend/services/system/__init__.py | Mejora - exports de cifrado |
| backend/database/encrypted_token_storage.py | Nuevo - decorador de cifrado de tokens |
| backend/database/__init__.py | Mejora - export de `EncryptedTokenStorage` |

---

## Pruebas

- `resources/tests/test_db_corruption_recovery.py` (2 casos): respaldo `.corrupt-*` en vez de borrado y BD sana sin respaldo.
- `resources/tests/test_encrypted_token_storage.py` (6 casos): cifrado selectivo, roundtrip, migración de texto plano, fallo de descifrado y factory de cifrador.
- `resources/tests/test_overlay_media_security.py` (4 casos): `commonpath` sibling-safe, allowlist, ausencia de raíces y bloqueo de traversal.
- Regresión completa: `resources/tests` en **180 pruebas superadas**. Los 2 fallos restantes
  (`test_daily_top_chatters.py::test_sqlite_widgets_storage_pruning` por fecha hardcodeada y
  `test_linux_auth_and_toast.py::test_modern_toast_dynamic_geometry_scaling` por geometría de fuente) son
  **preexistentes y ajenos** a esta fase.

---

## Pendiente / fuera de alcance

- Fases 2 (fiabilidad e higiene) y 3 (arquitectura) del plan: no iniciadas.
- Verificación manual interactiva exigida por el plan (login Kick/Twitch, reward con archivo local, overlays en
  el navegador): no ejecutada en esta sesión.
- Botón de UI para `regenerate_token()` (el plan pide dejar solo el método en Fase 1).
